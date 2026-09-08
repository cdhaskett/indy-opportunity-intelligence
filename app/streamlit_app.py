from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
from data.db import list_jobs, update_status
from run_collectors import run as run_collectors

st.set_page_config(
    page_title="Indy Opportunity Intelligence",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 Indy Opportunity Intelligence")
st.caption("Live opportunity triage built around fit, not endless scrolling.")

refresh_col, note_col = st.columns([1, 4])
with refresh_col:
    if st.button("🔄 Refresh live jobs", use_container_width=True):
        with st.spinner("Checking employer ATS feeds and rescoring the market..."):
            run_collectors()
        st.success("Live job refresh complete.")
        st.rerun()
with note_col:
    st.caption("Current alpha checks a curated Central Indiana + U.S. remote employer registry.")

jobs = list_jobs()

if not jobs:
    st.info("No jobs loaded yet. Click **Refresh live jobs** to pull the first real market snapshot.")
    st.stop()

df = pd.DataFrame(jobs)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Jobs found", len(df))
c2.metric("🔥 Apply", int((df["verdict"] == "APPLY").sum()))
c3.metric("👍 Strong consider", int((df["verdict"] == "STRONG CONSIDER").sum()))
c4.metric("Interviews", int((df["status"] == "interview").sum()))

st.subheader("Today's Market")

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
    status_options = ["new", "saved", "applied", "screen", "interview", "final", "offer", "rejected", "withdrawn"]
    status_filter = st.multiselect("Status", status_options)

view = df[df["verdict"].isin(verdict_filter)].copy()
if company_filter:
    view = view[view["company"].isin(company_filter)]
if status_filter:
    view = view[view["status"].isin(status_filter)]

statuses = ["new", "saved", "applied", "screen", "interview", "final", "offer", "rejected", "withdrawn"]

for _, row in view.iterrows():
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
            if row.get("url"):
                st.link_button("View posting", row["url"])
        with b:
            current_status = row["status"] if row["status"] in statuses else "new"
            new_status = st.selectbox(
                "Update",
                statuses,
                index=statuses.index(current_status),
                key=f"status-{row['id']}"
            )
            if new_status != row["status"]:
                update_status(int(row["id"]), new_status)
                st.rerun()

st.subheader("Application Analytics")
status_counts = df["status"].value_counts().rename_axis("status").reset_index(name="count")
st.dataframe(status_counts, use_container_width=True, hide_index=True)
