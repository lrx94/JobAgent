from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from src.domain import Job
from src.storage.database import (
    get_connection,
    init_database,
)
from src.storage.save_result import (
    RepositorySaveResult,
)
from src.utils.json_utils import json_dumps

class JobRepository:
    """
    Repository SQLite des offres d'emploi canoniques.

    La sauvegarde distingue désormais :

    - inserted : première découverte ;
    - updated : contenu métier modifié ;
    - unchanged : offre déjà connue sans changement.
    """

    def __init__(self) -> None:
        init_database()

    def save(
        self,
        job: Job,
    ) -> RepositorySaveResult:
        """
        Insère ou actualise une offre.

        La modification de `collected_at` seule ne transforme pas
        une offre inchangée en offre mise à jour.
        """

        if not isinstance(job, Job):
            raise TypeError(
                "JobRepository.save attend un objet Job."
            )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            existing_row = self._find_existing_row(
                cursor,
                job,
            )

            values = self._job_values(job)
            content_hash = self._content_hash(values)
            now = datetime.now().isoformat()

            if existing_row is None:
                result = self._insert_new_job(
                    cursor=cursor,
                    job=job,
                    values=values,
                    content_hash=content_hash,
                    now=now,
                )
            else:
                result = self._save_existing_job(
                    cursor=cursor,
                    job=job,
                    existing_row=existing_row,
                    values=values,
                    content_hash=content_hash,
                    now=now,
                )

            connection.commit()

            return result

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def exists(
        self,
        url: str,
    ) -> bool:
        if not url:
            return False

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT 1
                FROM jobs
                WHERE url = ?
                LIMIT 1
                """,
                (url,),
            )

            return cursor.fetchone() is not None

        finally:
            connection.close()

    def get_all(self) -> list[Job]:
        return self._fetch_jobs(
            """
            SELECT *
            FROM jobs
            ORDER BY score DESC,
                     first_seen_at DESC,
                     id DESC
            """
        )

    def get_by_source(
        self,
        source: str,
    ) -> list[Job]:
        return self._fetch_jobs(
            """
            SELECT *
            FROM jobs
            WHERE source = ?
            ORDER BY score DESC,
                     first_seen_at DESC,
                     id DESC
            """,
            (source,),
        )

    def get_new_jobs(
        self,
        days: int = 1,
    ) -> list[Job]:
        """
        Retourne les offres découvertes dans la période donnée.
        """

        threshold = self._threshold(days)

        return self._fetch_jobs(
            """
            SELECT *
            FROM jobs
            WHERE first_seen_at >= ?
            ORDER BY first_seen_at DESC,
                     score DESC,
                     id DESC
            """,
            (threshold,),
        )

    def get_updated_jobs(
        self,
        days: int = 1,
    ) -> list[Job]:
        """
        Retourne les offres réellement modifiées récemment.
        """

        threshold = self._threshold(days)

        return self._fetch_jobs(
            """
            SELECT *
            FROM jobs
            WHERE last_action = 'updated'
              AND updated_at >= ?
            ORDER BY updated_at DESC,
                     score DESC,
                     id DESC
            """,
            (threshold,),
        )

    def get_recent_jobs(
        self,
        days: int = 7,
    ) -> list[Job]:
        """
        Retourne les offres observées pendant la période.
        """

        threshold = self._threshold(days)

        return self._fetch_jobs(
            """
            SELECT *
            FROM jobs
            WHERE last_seen_at >= ?
            ORDER BY last_seen_at DESC,
                     score DESC,
                     id DESC
            """,
            (threshold,),
        )

    def get_best_jobs(
        self,
        limit: int = 20,
        minimum_score: float = 0,
    ) -> list[Job]:
        """
        Retourne les meilleures offres enregistrées.
        """

        normalized_limit = max(
            1,
            int(limit),
        )

        return self._fetch_jobs(
            """
            SELECT *
            FROM jobs
            WHERE score >= ?
            ORDER BY score DESC,
                     last_seen_at DESC,
                     id DESC
            LIMIT ?
            """,
            (
                float(minimum_score),
                normalized_limit,
            ),
        )

    def get_statistics(self) -> dict[str, Any]:
        """
        Produit les statistiques globales de la base.
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_jobs,
                    COALESCE(AVG(score), 0)
                        AS average_score,
                    COALESCE(MAX(score), 0)
                        AS best_score,
                    SUM(
                        CASE
                            WHEN remote_type = 'remote'
                            THEN 1
                            ELSE 0
                        END
                    ) AS remote_jobs,
                    SUM(
                        CASE
                            WHEN score >= 80
                            THEN 1
                            ELSE 0
                        END
                    ) AS excellent_jobs,
                    SUM(
                        CASE
                            WHEN first_seen_at >= ?
                            THEN 1
                            ELSE 0
                        END
                    ) AS new_today,
                    SUM(
                        CASE
                            WHEN last_action = 'updated'
                             AND updated_at >= ?
                            THEN 1
                            ELSE 0
                        END
                    ) AS updated_today
                FROM jobs
                """,
                (
                    self._threshold(1),
                    self._threshold(1),
                ),
            )

            summary_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT
                    source,
                    COUNT(*) AS total,
                    COALESCE(AVG(score), 0)
                        AS average_score,
                    COALESCE(MAX(score), 0)
                        AS best_score
                FROM jobs
                GROUP BY source
                ORDER BY total DESC,
                         source ASC
                """
            )

            source_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT MAX(last_seen_at)
                FROM jobs
                """
            )

            last_sync_row = cursor.fetchone()

            return {
                "total_jobs": int(
                    summary_row["total_jobs"] or 0
                ),
                "average_score": round(
                    float(
                        summary_row["average_score"]
                        or 0
                    ),
                    2,
                ),
                "best_score": float(
                    summary_row["best_score"] or 0
                ),
                "remote_jobs": int(
                    summary_row["remote_jobs"] or 0
                ),
                "excellent_jobs": int(
                    summary_row["excellent_jobs"] or 0
                ),
                "new_today": int(
                    summary_row["new_today"] or 0
                ),
                "updated_today": int(
                    summary_row["updated_today"] or 0
                ),
                "last_sync_at": (
                    last_sync_row[0]
                    if last_sync_row
                    else None
                ),
                "sources": {
                    str(row["source"]): {
                        "total": int(
                            row["total"] or 0
                        ),
                        "average_score": round(
                            float(
                                row["average_score"]
                                or 0
                            ),
                            2,
                        ),
                        "best_score": float(
                            row["best_score"] or 0
                        ),
                    }
                    for row in source_rows
                },
            }

        finally:
            connection.close()

    def get_job_metadata(
        self,
        job: Job,
    ) -> dict[str, Any] | None:
        """
        Retourne les métadonnées historiques d'une offre.
        """

        if not isinstance(job, Job):
            raise TypeError(
                "get_job_metadata attend un objet Job."
            )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            row = self._find_existing_row(
                cursor,
                job,
            )

            if row is None:
                return None

            return {
                "id": int(row["id"]),
                "content_hash": row["content_hash"],
                "first_seen_at": row["first_seen_at"],
                "last_seen_at": row["last_seen_at"],
                "updated_at": row["updated_at"],
                "seen_count": int(
                    row["seen_count"] or 1
                ),
                "last_action": row["last_action"],
            }

        finally:
            connection.close()

    def count(self) -> int:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM jobs"
            )

            return int(cursor.fetchone()[0])

        finally:
            connection.close()

    def delete(
        self,
        url: str,
    ) -> None:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                "DELETE FROM jobs WHERE url = ?",
                (url,),
            )

            connection.commit()

        finally:
            connection.close()

    def clear(self) -> None:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                "DELETE FROM jobs"
            )

            connection.commit()

        finally:
            connection.close()

    def _insert_new_job(
        self,
        cursor,
        job: Job,
        values: dict[str, Any],
        content_hash: str,
        now: str,
    ) -> RepositorySaveResult:
        history_values = {
            **values,
            "content_hash": content_hash,
            "first_seen_at": now,
            "last_seen_at": now,
            "updated_at": now,
            "seen_count": 1,
            "last_action": "inserted",
        }

        job_id = self._insert(
            cursor,
            history_values,
        )

        return RepositorySaveResult(
            action="inserted",
            job_id=job_id,
            identity=job.identity,
            seen_count=1,
        )

    def _save_existing_job(
        self,
        cursor,
        job: Job,
        existing_row,
        values: dict[str, Any],
        content_hash: str,
        now: str,
    ) -> RepositorySaveResult:
        job_id = int(existing_row["id"])

        previous_hash = (
            existing_row["content_hash"]
            or self._row_content_hash(existing_row)
        )

        previous_seen_count = int(
            existing_row["seen_count"] or 1
        )

        seen_count = previous_seen_count + 1

        if previous_hash == content_hash:
            cursor.execute(
                """
                UPDATE jobs
                SET collected_at = ?,
                    last_seen_at = ?,
                    seen_count = ?,
                    last_action = 'unchanged',
                    content_hash = ?
                WHERE id = ?
                """,
                (
                    values["collected_at"],
                    now,
                    seen_count,
                    content_hash,
                    job_id,
                ),
            )

            return RepositorySaveResult(
                action="unchanged",
                job_id=job_id,
                identity=job.identity,
                seen_count=seen_count,
            )

        update_values = {
            **values,
            "content_hash": content_hash,
            "last_seen_at": now,
            "updated_at": now,
            "seen_count": seen_count,
            "last_action": "updated",
        }

        self._update(
            cursor,
            job_id,
            update_values,
        )

        return RepositorySaveResult(
            action="updated",
            job_id=job_id,
            identity=job.identity,
            seen_count=seen_count,
        )

    def _fetch_jobs(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[Job]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                query,
                parameters,
            )

            rows = cursor.fetchall()

            return [
                self._row_to_job(row)
                for row in rows
            ]

        finally:
            connection.close()

    @staticmethod
    def _find_existing_row(
        cursor,
        job: Job,
    ):
        if job.external_id:
            cursor.execute(
                """
                SELECT *
                FROM jobs
                WHERE source = ?
                  AND external_id = ?
                LIMIT 1
                """,
                (
                    job.source,
                    job.external_id,
                ),
            )

            row = cursor.fetchone()

            if row is not None:
                return row

        if job.url:
            cursor.execute(
                """
                SELECT *
                FROM jobs
                WHERE url = ?
                LIMIT 1
                """,
                (job.url,),
            )

            row = cursor.fetchone()

            if row is not None:
                return row

        return None

    @staticmethod
    def _job_values(
        job: Job,
    ) -> dict[str, Any]:
        return {
            "external_id": job.external_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "source": job.source,
            "url": job.url,
            "contract_type": job.contract_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_currency": job.salary_currency,
            "salary_period": job.salary_period,
            "remote_type": job.remote_type,
            "published_at": (
                job.published_at.isoformat()
                if job.published_at
                else None
            ),
            "collected_at": (
                job.collected_at.isoformat()
                if job.collected_at
                else None
            ),
            "skills": json.dumps(
                job.skills,
              
            ),
            "languages": json.dumps(
                job.languages,
                
            ),
            "experience_level": (
                job.experience_level
            ),
            "experience_years": (
                job.experience_years
            ),
            "raw_data": json.dumps(
                job.raw_data,
                
            ),
            "score": job.score,
            "matched_skills": json.dumps(
                job.matched_skills,
               
            ),
            "missing_skills": json.dumps(
                job.missing_skills,
                
            ),
            "match_details": json.dumps(
                job.match_details,
                
            ),
            "explanation": job.explanation,
        }

    @staticmethod
    def _content_hash(
        values: dict[str, Any],
    ) -> str:
        """
        Calcule une empreinte stable du contenu significatif.

        `collected_at` est volontairement exclu : sa modification
        indique une nouvelle observation, pas une modification.
        """

        content = {
            key: value
            for key, value in values.items()
            if key != "collected_at"
        }

        serialized = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    @classmethod
    def _row_content_hash(
        cls,
        row,
    ) -> str:
        keys = set(row.keys())

        values = {
            column: (
                row[column]
                if column in keys
                else None
            )
            for column in (
                "external_id",
                "title",
                "company",
                "location",
                "description",
                "source",
                "url",
                "contract_type",
                "salary_min",
                "salary_max",
                "salary_currency",
                "salary_period",
                "remote_type",
                "published_at",
                "collected_at",
                "skills",
                "languages",
                "experience_level",
                "experience_years",
                "raw_data",
                "score",
                "matched_skills",
                "missing_skills",
                "match_details",
                "explanation",
            )
        }

        return cls._content_hash(values)

    @staticmethod
    def _insert(
        cursor,
        values: dict[str, Any],
    ) -> int:
        columns = ", ".join(values.keys())

        placeholders = ", ".join(
            "?"
            for _ in values
        )

        cursor.execute(
            f"""
            INSERT INTO jobs ({columns})
            VALUES ({placeholders})
            """,
            tuple(values.values()),
        )

        return int(cursor.lastrowid)

    @staticmethod
    def _update(
        cursor,
        job_id: int,
        values: dict[str, Any],
    ) -> None:
        assignments = ", ".join(
            f"{column} = ?"
            for column in values
        )

        cursor.execute(
            f"""
            UPDATE jobs
            SET {assignments}
            WHERE id = ?
            """,
            (
                *values.values(),
                job_id,
            ),
        )

    @staticmethod
    def _row_to_job(row) -> Job:
        keys = set(row.keys())

        def value(
            name: str,
            default=None,
        ):
            if name not in keys:
                return default

            row_value = row[name]

            return (
                row_value
                if row_value is not None
                else default
            )

        return Job(
            external_id=value("external_id"),
            title=value("title", ""),
            company=value(
                "company",
                "Entreprise inconnue",
            ),
            location=value(
                "location",
                "Localisation non précisée",
            ),
            description=value(
                "description",
                "",
            ),
            source=value(
                "source",
                "Inconnu",
            ),
            url=value("url"),
            contract_type=value("contract_type"),
            salary_min=value("salary_min"),
            salary_max=value("salary_max"),
            salary_currency=value(
                "salary_currency",
                "EUR",
            ),
            salary_period=value(
                "salary_period",
                "unknown",
            ),
            remote_type=value(
                "remote_type",
                "unknown",
            ),
            published_at=JobRepository._parse_datetime(
                value("published_at")
            ),
            collected_at=(
                JobRepository._parse_datetime(
                    value("collected_at")
                )
                or datetime.now()
            ),
            skills=JobRepository._parse_json_list(
                value("skills", "[]")
            ),
            languages=JobRepository._parse_json_list(
                value("languages", "[]")
            ),
            experience_level=value(
                "experience_level"
            ),
            experience_years=value(
                "experience_years"
            ),
            raw_data=JobRepository._parse_json_dict(
                value("raw_data", "{}")
            ),
            score=float(
                value("score", 0)
            ),
            matched_skills=(
                JobRepository._parse_json_list(
                    value(
                        "matched_skills",
                        "[]",
                    )
                )
            ),
            missing_skills=(
                JobRepository._parse_json_list(
                    value(
                        "missing_skills",
                        "[]",
                    )
                )
            ),
            match_details=(
                JobRepository._parse_json_dict(
                    value(
                        "match_details",
                        "{}",
                    )
                )
            ),
            explanation=value(
                "explanation",
                "",
            ),
        )

    @staticmethod
    def _parse_datetime(
        value: str | None,
    ) -> datetime | None:
        if not value:
            return None

        try:
            return datetime.fromisoformat(
                str(value)
            )
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_json_list(
        value: str | None,
    ) -> list[str]:
        try:
            decoded = json.loads(
                value or "[]"
            )
        except (
            TypeError,
            json.JSONDecodeError,
        ):
            return []

        return (
            decoded
            if isinstance(decoded, list)
            else []
        )

    @staticmethod
    def _parse_json_dict(
        value: str | None,
    ) -> dict[str, Any]:
        try:
            decoded = json.loads(
                value or "{}"
            )
        except (
            TypeError,
            json.JSONDecodeError,
        ):
            return {}

        return (
            decoded
            if isinstance(decoded, dict)
            else {}
        )

    @staticmethod
    def _threshold(
        days: int,
    ) -> str:
        normalized_days = max(
            0,
            int(days),
        )

        return (
            datetime.now()
            - timedelta(days=normalized_days)
        ).isoformat()