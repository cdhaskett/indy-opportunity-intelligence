from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "data" / "market_state.json"


def load_market_state() -> dict:
    try:
        payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"last_refresh": None, "new_job_ids": []}
    if not isinstance(payload, dict):
        return {"last_refresh": None, "new_job_ids": []}
    payload.setdefault("last_refresh", None)
    payload.setdefault("new_job_ids", [])
    return payload


def save_refresh_result(new_job_ids: Iterable[int]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_refresh": datetime.now(timezone.utc).isoformat(),
        "new_job_ids": sorted({int(job_id) for job_id in new_job_ids}),
    }
    STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
