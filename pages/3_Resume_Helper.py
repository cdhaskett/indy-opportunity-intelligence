from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from app.resume_helper_ui import render_resume_helper
from data.db import list_jobs

PROFILE = json.loads((ROOT / "data" / "candidate_profile.json").read_text(encoding="utf-8"))

st.set_page_config(page_title="Resume Helper", page_icon="📝", layout="wide")

st.markdown(
    """
<style>
html,body,[class*="css"]{font-family:Tahoma,Arial,sans-serif}
.stApp{color:#111;background:#ece9d8}
.block-container,[data-testid="stMainBlockContainer"]{max-width:1450px;padding-top:.8rem;padding-bottom:3rem}
div[data-testid="stMetric"]{background:#fffef5;border:1px solid #7f9db9;padding:.65rem .8rem;box-shadow:1px 1px #888}
[data-testid="stMetricLabel"] *,[data-testid="stMetricLabel"]{color:#0b3d91!important;font-weight:700!important}
[data-testid="stMetricValue"] *{color:#111!important}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{background:linear-gradient(#fff,#e5e5df)!important;border:1px solid #003c74!important;color:#111!important;border-radius:3px!important;font-weight:700!important}
input,textarea,[role="combobox"],div[data-baseweb="select"]>div{background:#fff!important;color:#111!important}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("## 🪟 Indy Opportunity Intelligence · Resume Helper")
render_resume_helper(PROFILE, list_jobs())
