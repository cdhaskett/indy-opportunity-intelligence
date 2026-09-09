from __future__ import annotations

import hashlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from matching.resume_parser import extract_resume_text, parse_resume_text
from profile_config import has_user_profile, load_profile_template, save_user_profile
from resume_store import save_resume


# Returning users go straight into the stable shareable application.
if has_user_profile():
    runpy.run_path(str(Path(__file__).with_name("shareable_app.py")), run_name="__main__")
    raise SystemExit


st.set_page_config(
    page_title="Opportunity Intelligence",
    page_icon="🪟",
    layout="wide",
)

st.markdown(
    """
<style>
:root {
  --blue:#0a5bd8; --blue-dark:#0753c7; --ivory:#ece9d8; --card:#fffef5;
  --border:#7f9db9; --text:#111; --link:#10479d;
  --window:min(1500px, calc(100vw - 36px));
}
html,body,[class*="css"]{font-family:Tahoma,Arial,sans-serif}
html,body,.stApp{overflow-x:hidden!important}
.stApp{color:var(--text);background:linear-gradient(#4b9df4 0 42%,#bfe4ff 59%,#79cf5c 60%,#3d9d34 100%)}
.stApp:before{content:"";position:fixed;inset:0;pointer-events:none;background:
 radial-gradient(ellipse at 12% 18%,rgba(255,255,255,.9) 0 2.5%,transparent 2.9%),
 radial-gradient(ellipse at 18% 17%,rgba(255,255,255,.74) 0 3.2%,transparent 3.6%),
 radial-gradient(ellipse at 76% 19%,rgba(255,255,255,.86) 0 2.4%,transparent 2.8%),
 radial-gradient(ellipse at 82% 19%,rgba(255,255,255,.70) 0 3.2%,transparent 3.6%),
 radial-gradient(ellipse at 20% 105%,#318c2c 0 34%,transparent 34.4%),
 radial-gradient(ellipse at 55% 110%,#68c94e 0 44%,transparent 44.4%),
 radial-gradient(ellipse at 92% 108%,#45a83b 0 38%,transparent 38.4%)}
.stApp:after{content:"";position:fixed;inset-block:0;left:50%;transform:translateX(-50%);width:var(--window);background:var(--ivory);border-inline:1px solid #7697bd;box-shadow:0 0 25px #285b8a88;pointer-events:none}
.block-container,[data-testid="stMainBlockContainer"]{position:relative;z-index:1;width:var(--window)!important;max-width:var(--window)!important;margin:auto!important;padding:.65rem 1.1rem 4rem!important;background:transparent!important;box-sizing:border-box;overflow-x:hidden!important}
.menu{background:#f5f3eb;border:1px solid #aca899;box-shadow:inset 1px 1px #fff;padding:.32rem .55rem;margin-bottom:.35rem;font-size:.78rem;color:#111}
.section{background:linear-gradient(#3f93ff,var(--blue-dark));color:#fff;border:1px solid #06459e;border-radius:5px 5px 0 0;padding:.38rem .58rem;font-weight:700;text-shadow:1px 1px #16448a;margin-top:.45rem}
.welcome{background:#fffef5;border:1px solid #7f9db9;box-shadow:inset 1px 1px #fff;padding:1rem 1.15rem;margin:.4rem 0 .7rem;color:#222}
.welcome h2{color:#10479d;margin:.05rem 0 .35rem;font-size:1.35rem}.welcome p{color:#333;margin:.2rem 0}
.resume-box{background:#dbe8f7;border:1px solid #7f9db9;padding:.75rem .85rem;margin:.5rem 0 .65rem;color:#183f75}
.resume-result{background:#fffef5;border:1px solid #aca899;padding:.65rem .75rem;margin:.4rem 0 .65rem;color:#222}
.help{background:#fff7a8;border:1px solid #d0bd3e;color:#4c4314;padding:.55rem .65rem;margin:.35rem 0 .6rem;font-size:.82rem}
.steps{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.35rem;margin:.55rem 0 .8rem}
.step{background:#dbe8f7;border:1px solid #7f9db9;color:#284b77;padding:.45rem .5rem;font-size:.78rem;font-weight:700;text-align:center}
.stButton>button{background:linear-gradient(#fff,#e5e5df)!important;border:1px solid #003c74!important;color:#111!important;border-radius:3px!important;font-weight:700!important;box-shadow:inset 1px 1px #fff!important}
input,textarea,[role="combobox"],div[data-baseweb="select"]>div{background:#fff!important;color:#111!important;border-color:var(--border)!important}
label,[data-testid="stWidgetLabel"] *,[data-testid="stMarkdownContainer"] p{color:#111}
input::placeholder,textarea::placeholder{color:#727272!important;opacity:1!important}
[data-testid="stFileUploader"] label,[data-testid="stFileUploader"] label *{color:#111!important}
[data-testid="stCheckbox"] label,[data-testid="stCheckbox"] label *{color:#111!important}
[data-baseweb="tag"]{background:#dbe8f7!important;border:1px solid var(--border)!important}[data-baseweb="tag"] *{color:var(--link)!important;background:transparent!important}
.taskbar{position:fixed;left:0;right:0;bottom:0;height:35px;background:linear-gradient(#2e7df1,#0757c8);z-index:9998;color:#fff;padding:.35rem .5rem}
.start{background:linear-gradient(#6bc65c,#2e9a2e);border:1px solid #1d7d1d;border-radius:0 14px 14px 0;padding:.27rem 1rem;font-weight:700;font-style:italic}
.task{margin-left:.55rem;background:#1e66c9;border:1px solid #0e4fae;padding:.23rem .7rem;display:inline-block}
@media(max-width:1000px){:root{--window:calc(100vw - 16px)}[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important}[data-testid="stColumn"]{min-width:min(100%,270px)!important;flex:1 1 270px!important}.steps{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:650px){:root{--window:calc(100vw - 6px)}.block-container,[data-testid="stMainBlockContainer"]{padding-inline:.4rem!important}.task{display:none}.steps{grid-template-columns:1fr}}
</style>
""",
    unsafe_allow_html=True,
)


def split_terms(text: str) -> list[str]:
    return [item.strip().lower() for item in text.replace("\n", ",").split(",") if item.strip()]


def join_terms(values) -> str:
    return ", ".join(values or [])


def draft_value(draft: dict, key: str, fallback=""):
    value = draft.get(key, fallback)
    return fallback if value is None else value


template = load_profile_template()

st.markdown(
    '<div class="menu">File &nbsp; View &nbsp; Help'
    '<span style="float:right;color:#16418a"><b>First-time setup</b></span></div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="section">🪟 Welcome to Opportunity Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    """
<div class="welcome">
<h2>Your job search, ranked around you.</h2>
<p>Start with your résumé and we’ll draft the profile for you. You review every field before anything is saved.</p>
</div>
<div class="steps">
  <div class="step">1 · Résumé</div>
  <div class="step">2 · Your market</div>
  <div class="step">3 · Your roles</div>
  <div class="step">4 · Your skills</div>
  <div class="step">5 · Preferences</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="resume-box"><b>📄 Build my profile from my résumé</b><br>'
    'Upload a PDF or Word résumé and we’ll pre-fill what we can. The original file is processed in memory. '
    'If you finish setup with it, only the extracted text is saved privately for future Résumé Match scoring.</div>',
    unsafe_allow_html=True,
)

resume = st.file_uploader(
    "Upload résumé (optional)",
    type=["pdf", "docx", "txt"],
    help="PDF, Word (.docx), and plain text files are supported.",
)

resume_draft: dict = {}
resume_summary: dict = {}
resume_storage_text = ""
resume_source_name = ""

if resume is not None:
    file_hash = hashlib.sha256(resume.getvalue()).hexdigest()
    cache_key = "resume_parse_" + file_hash
    if cache_key not in st.session_state:
        try:
            extracted_text = extract_resume_text(resume.getvalue(), resume.name)
            st.session_state[cache_key] = {
                "parsed": parse_resume_text(extracted_text),
                "text": extracted_text,
            }
        except Exception as exc:
            st.session_state[cache_key] = {"error": str(exc)}

    cached = st.session_state[cache_key]
    if cached.get("error"):
        st.error(f"Could not read that résumé: {cached['error']}")
    else:
        parsed = cached.get("parsed", {})
        resume_storage_text = str(cached.get("text") or "")
        resume_source_name = resume.name
        resume_draft = parsed.get("profile", {})
        resume_summary = parsed.get("summary", {})
        st.success("Résumé read successfully. Review the suggestions below before saving.")

        titles = resume_summary.get("titles", [])
        skills = resume_summary.get("skills", [])
        domains = resume_summary.get("domains", [])
        education = resume_summary.get("education", [])

        st.markdown(
            '<div class="resume-result"><b>What I found</b><br>'
            + (f'<b>Likely titles:</b> {", ".join(titles[:6])}<br>' if titles else '')
            + (f'<b>Skills / tools:</b> {", ".join(skills[:16])}<br>' if skills else '')
            + (f'<b>Professional domains:</b> {", ".join(domains)}<br>' if domains else '')
            + (f'<b>Education / certifications:</b> {"; ".join(education[:3])}' if education else '')
            + '</div>',
            unsafe_allow_html=True,
        )

st.markdown(
    '<div class="help"><b>Review, don’t just accept.</b> Résumés describe what you have done; '
    'they do not always describe what you want next. Salary, remote preference and dealbreakers are never inferred.</div>',
    unsafe_allow_html=True,
)

current = dict(template)
current.update(resume_draft)

with st.form("resume_first_profile"):
    st.markdown("### 👤 About you")
    name = st.text_input(
        "Your name",
        value=str(draft_value(current, "name", "")),
        placeholder="Example: Alex",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        city = st.text_input(
            "Home city",
            value=str(draft_value(current, "home_city", "")),
            placeholder="Louisville",
        )
    with c2:
        state = st.text_input(
            "State",
            value=str(draft_value(current, "home_state", "")),
            placeholder="Kentucky",
        )
    with c3:
        remote_ok = st.checkbox("Include U.S. remote jobs", value=True)

    nearby = st.text_input(
        "Nearby cities / areas to include",
        value="",
        placeholder="Jeffersonville, New Albany",
        help="Optional. Separate multiple areas with commas.",
    )

    st.markdown("### 💼 What work do you want next?")
    target_titles = st.text_area(
        "Target job titles",
        value=join_terms(current.get("target_titles", [])),
        placeholder="Project Manager, Operations Manager, Logistics Analyst",
        height=85,
        help="Edit the résumé suggestions to reflect what you actually want next.",
    )
    seniority = st.text_input(
        "Preferred levels / title words",
        value=join_terms(current.get("seniority_preferences", [])),
        placeholder="analyst, senior analyst, specialist, manager",
    )
    avoid_seniority = st.text_input(
        "Titles to de-prioritize",
        value="",
        placeholder="director, vice president, chief",
    )

    st.markdown("### 🧰 Skills the search should value")
    strong_skills = st.text_area(
        "Strong skills",
        value=join_terms(current.get("strong_skills", [])),
        placeholder="Excel, SAP, scheduling, team leadership, warehouse operations",
        height=95,
        help="Move, remove, or add anything the résumé parser got wrong.",
    )
    secondary_skills = st.text_area(
        "Other useful skills",
        value=join_terms(current.get("secondary_skills", [])),
        placeholder="Power BI, SQL, reporting",
        height=75,
    )
    focus_terms = st.text_area(
        "Work themes you enjoy",
        value=join_terms(current.get("focus_terms", [])),
        placeholder="project management, process improvement, operations, customer success",
        height=75,
    )
    bonus_terms = st.text_input(
        "Bonus tools / keywords",
        value=join_terms(current.get("bonus_terms", [])),
        placeholder="Salesforce, Jira, Tableau",
    )

    st.markdown("### 🏢 Professional domains")
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
        default=[x for x in current.get("domain_strengths", []) if x in domain_options],
        help="Confirm these carefully. They affect hard-requirement screening.",
    )

    st.markdown("### 💰 Preferences & dealbreakers")
    p1, p2, p3 = st.columns(3)
    with p1:
        salary_floor = st.number_input("Minimum salary", min_value=0, step=5000, value=0)
    with p2:
        salary_target = st.number_input("Target salary", min_value=0, step=5000, value=0)
    with p3:
        daily_goal = st.number_input("Daily application goal", min_value=1, max_value=10, step=1, value=3)

    avoid_terms = st.text_input(
        "Dealbreakers / avoid terms",
        value="",
        placeholder="commission only, contract only, night shift",
    )

    submitted = st.form_submit_button("🚀 Save & Find My Jobs", use_container_width=True)

if submitted:
    errors = []
    if not city.strip():
        errors.append("home city")
    if not state.strip():
        errors.append("state")
    if not split_terms(target_titles):
        errors.append("at least one target job title")
    if not split_terms(strong_skills):
        errors.append("at least one strong skill")

    if errors:
        st.error("Please add " + ", ".join(errors) + " before continuing.")
    else:
        locations = []
        if city.strip():
            locations.append(city.strip().lower())
        if state.strip():
            locations.append(state.strip().lower())
        locations.extend(split_terms(nearby))
        locations = list(dict.fromkeys(locations))

        targets = split_terms(target_titles)
        strong = split_terms(strong_skills)
        profile = dict(template)
        profile.update(
            {
                "name": name.strip() or "Job Seeker",
                "home_city": city.strip(),
                "home_state": state.strip(),
                "preferred_location_terms": locations,
                "remote_ok": bool(remote_ok),
                "target_titles": targets,
                "title_family_terms": targets,
                "seniority_preferences": split_terms(seniority),
                "deprioritize_seniority": split_terms(avoid_seniority),
                "strong_skills": strong,
                "secondary_skills": split_terms(secondary_skills),
                "focus_terms": split_terms(focus_terms) or strong,
                "bonus_terms": split_terms(bonus_terms),
                "domain_strengths": list(domain_strengths),
                "salary_floor": int(salary_floor),
                "salary_target": int(salary_target),
                "daily_application_goal": int(daily_goal),
                "avoid_terms": split_terms(avoid_terms),
            }
        )
        save_user_profile(profile)
        if resume_storage_text:
            save_resume(resume_storage_text, resume_source_name)
        st.session_state["welcome_complete"] = profile.get("name", "Job Seeker")
        st.rerun()

st.markdown(
    '<div class="taskbar"><span class="start">🪟 start</span>'
    '<span class="task">📁 Opportunity Intelligence · Résumé Setup</span></div>',
    unsafe_allow_html=True,
)
