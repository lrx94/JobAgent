import json

from src.storage.database import get_connection


class JobRepository:

    def save(self, job):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR REPLACE INTO jobs(
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

    def exists(self, url):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT 1 FROM jobs WHERE url = ? LIMIT 1",
            (url,),
        )

        exists = cur.fetchone() is not None

        conn.close()

        return exists

    def get_all(self):

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

        return rows

    def get_by_source(self, source):

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

        return rows

    def count(self):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM jobs")

        total = cur.fetchone()[0]

        conn.close()

        return total

    def delete(self, url):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM jobs WHERE url = ?",
            (url,),
        )

        conn.commit()
        conn.close()

    def clear(self):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM jobs")

        conn.commit()
        conn.close()
        