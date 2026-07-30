from pathlib import Path
import sqlite3

DB_PATH = Path("data/jobagent.db")


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


def init_database():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT,

        company TEXT,

        location TEXT,

        description TEXT,

        source TEXT,

        url TEXT UNIQUE,

        score INTEGER,

        matched_skills TEXT,

        missing_skills TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()

    conn.close()