from __future__ import annotations

from pathlib import Path

CORE = Path(__file__).with_name("shareable_dashboard_core.py")
source = CORE.read_text(encoding="utf-8")

helper_css = """
/* Integrated Resume Helper controls */
.stTextArea textarea,
[data-testid="stTextArea"] textarea {
    background: #fff !important;
    color: #111 !important;
    border: 1px solid #7f9db9 !important;
}
[data-testid="stTextArea"] label *,
[data-testid="stFileUploader"] label *,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small {
    color: #111 !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: #fff !important;
    border: 1px solid #7f9db9 !important;
}
[data-testid="stFileUploaderDropzone"] *,
[data-testid="stFileUploaderFile"] * {
    color: #111 !important;
}
[data-testid="stFileUploaderFile"] {
    background: #f7fbff !important;
    border: 1px solid #b8cde5 !important;
}
[data-testid="stAlert"] { color: #111 !important; }
[data-testid="stAlert"] * { color: inherit !important; }

/* Hosted beta owns its account/navigation chrome. */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stMainBlockContainer"],
.block-container {
    margin: 0 auto !important;
    align-self: flex-start !important;
    padding-top: .35rem !important;
}
.account-strip {
    background: #f5f3eb;
    border: 1px solid #aca899;
    box-shadow: inset 1px 1px #fff;
    color: #111;
    padding: .34rem .55rem;
    font-size: .78rem;
    min-height: 2rem;
    box-sizing: border-box;
}
.account-strip .product { color: #0b3d91; font-weight: 700; }
.account-strip .identity { float: right; color: #4e5f6f; font-weight: 700; }
"""

old_menu = """st.markdown(
    f'<div class=\"menu\">File &nbsp; View &nbsp; Favorites &nbsp; Tools &nbsp; Help'
    f'<span style=\"float:right;color:#16418a\"><b>{profile_name}</b></span></div>',
    unsafe_allow_html=True,
)
"""

new_menu = """identity = st.session_state.get(\"oi_identity\") or {}
signed_in_label = identity.get(\"email\") or identity.get(\"name\") or profile_name
account_left, account_right = st.columns([9, 1], vertical_alignment=\"center\")
with account_left:
    st.markdown(
        f'<div class=\"account-strip\"><span class=\"product\">🪟 Opportunity Intelligence</span>'
        f' &nbsp; File &nbsp; View &nbsp; Favorites &nbsp; Tools &nbsp; Help'
        f'<span class=\"identity\">{signed_in_label}</span></div>',
        unsafe_allow_html=True,
    )
with account_right:
    if st.button(\"Sign out\", key=\"top-sign-out\", use_container_width=True):
        st.logout()
"""

old_refresh_spinner = """            with st.spinner(\"Checking job sources for your market...\"):
                run_collectors()
"""
new_refresh_loader = """            refresh_loader = show_xp_loader(\"Checking career pages and ATS feeds\")
            try:
                run_collectors()
            finally:
                refresh_loader.empty()
"""

row_lane_patch = """job[\"verdict\"] = details[\"verdict\"]
    lane_info = classify_opportunity(job, profile, score, details)
    job[\"opportunity_lane\"] = lane_info[\"lane\"]
    job[\"lane_icon\"] = lane_info[\"lane_icon\"]
    job[\"lane_strength\"] = lane_info[\"lane_strength\"]
    job[\"hidden_fit\"] = lane_info[\"hidden_fit\"]"""

salary_explain_patch = """if key == \"salary\" and d[key].get(\"scored\") is False:
                st.write(\"**Compensation:** shown, not scored\")
            else:
                st.write(f\"**{label}:** {d[key]['score']}/{d[key]['max']}\")"""

old_sort = """view = view.sort_values(
            [\"score\", \"date_found\"],
            ascending=[False, False],
        )"""
new_sort = """view = diversify_dataframe(
            view.sort_values([\"score\", \"date_found\"], ascending=[False, False])
        )"""

replacements = [
    (
        "from data.db import count_today_status, list_jobs, update_status",
        "from app.loading_ui import show_xp_loader\nfrom app.opportunity_lanes_ui import render_lane_spotlight\nfrom app.resume_helper_ui import render_resume_helper\nfrom data.db import count_today_status, list_jobs, update_status\nfrom matching.opportunity_lanes import classify_opportunity, diversify_dataframe",
    ),
    (
        '["🏠 Job Market", "📂 My Applications", "🛠 Control Panel"]',
        '["🏠 Job Market", "📝 Resume Helper", "📂 My Applications", "🛠 Control Panel"]',
    ),
    (
        'job["verdict"] = details["verdict"]',
        row_lane_patch,
    ),
    (
        'st.write(f"**{label}:** {d[key][\'score\']}/{d[key][\'max\']}")',
        salary_explain_patch,
    ),
    (
        'm5.metric("Previous Applications", int((df["history_match"] == "exact").sum()))',
        'm5.metric("Previous Applications", int((df["history_match"] == "exact").sum()))\n\n        render_lane_spotlight(active, "section")',
    ),
    (
        old_sort,
        new_sort,
    ),
    (
        'elif section == "📂 My Applications":',
        'elif section == "📝 Resume Helper":\n    render_resume_helper(profile, rows)\n\nelif section == "📂 My Applications":',
    ),
    (old_menu, new_menu),
    (old_refresh_spinner, new_refresh_loader),
    ("</style>", helper_css + "\n</style>"),
]

for old, new in replacements:
    if old not in source:
        raise RuntimeError(f"Opportunity Intelligence hosted patch anchor missing: {old}")
    source = source.replace(old, new, 1)

exec(
    compile(source, str(CORE), "exec"),
    {"__file__": str(CORE), "__name__": "__main__"},
)
