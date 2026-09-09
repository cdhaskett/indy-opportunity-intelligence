from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from data.db import list_jobs
from matching.resume_intelligence import (
    extract_resume_text,
    infer_profile_from_resume,
    resume_health,
    resume_match_score,
)
from matching.scorer import score_job
from profile_config import load_profile, load_profile_template, save_user_profile

st.set_page_config(page_title="Resume Intelligence", page_icon="🧠", layout="wide")

st.title("🧠 Resume Intelligence")
st.caption("Separate what you can actually do from what your current resume proves on paper.")

if "oi_resume_text" not in st.session_state:
    st.session_state["oi_resume_text"] = ""
if "oi_resume_name" not in st.session_state:
    st.session_state["oi_resume_name"] = ""

profile = load_profile()
template = load_profile_template()

uploaded = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx", "txt"],
    help="Your resume is analyzed in your current app session. It is not added to the public repository.",
)

if uploaded is not None:
    try:
        text = extract_resume_text(uploaded.getvalue(), uploaded.name)
        if not text.strip():
            st.error("I couldn't extract readable text from that file. Try a DOCX or text-based PDF.")
        else:
            st.session_state["oi_resume_text"] = text
            st.session_state["oi_resume_name"] = uploaded.name
            inferred = infer_profile_from_resume(text, template)

            # Keep personal search constraints when they already exist; replace resume-evidence fields.
            for key in [
                "name", "preferred_location_terms", "home_city", "home_state",
                "remote_ok", "salary_target", "salary_floor", "employment_type",
                "avoid_terms", "deprioritize_seniority", "domain_strengths",
            ]:
                if profile.get(key) not in (None, "", []):
                    inferred[key] = profile.get(key)

            save_user_profile(inferred)
            profile = inferred
            st.success(f"Analyzed {uploaded.name}. Review the profile below before using it to score jobs.")
    except Exception as exc:
        st.error(str(exc))

resume_text = st.session_state.get("oi_resume_text", "")

if resume_text:
    health = resume_health(resume_text)
    c1, c2, c3 = st.columns(3)
    c1.metric("Resume Health", health["score"])
    c2.metric("Words", health["word_count"])
    c3.metric("Skills Explicitly Found", len(health["skills_found"]))

    if health["score"] < 60:
        st.warning("Your background may be stronger than this resume makes obvious. That's exactly what this page is designed to catch.")

    if health["notes"]:
        with st.expander("Resume health findings", expanded=health["score"] < 70):
            for note in health["notes"]:
                st.write(f"• {note}")

st.subheader("Editable Candidate Profile")
st.caption("This is the version Opportunity Intelligence uses for Job Fit. Fix anything the resume parser misunderstood or failed to see.")


def join_terms(values) -> str:
    return ", ".join(values or [])


def split_terms(value: str) -> list[str]:
    return [x.strip().lower() for x in value.replace("\n", ",").split(",") if x.strip()]


with st.form("resume_profile_editor"):
    name = st.text_input("Name", value=profile.get("name", "Job Seeker"))
    target_titles = st.text_area(
        "Target / relevant job titles",
        value=join_terms(profile.get("target_titles", [])),
        height=90,
        help="These should describe roles you can credibly pursue, not only exact historical titles.",
    )
    strong_skills = st.text_area(
        "Strong skills",
        value=join_terms(profile.get("strong_skills", [])),
        height=100,
    )
    secondary_skills = st.text_area(
        "Secondary / developing skills",
        value=join_terms(profile.get("secondary_skills", [])),
        height=90,
    )
    focus_terms = st.text_area(
        "Work themes you want more of",
        value=join_terms(profile.get("focus_terms", template.get("focus_terms", []))),
        height=80,
        help="Examples: process improvement, operations, stakeholder management, automation.",
    )

    col1, col2 = st.columns(2)
    with col1:
        salary_floor = st.number_input(
            "Minimum acceptable salary",
            min_value=0,
            step=5000,
            value=int(profile.get("salary_floor", template.get("salary_floor", 0)) or 0),
        )
    with col2:
        salary_target = st.number_input(
            "Target salary",
            min_value=0,
            step=5000,
            value=int(profile.get("salary_target", template.get("salary_target", 0)) or 0),
        )

    submitted = st.form_submit_button("Save Candidate Profile")

if submitted:
    updated = dict(profile)
    updated.update({
        "name": name.strip() or "Job Seeker",
        "target_titles": split_terms(target_titles),
        "title_family_terms": split_terms(target_titles) + profile.get("title_family_terms", []),
        "strong_skills": split_terms(strong_skills),
        "secondary_skills": split_terms(secondary_skills),
        "focus_terms": split_terms(focus_terms),
        "salary_floor": int(salary_floor),
        "salary_target": int(salary_target),
    })
    updated["title_family_terms"] = list(dict.fromkeys(updated["title_family_terms"]))
    save_user_profile(updated)
    profile = updated
    st.success("Candidate profile saved for this session.")

if resume_text:
    st.subheader("Job Fit vs Resume Match")
    st.caption(
        "Job Fit uses your editable candidate profile. Resume Match asks a different question: does the actual resume text prove that fit?"
    )

    rows = []
    for job in list_jobs():
        fit_score, fit_details = score_job(job, profile)
        resume_result = resume_match_score(job, resume_text, profile)
        resume_score = resume_result["score"]
        rows.append({
            "Job": job.get("title"),
            "Company": job.get("company"),
            "Job Fit": fit_score,
            "Resume Match": resume_score,
            "Gap": fit_score - resume_score,
            "Verdict": fit_details.get("verdict"),
            "Missing from resume": ", ".join(resume_result.get("missing_skills", [])[:6]),
        })

    if rows:
        df = pd.DataFrame(rows).sort_values(["Job Fit", "Gap"], ascending=[False, False])
        st.dataframe(df.head(30), width="stretch", hide_index=True)

        undersold = df[(df["Job Fit"] >= 65) & (df["Gap"] >= 20)]
        if not undersold.empty:
            top = undersold.iloc[0]
            st.warning(
                f"Your resume appears to undersell you for {top['Job']} at {top['Company']}: "
                f"Job Fit {int(top['Job Fit'])} vs Resume Match {int(top['Resume Match'])}."
            )
            missing = top.get("Missing from resume")
            if missing:
                st.write(f"Evidence to strengthen if it is truthful for your background: **{missing}**")
else:
    st.info("Upload a resume to unlock Resume Health and Job Fit vs Resume Match comparisons.")
