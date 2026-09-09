from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, Iterable

from data.discovery_enrichment import enrich_discovery_jobs
from matching.application_history import load_history, match_history

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "jobs.db"
HISTORY_PATH = DATA_DIR / "application_history.json"

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


def _history_status(prior: dict) -> str:
    """Translate common imported history stages into this app's status vocabulary."""
    raw = " ".join(
        str(prior.get(key) or "")
        for key in (
            "status", "stage", "outcome", "application_status",
            "current_status", "current_stage",
        )
    ).lower()
    raw = re.sub(r"[^a-z0-9]+", " ", raw).strip()

    if any(term in raw for term in ("offer", "offered")):
        return "offer"
    if any(term in raw for term in ("final round", "final interview", "finalist", "final")):
        return "final"
    if any(term in raw for term in ("rejected", "declined", "not selected", "not moving forward", "no longer considered")):
        return "rejected"
    if any(term in raw for term in ("withdrawn", "withdrew")):
        return "withdrawn"
    if any(term in raw for term in ("interview", "onsite", "on site", "panel")):
        return "interview"
    if any(term in raw for term in ("screen", "screening", "recruiter call", "phone call")):
        return "screen"
    if any(term in raw for term in ("applied", "submitted", "application received")):
        return "applied"
    return "applied"


def _reconcile_history_statuses(conn, rows: list[dict]) -> list[dict]:
    history = load_history(HISTORY_PATH)
    if not history:
        return rows

    for job in rows:
        if job.get("status") not in {"new", "saved"}:
            continue
        match = match_history(job, history)
        if not match or match.get("match_type") != "exact":
            continue

        target = _history_status(match.get("prior") or {})
        if target == job.get("status"):
            continue

        conn.execute("UPDATE jobs SET status=? WHERE id=?", (target, int(job["id"])))
        conn.execute(
            "INSERT INTO outcomes(job_id, status, notes) VALUES (?, ?, ?)",
            (int(job["id"]), target, "Reconciled from imported application history"),
        )
        job["status"] = target

    return rows


def list_jobs():
    initialize()
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM jobs ORDER BY score DESC, date_found DESC"
        ).fetchall()]
        rows = _reconcile_history_statuses(conn, rows)
        return enrich_discovery_jobs(rows)


def update_status(job_id: int, status: str):
    initialize()
    with connect() as conn:
        conn.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
        conn.execute(
            "INSERT INTO outcomes(job_id, status) VALUES (?, ?)",
            (job_id, status)
        )
