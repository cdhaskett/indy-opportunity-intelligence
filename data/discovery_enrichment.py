from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

DATA_DIR = Path(__file__).resolve().parent
DISCOVERY_PATH = DATA_DIR / "discovered_jobs.json"


def _norm(value: str | None) -> str:
    text = (value or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _load_discovery_maps() -> tuple[dict[str, dict], dict[tuple[str, str], dict]]:
    try:
        payload = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, {}

    rows = payload.get("jobs", []) if isinstance(payload, dict) else []
    by_id: dict[str, dict] = {}
    by_company_title: dict[tuple[str, str], dict] = {}

    for row in rows:
        if not isinstance(row, dict):
            continue
        external_id = str(row.get("external_id") or "").strip()
        if external_id:
            by_id[external_id] = row

        company_key = _norm(row.get("company"))
        title_key = _norm(row.get("title"))
        if company_key and title_key:
            by_company_title[(company_key, title_key)] = row

    return by_id, by_company_title


def enrich_discovery_jobs(rows: Iterable[dict]) -> list[dict]:
    """Overlay the newest discovery-feed metadata onto already-stored discovery jobs.

    Discovery records can become richer after a job was first saved. Older database
    rows may also have a stale or missing external ID, so exact company+title is used
    as a safe fallback for discovery-source records.
    """
    by_id, by_company_title = _load_discovery_maps()
    enriched: list[dict] = []

    for original in rows:
        job = dict(original)
        if str(job.get("source") or "").lower() == "discovery":
            external_id = str(job.get("external_id") or "").strip()
            current = by_id.get(external_id) if external_id else None

            if current is None:
                key = (_norm(job.get("company")), _norm(job.get("title")))
                current = by_company_title.get(key)

            if current:
                for key in (
                    "external_id", "company", "title", "location", "remote",
                    "salary_min", "salary_max", "url", "posted_at", "description",
                ):
                    if key in current and current.get(key) is not None:
                        job[key] = current.get(key)

        enriched.append(job)

    return enriched
