import sqlite3


def get_connection():
    conn = sqlite3.connect("data/jobs.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS jobs (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT,
        company TEXT,
        location TEXT,
        description TEXT,
        url TEXT UNIQUE,
        source TEXT,

        salary TEXT,
        contract TEXT,
        remote INTEGER
    )
    """)

    conn.commit()
    conn.close()