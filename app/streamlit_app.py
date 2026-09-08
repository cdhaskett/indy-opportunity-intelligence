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

st.set_page_config(page_title="Indy Opportunity Intelligence", page_icon="🧭", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --bg: #0b0f14;
        --panel: #111821;
        --panel-2: #151e28;
        --panel-3: #1a2530;
        --ink: #f4f1ea;
        --muted: #96a1ad;
        --line: #273542;
        --teal: #47c6b3;
        --teal-soft: #153a37;
        --gold: #d6a85f;
        --gold-soft: #3d3020;
        --copper: #d9784c;
        --slate: #7f8d9a;
        --red: #ef6b68;
    }

    html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    .stApp { background: var(--bg); color: var(--ink); }
    .block-container { max-width: 1240px; padding-top: 1.35rem; padding-bottom: 4rem; }

    h1, h2, h3, p, label, .stMarkdown { color: var(--ink); }
    h2 { letter-spacing: -.025em; }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 1.35rem 1.55rem 1.45rem;
        border: 1px solid var(--line);
        background: linear-gradient(135deg, #121a23 0%, #0f171f 64%, #172229 100%);
        border-radius: 18px;
        margin-bottom: .8rem;
        box-shadow: 0 18px 48px rgba(0,0,0,.24);
    }
    .hero:after {
        content: "";
        position: absolute;
        width: 220px;
        height: 220px;
        border: 1px solid rgba(71,198,179,.16);
        border-radius: 50%;
        right: -80px;
        top: -105px;
        box-shadow: 0 0 0 34px rgba(71,198,179,.025), 0 0 0 68px rgba(71,198,179,.018);
    }
    .hero-kicker {
        color: var(--copper);
        font-size: .69rem;
        font-weight: 800;
        letter-spacing: .18em;
        text-transform: uppercase;
        margin-bottom: .38rem;
    }
    .hero-title {
        color: var(--ink);
        font-size: 2.05rem;
        line-height: 1.08;
        font-weight: 780;
        letter-spacing: -.035em;
        margin: 0;
    }
    .hero-subtitle {
        color: var(--muted);
        font-size: .92rem;
        margin-top: .48rem;
        max-width: 840px;
    }

    div[role="radiogroup"] {
        display: flex;
        gap: .35rem;
        background: #0f161e;
        border: 1px solid var(--line);
        padding: .32rem;
        border-radius: 12px;
        width: fit-content;
        margin-bottom: .45rem;
    }
    div[role="radiogroup"] label {
        border-radius: 9px;
        padding: .22rem .45rem;
    }
    div[role="radiogroup"] p { color: #dce3e8 !important; font-weight: 650; }

    div[data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: .72rem .85rem;
        min-height: 92px;
        box-shadow: none;
    }
    div[data-testid="stMetricLabel"] p {
        color: var(--muted) !important;
        font-size: .68rem;
        text-transform: uppercase;
        letter-spacing: .09em;
        font-weight: 780;
    }
    div[data-testid="stMetricValue"] {
        color: var(--ink) !important;
        font-size: 1.55rem;
        font-weight: 740;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--panel) !important;
        border: 1px solid var(--line) !important;
        border-radius: 15px !important;
        box-shadow: 0 10px 28px rgba(0,0,0,.16);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div { padding-top: .25rem; padding-bottom: .25rem; }

    .job-title {
        color: var(--ink);
        font-size: 1.18rem;
        font-weight: 760;
        line-height: 1.24;
        letter-spacing: -.015em;
        margin-bottom: .3rem;
    }
    .score-pill {
        display: inline-block;
        min-width: 2.25rem;
        text-align: center;
        padding: .23rem .5rem;
        margin-right: .55rem;
        border-radius: 8px;
        background: #203b3a;
        border: 1px solid #2d5b57;
        color: #9ce9dd;
        font-size: .78rem;
        font-weight: 800;
        vertical-align: 2px;
    }
    .salary-pill {
        display: inline-block;
        padding: .22rem .5rem;
        margin-left: .5rem;
        border-radius: 8px;
        background: #30261b;
        border: 1px solid #5b462d;
        color: #f0c98b;
        font-size: .77rem;
        font-weight: 760;
        vertical-align: 2px;
    }
    .job-meta { color: var(--muted); font-size: .87rem; margin-bottom: .62rem; }
    .job-meta strong { color: #dfe6ea; }

    .verdict-row { display: flex; gap: .38rem; align-items: center; flex-wrap: wrap; margin: .35rem 0 .55rem; }
    .verdict-badge, .meta-badge {
        display: inline-block;
        padding: .2rem .48rem;
        border-radius: 7px;
        font-size: .68rem;
        font-weight: 820;
        letter-spacing: .055em;
        text-transform: uppercase;
    }
    .verdict-apply { background: var(--teal-soft); border: 1px solid #28675f; color: #7fe1d3; }
    .verdict-strong { background: var(--gold-soft); border: 1px solid #6d5732; color: #efc77f; }
    .verdict-stretch { background: #27313b; border: 1px solid #41505e; color: #bdc7cf; }
    .verdict-skip { background: #3a2224; border: 1px solid #6a383b; color: #f09a97; }
    .meta-badge { background: #18222c; border: 1px solid #2d3a47; color: #9daab5; }

    .duplicate-note {
        border-left: 3px solid var(--gold);
        background: #201c16;
        color: #d9c7a7;
        padding: .58rem .7rem;
        border-radius: 0 8px 8px 0;
        font-size: .82rem;
        margin: .45rem 0 .58rem;
    }
    .duplicate-note strong { color: #f1d59f; }

    .section-eyebrow {
        color: var(--copper);
        text-transform: uppercase;
        letter-spacing: .12em;
        font-size: .66rem;
        font-weight: 800;
        margin-top: .9rem;
        margin-bottom: .08rem;
    }

    .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
    .stCaption p, [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }

    .stButton > button, .stLinkButton > a {
        background: #18232d !important;
        border: 1px solid #344452 !important;
        color: #eef2f4 !important;
        border-radius: 9px !important;
        font-weight: 700 !important;
        min-height: 2.35rem;
    }
    .stButton > button:hover, .stLinkButton > a:hover {
        border-color: var(--teal) !important;
        color: #a9eee4 !important;
    }

    div[data-baseweb="select"] > div {
        background: var(--panel-2) !important;
        border-color: #344351 !important;
        color: var(--ink) !important;
        border-radius: 9px !important;
    }
    div[data-baseweb="select"] * { color: #dfe5e9 !important; }
    [data-baseweb="tag"] { background: #26343f !important; }

    div[data-testid="stExpander"] {
        border-color: #2a3946 !important;
        background: #0f161d;
        border-radius: 9px;
    }
    div[data-testid="stExpander"] summary p { color: #cbd4db !important; font-size: .82rem; }

    [data-testid="stToggle"] p, .stMultiSelect label p, .stSelectbox label p, .stFileUploader label p {
        color: #b9c3ca !important;
    }

    div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
    [data-testid="stAlert"] { border-radius: 9px; }
    hr { border-color: var(--line); }

    @media (max-width: 850px) {
        .hero-title { font-size: 1.62rem; }
        .block-container { padding-left: .9rem; padding-right: .9rem; }
        .salary-pill { margin-left: .15rem; margin-top: .25rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">INDY OPPORTUNITY INTELLIGENCE // MARKET WATCH</div>
      <div class="hero-title">Find the few jobs actually worth your time.</div>
      <div class="hero-subtitle">Central Indiana + remote opportunity discovery, fit scoring, duplicate protection, and application tracking.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

section = st.radio(
    "Navigation",
    ["🔎 Job Market", "🗺️ Market Coverage", "📊 My Applications"],
    horizontal=True,
    label_visibility="collapsed",
)

history = load_history(HISTORY_PATH)
jobs = list_jobs()
rescored_jobs = []
score_details = {}
history_matches = {}

for raw_job in jobs:
    score, detail = score_job(raw_job, PROFILE)
    job = dict(raw_job)
    job["score"] = score
    job["verdict"] = detail["verdict"]
    match = match_history(job, history)
    if match:
        history_matches[job["id"]] = match
        job["history_match"] = match["match_type"]
    else:
        job["history_match"] = None
    rescored_jobs.append(job)
    score_details[job["id"]] = detail


df = pd.DataFrame(rescored_jobs) if rescored_jobs else pd.DataFrame()
status_options = ["new", "saved", "applied", "screen", "interview", "final", "offer", "rejected", "withdrawn"]


def money(value):
    if value is None or pd.isna(value):
        return None
    value = float(value)
    if value >= 1000:
        return f"${value/1000:.0f}K"
    return f"${value:,.0f}"


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


def verdict_class(verdict):
    return {
        "APPLY": "verdict-apply",
        "STRONG CONSIDER": "verdict-strong",
        "STRETCH": "verdict-stretch",
        "SKIP": "verdict-skip",
    }.get(verdict, "verdict-stretch")


def render_score_explanation(row):
    details = score_details[row["id"]]
    with st.expander(f"Why {int(row['score'])}?"):
        score_rows = [
            ("Title / job family", details["title"]["score"], details["title"]["max"]),
            ("Skills", details["skills"]["score"], details["skills"]["max"]),
            ("Seniority", details["seniority"]["score"], details["seniority"]["max"]),
            ("Process / operations", details["process_ops"]["score"], details["process_ops"]["max"]),
            ("CRM / Power Platform bonus", details["crm_power_platform"]["score"], details["crm_power_platform"]["max"]),
            ("Location / remote", details["location"]["score"], details["location"]["max"]),
            ("Compensation", details["salary"]["score"], details["salary"]["max"]),
        ]
        for label, earned, possible in score_rows:
            st.write(f"**{label}:** {earned}/{possible}")

        matched = []
        matched.extend(details["skills"].get("strong_matches", []))
        matched.extend(details["skills"].get("secondary_matches", []))
        matched.extend(details["process_ops"].get("matches", []))
        matched.extend(details["crm_power_platform"].get("matches", []))
        matched = list(dict.fromkeys(matched))
        st.write("**Matched signals:** " + (", ".join(matched[:14]) if matched else "No strong keyword signals yet."))

        warnings = details["seniority"].get("warnings", [])
        if warnings:
            st.warning("Seniority warning: " + ", ".join(warnings))

        hard = details.get("hard_requirements", {})
        for finding in hard.get("findings", []):
            years = f"{finding['years']}+ years" if finding.get("years") else "direct experience"
            st.error(f"Hard requirement gap: {years} in {finding['domain']}. This can cap the recommendation.")

        if details["salary"].get("salary_min") is None:
            st.caption("Compensation was not listed, so the role receives neutral partial credit rather than a penalty.")


if section == "🔎 Job Market":
    refresh_col, note_col = st.columns([1, 4])
    with refresh_col:
        if st.button("↻ Refresh market", width="stretch"):
            with st.spinner("Checking employer career systems and rescoring the market..."):
                run_collectors()
            st.success("Market refresh complete.")
            st.rerun()
    with note_col:
        st.caption("Curated Central Indiana + U.S. remote roles from supported employer career systems.")

    if df.empty:
        st.info("No jobs loaded yet. Click **Refresh market** to pull the first market snapshot.")
        st.stop()

    exact_duplicates = int((df["history_match"] == "exact").sum()) if "history_match" in df else 0
    possible_duplicates = int((df["history_match"] == "possible").sum()) if "history_match" in df else 0

    active_queue = df[
        df["status"].isin(["new", "saved"])
        & (df["history_match"] != "exact")
    ].copy()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Market watch", len(df))
    c2.metric("Apply now", int((active_queue["verdict"] == "APPLY").sum()))
    c3.metric("Strong", int((active_queue["verdict"] == "STRONG CONSIDER").sum()))
    c4.metric("Already applied", exact_duplicates)
    c5.metric("Review dupes", possible_duplicates)

    st.markdown('<div class="section-eyebrow">ACTIVE QUEUE</div>', unsafe_allow_html=True)
    st.subheader("Today’s Shortlist")
    if history:
        st.caption(f"Duplicate guard active · {len(history)} private application-history records loaded.")
    else:
        st.warning("Duplicate guard is not loaded yet. Import your application history under **My Applications** before applying from this queue.")

    show_processed = st.toggle(
        "Show jobs I've already handled",
        value=False,
        help="Jobs you acted on stay in the database but are hidden from the main queue by default.",
    )
    show_exact_history = st.toggle(
        "Show jobs matched to a previous application",
        value=False,
        help="Exact history matches are hidden by default to protect you from duplicate applications.",
    )

    f1, f2, f3 = st.columns(3)
    with f1:
        verdict_filter = st.multiselect(
            "Verdict",
            ["APPLY", "STRONG CONSIDER", "STRETCH", "SKIP"],
            default=["APPLY", "STRONG CONSIDER", "STRETCH"],
        )
    with f2:
        company_filter = st.multiselect("Company", sorted(df["company"].dropna().unique().tolist()))
    with f3:
        status_filter = st.multiselect("Status", status_options)

    view = df[df["verdict"].isin(verdict_filter)].copy()
    if not show_processed and not status_filter:
        view = view[view["status"].isin(["new", "saved"])]
    if not show_exact_history:
        view = view[view["history_match"] != "exact"]
    if company_filter:
        view = view[view["company"].isin(company_filter)]
    if status_filter:
        view = view[view["status"].isin(status_filter)]
    view = view.sort_values(["score", "date_found"], ascending=[False, False])

    if view.empty:
        st.success("Your current queue is clear. Adjust the filters or refresh the market to see more.")

    for _, row in view.iterrows():
        match = history_matches.get(row["id"])
        salary = salary_label(row)
        with st.container(border=True):
            a, b = st.columns([5.1, 1])
            with a:
                salary_html = f'<span class="salary-pill">{salary}</span>' if salary else ""
                st.markdown(
                    f'<div class="job-title"><span class="score-pill">{int(row["score"])}</span>{row["title"]}{salary_html}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="job-meta"><strong>{row["company"]}</strong> · {row["location"] or "Location not listed"}</div>',
                    unsafe_allow_html=True,
                )

                if match and match["match_type"] == "possible":
                    prior = match["prior"]
                    prior_date = prior.get("date") or prior.get("applied_date") or "date unknown"
                    prior_title = prior.get("title") or "another role"
                    st.markdown(
                        f'<div class="duplicate-note">⚠ <strong>Possible duplicate</strong> · Previously applied to {prior_title} at {prior.get("company", row["company"])} · {prior_date}</div>',
                        unsafe_allow_html=True,
                    )

                source = row.get("source") or "unknown"
                klass = verdict_class(row["verdict"])
                st.markdown(
                    f'<div class="verdict-row"><span class="verdict-badge {klass}">{row["verdict"]}</span><span class="meta-badge">{row["status"]}</span><span class="meta-badge">{source}</span></div>',
                    unsafe_allow_html=True,
                )

                button_col, explain_col = st.columns([1.1, 4.9])
                with button_col:
                    if row.get("url"):
                        st.link_button("Open posting ↗", row["url"])
                with explain_col:
                    render_score_explanation(row)
            with b:
                current_status = row["status"] if row["status"] in status_options else "new"
                new_status = st.selectbox(
                    "Status",
                    status_options,
                    index=status_options.index(current_status),
                    key=f"status-{row['id']}",
                )
                if new_status != row["status"]:
                    update_status(int(row["id"]), new_status)
                    st.rerun()

elif section == "🗺️ Market Coverage":
    st.markdown('<div class="section-eyebrow">SOURCE MAP</div>', unsafe_allow_html=True)
    st.subheader("Market Coverage")
    st.caption("Who the app can collect today — and which Central Indiana employers are next on the integration list.")

    live = pd.DataFrame(LIVE_REGISTRY["employers"])
    watch = pd.DataFrame(WATCHLIST["employers"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Live ATS employers", len(live))
    c2.metric("Expansion watchlist", len(watch))
    c3.metric("High-priority gaps", int((watch["priority"] == "high").sum()))

    st.markdown("### Connected now")
    st.dataframe(
        live[["name", "ats", "priority", "market_note"]].sort_values(["priority", "name"]),
        width="stretch",
        hide_index=True,
    )

    st.markdown("### Expansion watchlist")
    p1, p2 = st.columns(2)
    with p1:
        priority = st.multiselect("Priority", ["high", "medium", "low"], default=["high", "medium"])
    with p2:
        segment = st.multiselect("Segment", sorted(watch["segment"].unique().tolist()))
    watch_view = watch[watch["priority"].isin(priority)].copy() if priority else watch.copy()
    if segment:
        watch_view = watch_view[watch_view["segment"].isin(segment)]
    st.dataframe(
        watch_view[["name", "segment", "priority", "why"]].sort_values(["priority", "segment", "name"]),
        width="stretch",
        hide_index=True,
    )

elif section == "📊 My Applications":
    st.markdown('<div class="section-eyebrow">PRIVATE LEDGER</div>', unsafe_allow_html=True)
    st.subheader("My Applications")
    st.caption("Your private history stays on your computer. It is ignored by Git and is not published to the public repository.")

    st.markdown("### Import application history")
    uploaded = st.file_uploader(
        "Upload the private JSON history file",
        type=["json"],
        help="The file is saved locally as data/application_history.json and is excluded from GitHub by .gitignore.",
    )
    if uploaded is not None:
        try:
            payload = json.loads(uploaded.getvalue().decode("utf-8"))
            rows = payload.get("applications", []) if isinstance(payload, dict) else payload
            rows = [row for row in rows if isinstance(row, dict)]
            save_history(HISTORY_PATH, rows)
            st.success(f"Imported {len(rows)} private application-history records. Duplicate guard is now active.")
            if st.button("Reload app with history"):
                st.rerun()
        except Exception as exc:
            st.error(f"Could not import that history file: {exc}")

    if history:
        st.success(f"Duplicate guard loaded: {len(history)} prior application records.")
        history_df = pd.DataFrame(history)
        display_cols = [c for c in ["company", "title", "date", "status", "requisition_id"] if c in history_df.columns]
        if display_cols:
            st.dataframe(history_df[display_cols], width="stretch", hide_index=True)
    else:
        st.info("No private history file has been loaded yet.")

    st.markdown("### Tracked outcomes from this app")
    if df.empty:
        st.info("No tracked jobs yet.")
        st.stop()

    handled = df[~df["status"].isin(["new", "saved"])].copy()
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Applied", int((df["status"] == "applied").sum()))
    a2.metric("Screens", int((df["status"] == "screen").sum()))
    a3.metric("Interviews", int((df["status"] == "interview").sum()))
    a4.metric("Offers", int((df["status"] == "offer").sum()))

    if handled.empty:
        st.info("Nothing has moved out of the job queue yet.")
    else:
        status_pick = st.multiselect(
            "Filter by status",
            ["applied", "screen", "interview", "final", "offer", "rejected", "withdrawn"],
        )
        if status_pick:
            handled = handled[handled["status"].isin(status_pick)]
        handled = handled.sort_values(["date_found"], ascending=False)
        st.dataframe(
            handled[["company", "title", "location", "score", "verdict", "status", "date_found"]],
            width="stretch",
            hide_index=True,
        )
