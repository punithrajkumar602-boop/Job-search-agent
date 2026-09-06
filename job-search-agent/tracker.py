"""SQLite-backed application tracker. Replaces a manual spreadsheet."""
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "applications.db"


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            job_id TEXT PRIMARY KEY,
            company TEXT,
            title TEXT,
            status TEXT,
            resume_version TEXT,
            date_applied TEXT,
            fit_score REAL,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()


def upsert_application(record):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO applications (job_id, company, title, status, resume_version, date_applied, fit_score, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            status=excluded.status,
            date_applied=excluded.date_applied,
            notes=excluded.notes
    """, (
        record["job_id"], record["company"], record["title"], record["status"],
        record.get("resume_version", ""), record.get("date_applied", str(date.today())),
        record.get("fit_score", 0.0), record.get("notes", "")
    ))
    conn.commit()
    conn.close()


def all_applications():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM applications ORDER BY fit_score DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
