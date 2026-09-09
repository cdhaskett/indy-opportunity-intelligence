from __future__ import annotations

import re
from typing import Dict, List, Tuple

WEIGHTS = {
    "title": 24,
    "skills": 24,
    "seniority": 14,
    "focus": 16,
    "bonus": 6,
    "location": 10,
    "salary": 6,
}

DEFAULT_FOCUS_TERMS = [
    "process improvement", "continuous improvement", "operations",
    "workflow", "requirements", "stakeholder", "business process",
    "process optimization", "change management", "cross-functional",
    "business requirements", "process mapping", "root cause",
    "operational efficiency",
]

DEFAULT_BONUS_TERMS = [
    "dynamics 365", "dataverse", "crm", "power automate",
    "power apps", "power platform", "salesforce",
]

DOMAIN_TERMS = {
    "HR / People Operations": [
        "hr operations", "human resources", "hr generalist", "people operations",
        "employee relations", "shared services", "workday hcm", "payroll operations",
        "benefits administration", "talent operations",
    ],
    "Healthcare / Clinical": [
        "clinical experience", "healthcare experience", "hospital experience",
        "health system", "payer experience", "provider experience", "clinical operations",
    ],
    "Finance / Accounting": [
        "accounting experience", "finance experience", "financial accounting",
        "gaap", "fp&a", "financial planning and analysis", "public accounting",
    ],
    "Insurance": [
        "insurance experience", "claims experience", "underwriting experience",
        "actuarial experience", "property and casualty", "p&c insurance",
    ],
    "Legal / Compliance": [
        "legal experience", "law firm experience", "regulatory compliance experience",
        "paralegal experience", "legal operations",
    ],
    "Supply Chain / Procurement": [
        "supply chain experience", "procurement experience", "purchasing experience",
        "logistics experience", "warehouse operations experience",
    ],
}

REQUIREMENT_CUES = [
    "required", "requirement", "must have", "minimum", "at least",
    "years of", "years experience", "years of experience", "proven experience",
    "direct experience", "prior experience", "demonstrated experience",
]


def normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def contains_any(text: str, terms: List[str]) -> List[str]:
    return [term for term in terms if term and normalize(term) in text]


def detect_hard_domain_requirements(description: str, profile: Dict) -> List[Dict]:
    findings: List[Dict] = []
    domain_strengths = set(profile.get("domain_strengths", []))
    chunks = [
        c.strip()
        for c in re.split(r"[\n\r•]|(?<=[.!?])\s+", description)
        if c.strip()
    ]

    for domain, terms in DOMAIN_TERMS.items():
        if domain in domain_strengths:
            continue
        for chunk in chunks:
            domain_hits = contains_any(chunk, terms)
            if not domain_hits:
                continue
            cue_hits = contains_any(chunk, REQUIREMENT_CUES)
            years_match = re.search(r"\b(\d+)\s*\+?\s*(?:years?|yrs?)\b", chunk)
            if not cue_hits and not years_match:
                continue

            years = int(years_match.group(1)) if years_match else None
            if years is not None and years >= 4:
                penalty, severity, gate = 24, "high", "hard"
            elif years is not None and years >= 2:
                penalty, severity, gate = 16, "medium", "soft"
            else:
                penalty, severity, gate = 10, "medium", "soft"

            findings.append({
                "domain": domain,
                "terms": domain_hits,
                "years": years,
                "penalty": penalty,
                "severity": severity,
                "gate": gate,
                "evidence": chunk[:260],
            })
            break

    return findings


def score_job(job: Dict, profile: Dict) -> Tuple[int, Dict]:
    title = normalize(job.get("title"))
    description = normalize(job.get("description"))
    location = normalize(job.get("location"))
    combined = f"{title} {description} {location}"

    details: Dict = {}
    total = 0

    target_titles = profile.get("target_titles", [])
    title_family_terms = profile.get("title_family_terms", target_titles)
    title_matches = contains_any(title, target_titles)
    family_matches = contains_any(title, title_family_terms)
    if title_matches:
        title_score = WEIGHTS["title"]
    elif family_matches:
        title_score = 19
    else:
        title_score = 0
    total += title_score
    details["title"] = {"score": title_score, "max": WEIGHTS["title"], "matches": title_matches or family_matches}

    strong = contains_any(combined, profile.get("strong_skills", []))
    secondary = contains_any(combined, profile.get("secondary_skills", []))
    raw = min(1.0, (len(strong) + len(secondary) * 0.5) / 5.0)
    skill_score = round(WEIGHTS["skills"] * raw)
    total += skill_score
    details["skills"] = {"score": skill_score, "max": WEIGHTS["skills"], "strong_matches": strong, "secondary_matches": secondary}

    bad_seniority = contains_any(title, profile.get("deprioritize_seniority", []))
    seniority_preferences = profile.get("seniority_preferences", [])
    if bad_seniority:
        seniority_score = 2
    elif contains_any(title, seniority_preferences):
        seniority_score = WEIGHTS["seniority"]
    elif family_matches:
        seniority_score = 12
    else:
        seniority_score = 8
    total += seniority_score
    details["seniority"] = {"score": seniority_score, "max": WEIGHTS["seniority"], "warnings": bad_seniority}

    focus_terms = profile.get("focus_terms", DEFAULT_FOCUS_TERMS)
    focus_matches = contains_any(combined, focus_terms)
    focus_score = min(WEIGHTS["focus"], len(set(focus_matches)) * 4)
    total += focus_score
    details["process_ops"] = {"score": focus_score, "max": WEIGHTS["focus"], "matches": focus_matches}

    bonus_terms = profile.get("bonus_terms", DEFAULT_BONUS_TERMS)
    bonus_matches = contains_any(combined, bonus_terms)
    bonus_score = min(WEIGHTS["bonus"], len(set(bonus_matches)) * 3)
    total += bonus_score
    details["crm_power_platform"] = {"score": bonus_score, "max": WEIGHTS["bonus"], "matches": bonus_matches}

    preferred_locations = contains_any(location, profile.get("preferred_location_terms", []))
    remote = bool(job.get("remote")) or "remote" in combined
    remote_ok = bool(profile.get("remote_ok", True))
    location_score = WEIGHTS["location"] if (preferred_locations or (remote and remote_ok)) else 3
    total += location_score
    details["location"] = {"score": location_score, "max": WEIGHTS["location"], "matches": preferred_locations, "remote": remote, "remote_ok": remote_ok}

    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    salary_target = int(profile.get("salary_target", 0) or 0)
    salary_floor = int(profile.get("salary_floor", 0) or 0)
    salary_below_floor = bool(salary_floor and salary_max is not None and float(salary_max) < salary_floor)

    if salary_below_floor:
        salary_score = 0
    elif salary_min is None:
        salary_score = 3
    elif salary_target and salary_min >= salary_target:
        salary_score = WEIGHTS["salary"]
    elif not salary_floor or salary_min >= salary_floor:
        salary_score = 5
    else:
        salary_score = 1 if salary_max is not None and salary_max >= salary_floor else 0
    total += salary_score
    details["salary"] = {
        "score": salary_score,
        "max": WEIGHTS["salary"],
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_floor": salary_floor,
        "below_floor": salary_below_floor,
    }

    avoid = contains_any(combined, profile.get("avoid_terms", []))
    if avoid:
        total -= 20
        details["avoid"] = avoid

    hard_domains = detect_hard_domain_requirements(description, profile)
    domain_penalty = min(30, sum(item["penalty"] for item in hard_domains))
    if domain_penalty:
        total -= domain_penalty

    has_hard_gate = any(item.get("gate") == "hard" for item in hard_domains)
    has_soft_gate = any(item.get("gate") == "soft" for item in hard_domains)
    if has_hard_gate:
        total = min(total, 49)
    elif has_soft_gate:
        total = min(total, 64)
    if salary_below_floor:
        total = min(total, 49)

    details["hard_requirements"] = {
        "penalty": domain_penalty,
        "findings": hard_domains,
        "hard_gate": has_hard_gate,
        "soft_gate": has_soft_gate,
        "salary_gate": salary_below_floor,
    }

    total = max(0, min(100, int(round(total))))

    if has_hard_gate or salary_below_floor:
        verdict = "SKIP"
    elif total >= 80:
        verdict = "APPLY"
    elif total >= 65:
        verdict = "STRONG CONSIDER"
    elif total >= 50:
        verdict = "STRETCH"
    else:
        verdict = "SKIP"

    details["verdict"] = verdict
    return total, details
