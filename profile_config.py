from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DEFAULT_PROFILE_PATH = DATA_DIR / "candidate_profile.json"
USER_PROFILE_PATH = DATA_DIR / "user_profile.json"
TEMPLATE_PROFILE_PATH = DATA_DIR / "profile_template.json"
SESSION_PROFILE_KEY = "oi_candidate_profile"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_profile() -> dict[str, Any]:
    """Load this visitor's profile without leaking profile edits across public sessions."""
    if SESSION_PROFILE_KEY in st.session_state:
        value = st.session_state[SESSION_PROFILE_KEY]
        return dict(value) if isinstance(value, dict) else {}

    # A local/private deployment may explicitly opt into a persisted profile.
    if os.getenv("OI_ALLOW_LOCAL_PROFILE") == "1" and USER_PROFILE_PATH.exists():
        profile = _read_json(USER_PROFILE_PATH)
    else:
        profile = _read_json(DEFAULT_PROFILE_PATH)

    st.session_state[SESSION_PROFILE_KEY] = dict(profile)
    return profile


def save_user_profile(profile: dict[str, Any], persist_local: bool = False) -> None:
    """Save profile to this browser session; optionally persist only on private/local installs."""
    st.session_state[SESSION_PROFILE_KEY] = dict(profile)
    if persist_local and os.getenv("OI_ALLOW_LOCAL_PROFILE") == "1":
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        USER_PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def reset_session_profile() -> None:
    st.session_state.pop(SESSION_PROFILE_KEY, None)


def load_profile_template() -> dict[str, Any]:
    path = TEMPLATE_PROFILE_PATH if TEMPLATE_PROFILE_PATH.exists() else DEFAULT_PROFILE_PATH
    return _read_json(path)


def profile_source() -> str:
    if SESSION_PROFILE_KEY in st.session_state:
        return "session"
    if os.getenv("OI_ALLOW_LOCAL_PROFILE") == "1" and USER_PROFILE_PATH.exists():
        return "private"
    return "default"
