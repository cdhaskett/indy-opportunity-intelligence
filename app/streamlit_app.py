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
    :root {
      --xp-blue:#0a5bd8; --xp-blue2:#2f83f7; --xp-dark:#0747a6;
      --xp-bg:#d6e7ff; --xp-panel:#f2f0e8; --xp-line:#7f9db9;
      --xp-text:#111; --xp-green:#37a445; --xp-yellow:#f4b400;
      --xp-red:#d94a3a; --xp-gray:#d4d0c8;
    }
    html, body, [class*="css"] { font-family: Tahoma, "Trebuchet MS", Arial, sans-serif; }
    .stApp {
      background:
        linear-gradient(rgba(72,145,255,.17), rgba(255,255,255,.07)),
        linear-gradient(180deg,#83b8ff 0,#b9dcff 22%,#74c959 63%,#49a13d 100%);
      color: var(--xp-text);
    }
    .block-container { max-width: 1360px; padding-top: .8rem; padding-bottom: 4rem; }

    /* Window chrome */
    .xp-window {
      border: 2px solid #1d4fa3; border-radius: 8px 8px 4px 4px;
      box-shadow: 0 12px 28px rgba(0,0,0,.25); overflow: hidden;
      background: var(--xp-panel); margin-bottom: .55rem;
    }
    .xp-titlebar {
      background: linear-gradient(180deg,#3f93ff 0,#0c63df 48%,#0753c7 100%);
      color:#fff; font-weight:700; padding:.48rem .7rem; font-size:1.02rem;
      border-bottom:1px solid #06459e; display:flex; justify-content:space-between; align-items:center;
      text-shadow:1px 1px #16448a;
    }
    .xp-controls { display:flex; gap:.24rem; }
    .xp-control { width:20px;height:20px;line-height:18px;text-align:center;border-radius:3px;border:1px solid #fff;background:#1e70dc;color:#fff;font-weight:900; }
    .xp-control.close { background:#e64d32; }
    .xp-menubar { background:#f5f3eb; border-bottom:1px solid #b6b4ad; padding:.28rem .65rem; font-size:.82rem; word-spacing:1rem; }
    .xp-banner { padding:.8rem 1rem; background:linear-gradient(180deg,#eef7ff,#d5eaff); border-bottom:1px solid #9ab6d2; }
    .xp-banner-title { color:#16418a;font-size:1.68rem;font-weight:800;margin:0; }
    .xp-banner-sub { color:#415b78;font-size:.9rem;margin-top:.18rem; }

    /* Streamlit navigation as XP toolbar */
    div[role="radiogroup"] { background:#ece9d8;border:1px solid #aca899;padding:.25rem;border-radius:2px;display:flex;gap:.15rem;width:fit-content;margin:.35rem 0 .6rem; }
    div[role="radiogroup"] label { padding:.32rem .55rem;border:1px solid transparent;border-radius:2px; }
    div[role="radiogroup"] label:hover { background:#fff;border-color:#7f9db9; }
    div[role="radiogroup"] p { color:#111 !important;font-weight:700;font-size:.86rem; }

    /* Group boxes */
    .xp-section-title { background:linear-gradient(180deg,#2c80ee,#0a5cd5); color:white; padding:.35rem .55rem; font-weight:700; border-radius:5px 5px 0 0; border:1px solid #084cae; }
    .xp-note { background:#fff7aa;border:1px solid #d8c84c;padding:.48rem .62rem;color:#4a431b;font-size:.82rem;box-shadow:1px 1px 0 #fff inset; }

    /* Metrics */
    div[data-testid="stMetric"] { background:#f7f5eb;border:1px solid #a9a79f;border-top-color:#fff;border-left-color:#fff;border-radius:2px;padding:.55rem .7rem;min-height:86px;box-shadow:1px 1px 0 #777; }
    div[data-testid="stMetricLabel"] p { color:#1f3e72 !important;font-size:.74rem;font-weight:700; }
    div[data-testid="stMetricValue"] { color:#111 !important;font-size:1.55rem;font-weight:800; }

    /* Cards / rows */
    div[data-testid="stVerticalBlockBorderWrapper"] { background:#fff !important;border:1px solid #9eb6cf !important;border-radius:0 !important;box-shadow:none !important; }
    .job-title { font-family:Tahoma,Arial,sans-serif;color:#10479d;font-size:1.02rem;font-weight:800;margin-bottom:.12rem; }
    .score-pill { display:inline-block;min-width:2.2rem;text-align:center;padding:.2rem .38rem;margin-right:.45rem;border:1px solid #18752a;background:linear-gradient(#66c96d,#32a342);color:#fff;font-size:.76rem;font-weight:800;border-radius:3px;text-shadow:1px 1px #287332; }
    .salary-pill { display:inline-block;padding:.18rem .4rem;margin-left:.45rem;border:1px solid #a47b00;background:#ffdf57;color:#493900;font-size:.74rem;font-weight:800;border-radius:3px; }
    .job-meta { color:#333;font-size:.82rem;margin:.12rem 0 .38rem; }
    .job-meta strong { color:#111; }
    .verdict-row { display:flex;gap:.3rem;align-items:center;flex-wrap:wrap;margin:.25rem 0 .42rem; }
    .verdict-badge,.meta-badge { display:inline-block;padding:.15rem .4rem;border-radius:2px;font-size:.67rem;font-weight:800;text-transform:uppercase;border:1px solid #777; }
    .verdict-apply { background:#39b54a;color:#fff;border-color:#1c7d2b; }
    .verdict-strong { background:#ffd65a;color:#4e3900;border-color:#a87800; }
    .verdict-stretch { background:#d9e6f5;color:#274a75;border-color:#7f9db9; }
    .verdict-skip { background:#efc2bd;color:#721b14;border-color:#b25349; }
    .meta-badge { background:#dbe8f7;color:#2b4a70;border-color:#7f9db9; }
    .duplicate-note { background:#fff7a8;border:1px solid #d0bd3e;color:#4c4314;padding:.42rem .52rem;font-size:.77rem;margin:.28rem 0 .4rem; }

    /* Buttons / inputs */
    .stButton>button,.stLinkButton>a { background:linear-gradient(#fff,#e5e5df)!important;border:1px solid #003c74!important;box-shadow:1px 1px 0 #fff inset;color:#111!important;border-radius:3px!important;font-weight:700!important;min-height:2rem!important; }
    .stButton>button:hover,.stLinkButton>a:hover { background:linear-gradient(#fffef0,#f2e7ad)!important; }
    div[data-baseweb="select"]>div { background:#fff!important;border:1px solid #7f9db9!important;color:#111!important;border-radius:2px!important; }
    div[data-baseweb="select"] * { color:#111!important; }
    [data-baseweb="tag"] { background:#dbe8f7!important;border:1px solid #7f9db9!important; }
    div[data-testid="stExpander"] { border:1px solid #9eb6cf!important;background:#f7fbff;border-radius:0!important; }
    div[data-testid="stExpander"] summary p { color:#10479d!important;font-size:.8rem;font-weight:700; }
    [data-testid="stToggle"] p,.stMultiSelect label p,.stSelectbox label p,.stFileUploader label p { color:#111!important; }
    .stCaption,[data-testid="stCaptionContainer"],.stCaption p,[data-testid="stCaptionContainer"] p { color:#4e5f6f!important; }
    div[data-testid="stDataFrame"] { border:1px solid #7f9db9;border-radius:0;overflow:hidden; }

    /* Bottom taskbar illusion */
    .xp-taskbar { position:fixed;left:0;right:0;bottom:0;height:36px;background:linear-gradient(#2e7df1,#0757c8);border-top:1px solid #5ba4ff;z-index:9998;display:flex;align-items:center;padding:0 .35rem;box-shadow:0 -1px 4px rgba(0,0,0,.25); }
    .xp-start { background:linear-gradient(#6bc65c,#2e9a2e);border:1px solid #1d7d1d;color:#fff;font-weight:800;font-style:italic;border-radius:0 14px 14px 0;padding:.28rem 1rem;text-shadow:1px 1px #1c681d; }
    .xp-task { margin-left:.45rem;background:#1e66c9;border:1px solid #0e4fae;color:#fff;padding:.25rem .7rem;font-size:.77rem;min-width:180px; }
    .xp-clock { margin-left:auto;color:#fff;font-size:.75rem;padding-right:.6rem; }

    @media(max-width:850px){.xp-banner-title{font-size:1.3rem}.block-container{padding-left:.5rem;padding-right:.5rem}.xp-task{display:none}.salary-pill{margin-left:.1rem}}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="xp-window">
      <div class="xp-titlebar"><span>📁 Indy Opportunity Intelligence</span><div class="xp-controls"><span class="xp-control">_</span><span class="xp-control">□</span><span class="xp-control close">×</span></div></div>
      <div class="xp-menubar">File View Tools Help</div>
      <div class="xp-banner"><div class="xp-banner-title">🧭 Indy Opportunity Intelligence</div><div class="xp-banner-sub">Real opportunities. Central Indiana + U.S. remote. Less scrolling, better odds.</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

section = st.radio("Navigation", ["🏠 Job Market", "🌐 Market Coverage", "📂 My Applications"], horizontal=True, label_visibility="collapsed")

history = load_history(HISTORY_PATH)
jobs = list_jobs()
rescored_jobs, score_details, history_matches = [], {}, {}
for raw_job in jobs:
    score, detail = score_job(raw_job, PROFILE)
    job = dict(raw_job)
    job["score"], job["verdict"] = score, detail["verdict"]
    match = match_history(job, history)
    job["history_match"] = match["match_type"] if match else None
    if match:
        history_matches[job["id"]] = match
    rescored_jobs.append(job)
    score_details[job["id"]] = detail

df = pd.DataFrame(rescored_jobs) if rescored_jobs else pd.DataFrame()
status_options = ["new", "saved", "applied", "screen", "interview", "final", "offer", "rejected", "withdrawn"]

def money(value):
    if value is None or pd.isna(value): return None
    value = float(value)
    return f"${value/1000:.0f}K" if value >= 1000 else f"${value:,.0f}"

def salary_label(row):
    low, high = money(row.get("salary_min")), money(row.get("salary_max"))
    if low and high: return f"{low}–{high}"
    if low: return f"{low}+"
    if high: return f"Up to {high}"
    return None

def verdict_class(verdict):
    return {"APPLY":"verdict-apply","STRONG CONSIDER":"verdict-strong","STRETCH":"verdict-stretch","SKIP":"verdict-skip"}.get(verdict,"verdict-stretch")

def render_score_explanation(row):
    details = score_details[row["id"]]
    with st.expander(f"Why {int(row['score'])}?"):
        rows = [
            ("Title / job family", details["title"]["score"], details["title"]["max"]),
            ("Skills", details["skills"]["score"], details["skills"]["max"]),
            ("Seniority", details["seniority"]["score"], details["seniority"]["max"]),
            ("Process / operations", details["process_ops"]["score"], details["process_ops"]["max"]),
            ("CRM / Power Platform", details["crm_power_platform"]["score"], details["crm_power_platform"]["max"]),
            ("Location / remote", details["location"]["score"], details["location"]["max"]),
            ("Compensation", details["salary"]["score"], details["salary"]["max"]),
        ]
        for label, earned, possible in rows: st.write(f"**{label}:** {earned}/{possible}")
        matched = list(dict.fromkeys(details["skills"].get("strong_matches", []) + details["skills"].get("secondary_matches", []) + details["process_ops"].get("matches", []) + details["crm_power_platform"].get("matches", [])))
        st.write("**Matched signals:** " + (", ".join(matched[:14]) if matched else "No strong signals yet."))
        for finding in details.get("hard_requirements", {}).get("findings", []):
            years = f"{finding['years']}+ years" if finding.get("years") else "direct experience"
            st.error(f"Hard requirement gap: {years} in {finding['domain']}.")
        if details["salary"].get("salary_min") is None: st.caption("Compensation not listed; neutral partial credit used.")

if section == "🏠 Job Market":
    refresh_col, note_col = st.columns([1,4])
    with refresh_col:
        if st.button("🔄 Refresh Market", width="stretch"):
            with st.spinner("Checking employer career systems..."):
                run_collectors()
            st.rerun()
    with note_col: st.caption("Live ATS feeds + verified discovery sources")
    if df.empty:
        st.info("No jobs loaded yet. Click Refresh Market.")
        st.stop()

    exact_duplicates = int((df["history_match"] == "exact").sum())
    possible_duplicates = int((df["history_match"] == "possible").sum())
    active = df[(df["status"].isin(["new","saved"])) & (df["history_match"] != "exact")].copy()

    st.markdown('<div class="xp-section-title">📊 Market Pulse</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("🔭 Market Watch", len(df)); c2.metric("▶ Apply Now", int((active["verdict"]=="APPLY").sum())); c3.metric("⭐ Strong Matches", int((active["verdict"]=="STRONG CONSIDER").sum())); c4.metric("📄 Already Applied", exact_duplicates); c5.metric("🔁 Review Duplicates", possible_duplicates)

    st.markdown('<div class="xp-section-title">📂 Today’s Shortlist</div>', unsafe_allow_html=True)
    if history: st.caption(f"Duplicate guard active · {len(history)} private application-history records loaded")
    else: st.warning("Duplicate guard is not loaded yet. Import history under My Applications.")

    show_processed = st.toggle("Show jobs I've already handled", value=False)
    show_exact_history = st.toggle("Show jobs matched to a previous application", value=False)
    f1,f2,f3 = st.columns(3)
    with f1: verdict_filter = st.multiselect("Verdict", ["APPLY","STRONG CONSIDER","STRETCH","SKIP"], default=["APPLY","STRONG CONSIDER","STRETCH"])
    with f2: company_filter = st.multiselect("Company", sorted(df["company"].dropna().unique().tolist()))
    with f3: status_filter = st.multiselect("Status", status_options)

    view = df[df["verdict"].isin(verdict_filter)].copy()
    if not show_processed and not status_filter: view = view[view["status"].isin(["new","saved"])]
    if not show_exact_history: view = view[view["history_match"] != "exact"]
    if company_filter: view = view[view["company"].isin(company_filter)]
    if status_filter: view = view[view["status"].isin(status_filter)]
    view = view.sort_values(["score","date_found"], ascending=[False,False])

    for _, row in view.iterrows():
        match, salary = history_matches.get(row["id"]), salary_label(row)
        with st.container(border=True):
            a,b = st.columns([5.2,1])
            with a:
                sal = f'<span class="salary-pill">💵 {salary}</span>' if salary else ""
                st.markdown(f'<div class="job-title"><span class="score-pill">{int(row["score"])}</span>{row["title"]}{sal}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="job-meta"><strong>{row["company"]}</strong> · {row["location"] or "Location not listed"}</div>', unsafe_allow_html=True)
                if match and match["match_type"] == "possible":
                    prior=match["prior"]; prior_date=prior.get("date") or prior.get("applied_date") or "date unknown"; prior_title=prior.get("title") or "another role"
                    st.markdown(f'<div class="duplicate-note">⚠️ Possible duplicate · Previously applied to <b>{prior_title}</b> at {prior.get("company",row["company"])} · {prior_date}</div>', unsafe_allow_html=True)
                source=row.get("source") or "unknown"; klass=verdict_class(row["verdict"])
                st.markdown(f'<div class="verdict-row"><span class="verdict-badge {klass}">{row["verdict"]}</span><span class="meta-badge">{row["status"]}</span><span class="meta-badge">{source}</span></div>', unsafe_allow_html=True)
                bc,ec=st.columns([1.15,4.85])
                with bc:
                    if row.get("url"): st.link_button("Open Posting", row["url"])
                with ec: render_score_explanation(row)
            with b:
                current=row["status"] if row["status"] in status_options else "new"
                new_status=st.selectbox("Status", status_options, index=status_options.index(current), key=f"status-{row['id']}")
                if new_status != row["status"]:
                    update_status(int(row["id"]),new_status); st.rerun()

elif section == "🌐 Market Coverage":
    st.markdown('<div class="xp-section-title">🌐 Market Coverage</div>', unsafe_allow_html=True)
    live,watch=pd.DataFrame(LIVE_REGISTRY["employers"]),pd.DataFrame(WATCHLIST["employers"])
    c1,c2,c3=st.columns(3); c1.metric("Connected Employers",len(live)); c2.metric("Expansion Watchlist",len(watch)); c3.metric("High Priority Gaps",int((watch["priority"]=="high").sum()))
    st.markdown("### Connected Now")
    st.dataframe(live[["name","ats","priority","market_note"]].sort_values(["priority","name"]),width="stretch",hide_index=True)
    st.markdown("### Expansion Watchlist")
    p1,p2=st.columns(2)
    with p1: priority=st.multiselect("Priority",["high","medium","low"],default=["high","medium"])
    with p2: segment=st.multiselect("Segment",sorted(watch["segment"].unique().tolist()))
    wv=watch[watch["priority"].isin(priority)].copy() if priority else watch.copy()
    if segment: wv=wv[wv["segment"].isin(segment)]
    st.dataframe(wv[["name","segment","priority","why"]].sort_values(["priority","segment","name"]),width="stretch",hide_index=True)

elif section == "📂 My Applications":
    st.markdown('<div class="xp-section-title">📂 My Applications</div>', unsafe_allow_html=True)
    st.caption("Your private history stays on your computer and is ignored by Git.")
    uploaded=st.file_uploader("Import application history",type=["json"])
    if uploaded is not None:
        try:
            payload=json.loads(uploaded.getvalue().decode("utf-8")); rows=payload.get("applications",[]) if isinstance(payload,dict) else payload; rows=[r for r in rows if isinstance(r,dict)]; save_history(HISTORY_PATH,rows); st.success(f"Imported {len(rows)} private records.")
            if st.button("Reload with history"): st.rerun()
        except Exception as exc: st.error(f"Could not import file: {exc}")
    if history:
        hdf=pd.DataFrame(history); cols=[c for c in ["company","title","date","status","requisition_id"] if c in hdf.columns]; st.dataframe(hdf[cols],width="stretch",hide_index=True)
    handled=df[~df["status"].isin(["new","saved"])].copy() if not df.empty else pd.DataFrame()
    if not df.empty:
        a1,a2,a3,a4=st.columns(4); a1.metric("Applied",int((df["status"]=="applied").sum())); a2.metric("Screens",int((df["status"]=="screen").sum())); a3.metric("Interviews",int((df["status"]=="interview").sum())); a4.metric("Offers",int((df["status"]=="offer").sum()))
        if not handled.empty: st.dataframe(handled[["company","title","location","score","verdict","status","date_found"]].sort_values("date_found",ascending=False),width="stretch",hide_index=True)

st.markdown('<div class="xp-taskbar"><div class="xp-start">🪟 start</div><div class="xp-task">📁 Indy Opportunity Intelligence</div><div class="xp-clock">local market watch</div></div>', unsafe_allow_html=True)
