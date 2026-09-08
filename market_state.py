from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from auth_user import database_configured, is_logged_in

ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "data" / "market_state.json"


def _persistent_mode() -> bool:
    return database_configured() and is_logged_in()


def load_market_state() -> dict:
    if _persistent_mode():
        from persistent_store import load_market_state as load_persistent_state

        return load_persistent_state()
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
    if _persistent_mode():
        from persistent_store import save_refresh_result as save_persistent_refresh

        save_persistent_refresh(new_job_ids)
        return
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_refresh": datetime.now(timezone.utc).isoformat(),
        "new_job_ids": sorted({int(job_id) for job_id in new_job_ids}),
    }
    STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
