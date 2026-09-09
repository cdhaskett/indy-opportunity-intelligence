from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from auth_user import database_configured, is_logged_in

ROOT = Path(__file__).resolve().parent
RESUME_PATH = ROOT / "data" / "resume_text.json"


def _persistent_mode() -> bool:
    return database_configured() and is_logged_in()


def _persistent_store(required_name: str):
    """Resolve the current hosted persistence module safely.

    Streamlit can keep imported modules alive across app reruns while a deploy is
    settling. If an older module object is still present, reload it once before
    reporting a missing résumé-storage function.
    """
    module = importlib.import_module("persistent_store")
    if not hasattr(module, required_name):
        module = importlib.reload(module)
    if not hasattr(module, required_name):
        raise RuntimeError(
            "Hosted résumé storage is updating. Refresh the app once and try again."
        )
    return module


def load_resume() -> dict[str, Any]:
    if _persistent_mode():
        store = _persistent_store("load_resume")
        return store.load_resume()
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
        store = _persistent_store("save_resume")
        return store.save_resume(cleaned, source_name)

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
        store = _persistent_store("delete_resume")
        store.delete_resume()
        return
    try:
        RESUME_PATH.unlink()
    except FileNotFoundError:
        pass
