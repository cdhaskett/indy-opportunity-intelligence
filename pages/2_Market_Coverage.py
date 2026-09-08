from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
WATCHLIST = json.loads((ROOT / "data" / "market_watchlist.json").read_text())
LIVE_REGISTRY = json.loads((ROOT / "data" / "employers.json").read_text())

st.set_page_config(page_title="Market Coverage", page_icon="🗺️", layout="wide")

st.title("🗺️ Market Coverage")
st.caption("Who the app can collect today — and which Central Indiana employers are next on the integration list.")

live = pd.DataFrame(LIVE_REGISTRY["employers"])
watch = pd.DataFrame(WATCHLIST["employers"])

c1, c2, c3 = st.columns(3)
c1.metric("Live ATS employers", len(live))
c2.metric("Expansion watchlist", len(watch))
c3.metric("High-priority gaps", int((watch["priority"] == "high").sum()))

st.subheader("✅ Currently collected")
st.write("These employers are connected to the live ATS refresh in the alpha app.")
st.dataframe(
    live[["name", "ats", "priority", "market_note"]].sort_values(["priority", "name"]),
    use_container_width=True,
    hide_index=True,
)

st.subheader("🎯 Expansion watchlist")
st.write(
    "These employers are intentionally tracked even though the alpha collector does not yet support their career platform. "
    "Keeping them visible prevents the current ATS cohort from being mistaken for the whole Indianapolis market."
)

priority = st.multiselect("Priority", ["high", "medium", "low"], default=["high", "medium"])
segment = st.multiselect("Segment", sorted(watch["segment"].unique().tolist()))

view = watch[watch["priority"].isin(priority)].copy() if priority else watch.copy()
if segment:
    view = view[view["segment"].isin(segment)]

st.dataframe(
    view[["name", "segment", "priority", "why"]].sort_values(["priority", "segment", "name"]),
    use_container_width=True,
    hide_index=True,
)

st.info(
    "Next engineering target: add collectors for the career platforms used by the high-priority employers, then move them from this watchlist into live coverage."
)
