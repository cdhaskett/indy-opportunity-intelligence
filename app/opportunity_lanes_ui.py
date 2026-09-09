from __future__ import annotations

import pandas as pd
import streamlit as st


def render_lane_spotlight(active: pd.DataFrame, section_class: str = "xp-section") -> None:
    if active is None or active.empty or "opportunity_lane" not in active.columns:
        return

    eligible = active[active["verdict"].isin(["APPLY", "STRONG CONSIDER", "STRETCH"])].copy()
    if eligible.empty:
        return

    st.markdown(
        f'<div class="{section_class}">🧭 Opportunity Lanes</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "The shortlist below gets a small diversity boost so one job family does not crowd out other strong directions. Fit scores are unchanged."
    )

    best_by_lane = (
        eligible.sort_values(["score", "date_found"], ascending=[False, False])
        .drop_duplicates("opportunity_lane")
        .sort_values("score", ascending=False)
        .head(6)
    )

    cols = st.columns(3)
    for i, (_, row) in enumerate(best_by_lane.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                icon = row.get("lane_icon") or "🧭"
                st.markdown(f"**{icon} {row['opportunity_lane']}**")
                st.markdown(f"**{int(row['score'])} · {row['title']}**")
                st.caption(str(row.get("company") or "Unknown company"))

    hidden = eligible[eligible.get("hidden_fit", False) == True].copy()  # noqa: E712
    if not hidden.empty:
        hidden = hidden.sort_values(["score", "date_found"], ascending=[False, False]).head(8)
        with st.expander(f"🌶️ Hidden Fits · {len(hidden)} strong roles with less-obvious titles"):
            for _, row in hidden.iterrows():
                icon = row.get("lane_icon") or "🧭"
                st.write(
                    f"**{int(row['score'])} · {row['title']}** — {row.get('company') or 'Unknown company'} · {icon} {row['opportunity_lane']}"
                )
