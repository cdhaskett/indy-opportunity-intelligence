from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from auth_user import auth_configured, database_configured, require_login
from profile_config import has_user_profile

st.set_page_config(
    page_title="Opportunity Intelligence",
    page_icon="🪟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

secure_mode = auth_configured() and database_configured()
if secure_mode:
    identity = require_login()
    from persistent_store import touch_current_user

    touch_current_user()
    st.session_state["oi_identity"] = {
        "user_id": identity["user_id"],
        "email": identity.get("email", ""),
        "name": identity.get("name", ""),
    }
    with st.sidebar:
        st.markdown("### 🪟 Opportunity Intelligence")
        st.caption(identity.get("email") or identity.get("name") or "Signed in")
        if st.button("Sign out", use_container_width=True):
            st.logout()
else:
    st.session_state.pop("oi_identity", None)

if has_user_profile():
    runpy.run_path(str(Path(__file__).with_name("shareable_dashboard.py")), run_name="__main__")
    st.stop()

runpy.run_path(str(Path(__file__).with_name("shareable_resume_app.py")), run_name="__main__")
