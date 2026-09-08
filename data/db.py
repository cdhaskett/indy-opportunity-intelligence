from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Iterable

from auth_user import database_configured, is_logged_in

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


def _persistent_mode() -> bool:
    return database_configured() and is_logged_in()


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize():
    if _persistent_mode():
        from persistent_store import ensure_schema

        ensure_schema()
        return
    with connect() as conn:
        conn.executescript(SCHEMA)


def upsert_jobs(jobs: Iterable[Dict]):
    if _persistent_mode():
        from persistent_store import upsert_jobs as upsert_persistent_jobs

        upsert_persistent_jobs(jobs)
        return
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
    if _persistent_mode():
        from persistent_store import list_jobs as list_persistent_jobs

        return list_persistent_jobs()
    initialize()
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM jobs ORDER BY score DESC, date_found DESC"
        ).fetchall()]


def update_status(job_id: int, status: str):
    if _persistent_mode():
        from persistent_store import update_status as update_persistent_status

        update_persistent_status(job_id, status)
        return
    initialize()
    with connect() as conn:
        conn.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
        conn.execute(
            "INSERT INTO outcomes(job_id, status) VALUES (?, ?)",
            (job_id, status)
        )


def count_today_status(status: str) -> int:
    if _persistent_mode():
        from persistent_store import count_today_status as count_persistent_today

        return count_persistent_today(status)
    initialize()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(DISTINCT job_id) AS n
            FROM outcomes
            WHERE status = ?
              AND date(changed_at, 'localtime') = date('now', 'localtime')
            """,
            (status,),
        ).fetchone()
    return int(row["n"] if row else 0)
