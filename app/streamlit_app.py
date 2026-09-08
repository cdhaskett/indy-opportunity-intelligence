from __future__ import annotations
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
from data.db import list_jobs, update_status
from run_collectors import run as run_collectors
from matching.scorer import score_job

PROFILE = json.loads((ROOT / "data" / "candidate_profile.json").read_text())
WATCHLIST = json.loads((ROOT / "data" / "market_watchlist.json").read_text())
LIVE_REGISTRY = json.loads((ROOT / "data" / "employers.json").read_text())

st.set_page_config(
    page_title="Indy Opportunity Intelligence",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 Indy Opportunity Intelligence")
st.caption("Live opportunity triage built around fit, not endless scrolling.")

section = st.radio(
    "Navigation",
    ["🔎 Job Market", "🗺️ Market Coverage", "📊 My Applications"],
    horizontal=True,
    label_visibility="collapsed",
)

jobs = list_jobs()
rescored_jobs = []
score_details = {}
for job in jobs:
    score, detail = score_job(job, PROFILE)
    job = dict(job)
    job["score"] = score
    job["verdict"] = detail["verdict"]
    rescored_jobs.append(job)
    score_details[job["id"]] = detail

df = pd.DataFrame(rescored_jobs) if rescored_jobs else pd.DataFrame()
status_options = ["new", "saved", "applied", "screen", "interview", "final", "offer", "rejected", "withdrawn"]

if section == "🔎 Job Market":
    refresh_col, note_col = st.columns([1, 4])
    with refresh_col:
        if st.button("🔄 Refresh live jobs", use_container_width=True):
            with st.spinner("Checking employer ATS feeds and rescoring the market..."):
                run_collectors()
            st.success("Live job refresh complete.")
            st.rerun()
    with note_col:
        st.caption("Current alpha checks a curated Central Indiana + U.S. remote employer registry.")

    if df.empty:
        st.info("No jobs loaded yet. Click **Refresh live jobs** to pull the first real market snapshot.")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jobs found", len(df))
    c2.metric("🔥 Apply", int((df["verdict"] == "APPLY").sum()))
    c3.metric("👍 Strong consider", int((df["verdict"] == "STRONG CONSIDER").sum()))
    c4.metric("Interviews", int((df["status"] == "interview").sum()))

    st.subheader("Today's Market")

    show_processed = st.toggle(
        "Show jobs I've already handled",
        value=False,
        help="Applied, interview, rejected, withdrawn, and other completed statuses stay in your database but are hidden from the main queue by default.",
    )

    filter_a, filter_b, filter_c = st.columns(3)
    with filter_a:
        verdict_filter = st.multiselect(
            "Verdict",
            ["APPLY", "STRONG CONSIDER", "STRETCH", "SKIP"],
            default=["APPLY", "STRONG CONSIDER", "STRETCH"],
        )
    with filter_b:
        company_options = sorted(df["company"].dropna().unique().tolist())
        company_filter = st.multiselect("Company", company_options)
    with filter_c:
        status_filter = st.multiselect("Status", status_options)

    view = df[df["verdict"].isin(verdict_filter)].copy()

    if not show_processed and not status_filter:
        view = view[view["status"].isin(["new", "saved"])]

    if company_filter:
        view = view[view["company"].isin(company_filter)]
    if status_filter:
        view = view[view["status"].isin(status_filter)]

    view = view.sort_values(["score", "date_found"], ascending=[False, False])

    if view.empty:
        st.success("Your current queue is clear. Turn on **Show jobs I've already handled** or refresh live jobs to see more.")

    for _, row in view.iterrows():
        details = score_details[row["id"]]
        with st.container(border=True):
            a, b = st.columns([4, 1])
            with a:
                st.markdown(f"### {int(row['score'])} — {row['title']}")
                st.write(f"**{row['company']}** · {row['location'] or 'Location not listed'}")
                salary = ""
                if pd.notna(row.get("salary_min")):
                    salary = f"${int(row['salary_min']):,}+"
                source = row.get("source") or "unknown"
                st.write(
                    f"**Verdict:** {row['verdict']}  |  **Status:** {row['status']}  |  **Source:** {source}"
                    f"  {('|  **Salary:** ' + salary) if salary else ''}"
                )

                button_col, explain_col = st.columns([1, 5])
                with button_col:
                    if row.get("url"):
                        st.link_button("View posting", row["url"])
                with explain_col:
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

                        if matched:
                            st.write("**Matched signals:** " + ", ".join(matched[:14]))
                        else:
                            st.write("**Matched signals:** No strong keyword signals yet.")

                        warnings = details["seniority"].get("warnings", [])
                        if warnings:
                            st.warning("Seniority warning: " + ", ".join(warnings))
                        if details["salary"].get("salary_min") is None:
                            st.caption("Compensation was not listed, so the role receives neutral partial credit rather than a penalty.")
            with b:
                current_status = row["status"] if row["status"] in status_options else "new"
                new_status = st.selectbox(
                    "Update",
                    status_options,
                    index=status_options.index(current_status),
                    key=f"status-{row['id']}"
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

    st.markdown("### ✅ Currently collected")
    st.write("These employers are connected to the live ATS refresh in the alpha app.")
    st.dataframe(
        live[["name", "ats", "priority", "market_note"]].sort_values(["priority", "name"]),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### 🎯 Expansion watchlist")
    st.write(
        "These employers are tracked even though the current collector does not yet support their career platform. "
        "Keeping them visible prevents the live ATS cohort from being mistaken for the whole Indianapolis market."
    )

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
        use_container_width=True,
        hide_index=True,
    )

    st.info("Next engineering target: add collectors for high-priority employer career platforms and move them from watchlist to live coverage.")

elif section == "📊 My Applications":
    st.subheader("My Applications")
    st.caption("Everything you've acted on stays here for outcome tracking and future interview-rate analytics.")

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
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Outcome snapshot")
        status_counts = handled["status"].value_counts().rename_axis("status").reset_index(name="count")
        st.dataframe(status_counts, use_container_width=True, hide_index=True)
