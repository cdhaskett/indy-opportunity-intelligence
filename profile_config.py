from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DEFAULT_PROFILE_PATH = DATA_DIR / "candidate_profile.json"
USER_PROFILE_PATH = DATA_DIR / "user_profile.json"
TEMPLATE_PROFILE_PATH = DATA_DIR / "profile_template.json"


def load_profile() -> dict[str, Any]:
    """Load the private local profile when present, otherwise use the repository default."""
    path = USER_PROFILE_PATH if USER_PROFILE_PATH.exists() else DEFAULT_PROFILE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    return payload if isinstance(payload, dict) else {}


def save_user_profile(profile: dict[str, Any]) -> None:
    """Persist a user-specific profile locally. This file is ignored by Git."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def load_profile_template() -> dict[str, Any]:
    path = TEMPLATE_PROFILE_PATH if TEMPLATE_PROFILE_PATH.exists() else DEFAULT_PROFILE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    return payload if isinstance(payload, dict) else {}


def profile_source() -> str:
    return "private" if USER_PROFILE_PATH.exists() else "default"
