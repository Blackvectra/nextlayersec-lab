"""SQLite access layer for the MSSP Ops App.

Handles connection setup, first-run initialization from schema.sql + seed.sql,
and small helpers. Stores billing/ops metadata only — never PHI.
"""

import os
import sqlite3

# Project root = parent of this app/ package. DB lives at the project root so it
# sits right next to schema.sql and is matched by the *.db .gitignore rule.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "mssp.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "seed.sql")


def get_connection():
    """Return a SQLite connection with rows accessible by column name and
    foreign-key enforcement enabled (off by default in SQLite)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Create the database from schema.sql on first run, then apply seed data.

    Seed data is only applied to a freshly created file so re-running the app
    never duplicates rows. The schema itself is idempotent (CREATE IF NOT
    EXISTS), so running it again on an existing DB is harmless.
    """
    is_new = not os.path.exists(DB_PATH)

    conn = get_connection()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

        if is_new:
            with open(SEED_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()

    return is_new
