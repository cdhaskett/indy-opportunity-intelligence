from __future__ import annotations

from pathlib import Path

CORE = Path(__file__).with_name("personal_dashboard_core.py")
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
[data-testid="stAlert"] {
    color: #111 !important;
}
[data-testid="stAlert"] * {
    color: inherit !important;
}
"""

row_lane_patch = """job[\"verdict\"] = detail[\"verdict\"]
    lane_info = classify_opportunity(job, PROFILE, score, detail)
    job[\"opportunity_lane\"] = lane_info[\"lane\"]
    job[\"lane_icon\"] = lane_info[\"lane_icon\"]
    job[\"lane_strength\"] = lane_info[\"lane_strength\"]
    job[\"hidden_fit\"] = lane_info[\"hidden_fit\"]"""

salary_explain_patch = """if key == \"salary\" and details[key].get(\"scored\") is False:
                st.write(\"**Compensation:** shown, not scored\")
            else:
                st.write(f\"**{label}:** {details[key]['score']}/{details[key]['max']}\")"""

replacements = [
    (
        "from data.db import list_jobs, update_status",
        "from app.opportunity_lanes_ui import render_lane_spotlight\nfrom app.resume_helper_ui import render_resume_helper\nfrom data.db import list_jobs, update_status\nfrom matching.opportunity_lanes import classify_opportunity, diversify_dataframe",
    ),
    (
        '["🏠 Job Market", "🌐 Market Coverage", "📂 My Applications"]',
        '["🏠 Job Market", "📝 Resume Helper", "🌐 Market Coverage", "📂 My Applications"]',
    ),
    (
        'job["verdict"] = detail["verdict"]',
        row_lane_patch,
    ),
    (
        'st.write(f"**{label}:** {details[key][\'score\']}/{details[key][\'max\']}")',
        salary_explain_patch,
    ),
    (
        'c5.metric("Review Duplicates", int((df["history_match"] == "possible").sum()))',
        'c5.metric("Review Duplicates", int((df["history_match"] == "possible").sum()))\n\n    render_lane_spotlight(active, "xp-section")',
    ),
    (
        'view = view.sort_values(["score", "date_found"], ascending=[False, False])',
        'view = diversify_dataframe(view.sort_values(["score", "date_found"], ascending=[False, False]))',
    ),
    (
        'elif section == "🌐 Market Coverage":',
        'elif section == "📝 Resume Helper":\n    render_resume_helper(PROFILE, rows)\n\nelif section == "🌐 Market Coverage":',
    ),
    (
        "</style>",
        helper_css + "\n</style>",
    ),
]

for old, new in replacements:
    if old not in source:
        raise RuntimeError(f"Opportunity Intelligence patch anchor missing: {old}")
    source = source.replace(old, new, 1)

exec(
    compile(source, str(CORE), "exec"),
    {"__file__": str(CORE), "__name__": "__main__"},
)
