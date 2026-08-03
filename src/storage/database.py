from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Final


DB_PATH: Path = Path("data/jobagent.db")


JOB_COLUMNS: Final[dict[str, str]] = {
    "external_id": "TEXT",
    "title": "TEXT NOT NULL DEFAULT ''",
    "company": "TEXT NOT NULL DEFAULT ''",
    "location": "TEXT NOT NULL DEFAULT ''",
    "description": "TEXT NOT NULL DEFAULT ''",
    "source": "TEXT NOT NULL DEFAULT ''",
    "url": "TEXT",
    "contract_type": "TEXT",
    "salary_min": "INTEGER",
    "salary_max": "INTEGER",
    "salary_currency": (
        "TEXT NOT NULL DEFAULT 'EUR'"
    ),
    "salary_period": (
        "TEXT NOT NULL DEFAULT 'unknown'"
    ),
    "remote_type": (
        "TEXT NOT NULL DEFAULT 'unknown'"
    ),
    "published_at": "TEXT",
    "collected_at": "TEXT",
    "skills": "TEXT NOT NULL DEFAULT '[]'",
    "languages": "TEXT NOT NULL DEFAULT '[]'",
    "experience_level": "TEXT",
    "experience_years": "INTEGER",
    "raw_data": "TEXT NOT NULL DEFAULT '{}'",
    "score": "REAL NOT NULL DEFAULT 0",
    "matched_skills": (
        "TEXT NOT NULL DEFAULT '[]'"
    ),
    "missing_skills": (
        "TEXT NOT NULL DEFAULT '[]'"
    ),
    "match_details": (
        "TEXT NOT NULL DEFAULT '{}'"
    ),
    "explanation": "TEXT NOT NULL DEFAULT ''",
    "content_hash": "TEXT",
    "first_seen_at": "TEXT",
    "last_seen_at": "TEXT",
    "updated_at": "TEXT",
    "seen_count": "INTEGER NOT NULL DEFAULT 1",
    "last_action": (
        "TEXT NOT NULL DEFAULT 'inserted'"
    ),
    "created_at": (
        "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    ),
}


def get_connection() -> sqlite3.Connection:
    """
    Ouvre une connexion SQLite configurée pour JobAgent.
    """

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    connection.execute(
        "PRAGMA busy_timeout = 5000"
    )

    return connection


def init_database() -> None:
    """
    Initialise la base et applique les migrations compatibles.

    Cette fonction peut être appelée plusieurs fois sans risque.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT,
                title TEXT NOT NULL DEFAULT '',
                company TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                url TEXT,
                contract_type TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                salary_currency TEXT
                    NOT NULL DEFAULT 'EUR',
                salary_period TEXT
                    NOT NULL DEFAULT 'unknown',
                remote_type TEXT
                    NOT NULL DEFAULT 'unknown',
                published_at TEXT,
                collected_at TEXT,
                skills TEXT NOT NULL DEFAULT '[]',
                languages TEXT NOT NULL DEFAULT '[]',
                experience_level TEXT,
                experience_years INTEGER,
                raw_data TEXT NOT NULL DEFAULT '{}',
                score REAL NOT NULL DEFAULT 0,
                matched_skills TEXT
                    NOT NULL DEFAULT '[]',
                missing_skills TEXT
                    NOT NULL DEFAULT '[]',
                match_details TEXT
                    NOT NULL DEFAULT '{}',
                explanation TEXT
                    NOT NULL DEFAULT '',
                content_hash TEXT,
                first_seen_at TEXT,
                last_seen_at TEXT,
                updated_at TEXT,
                seen_count INTEGER
                    NOT NULL DEFAULT 1,
                last_action TEXT
                    NOT NULL DEFAULT 'inserted',
                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        _migrate_existing_jobs_table(cursor)
        _backfill_history_columns(cursor)
        _create_indexes(cursor)

        connection.commit()

    finally:
        connection.close()


def _migrate_existing_jobs_table(
    cursor: sqlite3.Cursor,
) -> None:
    """
    Ajoute les colonnes absentes sans supprimer les données.
    """

    cursor.execute(
        "PRAGMA table_info(jobs)"
    )

    existing_columns = {
        str(row["name"])
        for row in cursor.fetchall()
    }

    for column_name, definition in JOB_COLUMNS.items():
        if column_name in existing_columns:
            continue

        cursor.execute(
            f"""
            ALTER TABLE jobs
            ADD COLUMN {column_name} {definition}
            """
        )


def _backfill_history_columns(
    cursor: sqlite3.Cursor,
) -> None:
    """
    Initialise les métadonnées historiques des anciennes lignes.
    """

    cursor.execute(
        """
        UPDATE jobs
        SET first_seen_at = COALESCE(
                first_seen_at,
                collected_at,
                created_at,
                CURRENT_TIMESTAMP
            ),
            last_seen_at = COALESCE(
                last_seen_at,
                collected_at,
                created_at,
                CURRENT_TIMESTAMP
            ),
            updated_at = COALESCE(
                updated_at,
                collected_at,
                created_at,
                CURRENT_TIMESTAMP
            ),
            seen_count = CASE
                WHEN seen_count IS NULL
                    OR seen_count < 1
                THEN 1
                ELSE seen_count
            END,
            last_action = COALESCE(
                NULLIF(last_action, ''),
                'inserted'
            )
        """
    )


def _create_indexes(
    cursor: sqlite3.Cursor,
) -> None:
    """
    Crée les index utiles aux recherches et statistiques.
    """

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
            idx_jobs_source_external_id
        ON jobs(source, external_id)
        WHERE external_id IS NOT NULL
          AND external_id <> ''
        """
    )

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
            idx_jobs_url
        ON jobs(url)
        WHERE url IS NOT NULL
          AND url <> ''
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_jobs_source
        ON jobs(source)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_jobs_score
        ON jobs(score DESC)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_jobs_first_seen
        ON jobs(first_seen_at DESC)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_jobs_last_seen
        ON jobs(last_seen_at DESC)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_jobs_updated_at
        ON jobs(updated_at DESC)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_jobs_last_action
        ON jobs(last_action)
        """
    )