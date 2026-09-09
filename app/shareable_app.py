from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from app.loading_ui import show_xp_loader
from auth_user import auth_configured, database_configured, require_login
from profile_config import has_user_profile

st.set_page_config(
    page_title="Opportunity Intelligence",
    page_icon="🪟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# The hosted beta owns its navigation/account chrome. Remove Streamlit's
# reserved header/sidebar space so the XP workspace starts near the top of
# the browser instead of several hundred pixels below it.
st.markdown(
    """
<style>
header[data-testid="stHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    visibility: hidden !important;
    overflow: hidden !important;
}
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main {
    margin-top: 0 !important;
    padding-top: 0 !important;
    top: 0 !important;
}
[data-testid="stMainBlockContainer"],
.block-container {
    margin: 0 auto !important;
    padding-top: .35rem !important;
}
</style>
""",
    unsafe_allow_html=True,
)

secure_mode = auth_configured() and database_configured()
startup_loader = None
if secure_mode:
    identity = require_login()
    startup_loader = show_xp_loader("Opening your private job-search workspace")
    from persistent_store import touch_current_user

    touch_current_user()
    st.session_state["oi_identity"] = {
        "user_id": identity["user_id"],
        "email": identity.get("email", ""),
        "name": identity.get("name", ""),
    }
else:
    startup_loader = show_xp_loader("Opening Opportunity Intelligence")
    st.session_state.pop("oi_identity", None)

profile_ready = has_user_profile()
if startup_loader is not None:
    startup_loader.empty()

if profile_ready:
    runpy.run_path(str(Path(__file__).with_name("shareable_dashboard.py")), run_name="__main__")
    st.stop()

runpy.run_path(str(Path(__file__).with_name("shareable_resume_app.py")), run_name="__main__")
