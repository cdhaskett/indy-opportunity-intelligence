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
html, body, [class*="css"] {
    font-family: Tahoma, Arial, sans-serif;
}

.stApp {
    color: #111;
    background: linear-gradient(#4b9df4 0 42%, #bfe4ff 59%, #79cf5c 60%, #3d9d34 100%);
}

.stApp:before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background:
      radial-gradient(ellipse at 12% 18%, rgba(255,255,255,.90) 0 2.4%, transparent 2.7%),
      radial-gradient(ellipse at 18% 17%, rgba(255,255,255,.75) 0 3.2%, transparent 3.5%),
      radial-gradient(ellipse at 74% 21%, rgba(255,255,255,.84) 0 2.5%, transparent 2.8%),
      radial-gradient(ellipse at 80% 20%, rgba(255,255,255,.70) 0 3.3%, transparent 3.6%),
      radial-gradient(ellipse at 20% 105%, #318c2c 0 34%, transparent 34.4%),
      radial-gradient(ellipse at 55% 110%, #68c94e 0 44%, transparent 44.4%),
      radial-gradient(ellipse at 92% 108%, #45a83b 0 38%, transparent 38.4%);
}

.block-container {
    position: relative;
    max-width: 1540px;
    margin: auto;
    padding: .65rem 1.2rem 4rem;
    background: rgba(236,233,216,.975);
    min-height: 100vh;
    border-left: 1px solid #7697bd;
    border-right: 1px solid #7697bd;
    box-shadow: 0 0 25px #285b8a88;
}

.xp-menubar {
    background: #f5f3eb;
    color: #111;
    padding: .30rem .60rem;
    border: 1px solid #aca899;
    border-bottom-color: #777;
    margin-bottom: .35rem;
    font-size: .78rem;
    box-shadow: inset 1px 1px #fff;
}

/* Navigation toolbar */
div[role="radiogroup"] {
    background: #ece9d8;
    border: 1px solid #aca899;
    padding: .22rem;
    width: fit-content;
    margin: .25rem 0 .55rem;
    box-shadow: inset 1px 1px #fff;
}
div[role="radiogroup"] label {
    padding: .28rem .48rem;
    border: 1px solid transparent;
    border-radius: 2px;
}
div[role="radiogroup"] label:hover {
    background: #fff;
    border-color: #7f9db9;
}
div[role="radiogroup"] p {
    color: #111 !important;
    font-weight: bold;
    font-size: .84rem;
}

.xp-section {
    background: linear-gradient(#3f93ff, #0753c7);
    color: white;
    font-weight: bold;
    padding: .36rem .56rem;
    border: 1px solid #06459e;
    border-radius: 5px 5px 0 0;
    margin-top: .45rem;
    text-shadow: 1px 1px #16448a;
}

/* Market Pulse */
div[data-testid="stMetric"] {
    background: #fffef5;
    border: 1px solid #888;
    border-top-color: #fff;
    border-left-color: #fff;
    padding: .52rem .68rem;
    min-height: 78px;
    box-shadow: 1px 1px 0 #777;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] *,
div[data-testid="stMetricLabel"] p {
    color: #0b3d91 !important;
    opacity: 1 !important;
    visibility: visible !important;
    font-size: .76rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    color: #111 !important;
    font-size: 1.52rem !important;
    font-weight: 400 !important;
}

/* Result card shell */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #fff !important;
    border: 1px solid #7f9db9 !important;
    border-radius: 4px !important;
    box-shadow: inset 1px 1px #fff !important;
    margin-bottom: .48rem;
    overflow: hidden;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    padding-top: .16rem !important;
    padding-bottom: .16rem !important;
}

.job-titlebar {
    display: flex;
    align-items: center;
    gap: .45rem;
    width: 100%;
    padding: .35rem .48rem;
    margin: -.05rem 0 .40rem 0;
    background: linear-gradient(180deg, #3f93ff 0%, #0c63df 48%, #0753c7 100%);
    border: 1px solid #06459e;
    color: #fff;
    text-shadow: 1px 1px #16448a;
    box-sizing: border-box;
}
.job-title-text {
    font-size: .96rem;
    font-weight: 700;
    flex: 1;
    min-width: 0;
}
.score {
    min-width: 2.05rem;
    text-align: center;
    background: linear-gradient(#72d377, #33a542);
    color: white;
    border: 1px solid #176f27;
    padding: .13rem .33rem;
    border-radius: 3px;
    font-size: .76rem;
    font-weight: bold;
    text-shadow: 1px 1px #287332;
}
.salary {
    flex: 0 0 auto;
    background: #ffdf57;
    color: #493900;
    border: 1px solid #a47b00;
    padding: .13rem .34rem;
    border-radius: 3px;
    font-size: .73rem;
    font-weight: bold;
    text-shadow: none;
}
.meta {
    font-size: .80rem;
    color: #444;
    margin: .08rem 0 .30rem;
}
.badge {
    display: inline-block;
    padding: .13rem .34rem;
    margin: 0 .22rem .18rem 0;
    font-size: .66rem;
    font-weight: bold;
    border: 1px solid #7f9db9;
    background: #dbe8f7;
    color: #284b77;
    text-transform: uppercase;
}
.apply { background: #39b54a; color: #fff; border-color: #1c7d2b; }
.strong { background: #ffd65a; color: #4e3900; border-color: #a87800; }
.stretch { background: #e2eaf3; color: #274a75; border-color: #7f9db9; }
.skip { background: #efc2bd; color: #721b14; border-color: #b25349; }
.dup {
    background: #fff7a8;
    border: 1px solid #d0bd3e;
    color: #4c4314;
    padding: .34rem .46rem;
    margin: .24rem 0 .34rem;
    font-size: .76rem;
}

/* XP buttons */
.stButton > button,
.stLinkButton > a {
    background: linear-gradient(#fff, #e5e5df) !important;
    border: 1px solid #003c74 !important;
    box-shadow: inset 1px 1px #fff !important;
    color: #111 !important;
    border-radius: 3px !important;
    font-weight: 700 !important;
    min-height: 1.95rem !important;
    padding-top: .15rem !important;
    padding-bottom: .15rem !important;
}
.stButton > button:hover,
.stLinkButton > a:hover {
    background: linear-gradient(#fffef0, #f2e7ad) !important;
}

/* Kill the black modern-looking select arrow block */
div[data-testid="stSelectbox"] div[data-baseweb="select"],
div[data-testid="stMultiSelect"] div[data-baseweb="select"] {
    background: #fff !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div,
div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div,
div[data-baseweb="select"] > div,
[role="combobox"] {
    background: #fff !important;
    color: #111 !important;
    border-color: #7f9db9 !important;
    border-radius: 2px !important;
}
div[data-baseweb="select"] *,
div[data-testid="stSelectbox"] *,
div[data-testid="stMultiSelect"] * {
    color: #111 !important;
}
div[data-baseweb="select"] svg,
div[data-testid="stSelectbox"] svg,
div[data-testid="stMultiSelect"] svg {
    fill: #111 !important;
    color: #111 !important;
}
[data-baseweb="tag"] {
    background: #dbe8f7 !important;
    border: 1px solid #7f9db9 !important;
    border-radius: 2px !important;
}
[data-baseweb="tag"] *,
[data-baseweb="tag"] span {
    color: #10479d !important;
}

/* Score explanation = XP details pane */
div[data-testid="stExpander"] {
    border: 1px solid #7f9db9 !important;
    background: #fff !important;
    border-radius: 2px !important;
    max-width: 390px;
}
div[data-testid="stExpander"] summary {
    background: linear-gradient(#f7fbff, #dceaf8) !important;
    min-height: 1.72rem;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
div[data-testid="stExpander"] summary p {
    color: #10479d !important;
    font-size: .76rem;
    font-weight: 700;
}
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] li,
div[data-testid="stExpander"] strong {
    color: #111 !important;
}

[data-testid="stToggle"] p,
.stMultiSelect label p,
.stSelectbox label p,
.stFileUploader label p {
    color: #111 !important;
}
.stCaption p,
[data-testid="stCaptionContainer"] p {
    color: #4e5f6f !important;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #7f9db9;
    border-radius: 0;
    overflow: hidden;
}

.taskbar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 35px;
    background: linear-gradient(#2e7df1, #0757c8);
    z-index: 9998;
    color: white;
    padding: .35rem .5rem;
    box-shadow: 0 -1px 4px #0005;
}
.start {
    background: linear-gradient(#6bc65c, #2e9a2e);
    border: 1px solid #1d7d1d;
    border-radius: 0 14px 14px 0;
    padding: .27rem 1rem;
    font-weight: bold;
    font-style: italic;
    text-shadow: 1px 1px #1c681d;
}
.task-name {
    margin-left: .55rem;
    background: #1e66c9;
    border: 1px solid #0e4fae;
    padding: .23rem .7rem;
    min-width: 220px;
    display: inline-block;
}

@media(max-width:850px) {
    .block-container { padding-left: .5rem; padding-right: .5rem; }
    .task-name { display: none; }
    .job-titlebar { flex-wrap: wrap; }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="xp-menubar">File &nbsp; View &nbsp; Tools &nbsp; Help</div>', unsafe_allow_html=True)
section = st.radio(
    "Navigation",
    ["🏠 Job Market", "🌐 Market Coverage", "📂 My Applications"],
    horizontal=True,
    label_visibility="collapsed",
)

history = load_history(HISTORY_PATH)
score_details = {}
history_matches = {}
rows = []

for raw in list_jobs():
    score, detail = score_job(raw, PROFILE)
    job = dict(raw)
    job["score"] = score
    job["verdict"] = detail["verdict"]
    match = match_history(job, history)
    job["history_match"] = match["match_type"] if match else None
    if match:
        history_matches[job["id"]] = match
    score_details[job["id"]] = detail
    rows.append(job)

df = pd.DataFrame(rows) if rows else pd.DataFrame()
statuses = ["new", "saved", "applied", "screen", "interview", "final", "offer", "rejected", "withdrawn"]


def money(value):
    if value is None or pd.isna(value):
        return None
    value = float(value)
    return f"${value/1000:.0f}K" if value >= 1000 else f"${value:,.0f}"


def salary_label(row):
    low = money(row.get("salary_min"))
    high = money(row.get("salary_max"))
    if low and high:
        return f"{low}–{high}"
    if low:
        return f"{low}+"
    if high:
        return f"Up to {high}"
    return None


def explain(row):
    details = score_details[row["id"]]
    with st.expander(f"Why {int(row['score'])}?"):
        for label, key in [
            ("Title / job family", "title"),
            ("Skills", "skills"),
            ("Seniority", "seniority"),
            ("Process / operations", "process_ops"),
            ("CRM / Power Platform", "crm_power_platform"),
            ("Location / remote", "location"),
            ("Compensation", "salary"),
        ]:
            st.write(f"**{label}:** {details[key]['score']}/{details[key]['max']}")
        matched = list(dict.fromkeys(
            details["skills"].get("strong_matches", [])
            + details["skills"].get("secondary_matches", [])
            + details["process_ops"].get("matches", [])
            + details["crm_power_platform"].get("matches", [])
        ))
        if matched:
            st.write("**Matched signals:** " + ", ".join(matched[:14]))
        for finding in details.get("hard_requirements", {}).get("findings", []):
            years = f"{finding.get('years')}+ years" if finding.get("years") else "direct experience"
            st.error(f"Hard requirement gap: {years} in {finding['domain']}.")


if section == "🏠 Job Market":
    refresh_col, note_col = st.columns([1, 4])
    with refresh_col:
        if st.button("🔄 Refresh Market", width="stretch"):
            with st.spinner("Checking employer career systems..."):
                run_collectors()
            st.rerun()
    with note_col:
        st.caption("Live ATS feeds + verified discovery sources")

    if df.empty:
        st.info("No jobs loaded yet. Click Refresh Market.")
        st.stop()

    active = df[(df["status"].isin(["new", "saved"])) & (df["history_match"] != "exact")].copy()

    st.markdown('<div class="xp-section">📊 Market Pulse</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Market Watch", len(df))
    c2.metric("Apply Now", int((active["verdict"] == "APPLY").sum()))
    c3.metric("Strong Matches", int((active["verdict"] == "STRONG CONSIDER").sum()))
    c4.metric("Already Applied", int((df["history_match"] == "exact").sum()))
    c5.metric("Review Duplicates", int((df["history_match"] == "possible").sum()))

    st.markdown('<div class="xp-section">📂 Today’s Shortlist</div>', unsafe_allow_html=True)
    st.caption(f"Duplicate guard active · {len(history)} private application-history records loaded")

    show_processed = st.toggle("Show jobs I've already handled")
    show_exact = st.toggle("Show jobs matched to a previous application")

    f1, f2, f3 = st.columns(3)
    with f1:
        verdict_filter = st.multiselect(
            "Verdict",
            ["APPLY", "STRONG CONSIDER", "STRETCH", "SKIP"],
            default=["APPLY", "STRONG CONSIDER", "STRETCH"],
        )
    with f2:
        company_filter = st.multiselect("Company", sorted(df["company"].dropna().unique()))
    with f3:
        status_filter = st.multiselect("Status", statuses)

    view = df[df["verdict"].isin(verdict_filter)].copy()
    if not show_processed and not status_filter:
        view = view[view["status"].isin(["new", "saved"])]
    if not show_exact:
        view = view[view["history_match"] != "exact"]
    if company_filter:
        view = view[view["company"].isin(company_filter)]
    if status_filter:
        view = view[view["status"].isin(status_filter)]
    view = view.sort_values(["score", "date_found"], ascending=[False, False])

    for _, row in view.iterrows():
        with st.container(border=True):
            pay = salary_label(row)
            pay_html = f'<span class="salary">💵 {pay}</span>' if pay else ""
            st.markdown(
                f'<div class="job-titlebar"><span class="score">{int(row["score"])}</span>'
                f'<span class="job-title-text">{row["title"]}</span>{pay_html}</div>',
                unsafe_allow_html=True,
            )

            left, right = st.columns([5.6, 1])
            with left:
                st.markdown(
                    f'<div class="meta"><b>{row["company"]}</b> · {row["location"] or "Location not listed"}</div>',
                    unsafe_allow_html=True,
                )

                match = history_matches.get(row["id"])
                if match and match["match_type"] == "possible":
                    prior = match["prior"]
                    st.markdown(
                        f'<div class="dup">⚠ Possible duplicate · Previously applied to '
                        f'<b>{prior.get("title") or "another role"}</b> at {prior.get("company", row["company"])}</div>',
                        unsafe_allow_html=True,
                    )

                klass = (
                    "apply" if row["verdict"] == "APPLY"
                    else "strong" if row["verdict"] == "STRONG CONSIDER"
                    else "stretch" if row["verdict"] == "STRETCH"
                    else "skip"
                )
                st.markdown(
                    f'<span class="badge {klass}">{row["verdict"]}</span>'
                    f'<span class="badge">{row["status"]}</span>'
                    f'<span class="badge">{row.get("source") or "unknown"}</span>',
                    unsafe_allow_html=True,
                )

                action_col, why_col, spacer_col = st.columns([1, 2.4, 3.2])
                with action_col:
                    if row.get("url"):
                        st.link_button("Open Posting", row["url"])
                with why_col:
                    explain(row)

            with right:
                current = row["status"] if row["status"] in statuses else "new"
                new_status = st.selectbox(
                    "Status",
                    statuses,
                    index=statuses.index(current),
                    key=f"status-{row['id']}",
                )
                if new_status != row["status"]:
                    update_status(int(row["id"]), new_status)
                    st.rerun()

elif section == "🌐 Market Coverage":
    st.markdown('<div class="xp-section">🌐 Market Coverage</div>', unsafe_allow_html=True)
    live = pd.DataFrame(LIVE_REGISTRY["employers"])
    watch = pd.DataFrame(WATCHLIST["employers"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Connected Employers", len(live))
    c2.metric("Expansion Watchlist", len(watch))
    c3.metric("High Priority Gaps", int((watch["priority"] == "high").sum()))
    st.dataframe(live, width="stretch", hide_index=True)
    st.dataframe(watch, width="stretch", hide_index=True)

else:
    st.markdown('<div class="xp-section">📂 My Applications</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Import application history", type=["json"])
    if uploaded:
        try:
            payload = json.loads(uploaded.getvalue().decode())
            items = payload.get("applications", []) if isinstance(payload, dict) else payload
            save_history(HISTORY_PATH, [x for x in items if isinstance(x, dict)])
            st.success("History imported.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    if history:
        st.dataframe(pd.DataFrame(history), width="stretch", hide_index=True)
    if not df.empty:
        handled = df[~df["status"].isin(["new", "saved"])]
        st.dataframe(handled, width="stretch", hide_index=True)

st.markdown(
    '<div class="taskbar"><span class="start">🪟 start</span>'
    '<span class="task-name">📁 Indy Opportunity Intelligence</span></div>',
    unsafe_allow_html=True,
)
