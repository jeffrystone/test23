import sqlite3


def get_conn(db_path):
    conn = sqlite3.connect(db_path)
    return conn


def init_db(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            pk INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL UNIQUE,
            name TEXT,
            description TEXT,
            url TEXT,
            meta TEXT
        )
    """
    )
    conn.commit()
