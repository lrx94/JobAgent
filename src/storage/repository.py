import json

from src.domain import Job
from src.storage.database import get_connection


class JobRepository:
    """Repository d'accès aux offres d'emploi."""

    def save(self, job: Job) -> None:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR REPLACE INTO jobs (
                title,
                company,
                location,
                description,
                source,
                url,
                score,
                matched_skills,
                missing_skills
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.title,
                job.company,
                job.location,
                job.description,
                job.source,
                job.url,
                job.score,
                json.dumps(job.matched_skills),
                json.dumps(job.missing_skills),
            ),
        )

        conn.commit()
        conn.close()

    def exists(self, url: str) -> bool:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT 1 FROM jobs WHERE url = ? LIMIT 1",
            (url,),
        )

        exists = cur.fetchone() is not None

        conn.close()

        return exists

    def get_all(self) -> list[Job]:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM jobs
            ORDER BY score DESC
            """
        )

        rows = cur.fetchall()

        conn.close()

        return [self._row_to_job(row) for row in rows]

    def get_by_source(self, source: str) -> list[Job]:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM jobs
            WHERE source = ?
            ORDER BY score DESC
            """,
            (source,),
        )

        rows = cur.fetchall()

        conn.close()

        return [self._row_to_job(row) for row in rows]

    def count(self) -> int:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM jobs")

        total = cur.fetchone()[0]

        conn.close()

        return total

    def delete(self, url: str) -> None:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM jobs WHERE url = ?",
            (url,),
        )

        conn.commit()
        conn.close()

    def clear(self) -> None:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM jobs")

        conn.commit()
        conn.close()

    @staticmethod
    def _row_to_job(row) -> Job:
        return Job(
            title=row["title"],
            company=row["company"],
            location=row["location"],
            description=row["description"],
            source=row["source"],
            url=row["url"],
            salary=0,
            remote=False,
            score=row["score"],
            matched_skills=json.loads(row["matched_skills"] or "[]"),
            missing_skills=json.loads(row["missing_skills"] or "[]"),
        )
        