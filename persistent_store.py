from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable

import streamlit as st

from auth_user import current_identity, current_user_id, database_configured


def _database_url() -> str:
    if not database_configured():
        raise RuntimeError("Persistent database is not configured in Streamlit Secrets.")
    return str(st.secrets["database"]["url"])


def _connect():
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(_database_url(), row_factory=dict_row)


def ensure_schema() -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS oi_users (
            user_id TEXT PRIMARY KEY,
            email TEXT,
            display_name TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS oi_profiles (
            user_id TEXT PRIMARY KEY REFERENCES oi_users(user_id) ON DELETE CASCADE,
            profile JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS oi_histories (
            user_id TEXT PRIMARY KEY REFERENCES oi_users(user_id) ON DELETE CASCADE,
            history JSONB NOT NULL DEFAULT '[]'::jsonb,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS oi_jobs (
            id BIGSERIAL PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES oi_users(user_id) ON DELETE CASCADE,
            external_id TEXT NOT NULL,
            source TEXT NOT NULL,
            company TEXT,
            title TEXT NOT NULL,
            location TEXT,
            remote BOOLEAN NOT NULL DEFAULT FALSE,
            salary_min INTEGER,
            salary_max INTEGER,
            url TEXT,
            posted_at TEXT,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            date_found TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(user_id, source, external_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS oi_outcomes (
            id BIGSERIAL PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES oi_users(user_id) ON DELETE CASCADE,
            job_id BIGINT NOT NULL REFERENCES oi_jobs(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS oi_market_state (
            user_id TEXT PRIMARY KEY REFERENCES oi_users(user_id) ON DELETE CASCADE,
            last_refresh TIMESTAMPTZ,
            new_job_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_oi_jobs_user_status ON oi_jobs(user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_oi_outcomes_user_changed ON oi_outcomes(user_id, changed_at)",
    ]
    with _connect() as conn:
        for statement in statements:
            conn.execute(statement)
        conn.commit()


def touch_current_user() -> str:
    identity = current_identity()
    if not identity:
        raise RuntimeError("No authenticated user is available.")
    ensure_schema()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO oi_users(user_id, email, display_name)
            VALUES (%s, %s, %s)
            ON CONFLICT(user_id) DO UPDATE SET
                email=EXCLUDED.email,
                display_name=EXCLUDED.display_name,
                last_seen_at=NOW()
            """,
            (identity["user_id"], identity.get("email"), identity.get("name")),
        )
        conn.commit()
    return identity["user_id"]


def _uid() -> str:
    user_id = current_user_id()
    if not user_id:
        raise RuntimeError("No authenticated user is available.")
    return user_id


def has_profile() -> bool:
    user_id = touch_current_user()
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM oi_profiles WHERE user_id=%s",
            (user_id,),
        ).fetchone()
    return bool(row)


def load_profile() -> dict[str, Any]:
    user_id = touch_current_user()
    with _connect() as conn:
        row = conn.execute(
            "SELECT profile FROM oi_profiles WHERE user_id=%s",
            (user_id,),
        ).fetchone()
    if not row:
        return {}
    value = row["profile"]
    return value if isinstance(value, dict) else json.loads(value)


def save_profile(profile: dict[str, Any]) -> None:
    from psycopg.types.json import Jsonb

    user_id = touch_current_user()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO oi_profiles(user_id, profile)
            VALUES (%s, %s)
            ON CONFLICT(user_id) DO UPDATE SET profile=EXCLUDED.profile, updated_at=NOW()
            """,
            (user_id, Jsonb(profile)),
        )
        conn.commit()


def delete_profile() -> None:
    user_id = touch_current_user()
    with _connect() as conn:
        conn.execute("DELETE FROM oi_profiles WHERE user_id=%s", (user_id,))
        conn.commit()


def load_history() -> list[dict[str, Any]]:
    user_id = touch_current_user()
    with _connect() as conn:
        row = conn.execute(
            "SELECT history FROM oi_histories WHERE user_id=%s",
            (user_id,),
        ).fetchone()
    if not row:
        return []
    value = row["history"]
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    try:
        parsed = json.loads(value)
    except Exception:
        return []
    return [x for x in parsed if isinstance(x, dict)] if isinstance(parsed, list) else []


def save_history(rows: list[dict[str, Any]]) -> None:
    from psycopg.types.json import Jsonb

    user_id = touch_current_user()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO oi_histories(user_id, history)
            VALUES (%s, %s)
            ON CONFLICT(user_id) DO UPDATE SET history=EXCLUDED.history, updated_at=NOW()
            """,
            (user_id, Jsonb(rows)),
        )
        conn.commit()


def _external_key(job: dict[str, Any]) -> str:
    value = str(job.get("external_id") or "").strip()
    if value:
        return value
    raw = "|".join(
        str(job.get(key) or "").strip().lower()
        for key in ("source", "company", "title", "location", "url")
    )
    return "generated-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def upsert_jobs(jobs: Iterable[dict[str, Any]]) -> None:
    user_id = touch_current_user()
    with _connect() as conn:
        for job in jobs:
            conn.execute(
                """
                INSERT INTO oi_jobs(
                    user_id, external_id, source, company, title, location, remote,
                    salary_min, salary_max, url, posted_at, description
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(user_id, source, external_id) DO UPDATE SET
                    company=EXCLUDED.company,
                    title=EXCLUDED.title,
                    location=EXCLUDED.location,
                    remote=EXCLUDED.remote,
                    salary_min=EXCLUDED.salary_min,
                    salary_max=EXCLUDED.salary_max,
                    url=EXCLUDED.url,
                    posted_at=EXCLUDED.posted_at,
                    description=EXCLUDED.description,
                    updated_at=NOW()
                """,
                (
                    user_id,
                    _external_key(job),
                    str(job.get("source") or "unknown"),
                    job.get("company"),
                    str(job.get("title") or "Untitled role"),
                    job.get("location"),
                    bool(job.get("remote")),
                    job.get("salary_min"),
                    job.get("salary_max"),
                    job.get("url"),
                    job.get("posted_at"),
                    job.get("description"),
                ),
            )
        conn.commit()


def list_jobs() -> list[dict[str, Any]]:
    from matching.application_history import history_status, match_history

    user_id = touch_current_user()
    history = load_history()
    with _connect() as conn:
        rows = [dict(row) for row in conn.execute(
            """
            SELECT id, external_id, source, company, title, location, remote,
                   salary_min, salary_max, url, posted_at, description, status,
                   date_found
            FROM oi_jobs
            WHERE user_id=%s
            ORDER BY date_found DESC, id DESC
            """,
            (user_id,),
        ).fetchall()]

        for job in rows:
            if job.get("status") not in {"new", "saved"}:
                continue
            match = match_history(job, history)
            if not match or match.get("match_type") != "exact":
                continue
            target = history_status(match.get("prior") or {})
            if target == job.get("status"):
                continue
            result = conn.execute(
                "UPDATE oi_jobs SET status=%s, updated_at=NOW() WHERE id=%s AND user_id=%s",
                (target, int(job["id"]), user_id),
            )
            if result.rowcount:
                conn.execute(
                    "INSERT INTO oi_outcomes(user_id, job_id, status) VALUES (%s,%s,%s)",
                    (user_id, int(job["id"]), target),
                )
                job["status"] = target
        conn.commit()

    return rows


def update_status(job_id: int, status: str) -> None:
    user_id = touch_current_user()
    with _connect() as conn:
        result = conn.execute(
            "UPDATE oi_jobs SET status=%s, updated_at=NOW() WHERE id=%s AND user_id=%s",
            (status, int(job_id), user_id),
        )
        if result.rowcount:
            conn.execute(
                "INSERT INTO oi_outcomes(user_id, job_id, status) VALUES (%s,%s,%s)",
                (user_id, int(job_id), status),
            )
        conn.commit()


def count_today_status(status: str) -> int:
    user_id = touch_current_user()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(DISTINCT job_id) AS n
            FROM oi_outcomes
            WHERE user_id=%s AND status=%s AND changed_at >= DATE_TRUNC('day', NOW())
            """,
            (user_id, status),
        ).fetchone()
    return int(row["n"] if row else 0)


def load_market_state() -> dict[str, Any]:
    user_id = touch_current_user()
    with _connect() as conn:
        row = conn.execute(
            "SELECT last_refresh, new_job_ids FROM oi_market_state WHERE user_id=%s",
            (user_id,),
        ).fetchone()
    if not row:
        return {"last_refresh": None, "new_job_ids": []}
    ids = row["new_job_ids"] or []
    if not isinstance(ids, list):
        try:
            ids = json.loads(ids)
        except Exception:
            ids = []
    last = row["last_refresh"]
    return {
        "last_refresh": last.isoformat() if hasattr(last, "isoformat") else last,
        "new_job_ids": [int(x) for x in ids],
    }


def save_refresh_result(new_job_ids: Iterable[int]) -> None:
    from psycopg.types.json import Jsonb

    user_id = touch_current_user()
    ids = sorted({int(x) for x in new_job_ids})
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO oi_market_state(user_id, last_refresh, new_job_ids)
            VALUES (%s, NOW(), %s)
            ON CONFLICT(user_id) DO UPDATE SET
                last_refresh=NOW(), new_job_ids=EXCLUDED.new_job_ids, updated_at=NOW()
            """,
            (user_id, Jsonb(ids)),
        )
        conn.commit()


def delete_all_user_data() -> None:
    user_id = touch_current_user()
    with _connect() as conn:
        conn.execute("DELETE FROM oi_users WHERE user_id=%s", (user_id,))
        conn.commit()
