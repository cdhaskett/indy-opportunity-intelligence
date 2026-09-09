from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from auth_user import database_configured, is_logged_in

ROOT = Path(__file__).resolve().parent
RESUME_PATH = ROOT / "data" / "resume_text.json"


def _persistent_mode() -> bool:
    return database_configured() and is_logged_in()


def load_resume() -> dict[str, Any]:
    if _persistent_mode():
        from persistent_store import load_resume as load_persistent_resume

        return load_persistent_resume()
    try:
        payload = json.loads(RESUME_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def has_resume() -> bool:
    return bool(load_resume().get("text"))


def save_resume(text: str, source_name: str = "") -> dict[str, Any]:
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Resume text is empty.")
    if _persistent_mode():
        from persistent_store import save_resume as save_persistent_resume

        return save_persistent_resume(cleaned, source_name)

    RESUME_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "text": cleaned,
        "source_name": (source_name or "").strip(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    RESUME_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def delete_resume() -> None:
    if _persistent_mode():
        from persistent_store import delete_resume as delete_persistent_resume

        delete_persistent_resume()
        return
    try:
        RESUME_PATH.unlink()
    except FileNotFoundError:
        pass
