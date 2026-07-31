from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("data/jobagent.db")


JOB_COLUMNS: dict[str, str] = {
    "external_id": "TEXT",
    "contract_type": "TEXT",
    "salary_min": "INTEGER",
    "salary_max": "INTEGER",
    "salary_currency": "TEXT DEFAULT 'EUR'",
    "salary_period": "TEXT DEFAULT 'unknown'",
    "remote_type": "TEXT DEFAULT 'unknown'",
    "published_at": "TEXT",
    "collected_at": "TEXT",
    "skills": "TEXT DEFAULT '[]'",
    "languages": "TEXT DEFAULT '[]'",
    "experience_level": "TEXT",
    "experience_years": "INTEGER",
    "raw_data": "TEXT DEFAULT '{}'",
    "match_details": "TEXT DEFAULT '{}'",
    "explanation": "TEXT DEFAULT ''",
}


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


def init_database() -> None:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                external_id TEXT,

                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                description TEXT,
                source TEXT NOT NULL,
                url TEXT UNIQUE,

                contract_type TEXT,

                salary_min INTEGER,
                salary_max INTEGER,
                salary_currency TEXT DEFAULT 'EUR',
                salary_period TEXT DEFAULT 'unknown',

                remote_type TEXT DEFAULT 'unknown',

                published_at TEXT,
                collected_at TEXT,

                skills TEXT DEFAULT '[]',
                languages TEXT DEFAULT '[]',

                experience_level TEXT,
                experience_years INTEGER,

                raw_data TEXT DEFAULT '{}',

                score REAL DEFAULT 0,
                matched_skills TEXT DEFAULT '[]',
                missing_skills TEXT DEFAULT '[]',
                match_details TEXT DEFAULT '{}',
                explanation TEXT DEFAULT '',

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        _migrate_existing_jobs_table(
            conn
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_jobs_source_external_id
            ON jobs(source, external_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_jobs_score
            ON jobs(score DESC)
            """
        )

        conn.commit()

    finally:
        conn.close()


def _migrate_existing_jobs_table(
    conn: sqlite3.Connection,
) -> None:
    cursor = conn.cursor()

    cursor.execute(
        "PRAGMA table_info(jobs)"
    )

    existing_columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    for column_name, column_definition in (
        JOB_COLUMNS.items()
    ):
        if column_name in existing_columns:
            continue

        cursor.execute(
            f"""
            ALTER TABLE jobs
            ADD COLUMN {column_name}
            {column_definition}
            """
        )