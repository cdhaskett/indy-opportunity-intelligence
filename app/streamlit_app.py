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
        --bg: #f7f4ee;
        --card: #fffdfa;
        --ink: #242424;
        --muted: #74706a;
        --accent: #3f5f5a;
        --accent-2: #9f6f5d;
        --line: #ddd6cc;
        --soft: #ece7df;
    }

    .stApp {
        background: linear-gradient(180deg, #fbf9f4 0%, var(--bg) 42%, #f3efe7 100%);
        color: var(--ink);
    }

    .block-container {
        max-width: 1320px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.02em;
    }

    .hero {
        padding: 1.1rem 1.25rem 1.25rem;
        border: 1px solid var(--line);
        background: rgba(255,253,250,.9);
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(60, 50, 40, .05);
        margin-bottom: 1rem;
    }

    .hero-kicker {
        text-transform: uppercase;
        letter-spacing: .14em;
        font-size: .72rem;
        color: var(--accent-2);
        font-weight: 700;
        margin-bottom: .25rem;
    }

    .hero-title {
        font-size: 2.25rem;
        line-height: 1.05;
        font-weight: 760;
        color: var(--ink);
        margin: 0;
    }

    .hero-subtitle {
        margin-top: .5rem;
        color: var(--muted);
        font-size: 1rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,253,250,.8);
        border: 1px solid var(--line);
        padding: .9rem 1rem;
        border-radius: 18px;
        box-shadow: 0 5px 18px rgba(60, 50, 40, .035);
    }

    div[data-testid="stMetricLabel"] p {
        color: var(--muted);
        font-size: .78rem;
        text-transform: uppercase;
        letter-spacing: .08em;
        font-weight: 700;
    }

    div[data-testid="stMetricValue"] {
        color: var(--ink);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,253,250,.92);
        border-color: var(--line) !important;
        border-radius: 22px;
        box-shadow: 0 8px 26px rgba(60, 50, 40, .045);
    }

    .job-title {
        font-size: 1.28rem;
        font-weight: 760;
        line-height: 1.2;
        color: var(--ink);
        margin-bottom: .25rem;
    }

    .score-pill {
        display: inline-block;
        padding: .2rem .55rem;
        margin-right: .45rem;
        border-radius: 999px;
        background: var(--accent);
        color: white;
        font-size: .82rem;
        font-weight: 700;
        vertical-align: 2px;
    }

    .salary-pill {
        display: inline-block;
        padding: .2rem .55rem;
        margin-left: .35rem;
        border-radius: 999px;
        background: #eee4dc;
        color: #6b4c40;
        font-size: .82rem;
        font-weight: 700;
        vertical-align: 2px;
    }

    .job-meta {
        color: var(--muted);
        font-size: .93rem;
        margin-bottom: .4rem;
    }

    .verdict-line {
        color: #4d4a45;
        font-size: .91rem;
        margin-top: .15rem;
    }

    div[role="radiogroup"] {
        background: rgba(255,253,250,.7);
        border: 1px solid var(--line);
        padding: .35rem;
        border-radius: 16px;
        width: fit-content;
    }

    .stButton > button, .stLinkButton > a {
        border-radius: 999px !important;
        font-weight: 650 !important;
    }

    hr {
        border-color: var(--line);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">INDY OPPORTUNITY INTELLIGENCE</div>
      <div class="hero-title">Find the few jobs actually worth your time.</div>
      <div class="hero-subtitle">Central Indiana + remote role discovery, fit scoring, duplicate protection, and application tracking — without the endless scroll.</div>
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


def render_score_explanation(row):
    details = score_details[row["id"]]
    with st.expander("Why this score?"):
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

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Jobs monitored", len(df))
    c2.metric("Apply now", int((df["verdict"] == "APPLY").sum()))
    c3.metric("Strong consider", int((df["verdict"] == "STRONG CONSIDER").sum()))
    c4.metric("Already applied", exact_duplicates)
    c5.metric("Check duplicates", possible_duplicates)

    st.subheader("Today’s Market")
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
            a, b = st.columns([4.7, 1])
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
                    st.warning(
                        f"Possible previous application: **{prior_title}** at **{prior.get('company', row['company'])}** ({prior_date}). Review before applying."
                    )

                source = row.get("source") or "unknown"
                st.markdown(
                    f'<div class="verdict-line"><strong>{row["verdict"]}</strong> · {row["status"].title()} · {source}</div>',
                    unsafe_allow_html=True,
                )

                button_col, explain_col = st.columns([1, 5])
                with button_col:
                    if row.get("url"):
                        st.link_button("Open posting ↗", row["url"])
                with explain_col:
                    render_score_explanation(row)
            with b:
                current_status = row["status"] if row["status"] in status_options else "new"
                new_status = st.selectbox(
                    "Update",
                    status_options,
                    index=status_options.index(current_status),
                    key=f"status-{row['id']}",
                )
                if new_status != row["status"]:
                    update_status(int(row["id"]), new_status)
                    st.rerun()

elif section == "🗺️ Market Coverage":
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
