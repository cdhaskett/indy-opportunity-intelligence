from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from data.db import list_jobs, update_status
from matching.application_history import load_history, match_history, save_history
from matching.scorer import score_job
from run_collectors import run as run_collectors

PROFILE = json.loads((ROOT / "data" / "candidate_profile.json").read_text())
WATCHLIST = json.loads((ROOT / "data" / "market_watchlist.json").read_text())
LIVE_REGISTRY = json.loads((ROOT / "data" / "employers.json").read_text())
HISTORY_PATH = ROOT / "data" / "application_history.json"

st.set_page_config(page_title="Indy Opportunity Intelligence", page_icon="🪟", layout="wide")

st.markdown(
    """
    <style>
    :root { --xp-blue:#0a5bd8; --xp-panel:#f2f0e8; --xp-line:#7f9db9; --xp-text:#111; }
    html, body, [class*="css"] { font-family: Tahoma, "Trebuchet MS", Arial, sans-serif; }

    /* Bliss-inspired desktop: pure CSS, so the public app has no external image dependency. */
    .stApp {
      background: linear-gradient(180deg,#4b9df4 0%,#78b9f7 38%,#bfe4ff 59%,#8ed66a 60%,#58b846 100%);
      color:var(--xp-text); min-height:100vh;
    }
    .stApp:before {
      content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
      background:
        radial-gradient(ellipse at 8% 72%, rgba(255,255,255,.78) 0 2.2%, transparent 2.5%),
        radial-gradient(ellipse at 12% 70%, rgba(255,255,255,.68) 0 3%, transparent 3.3%),
        radial-gradient(ellipse at 74% 18%, rgba(255,255,255,.72) 0 2.4%, transparent 2.7%),
        radial-gradient(ellipse at 79% 17%, rgba(255,255,255,.62) 0 3.2%, transparent 3.5%),
        radial-gradient(ellipse at 15% 105%, #3e9e34 0 34%, transparent 34.3%),
        radial-gradient(ellipse at 52% 111%, #66c64f 0 43%, transparent 43.3%),
        radial-gradient(ellipse at 88% 106%, #48aa3c 0 39%, transparent 39.3%);
    }
    .block-container {
      position:relative; z-index:1; max-width:1580px; margin:0 auto;
      padding:1rem 1.15rem 4.5rem;
      background:rgba(236,233,216,.96); border-left:1px solid #6f91b7; border-right:1px solid #6f91b7;
      box-shadow:0 0 28px rgba(0,45,110,.28); min-height:100vh;
    }

    .xp-window { border:2px solid #1d4fa3;border-radius:8px 8px 4px 4px;box-shadow:0 8px 20px rgba(0,0,0,.22);overflow:hidden;background:var(--xp-panel);margin-bottom:.55rem; }
    .xp-titlebar { background:linear-gradient(180deg,#3f93ff 0,#0c63df 48%,#0753c7 100%);color:#fff;font-weight:700;padding:.48rem .7rem;font-size:1.02rem;border-bottom:1px solid #06459e;display:flex;justify-content:space-between;align-items:center;text-shadow:1px 1px #16448a; }
    .xp-controls{display:flex;gap:.24rem}.xp-control{width:20px;height:20px;line-height:18px;text-align:center;border-radius:3px;border:1px solid #fff;background:#1e70dc;color:#fff;font-weight:900}.xp-control.close{background:#e64d32}
    .xp-menubar{background:#f5f3eb;border-bottom:1px solid #b6b4ad;padding:.28rem .65rem;font-size:.82rem;word-spacing:1rem}
    .xp-banner{padding:.75rem 1rem;background:linear-gradient(90deg,#d9edff,#eef7ff 62%,#c8e4ff);border-bottom:1px solid #9ab6d2}
    .xp-banner-title{color:#16418a;font-size:1.65rem;font-weight:800;margin:0}.xp-banner-sub{color:#415b78;font-size:.88rem;margin-top:.16rem}

    div[role="radiogroup"]{background:#ece9d8;border:1px solid #aca899;padding:.25rem;border-radius:2px;display:flex;gap:.15rem;width:fit-content;margin:.35rem 0 .6rem}
    div[role="radiogroup"] label{padding:.32rem .55rem;border:1px solid transparent;border-radius:2px} div[role="radiogroup"] label:hover{background:#fff;border-color:#7f9db9} div[role="radiogroup"] p{color:#111!important;font-weight:700;font-size:.86rem}

    .xp-section-title{background:linear-gradient(180deg,#2c80ee,#0a5cd5);color:white;padding:.38rem .58rem;font-weight:700;border-radius:5px 5px 0 0;border:1px solid #084cae;margin-top:.45rem}
    div[data-testid="stMetric"]{background:#fffef5;border:1px solid #a9a79f;border-top-color:#fff;border-left-color:#fff;border-radius:2px;padding:.55rem .7rem;min-height:82px;box-shadow:1px 1px 0 #777}
    div[data-testid="stMetricLabel"] p{color:#1f3e72!important;font-size:.74rem;font-weight:700} div[data-testid="stMetricValue"]{color:#111!important;font-size:1.55rem;font-weight:800}

    /* Explorer workspace: keep the hills on the desktop, not behind the job text. */
    div[data-testid="stVerticalBlockBorderWrapper"]{background:#fff!important;border:1px solid #9eb6cf!important;border-radius:0!important;box-shadow:none!important}
    .job-title{color:#10479d;font-size:1.02rem;font-weight:800;margin-bottom:.12rem}.score-pill{display:inline-block;min-width:2.2rem;text-align:center;padding:.2rem .38rem;margin-right:.45rem;border:1px solid #18752a;background:linear-gradient(#66c96d,#32a342);color:#fff;font-size:.76rem;font-weight:800;border-radius:3px;text-shadow:1px 1px #287332}.salary-pill{display:inline-block;padding:.18rem .4rem;margin-left:.45rem;border:1px solid #a47b00;background:#ffdf57;color:#493900;font-size:.74rem;font-weight:800;border-radius:3px}.job-meta{color:#333;font-size:.82rem;margin:.12rem 0 .38rem}.job-meta strong{color:#111}
    .verdict-row{display:flex;gap:.3rem;align-items:center;flex-wrap:wrap;margin:.25rem 0 .42rem}.verdict-badge,.meta-badge{display:inline-block;padding:.15rem .4rem;border-radius:2px;font-size:.67rem;font-weight:800;text-transform:uppercase;border:1px solid #777}.verdict-apply{background:#39b54a;color:#fff;border-color:#1c7d2b}.verdict-strong{background:#ffd65a;color:#4e3900;border-color:#a87800}.verdict-stretch{background:#d9e6f5;color:#274a75;border-color:#7f9db9}.verdict-skip{background:#efc2bd;color:#721b14;border-color:#b25349}.meta-badge{background:#dbe8f7;color:#2b4a70;border-color:#7f9db9}.duplicate-note{background:#fff7a8;border:1px solid #d0bd3e;color:#4c4314;padding:.42rem .52rem;font-size:.77rem;margin:.28rem 0 .4rem}

    .stButton>button,.stLinkButton>a{background:linear-gradient(#fff,#e5e5df)!important;border:1px solid #003c74!important;box-shadow:1px 1px 0 #fff inset;color:#111!important;border-radius:3px!important;font-weight:700!important;min-height:2rem!important}.stButton>button:hover,.stLinkButton>a:hover{background:linear-gradient(#fffef0,#f2e7ad)!important}
    div[data-baseweb="select"]>div{background:#fff!important;border:1px solid #7f9db9!important;color:#111!important;border-radius:2px!important} div[data-baseweb="select"] *{color:#111!important}[data-baseweb="tag"]{background:#dbe8f7!important;border:1px solid #7f9db9!important}
    div[data-testid="stExpander"]{border:1px solid #9eb6cf!important;background:#fff!important;border-radius:0!important} div[data-testid="stExpander"] summary{background:linear-gradient(#f7fbff,#dceaf8)!important} div[data-testid="stExpander"] summary p{color:#10479d!important;font-size:.8rem;font-weight:700} div[data-testid="stExpander"] p{color:#111!important}
    [data-testid="stToggle"] p,.stMultiSelect label p,.stSelectbox label p,.stFileUploader label p{color:#111!important}.stCaption,[data-testid="stCaptionContainer"],.stCaption p,[data-testid="stCaptionContainer"] p{color:#4e5f6f!important} div[data-testid="stDataFrame"]{border:1px solid #7f9db9;border-radius:0;overflow:hidden}

    .xp-taskbar{position:fixed;left:0;right:0;bottom:0;height:36px;background:linear-gradient(#2e7df1,#0757c8);border-top:1px solid #5ba4ff;z-index:9998;display:flex;align-items:center;padding:0 .35rem;box-shadow:0 -1px 4px rgba(0,0,0,.25)}.xp-start{background:linear-gradient(#6bc65c,#2e9a2e);border:1px solid #1d7d1d;color:#fff;font-weight:800;font-style:italic;border-radius:0 14px 14px 0;padding:.28rem 1rem;text-shadow:1px 1px #1c681d}.xp-task{margin-left:.45rem;background:#1e66c9;border:1px solid #0e4fae;color:#fff;padding:.25rem .7rem;font-size:.77rem;min-width:210px}.xp-clock{margin-left:auto;color:#fff;font-size:.75rem;padding-right:.6rem}
    @media(max-width:850px){.block-container{padding-left:.5rem;padding-right:.5rem}.xp-banner-title{font-size:1.3rem}.xp-task{display:none}.salary-pill{margin-left:.1rem}}
    </style>
    """, unsafe_allow_html=True)

st.markdown("""<div class="xp-window"><div class="xp-titlebar"><span>📁 Indy Opportunity Intelligence</span><div class="xp-controls"><span class="xp-control">_</span><span class="xp-control">□</span><span class="xp-control close">×</span></div></div><div class="xp-menubar">File View Tools Help</div><div class="xp-banner"><div class="xp-banner-title">🧭 Indy Opportunity Intelligence</div><div class="xp-banner-sub">Real opportunities. Central Indiana + U.S. remote. Less scrolling, better odds.</div></div></div>""", unsafe_allow_html=True)
section=st.radio("Navigation",["🏠 Job Market","🌐 Market Coverage","📂 My Applications"],horizontal=True,label_visibility="collapsed")
history=load_history(HISTORY_PATH); jobs=list_jobs(); rescored_jobs=[]; score_details={}; history_matches={}
for raw_job in jobs:
    score,detail=score_job(raw_job,PROFILE); job=dict(raw_job); job["score"],job["verdict"]=score,detail["verdict"]; match=match_history(job,history); job["history_match"]=match["match_type"] if match else None
    if match: history_matches[job["id"]]=match
    rescored_jobs.append(job); score_details[job["id"]]=detail
df=pd.DataFrame(rescored_jobs) if rescored_jobs else pd.DataFrame(); status_options=["new","saved","applied","screen","interview","final","offer","rejected","withdrawn"]
def money(value):
    if value is None or pd.isna(value): return None
    value=float(value); return f"${value/1000:.0f}K" if value>=1000 else f"${value:,.0f}"
def salary_label(row):
    low,high=money(row.get("salary_min")),money(row.get("salary_max"))
    if low and high:return f"{low}–{high}"
    if low:return f"{low}+"
    if high:return f"Up to {high}"
    return None
def verdict_class(v): return {"APPLY":"verdict-apply","STRONG CONSIDER":"verdict-strong","STRETCH":"verdict-stretch","SKIP":"verdict-skip"}.get(v,"verdict-stretch")
def render_score_explanation(row):
    d=score_details[row["id"]]
    with st.expander(f"Why {int(row['score'])}?"):
        for label,key in [("Title / job family","title"),("Skills","skills"),("Seniority","seniority"),("Process / operations","process_ops"),("CRM / Power Platform","crm_power_platform"),("Location / remote","location"),("Compensation","salary")]: st.write(f"**{label}:** {d[key]['score']}/{d[key]['max']}")
        matched=list(dict.fromkeys(d["skills"].get("strong_matches",[])+d["skills"].get("secondary_matches",[])+d["process_ops"].get("matches",[])+d["crm_power_platform"].get("matches",[]))); st.write("**Matched signals:** "+(", ".join(matched[:14]) if matched else "No strong signals yet."))
        for f in d.get("hard_requirements",{}).get("findings",[]): st.error(f"Hard requirement gap: {str(f.get('years'))+'+ years' if f.get('years') else 'direct experience'} in {f['domain']}.")
        if d["salary"].get("salary_min") is None: st.caption("Compensation not listed; neutral partial credit used.")

if section=="🏠 Job Market":
    rc,nc=st.columns([1,4])
    with rc:
        if st.button("🔄 Refresh Market",width="stretch"):
            with st.spinner("Checking employer career systems..."): run_collectors()
            st.rerun()
    with nc: st.caption("Live ATS feeds + verified discovery sources")
    if df.empty: st.info("No jobs loaded yet. Click Refresh