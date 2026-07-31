from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from src.domain import Job
from src.storage.database import (
    get_connection,
    init_database,
)


class JobRepository:
    """
    Repository SQLite des offres d'emploi canoniques.
    """

    def __init__(self) -> None:
        init_database()

    def save(
        self,
        job: Job,
    ) -> None:
        if not isinstance(job, Job):
            raise TypeError(
                "JobRepository.save attend un objet Job."
            )

        conn = get_connection()

        try:
            cursor = conn.cursor()

            existing_id = self._find_existing_id(
                cursor,
                job,
            )

            values = self._job_values(job)

            if existing_id is None:
                self._insert(
                    cursor,
                    values,
                )
            else:
                self._update(
                    cursor,
                    existing_id,
                    values,
                )

            conn.commit()

        finally:
            conn.close()

    def exists(
        self,
        url: str,
    ) -> bool:
        if not url:
            return False

        conn = get_connection()

        try:
            cursor = conn.cursor()

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
            conn.close()

    def get_all(self) -> list[Job]:
        return self._fetch_jobs(
            """
            SELECT *
            FROM jobs
            ORDER BY score DESC, created_at DESC
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
            ORDER BY score DESC, created_at DESC
            """,
            (source,),
        )

    def count(self) -> int:
        conn = get_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM jobs"
            )

            return int(cursor.fetchone()[0])

        finally:
            conn.close()

    def delete(
        self,
        url: str,
    ) -> None:
        conn = get_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM jobs WHERE url = ?",
                (url,),
            )

            conn.commit()

        finally:
            conn.close()

    def clear(self) -> None:
        conn = get_connection()

        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM jobs")
            conn.commit()

        finally:
            conn.close()

    def _fetch_jobs(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[Job]:
        conn = get_connection()

        try:
            cursor = conn.cursor()
            cursor.execute(query, parameters)
            rows = cursor.fetchall()

            return [
                self._row_to_job(row)
                for row in rows
            ]

        finally:
            conn.close()

    @staticmethod
    def _find_existing_id(
        cursor,
        job: Job,
    ) -> int | None:
        if job.external_id:
            cursor.execute(
                """
                SELECT id
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
                return int(row["id"])

        if job.url:
            cursor.execute(
                """
                SELECT id
                FROM jobs
                WHERE url = ?
                LIMIT 1
                """,
                (job.url,),
            )

            row = cursor.fetchone()

            if row is not None:
                return int(row["id"])

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
                ensure_ascii=False,
            ),
            "languages": json.dumps(
                job.languages,
                ensure_ascii=False,
            ),
            "experience_level": (
                job.experience_level
            ),
            "experience_years": (
                job.experience_years
            ),
            "raw_data": json.dumps(
                job.raw_data,
                ensure_ascii=False,
            ),
            "score": job.score,
            "matched_skills": json.dumps(
                job.matched_skills,
                ensure_ascii=False,
            ),
            "missing_skills": json.dumps(
                job.missing_skills,
                ensure_ascii=False,
            ),
            "match_details": json.dumps(
                job.match_details,
                ensure_ascii=False,
            ),
            "explanation": job.explanation,
        }

    @staticmethod
    def _insert(
        cursor,
        values: dict[str, Any],
    ) -> None:
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
            return (
                row[name]
                if name in keys
                and row[name] is not None
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
            source=value("source", "Inconnu"),
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
            score=float(value("score", 0)),
            matched_skills=(
                JobRepository._parse_json_list(
                    value("matched_skills", "[]")
                )
            ),
            missing_skills=(
                JobRepository._parse_json_list(
                    value("missing_skills", "[]")
                )
            ),
            match_details=(
                JobRepository._parse_json_dict(
                    value("match_details", "{}")
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
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_json_list(
        value: str | None,
    ) -> list[str]:
        try:
            decoded = json.loads(value or "[]")
        except (TypeError, json.JSONDecodeError):
            return []

        return decoded if isinstance(decoded, list) else []

    @staticmethod
    def _parse_json_dict(
        value: str | None,
    ) -> dict[str, Any]:
        try:
            decoded = json.loads(value or "{}")
        except (TypeError, json.JSONDecodeError):
            return {}

        return decoded if isinstance(decoded, dict) else {}