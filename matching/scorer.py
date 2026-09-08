from __future__ import annotations
import re
from typing import Dict, List, Tuple

WEIGHTS = {
    "title": 20,
    "skills": 25,
    "seniority": 15,
    "process_ops": 15,
    "crm_power_platform": 10,
    "location": 10,
    "salary": 5,
}

PROCESS_TERMS = [
    "process improvement", "continuous improvement", "operations",
    "workflow", "requirements", "stakeholder", "business process",
    "process optimization", "change management"
]

CRM_TERMS = [
    "dynamics 365", "dataverse", "crm", "power automate",
    "power apps", "power platform", "salesforce"
]

def normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()

def contains_any(text: str, terms: List[str]) -> List[str]:
    return [term for term in terms if term in text]

def score_job(job: Dict, profile: Dict) -> Tuple[int, Dict]:
    title = normalize(job.get("title"))
    description = normalize(job.get("description"))
    location = normalize(job.get("location"))
    combined = f"{title} {description} {location}"

    details = {}
    total = 0

    title_matches = contains_any(title, profile["target_titles"])
    title_score = WEIGHTS["title"] if title_matches else 0
    if not title_score:
        analystish = any(t in title for t in ["analyst", "systems", "business intelligence"])
        title_score = 10 if analystish else 0
    total += title_score
    details["title"] = {"score": title_score, "matches": title_matches}

    strong = contains_any(combined, profile["strong_skills"])
    secondary = contains_any(combined, profile["secondary_skills"])
    raw = min(1.0, (len(strong) + len(secondary) * 0.45) / 7.0)
    skill_score = round(WEIGHTS["skills"] * raw)
    total += skill_score
    details["skills"] = {
        "score": skill_score,
        "strong_matches": strong,
        "secondary_matches": secondary,
    }

    bad_seniority = contains_any(title, profile["deprioritize_seniority"])
    if bad_seniority:
        seniority_score = 2
    elif any(x in title for x in profile["seniority_preferences"]):
        seniority_score = WEIGHTS["seniority"]
    else:
        seniority_score = 9
    total += seniority_score
    details["seniority"] = {"score": seniority_score, "warnings": bad_seniority}

    process_matches = contains_any(combined, PROCESS_TERMS)
    process_score = min(WEIGHTS["process_ops"], len(process_matches) * 3)
    total += process_score
    details["process_ops"] = {"score": process_score, "matches": process_matches}

    crm_matches = contains_any(combined, CRM_TERMS)
    crm_score = min(WEIGHTS["crm_power_platform"], len(crm_matches) * 3)
    total += crm_score
    details["crm_power_platform"] = {"score": crm_score, "matches": crm_matches}

    preferred_locations = contains_any(location, profile["preferred_location_terms"])
    remote = bool(job.get("remote")) or "remote" in combined
    location_score = WEIGHTS["location"] if (preferred_locations or remote) else 3
    total += location_score
    details["location"] = {
        "score": location_score,
        "matches": preferred_locations,
        "remote": remote,
    }

    salary_min = job.get("salary_min")
    if salary_min is None:
        salary_score = 2
    elif salary_min >= profile["salary_target"]:
        salary_score = WEIGHTS["salary"]
    elif salary_min >= profile["salary_floor"]:
        salary_score = 4
    else:
        salary_score = 0
    total += salary_score
    details["salary"] = {"score": salary_score, "salary_min": salary_min}

    avoid = contains_any(combined, profile["avoid_terms"])
    if avoid:
        total -= 20
        details["avoid"] = avoid

    total = max(0, min(100, int(round(total))))
    if total >= 85:
        verdict = "APPLY"
    elif total >= 70:
        verdict = "STRONG CONSIDER"
    elif total >= 55:
        verdict = "STRETCH"
    else:
        verdict = "SKIP"

    details["verdict"] = verdict
    return total, details
