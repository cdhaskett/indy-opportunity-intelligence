from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

DATA_DIR = Path(__file__).resolve().parent
DISCOVERY_PATH = DATA_DIR / "discovered_jobs.json"


def _load_discovery_map() -> dict[str, dict]:
    try:
        payload = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    rows = payload.get("jobs", []) if isinstance(payload, dict) else []
    result: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        external_id = str(row.get("external_id") or "").strip()
        if external_id:
            result[external_id] = row
    return result


def enrich_discovery_jobs(rows: Iterable[dict]) -> list[dict]:
    """Overlay the newest discovery-feed metadata onto already-stored discovery jobs."""
    discovery = _load_discovery_map()
    enriched: list[dict] = []

    for original in rows:
        job = dict(original)
        if str(job.get("source") or "").lower() == "discovery":
            current = discovery.get(str(job.get("external_id") or "").strip())
            if current:
                for key in (
                    "company", "title", "location", "remote", "salary_min",
                    "salary_max", "url", "posted_at", "description",
                ):
                    if key in current and current.get(key) is not None:
                        job[key] = current.get(key)
        enriched.append(job)

    return enriched
