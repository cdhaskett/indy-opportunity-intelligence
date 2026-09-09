from __future__ import annotations

from typing import Any

import streamlit as st

from matching.resume_helper import analyze_resume_for_job
from matching.resume_parser import extract_resume_text
from matching.scorer import score_job
from resume_store import delete_resume, load_resume, save_resume


def _job_label(job: dict[str, Any], score: int) -> str:
    return f"{score} · {job.get('title') or 'Untitled role'} — {job.get('company') or 'Unknown company'}"


def _chips(values: list[str]) -> str:
    if not values:
        return "None detected"
    return " · ".join(values)


def _coaching_text(job: dict[str, Any], analysis: dict[str, Any]) -> str:
    lines = [
        "Opportunity Intelligence — Resume Helper",
        f"Role: {job.get('title', '')}",
        f"Company: {job.get('company', '')}",
        f"Job Fit: {analysis['job_fit_score']}",
        f"Resume Match: {analysis['resume_match_score']}",
        "",
        analysis["headline"],
        "",
        "ALREADY PROVING",
        ", ".join(analysis.get("matched_signals", [])) or "None detected",
        "",
        "MISSING / ADD ONLY IF TRUE",
        ", ".join(analysis.get("missing_signals", [])) or "None",
        "",
        "RESUME HEALTH",
        analysis.get("resume_health", {}).get("label", ""),
    ]
    for issue in analysis.get("resume_health", {}).get("issues", []):
        lines.append(f"- {issue.get('message', '')}")
    if analysis.get("dont_claim"):
        lines.extend(["", "DO NOT CLAIM JUST TO MATCH"])
        for item in analysis["dont_claim"]:
            lines.append(f"- {item.get('domain')}: {item.get('evidence')}")
    if analysis.get("bullet_coach"):
        lines.extend(["", "BULLET COACH"])
        for item in analysis["bullet_coach"]:
            lines.append(f"Original: {item['original']}")
            lines.append(f"Coach: {item['tip']}")
            lines.append(f"Structure: {item['structure']}")
            lines.append("")
    return "\n".join(lines)


def _resume_editor(stored: dict[str, Any]) -> None:
    has_stored = bool(stored.get("text"))
    if has_stored:
        source = stored.get("source_name") or "saved résumé"
        st.success(f"My Résumé is saved · {source}")
        st.caption(
            "Only extracted résumé text is stored. The original PDF/Word file is not kept by Opportunity Intelligence."
        )
        label = "Update / replace My Résumé"
    else:
        st.info(
            "Add your résumé once. After that, Résumé Match can be calculated automatically for every role you review."
        )
        label = "Add My Résumé"

    with st.expander(label, expanded=not has_stored):
        upload = st.file_uploader(
            "Upload PDF, Word, or TXT",
            type=["pdf", "docx", "txt"],
            key="my-resume-upload",
            help="The document is read in memory; only extracted text is saved.",
        )
        pasted = st.text_area(
            "Or paste résumé text — rough drafts are fine",
            height=160,
            key="my-resume-paste",
            placeholder="Paste an old résumé, current résumé, or rough work-history notes here...",
        )

        if st.button("💾 Save My Résumé", use_container_width=True, key="save-my-resume"):
            text = ""
            source_name = "Pasted résumé text"
            if upload is not None:
                try:
                    text = extract_resume_text(upload.getvalue(), upload.name)
                    source_name = upload.name
                except Exception as exc:
                    st.error(f"I couldn't read that résumé: {exc}")
                    return
            elif pasted.strip():
                text = pasted.strip()

            if not text.strip():
                st.error("Upload a résumé or paste some résumé/work-history text first.")
                return

            try:
                save_resume(text, source_name)
            except Exception as exc:
                st.error(f"Could not save My Résumé: {exc}")
                return
            st.session_state["resume_saved_message"] = "My Résumé saved. Résumé Match scores are ready."
            st.rerun()

    if has_stored:
        with st.expander("Remove My Résumé"):
            st.caption("This removes the stored extracted text. Your job profile and application history stay intact.")
            if st.button("Remove stored résumé", key="remove-my-resume"):
                delete_resume()
                st.rerun()


def render_resume_helper(profile: dict[str, Any], jobs: list[dict[str, Any]]) -> None:
    st.markdown("### 📝 Resume Helper")
    st.caption(
        "Two separate questions: How well do you fit the job, and how well does your résumé prove it? "
        "A weak résumé should trigger coaching — not lower the person's Job Fit."
    )

    if "resume_saved_message" in st.session_state:
        st.success(st.session_state.pop("resume_saved_message"))

    if not jobs:
        st.info("Load or refresh the job market first, then come back here to tailor a résumé to a real role.")
        return

    scored: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    for raw in jobs:
        score, details = score_job(raw, profile)
        scored.append((score, dict(raw), details))
    scored.sort(key=lambda item: item[0], reverse=True)

    options = list(range(len(scored)))
    selected_index = st.selectbox(
        "Choose a job to tailor toward",
        options,
        format_func=lambda i: _job_label(scored[i][1], scored[i][0]),
    )
    fit_score, job, fit_details = scored[selected_index]
    stored = load_resume()
    resume_text = str(stored.get("text") or "")
    analysis = (
        analyze_resume_for_job(resume_text, job, profile, fit_score, fit_details)
        if resume_text
        else None
    )

    st.markdown(f"**{job.get('title')}** · {job.get('company')} · {job.get('location') or 'Location not listed'}")
    if job.get("url"):
        st.link_button("Open job posting", job["url"])

    st.markdown("#### 📊 Two-score view")
    c1, c2 = st.columns(2)
    c1.metric("Job Fit", fit_score)
    c2.metric("Résumé Match", analysis["resume_match_score"] if analysis else "—")
    if analysis:
        st.info(analysis["headline"])
    else:
        st.caption("Résumé Match is waiting for My Résumé. Add it once below; Job Fit is already available.")

    st.markdown("#### 📄 My Résumé")
    _resume_editor(stored)

    if not analysis:
        return

    health = analysis["resume_health"]
    st.markdown(f"#### 🩺 Résumé health: {health['label']}")
    if health["issues"]:
        for issue in health["issues"]:
            st.write(f"- {issue['message']}")
    else:
        st.write("The document has a solid structure. Focus on tailoring rather than rebuilding.")

    left, right = st.columns(2)
    with left:
        st.markdown("#### ✅ Already proving")
        st.write(_chips(analysis["matched_signals"]))
        if analysis["proof_lines"]:
            with st.expander("Show proof already in the résumé"):
                for item in analysis["proof_lines"]:
                    st.write(f"• {item['line']}")
                    st.caption("Matched: " + ", ".join(item["signals"]))

    with right:
        st.markdown("#### 🔧 Missing or buried")
        if analysis["missing_signals"]:
            st.write(_chips(analysis["missing_signals"]))
            st.caption("Add or emphasize these only when they are genuinely part of the candidate's experience.")
        else:
            st.write("The major detected job signals are already visible.")

        if analysis["required_missing"]:
            st.warning(
                "Required-looking signals not visible in the résumé: "
                + ", ".join(analysis["required_missing"])
                + ". Confirm the experience before adding anything."
            )

    if analysis["dont_claim"]:
        st.markdown("#### ⛔ Don't résumé-your-way-around this")
        for item in analysis["dont_claim"]:
            st.error(
                f"{item.get('domain')}: {item.get('message')}\n\nPosting evidence: {item.get('evidence') or 'Required domain experience'}"
            )

    st.markdown("#### ✍️ Bullet coach")
    if not analysis["bullet_coach"]:
        st.write(
            "I couldn't find enough job-relevant proof lines to coach yet. That usually means the résumé needs "
            "more specific work-history detail, not just more keywords."
        )
    else:
        for i, item in enumerate(analysis["bullet_coach"], start=1):
            with st.expander(f"Bullet {i}: strengthen existing evidence"):
                st.write("**Current line**")
                st.write(item["original"])
                st.write("**What to improve**")
                st.write(item["tip"])
                st.write("**Safe structure**")
                st.code(item["structure"], language=None)

    st.markdown("#### 🧭 What I would fix first")
    priorities: list[str] = []
    if analysis["resume_health"]["issues"]:
        priorities.extend(issue["message"] for issue in analysis["resume_health"]["issues"][:3])
    if analysis["required_missing"]:
        priorities.append(
            "Verify whether the candidate truly has the required-looking experience that is currently absent from the résumé."
        )
    elif analysis["missing_signals"]:
        priorities.append(
            "Bring truthful job-relevant terms already supported by the candidate's experience into the summary, skills, or relevant work bullets."
        )
    if not priorities:
        priorities.append("Keep the structure and tailor the strongest existing evidence toward this specific posting.")

    for i, priority in enumerate(priorities, start=1):
        st.write(f"**{i}.** {priority}")

    notes = _coaching_text(job, analysis)
    st.download_button(
        "⬇ Download coaching notes",
        data=notes,
        file_name="resume_helper_notes.txt",
        mime="text/plain",
        use_container_width=True,
    )
