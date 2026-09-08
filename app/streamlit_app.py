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
from profile_config import load_profile, load_profile_template, profile_source, save_user_profile
from run_collectors import run as run_collectors

WATCHLIST = json.loads((ROOT / "data" / "market_watchlist.json").read_text())
LIVE_REGISTRY = json.loads((ROOT / "data" / "employers.json").read_text())
HISTORY_PATH = ROOT / "data" / "application_history.json"

st.set_page_config(
    page_title="Opportunity Intelligence",
    page_icon="🪟",
    layout="wide",
)

st.markdown(
    """
<style>
:root {
    --xp-blue: #0a5bd8;
    --xp-blue-dark: #0753c7;
    --xp-blue-line: #06459e;
    --xp-ivory: #ece9d8;
    --xp-card: #fffef5;
    --xp-white: #ffffff;
    --xp-border: #7f9db9;
    --xp-text: #111111;
    --xp-link: #10479d;
    --xp-window-width: min(1540px, calc(100vw - 48px));
}

html, body, [class*="css"] {
    font-family: Tahoma, Arial, sans-serif;
}
html, body, .stApp {
    overflow-x: hidden !important;
}

/* Bliss-inspired desktop */
.stApp {
    color: var(--xp-text);
    background: linear-gradient(
        #4b9df4 0 42%,
        #bfe4ff 59%,
        #79cf5c 60%,
        #3d9d34 100%
    );
}
.stApp:before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background:
      radial-gradient(ellipse at 12% 18%, rgba(255,255,255,.92) 0 2.4%, transparent 2.8%),
      radial-gradient(ellipse at 18% 17%, rgba(255,255,255,.76) 0 3.2%, transparent 3.6%),
      radial-gradient(ellipse at 74% 21%, rgba(255,255,255,.86) 0 2.5%, transparent 2.9%),
      radial-gradient(ellipse at 80% 20%, rgba(255,255,255,.72) 0 3.3%, transparent 3.7%),
      radial-gradient(ellipse at 20% 105%, #318c2c 0 34%, transparent 34.4%),
      radial-gradient(ellipse at 55% 110%, #68c94e 0 44%, transparent 44.4%),
      radial-gradient(ellipse at 92% 108%, #45a83b 0 38%, transparent 38.4%);
}

/* Fixed Explorer window underneath the entire scrolling page */
.stApp:after {
    content: "";
    position: fixed;
    z-index: 0;
    inset-block: 0;
    left: 50%;
    transform: translateX(-50%);
    width: var(--xp-window-width);
    background: var(--xp-ivory);
    border-left: 1px solid #7697bd;
    border-right: 1px solid #7697bd;
    box-shadow: 0 0 25px #285b8a88;
    pointer-events: none;
}
.block-container,
[data-testid="stMainBlockContainer"] {
    position: relative;
    z-index: 1;
    width: var(--xp-window-width) !important;
    max-width: var(--xp-window-width) !important;
    margin: 0 auto !important;
    padding: .65rem 1.2rem 4rem !important;
    background: transparent !important;
    min-height: 100vh;
    box-sizing: border-box;
    overflow-x: hidden !important;
}
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
[data-testid="stColumn"] {
    max-width: 100%;
    box-sizing: border-box;
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

div[role="radiogroup"] {
    background: #ece9d8;
    border: 1px solid #aca899;
    padding: .22rem;
    width: fit-content;
    max-width: 100%;
    margin: .25rem 0 .55rem;
    box-shadow: inset 1px 1px #fff;
    flex-wrap: wrap !important;
}
div[role="radiogroup"] label {
    padding: .28rem .48rem;
    border: 1px solid transparent;
    border-radius: 2px;
}
div[role="radiogroup"] label:hover {
    background: #fff;
    border-color: var(--xp-border);
}
div[role="radiogroup"] p {
    color: #111 !important;
    font-weight: bold;
    font-size: .84rem;
}

.xp-section {
    background: linear-gradient(#3f93ff, var(--xp-blue-dark));
    color: white;
    font-weight: bold;
    padding: .36rem .56rem;
    border: 1px solid var(--xp-blue-line);
    border-radius: 5px 5px 0 0;
    margin-top: .45rem;
    text-shadow: 1px 1px #16448a;
}
.xp-help {
    background: #fff7a8;
    border: 1px solid #d0bd3e;
    color: #4c4314;
    padding: .55rem .65rem;
    margin: .35rem 0 .65rem;
    font-size: .80rem;
}
.xp-profile-summary {
    background: #fffef5;
    border: 1px solid #aca899;
    box-shadow: inset 1px 1px #fff;
    padding: .55rem .7rem;
    margin: .3rem 0 .6rem;
    color: #222;
    font-size: .82rem;
}

/* Metrics */
div[data-testid="stMetric"] {
    background: var(--xp-card) !important;
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

/* Opaque job cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--xp-card) !important;
    border: 1px solid var(--xp-border) !important;
    border-radius: 4px !important;
    box-shadow: inset 1px 1px #fff !important;
    margin-bottom: .48rem;
    overflow: hidden !important;
    max-width: 100% !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stColumn"] {
    background-color: var(--xp-card) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    padding-top: .12rem !important;
    padding-bottom: .12rem !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] p,
div[data-testid="stVerticalBlockBorderWrapper"] label {
    color: #111 !important;
}

.job-titlebar {
    display: flex;
    align-items: center;
    gap: .45rem;
    width: 100%;
    max-width: 100%;
    padding: .34rem .48rem;
    margin: -.02rem 0 .34rem;
    background: linear-gradient(180deg, #3f93ff 0%, #0c63df 48%, #0753c7 100%);
    border: 1px solid var(--xp-blue-line);
    color: #fff !important;
    text-shadow: 1px 1px #16448a;
    box-sizing: border-box;
}
.job-title-text {
    color: #fff !important;
    font-size: .96rem;
    font-weight: 700;
    flex: 1;
    min-width: 0;
    overflow-wrap: anywhere;
}
.score {
    min-width: 2.05rem;
    text-align: center;
    background: linear-gradient(#72d377, #33a542);
    color: white !important;
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
    color: #493900 !important;
    border: 1px solid #a47b00;
    padding: .13rem .34rem;
    border-radius: 3px;
    font-size: .73rem;
    font-weight: bold;
    text-shadow: none;
}
.meta {
    font-size: .80rem;
    color: #333 !important;
    margin: .06rem 0 .28rem;
}
.meta b { color: #111 !important; }
.badge {
    display: inline-block;
    padding: .13rem .34rem;
    margin: 0 .22rem .18rem 0;
    font-size: .66rem;
    font-weight: bold;
    border: 1px solid var(--xp-border);
    background: #dbe8f7;
    color: #284b77 !important;
    text-transform: uppercase;
}
.apply { background: #39b54a; color: #fff !important; border-color: #1c7d2b; }
.strong { background: #ffd65a; color: #4e3900 !important; border-color: #a87800; }
.stretch { background: #e2eaf3; color: #274a75 !important; border-color: #7f9db9; }
.skip { background: #efc2bd; color: #721b14 !important; border-color: #b25349; }
.dup {
    background: #fff7a8;
    border: 1px solid #d0bd3e;
    color: #4c4314 !important;
    padding: .34rem .46rem;
    margin: .22rem 0 .32rem;
    font-size: .76rem;
}

/* XP controls */
.stButton > button,
.stLinkButton > a {
    background: linear-gradient(#fff, #e5e5df) !important;
    border: 1px solid #003c74 !important;
    box-shadow: inset 1px 1px #fff !important;
    color: #111 !important;
    border-radius: 3px !important;
    font-weight: 700 !important;
    min-height: 1.95rem !important;
}
.stButton > button:hover,
.stLinkButton > a:hover {
    background: linear-gradient(#fffef0, #f2e7ad) !important;
}

/* Inputs */
input, textarea,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background: #fff !important;
    color: #111 !important;
    border-color: var(--xp-border) !important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"],
div[data-testid="stSelectbox"] [data-baseweb="select"] *,
div[data-testid="stMultiSelect"] [data-baseweb="select"],
div[data-testid="stMultiSelect"] [data-baseweb="select"] * {
    background-color: #fff !important;
    color: #111 !important;
}
div[data-testid="stSelectbox"] [role="combobox"],
div[data-testid="stMultiSelect"] [role="combobox"],
div[data-baseweb="select"] > div {
    background: #fff !important;
    border-color: var(--xp-border) !important;
    border-radius: 2px !important;
    color: #111 !important;
}
div[data-testid="stSelectbox"] svg,
div[data-testid="stMultiSelect"] svg,
div[data-baseweb="select"] svg {
    fill: #111 !important;
    color: #111 !important;
    background: #fff !important;
}
[data-baseweb="tag"] {
    background: #dbe8f7 !important;
    border: 1px solid var(--xp-border) !important;
    border-radius: 2px !important;
}
[data-baseweb="tag"] *,
[data-baseweb="tag"] span {
    background: transparent !important;
    color: var(--xp-link) !important;
}

/* Why score pane */
div[data-testid="stExpander"] {
    border: 1px solid var(--xp-border) !important;
    background: #fff !important;
    border-radius: 2px !important;
    max-width: 390px;
}
div[data-testid="stExpander"] > div,
div[data-testid="stExpander"] details,
div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: #fff !important;
}
div[data-testid="stExpander"] summary {
    background: linear-gradient(#f7fbff, #dceaf8) !important;
    min-height: 1.72rem;
}
div[data-testid="stExpander"] summary p {
    color: var(--xp-link) !important;
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
.stFileUploader label p,
.stTextInput label p,
.stTextArea label p,
.stNumberInput label p {
    color: #111 !important;
}
.stCaption p,
[data-testid="stCaptionContainer"] p {
    color: #4e5f6f !important;
}
div[data-testid="stDataFrame"] {
    border: 1px solid var(--xp-border);
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

@media (max-width: 1100px) {
    :root { --xp-window-width: calc(100vw - 24px); }
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    [data-testid="stColumn"] {
        min-width: min(100%, 280px) !important;
        flex: 1 1 280px !important;
    }
}
@media (max-width: 700px) {
    :root { --xp-window-width: calc(100vw - 8px); }
    .block-container,
    [data-testid="stMainBlockContainer"] {
        padding-left: .45rem !important;
        padding-right: .45rem !important;
    }
    .task-name { display: none; }
    .job-titlebar { flex-wrap: wrap; }
    div[role="radiogroup"] { width: 100%; }
}
</style>
""",
    unsafe_allow_html=True,
)


def split_terms(value: str) -> list[str]:
    return [item.strip().lower() for item in value.replace("\n", ",").split(",") if item.strip()]


def join_terms(values) -> str:
    return ", ".join(values or [])


PROFILE = load_profile()
TEMPLATE = load_profile_template()
profile_name = PROFILE.get("name") or "Job Seeker"

st.markdown(
    '<div class="xp-menubar">File &nbsp; View &nbsp; Favorites &nbsp; Tools &nbsp; Help'</n    f'<span style="float:right;color:#16418a"><b>{profile_name}</b></span></div>',
    unsafe_allow_html=True,
)

section = st.radio(
    "Navigation",
    ["🏠 Job Market", "🌐 Market Coverage", "📂 My Applications", "🛠 Control Panel"],
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
statuses = [
    "new", "saved", "applied", "screen", "interview",
    "final", "offer", "rejected", "withdrawn",
]


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
            ("Core work themes", "process_ops"),
            ("Bonus skills", "crm_power_platform"),
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
            with st.spinner("Checking employer career systems for your market..."):
                run_collectors()
            st.rerun()
    with note_col:
        locations = PROFILE.get("preferred_location_terms", [])
        market_label = ", ".join(locations[:4]) if locations else "No local market configured"
        remote_label = " + U.S. remote" if PROFILE.get("remote_ok", True) else ""
        st.caption(f"Current market: {market_label}{remote_label}")

    if df.empty:
        st.info("No jobs loaded yet. Click Refresh Market.")
        st.stop()

    active = df[
        (df["status"].isin(["new", "saved"]))
        & (df["history_match"] != "exact")
    ].copy()

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
                f'<div class="job-titlebar">'
                f'<span class="score">{int(row["score"])}</span>'
                f'<span class="job-title-text">{row["title"]}</span>'
                f'{pay_html}</div>',
                unsafe_allow_html=True,
            )

            left, right = st.columns([5.6, 1])
            with left:
                st.markdown(
                    f'<div class="meta"><b>{row["company"]}</b> · '
                    f'{row["location"] or "Location not listed"}</div>',
                    unsafe_allow_html=True,
                )
                match = history_matches.get(row["id"])
                if match and match["match_type"] == "possible":
                    prior = match["prior"]
                    st.markdown(
                        f'<div class="dup">⚠ Possible duplicate · Previously applied to '
                        f'<b>{prior.get("title") or "another role"}</b> at '
                        f'{prior.get("company", row["company"])}</div>',
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

elif section == "📂 My Applications":
    st.markdown('<div class="xp-section">📂 My Applications</div>', unsafe_allow_html=True)
    st.caption("Application history is private and separate from the public project.")
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
        if not handled.empty:
            st.markdown("### Tracked in this app")
            st.dataframe(handled, width="stretch", hide_index=True)

else:
    st.markdown('<div class="xp-section">🛠 Control Panel · Job Search Profile</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="xp-help"><b>No coding required.</b> Change these settings and click '
        '<b>Save Profile</b>. Your job scores and local market will update automatically.</div>',
        unsafe_allow_html=True,
    )

    current_locations = PROFILE.get("preferred_location_terms", [])
    home_city = PROFILE.get("home_city", current_locations[0] if current_locations else "")
    home_state = PROFILE.get("home_state", "")
    nearby_default = [x for x in current_locations if x not in {home_city.lower(), home_state.lower()}]

    with st.form("profile_setup"):
        st.markdown("### 👤 About you")
        name = st.text_input("Your name", value=PROFILE.get("name", "Job Seeker"))

        loc1, loc2, loc3 = st.columns(3)
        with loc1:
            city = st.text_input("Home city", value=home_city)
        with loc2:
            state = st.text_input("State / province", value=home_state)
        with loc3:
            remote_ok = st.checkbox("Include U.S. remote jobs", value=bool(PROFILE.get("remote_ok", True)))

        nearby = st.text_input(
            "Nearby cities / areas to include (comma separated)",
            value=join_terms(nearby_default),
            help="Example: Carmel, Fishers, Indianapolis",
        )

        st.markdown("### 💼 What work are you looking for?")
        target_titles = st.text_area(
            "Target job titles (comma separated)",
            value=join_terms(PROFILE.get("target_titles", TEMPLATE.get("target_titles", []))),
            height=80,
        )
        seniority = st.text_input(
            "Preferred levels / title words",
            value=join_terms(PROFILE.get("seniority_preferences", TEMPLATE.get("seniority_preferences", []))),
            help="Example: analyst, senior analyst, specialist, manager",
        )
        avoid_seniority = st.text_input(
            "Titles or seniority to de-prioritize",
            value=join_terms(PROFILE.get("deprioritize_seniority", TEMPLATE.get("deprioritize_seniority", []))),
            help="Example: director, vice president, chief",
        )

        st.markdown("### 🧰 Your skills")
        strong_skills = st.text_area(
            "Strong skills (comma separated)",
            value=join_terms(PROFILE.get("strong_skills", TEMPLATE.get("strong_skills", []))),
            height=90,
        )
        secondary_skills = st.text_area(
            "Skills you can use but are less central",
            value=join_terms(PROFILE.get("secondary_skills", TEMPLATE.get("secondary_skills", []))),
            height=75,
        )
        focus_terms = st.text_area(
            "Core work themes you enjoy",
            value=join_terms(PROFILE.get("focus_terms", TEMPLATE.get("focus_terms", []))),
            height=75,
            help="Examples: project management, process improvement, customer success, reporting, operations",
        )
        bonus_terms = st.text_input(
            "Bonus keywords / tools",
            value=join_terms(PROFILE.get("bonus_terms", TEMPLATE.get("bonus_terms", []))),
            help="These help break ties; they are not mandatory.",
        )

        st.markdown("### 🏢 Domain experience")
        domain_options = [
            "HR / People Operations",
            "Healthcare / Clinical",
            "Finance / Accounting",
            "Insurance",
            "Legal / Compliance",
            "Supply Chain / Procurement",
        ]
        domain_strengths = st.multiselect(
            "Areas where you have meaningful professional experience",
            domain_options,
            default=[x for x in PROFILE.get("domain_strengths", []) if x in domain_options],
            help="This prevents a job from being penalized for domain experience you actually have.",
        )

        st.markdown("### 💰 Compensation & dealbreakers")
        money1, money2 = st.columns(2)
        with money1:
            salary_floor = st.number_input(
                "Minimum salary",
                min_value=0,
                step=5000,
                value=int(PROFILE.get("salary_floor", TEMPLATE.get("salary_floor", 0)) or 0),
            )
        with money2:
            salary_target = st.number_input(
                "Target salary",
                min_value=0,
                step=5000,
                value=int(PROFILE.get("salary_target", TEMPLATE.get("salary_target", 0)) or 0),
            )
        avoid_terms = st.text_input(
            "Dealbreakers / avoid terms",
            value=join_terms(PROFILE.get("avoid_terms", TEMPLATE.get("avoid_terms", []))),
            help="Example: commission only, contract only, door-to-door",
        )

        submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)

    if submitted:
        locations = []
        if city.strip():
            locations.append(city.strip().lower())
        if state.strip():
            locations.append(state.strip().lower())
        locations.extend(split_terms(nearby))
        locations = list(dict.fromkeys(locations))

        targets = split_terms(target_titles)
        strong = split_terms(strong_skills)
        secondary = split_terms(secondary_skills)
        focus = split_terms(focus_terms)
        bonus = split_terms(bonus_terms)

        new_profile = dict(TEMPLATE)
        new_profile.update({
            "name": name.strip() or "Job Seeker",
            "home_city": city.strip(),
            "home_state": state.strip(),
            "target_titles": targets,
            "title_family_terms": targets,
            "strong_skills": strong,
            "secondary_skills": secondary,
            "focus_terms": focus or strong,
            "bonus_terms": bonus,
            "preferred_location_terms": locations,
            "remote_ok": remote_ok,
            "salary_floor": int(salary_floor),
            "salary_target": int(salary_target),
            "avoid_terms": split_terms(avoid_terms),
            "seniority_preferences": split_terms(seniority),
            "deprioritize_seniority": split_terms(avoid_seniority),
            "domain_strengths": domain_strengths,
        })
        save_user_profile(new_profile)
        st.success("Profile saved. Your existing jobs are being rescored for this profile now.")
        st.rerun()

    st.markdown('<div class="xp-section">ℹ Current Profile</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="xp-profile-summary"><b>{PROFILE.get("name", "Job Seeker")}</b><br>'
        f'Market: {join_terms(PROFILE.get("preferred_location_terms", [])) or "not configured"}<br>'
        f'Remote: {"Yes" if PROFILE.get("remote_ok", True) else "No"}<br>'
        f'Target roles: {join_terms(PROFILE.get("target_titles", [])) or "not configured"}<br>'
        f'Profile storage: {profile_source()}</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="taskbar">'
    '<span class="start">🪟 start</span>'
    f'<span class="task-name">📁 Opportunity Intelligence · {profile_name}</span>'
    '</div>',
    unsafe_allow_html=True,
)
