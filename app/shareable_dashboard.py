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
[data-testid="stAlert"] {
    color: #111 !important;
}
[data-testid="stAlert"] * {
    color: inherit !important;
}
"""

replacements = [
    (
        "from data.db import count_today_status, list_jobs, update_status",
        "from app.resume_helper_ui import render_resume_helper\nfrom data.db import count_today_status, list_jobs, update_status",
    ),
    (
        '["🏠 Job Market", "📂 My Applications", "🛠 Control Panel"]',
        '["🏠 Job Market", "📝 Resume Helper", "📂 My Applications", "🛠 Control Panel"]',
    ),
    (
        'elif section == "📂 My Applications":',
        'elif section == "📝 Resume Helper":\n    render_resume_helper(profile, rows)\n\nelif section == "📂 My Applications":',
    ),
    (
        "</style>",
        helper_css + "\n</style>",
    ),
]

for old, new in replacements:
    if old not in source:
        raise RuntimeError(f"Resume Helper navigation patch anchor missing: {old}")
    source = source.replace(old, new, 1)

exec(
    compile(source, str(CORE), "exec"),
    {"__file__": str(CORE), "__name__": "__main__"},
)
