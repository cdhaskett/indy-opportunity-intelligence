from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterable, Dict

DB_PATH = Path(__file__).resolve().parent / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT,
    source TEXT NOT NULL,
    company TEXT,
    title TEXT NOT NULL,
    location TEXT,
    remote INTEGER DEFAULT 0,
    salary_min INTEGER,
    salary_max INTEGER,
    url TEXT,
    posted_at TEXT,
    description TEXT,
    score INTEGER,
    verdict TEXT,
    status TEXT DEFAULT 'new',
    date_found TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
"""

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize():
    with connect() as conn:
        conn.executescript(SCHEMA)

def upsert_jobs(jobs: Iterable[Dict]):
    initialize()
    with connect() as conn:
        for job in jobs:
            conn.execute(
                """
                INSERT INTO jobs (
                    external_id, source, company, title, location, remote,
                    salary_min, salary_max, url, posted_at, description,
                    score, verdict
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, external_id) DO UPDATE SET
                    company=excluded.company,
                    title=excluded.title,
                    location=excluded.location,
                    remote=excluded.remote,
                    salary_min=excluded.salary_min,
                    salary_max=excluded.salary_max,
                    url=excluded.url,
                    posted_at=excluded.posted_at,
                    description=excluded.description,
                    score=excluded.score,
                    verdict=excluded.verdict
                """,
                (
                    job.get("external_id"), job.get("source"), job.get("company"),
                    job.get("title"), job.get("location"), int(bool(job.get("remote"))),
                    job.get("salary_min"), job.get("salary_max"), job.get("url"),
                    job.get("posted_at"), job.get("description"),
                    job.get("score"), job.get("verdict")
                )
            )

def list_jobs():
    initialize()
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM jobs ORDER BY score DESC, date_found DESC"
        ).fetchall()]

def update_status(job_id: int, status: str):
    initialize()
    with connect() as conn:
        conn.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
        conn.execute(
            "INSERT INTO outcomes(job_id, status) VALUES (?, ?)",
            (job_id, status)
        )
