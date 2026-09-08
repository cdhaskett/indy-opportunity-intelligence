from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from auth_user import database_configured, is_logged_in

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DEFAULT_PROFILE_PATH = DATA_DIR / "candidate_profile.json"
USER_PROFILE_PATH = DATA_DIR / "user_profile.json"
TEMPLATE_PROFILE_PATH = DATA_DIR / "profile_template.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _persistent_mode() -> bool:
    return database_configured() and is_logged_in()


def has_user_profile() -> bool:
    if _persistent_mode():
        from persistent_store import has_profile

        return has_profile()
    return USER_PROFILE_PATH.exists()


def load_profile_template() -> dict[str, Any]:
    if TEMPLATE_PROFILE_PATH.exists():
        return _read_json(TEMPLATE_PROFILE_PATH)
    return _read_json(DEFAULT_PROFILE_PATH)


def load_profile() -> dict[str, Any]:
    if _persistent_mode():
        from persistent_store import load_profile as load_persistent_profile

        profile = load_persistent_profile()
        return profile if profile else load_profile_template()
    if USER_PROFILE_PATH.exists():
        profile = _read_json(USER_PROFILE_PATH)
        if profile:
            return profile
    return load_profile_template()


def save_user_profile(profile: dict[str, Any]) -> None:
    if _persistent_mode():
        from persistent_store import save_profile

        save_profile(profile)
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def reset_user_profile() -> None:
    if _persistent_mode():
        from persistent_store import delete_profile

        delete_profile()
        return
    try:
        USER_PROFILE_PATH.unlink()
    except FileNotFoundError:
        pass


def profile_source() -> str:
    if _persistent_mode():
        return "secure cloud profile"
    return "private local profile" if USER_PROFILE_PATH.exists() else "template"
