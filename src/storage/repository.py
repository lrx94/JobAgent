import json

from src.storage.database import get_connection


class JobRepository:

    def save(self, job):

        conn = get_connection()

        cur = conn.cursor()

        cur.execute("""

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

        VALUES(?,?,?,?,?,?,?,?,?)

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

            json.dumps(job.missing_skills)

        )

        )

        conn.commit()

        conn.close()

    def get_all(self):

        conn = get_connection()

        cur = conn.cursor()

        cur.execute("""

        SELECT *

        FROM jobs

        ORDER BY score DESC

        """)

        rows = cur.fetchall()

        conn.close()

        return rows