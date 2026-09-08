from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from profile_config import has_user_profile


if has_user_profile():
    runpy.run_path(str(Path(__file__).with_name("shareable_dashboard.py")), run_name="__main__")
    st.stop()

runpy.run_path(str(Path(__file__).with_name("shareable_resume_app.py")), run_name="__main__")
