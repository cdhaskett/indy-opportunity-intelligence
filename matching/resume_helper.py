from __future__ import annotations

import re
from typing import Any

from matching.resume_parser import SKILL_TERMS

ACTION_VERBS = {
    "built", "created", "developed", "designed", "implemented", "improved", "reduced",
    "increased", "managed", "led", "owned", "automated", "analyzed", "delivered",
    "launched", "standardized", "streamlined", "optimized", "resolved", "partnered",
    "translated", "configured", "administered", "supported", "trained", "documented",
    "coordinated", "identified", "established", "integrated", "migrated", "maintained",
}

REQUIREMENT_CUES = (
    "required", "requirements", "minimum", "must have", "must-have", "at least",
    "years of experience", "experience with", "proficiency", "proficient", "demonstrated",
)


def _norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").lower()).strip()


def _contains(text: str, term: str) -> bool:
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])", text))


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = _norm(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _resume_lines(text: str) -> list[str]:
    rows = []
    for raw in text.replace("\r", "\n").split("\n"):
        line = re.sub(r"\s+", " ", raw).strip(" \t•·-–—|")
        if line:
            rows.append(line)
    return rows


def _job_signals(job: dict[str, Any], profile: dict[str, Any]) -> list[str]:
    text = _norm(f"{job.get('title', '')} {job.get('description', '')}")
    candidates: list[str] = []

    for field in ("strong_skills", "secondary_skills", "focus_terms", "bonus_terms"):
        for term in profile.get(field, []) or []:
            if term and _contains(text, str(term)):
                candidates.append(str(term))

    for term in SKILL_TERMS:
        if _contains(text, term):
            candidates.append(term)

    title = _norm(job.get("title"))
    for phrase in profile.get("target_titles", []) or []:
        if phrase and _contains(title, str(phrase)):
            candidates.append(str(phrase))

    return _unique(candidates)[:28]


def _required_signals(job: dict[str, Any], signals: list[str]) -> list[str]:
    raw = job.get("description") or ""
    chunks = [
        _norm(part)
        for part in re.split(r"[\n\r•]|(?<=[.!?])\s+|</li>|</p>|<br\s*/?>", raw, flags=re.I)
        if _norm(part)
    ]
    required: list[str] = []
    for chunk in chunks:
        if not any(cue in chunk for cue in REQUIREMENT_CUES) and not re.search(r"\b\d+\+?\s+years?\b", chunk):
            continue
        for signal in signals:
            if _contains(chunk, signal):
                required.append(signal)
    return _unique(required)


def _title_alignment(resume_text: str, job: dict[str, Any], profile: dict[str, Any]) -> int:
    resume = _norm(resume_text)
    title = _norm(job.get("title"))
    if title and title in resume:
        return 20

    role_terms = []
    for term in (profile.get("target_titles", []) or []) + (profile.get("title_family_terms", []) or []):
        if term and (_contains(title, str(term)) or _contains(resume, str(term))):
            role_terms.append(str(term))
    if role_terms:
        matched = sum(1 for term in _unique(role_terms) if _contains(resume, term))
        return min(20, 8 + matched * 4)

    title_words = [w for w in re.findall(r"[a-z]+", title) if len(w) > 4]
    overlap = sum(1 for word in title_words if _contains(resume, word))
    return min(12, overlap * 3)


def _proof_lines(resume_text: str, matched_signals: list[str]) -> list[dict[str, Any]]:
    proof: list[dict[str, Any]] = []
    for line in _resume_lines(resume_text):
        lower = _norm(line)
        hits = [term for term in matched_signals if _contains(lower, term)]
        if hits:
            proof.append({"line": line, "signals": hits})
    proof.sort(key=lambda item: (len(item["signals"]), len(item["line"])), reverse=True)
    return proof[:8]


def _resume_health(resume_text: str) -> dict[str, Any]:
    text = resume_text or ""
    lower = text.lower()
    lines = _resume_lines(text)
    issues: list[dict[str, str]] = []

    bulletish = [line for line in text.splitlines() if line.strip().startswith(("•", "-", "–", "—", "*"))]
    quantified = [
        line for line in lines
        if re.search(r"(?:\$|%|\b\d+(?:\.\d+)?\b)", line)
        and not re.fullmatch(r".*(?:19|20)\d{2}.*", line)
    ]
    action_led = []
    for line in lines:
        first = re.findall(r"[A-Za-z]+", line.lower())[:1]
        if first and first[0] in ACTION_VERBS:
            action_led.append(line)

    if len(text.strip()) < 1400:
        issues.append({"kind": "coverage", "message": "The résumé is fairly sparse. Add more evidence from recent work before worrying about perfect wording."})
    if len(bulletish) < 5 and len(lines) > 8:
        issues.append({"kind": "structure", "message": "Work history is not very scannable. Use concise accomplishment bullets instead of dense paragraphs."})
    if len(quantified) < 3:
        issues.append({"kind": "impact", "message": "Very few measurable outcomes are visible. Add real counts, percentages, dollars, time saved, adoption, volume, or scope where you know them."})
    if len(action_led) < 4:
        issues.append({"kind": "bullets", "message": "More bullets should lead with strong actions such as Built, Improved, Automated, Managed, Reduced, or Led."})
    if not re.search(r"\bskills?\b", lower):
        issues.append({"kind": "skills", "message": "A clear Skills section would make tools and keywords easier for recruiters and ATS systems to find."})
    if not re.search(r"\b(summary|profile|professional summary)\b", lower):
        issues.append({"kind": "positioning", "message": "A short professional summary could help explain the candidate's direction, especially if their past titles do not match the target role."})

    long_lines = [line for line in lines if len(line) > 220]
    if len(long_lines) >= 3:
        issues.append({"kind": "density", "message": "Several sections are text-heavy. Break long blocks into shorter accomplishment bullets."})

    if len(issues) <= 1:
        label = "Strong foundation"
    elif len(issues) <= 3:
        label = "Good foundation — needs sharpening"
    else:
        label = "Needs rebuilding, not just keyword tweaks"

    return {
        "label": label,
        "issues": issues,
        "bullet_count": len(bulletish),
        "quantified_lines": len(quantified),
        "action_led_lines": len(action_led),
    }


def _bullet_coach(proof: list[dict[str, Any]]) -> list[dict[str, str]]:
    coached: list[dict[str, str]] = []
    for item in proof[:5]:
        line = item["line"]
        signals = ", ".join(item["signals"][:4])
        has_metric = bool(re.search(r"(?:\$|%|\b\d+(?:\.\d+)?\b)", line))
        tip = (
            f"Lead with the action and result, keep the verified detail about {signals}, "
            + ("and make the business outcome clearer." if has_metric else "and add a real metric or scope only if you know it.")
        )
        structure = (
            f"[Strong action] [what you changed/owned] using {signals or 'the relevant tool/process'} "
            "to [business result]; add a truthful metric, scale, adoption, time saved, or volume if available."
        )
        coached.append({"original": line, "tip": tip, "structure": structure})
    return coached


def analyze_resume_for_job(
    resume_text: str,
    job: dict[str, Any],
    profile: dict[str, Any],
    job_fit_score: int,
    job_fit_details: dict[str, Any],
) -> dict[str, Any]:
    resume = _norm(resume_text)
    signals = _job_signals(job, profile)
    required = _required_signals(job, signals)
    matched = [signal for signal in signals if _contains(resume, signal)]
    missing = [signal for signal in signals if signal not in matched]
    required_missing = [signal for signal in required if signal not in matched]

    if signals:
        coverage = len(matched) / len(signals)
        signal_score = round(55 * coverage)
    else:
        signal_score = 28

    title_score = _title_alignment(resume_text, job, profile)
    proof = _proof_lines(resume_text, matched)
    proof_score = min(15, len(proof) * 3)

    if required:
        required_score = round(10 * (1 - len(required_missing) / len(required)))
    else:
        required_score = 7

    resume_match = max(0, min(100, signal_score + title_score + proof_score + required_score))

    hard_findings = job_fit_details.get("hard_requirements", {}).get("findings", [])
    dont_claim = []
    for finding in hard_findings:
        if finding.get("gate") != "hard":
            continue
        dont_claim.append({
            "domain": finding.get("domain"),
            "evidence": finding.get("evidence"),
            "message": "Do not add this just to match the posting unless the candidate truly has the experience.",
        })

    health = _resume_health(resume_text)

    if job_fit_score >= 75 and resume_match <= job_fit_score - 18:
        headline = "The candidate looks stronger than the résumé makes them look."
    elif resume_match >= 80:
        headline = "The résumé already tells a strong story for this role."
    elif job_fit_score < 50:
        headline = "Résumé edits cannot fix a genuine job-fit or hard-requirement gap."
    else:
        headline = "The résumé has usable evidence, but the match is not obvious enough yet."

    return {
        "job_fit_score": int(job_fit_score),
        "resume_match_score": int(resume_match),
        "headline": headline,
        "matched_signals": matched,
        "missing_signals": missing,
        "required_missing": required_missing,
        "proof_lines": proof,
        "bullet_coach": _bullet_coach(proof),
        "resume_health": health,
        "dont_claim": dont_claim,
        "job_signals": signals,
        "required_signals": required,
    }
