from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


def has_user_profile() -> bool:
    """Return True only when this installation has completed its own setup."""
    return USER_PROFILE_PATH.exists()


def load_profile_template() -> dict[str, Any]:
    """Load the neutral, shareable profile template."""
    if TEMPLATE_PROFILE_PATH.exists():
        return _read_json(TEMPLATE_PROFILE_PATH)
    return _read_json(DEFAULT_PROFILE_PATH)


def load_profile() -> dict[str, Any]:
    """Load this user's private profile, or a neutral template before first-run setup."""
    if has_user_profile():
        profile = _read_json(USER_PROFILE_PATH)
        if profile:
            return profile
    return load_profile_template()


def save_user_profile(profile: dict[str, Any]) -> None:
    """Persist a user-specific profile locally. This file is ignored by Git."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def reset_user_profile() -> None:
    """Remove only the private local profile so onboarding can be run again."""
    try:
        USER_PROFILE_PATH.unlink()
    except FileNotFoundError:
        pass


def profile_source() -> str:
    return "private" if has_user_profile() else "template"
