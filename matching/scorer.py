from __future__ import annotations
import re
from typing import Dict, List, Tuple

WEIGHTS = {
    "title": 24,
    "skills": 24,
    "seniority": 14,
    "process_ops": 16,
    "crm_power_platform": 6,
    "location": 10,
    "salary": 6,
}

PROCESS_TERMS = [
    "process improvement", "continuous improvement", "operations",
    "workflow", "requirements", "stakeholder", "business process",
    "process optimization", "change management", "cross-functional",
    "business requirements", "process mapping", "root cause",
    "operational efficiency", "continuous improvement"
]

CRM_TERMS = [
    "dynamics 365", "dataverse", "crm", "power automate",
    "power apps", "power platform", "salesforce"
]

ANALYST_TERMS = [
    "business analyst", "business systems analyst", "systems analyst",
    "operations analyst", "business intelligence analyst", "bi analyst",
    "data analyst", "performance analyst", "crm analyst",
    "continuous improvement analyst"
]

# Domains where years of direct functional experience can be a real gate rather
# than a transferable-skills preference. These only matter when paired with
# explicit requirement language.
DOMAIN_TERMS = {
    "HR / People Operations": [
        "hr operations", "human resources", "hr generalist", "people operations",
        "employee relations", "shared services", "workday hcm", "payroll operations",
        "benefits administration", "talent operations"
    ],
    "Healthcare / Clinical": [
        "clinical experience", "healthcare experience", "hospital experience",
        "health system", "payer experience", "provider experience", "clinical operations"
    ],
    "Finance / Accounting": [
        "accounting experience", "finance experience", "financial accounting",
        "gaap", "fp&a", "financial planning and analysis", "public accounting"
    ],
    "Insurance": [
        "insurance experience", "claims experience", "underwriting experience",
        "actuarial experience", "property and casualty", "p&c insurance"
    ],
    "Legal / Compliance": [
        "legal experience", "law firm experience", "regulatory compliance experience",
        "paralegal experience", "legal operations"
    ],
    "Supply Chain / Procurement": [
        "supply chain experience", "procurement experience", "purchasing experience",
        "logistics experience", "warehouse operations experience"
    ],
}

# Domains supported by the candidate's background strongly enough that an
# explicit domain requirement should not be treated as a gap.
PROFILE_DOMAIN_STRENGTHS = {
    "Supply Chain / Procurement",
}

REQUIREMENT_CUES = [
    "required", "requirement", "must have", "minimum", "at least",
    "years of", "years experience", "years of experience", "proven experience",
    "direct experience", "prior experience", "demonstrated experience"
]


def normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def contains_any(text: str, terms: List[str]) -> List[str]:
    return [term for term in terms if term in text]


def detect_hard_domain_requirements(description: str) -> List[Dict]:
    """Find explicit domain-experience gates without penalizing casual mentions."""
    findings: List[Dict] = []
    # Split loosely into sentences/bullets so requirement cues and domain terms
    # need to occur near one another.
    chunks = [c.strip() for c in re.split(r"[\n\r•]|(?<=[.!?])\s+", description) if c.strip()]

    for domain, terms in DOMAIN_TERMS.items():
        if domain in PROFILE_DOMAIN_STRENGTHS:
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
            # Explicit multi-year requirements are more serious than generic
            # "experience required" wording.
            if years is not None and years >= 4:
                penalty = 18
                severity = "high"
            elif years is not None and years >= 2:
                penalty = 12
                severity = "medium"
            else:
                penalty = 9
                severity = "medium"

            findings.append({
                "domain": domain,
                "terms": domain_hits,
                "years": years,
                "penalty": penalty,
                "severity": severity,
                "evidence": chunk[:260],
            })
            break

    # Multiple unrelated domain gates should matter, but cap the deduction so a
    # single parsing mistake cannot zero out an otherwise relevant role.
    return findings


def score_job(job: Dict, profile: Dict) -> Tuple[int, Dict]:
    title = normalize(job.get("title"))
    description = normalize(job.get("description"))
    location = normalize(job.get("location"))
    combined = f"{title} {description} {location}"

    details = {}
    total = 0

    title_matches = contains_any(title, profile["target_titles"])
    analyst_matches = contains_any(title, ANALYST_TERMS)
    if title_matches:
        title_score = WEIGHTS["title"]
    elif analyst_matches or "analyst" in title:
        title_score = 19
    elif any(t in title for t in ["systems", "business intelligence", "operations"]):
        title_score = 13
    else:
        title_score = 0
    total += title_score
    details["title"] = {"score": title_score, "max": WEIGHTS["title"], "matches": title_matches or analyst_matches}

    strong = contains_any(combined, profile["strong_skills"])
    secondary = contains_any(combined, profile["secondary_skills"])
    raw = min(1.0, (len(strong) + len(secondary) * 0.5) / 5.0)
    skill_score = round(WEIGHTS["skills"] * raw)
    total += skill_score
    details["skills"] = {
        "score": skill_score,
        "max": WEIGHTS["skills"],
        "strong_matches": strong,
        "secondary_matches": secondary,
    }

    bad_seniority = contains_any(title, profile["deprioritize_seniority"])
    if bad_seniority:
        seniority_score = 2
    elif "senior" in title and "analyst" in title:
        seniority_score = WEIGHTS["seniority"]
    elif any(x in title for x in profile["seniority_preferences"]):
        seniority_score = WEIGHTS["seniority"]
    elif "analyst" in title:
        seniority_score = 12
    else:
        seniority_score = 8
    total += seniority_score
    details["seniority"] = {"score": seniority_score, "max": WEIGHTS["seniority"], "warnings": bad_seniority}

    process_matches = contains_any(combined, PROCESS_TERMS)
    process_score = min(WEIGHTS["process_ops"], len(set(process_matches)) * 4)
    total += process_score
    details["process_ops"] = {"score": process_score, "max": WEIGHTS["process_ops"], "matches": process_matches}

    crm_matches = contains_any(combined, CRM_TERMS)
    crm_score = min(WEIGHTS["crm_power_platform"], len(set(crm_matches)) * 3)
    total += crm_score
    details["crm_power_platform"] = {"score": crm_score, "max": WEIGHTS["crm_power_platform"], "matches": crm_matches}

    preferred_locations = contains_any(location, profile["preferred_location_terms"])
    remote = bool(job.get("remote")) or "remote" in combined
    location_score = WEIGHTS["location"] if (preferred_locations or remote) else 3
    total += location_score
    details["location"] = {
        "score": location_score,
        "max": WEIGHTS["location"],
        "matches": preferred_locations,
        "remote": remote,
    }

    salary_min = job.get("salary_min")
    if salary_min is None:
        salary_score = 3
    elif salary_min >= profile["salary_target"]:
        salary_score = WEIGHTS["salary"]
    elif salary_min >= profile["salary_floor"]:
        salary_score = 5
    else:
        salary_score = 0
    total += salary_score
    details["salary"] = {"score": salary_score, "max": WEIGHTS["salary"], "salary_min": salary_min}

    avoid = contains_any(combined, profile["avoid_terms"])
    if avoid:
        total -= 20
        details["avoid"] = avoid

    hard_domains = detect_hard_domain_requirements(description)
    domain_penalty = min(24, sum(item["penalty"] for item in hard_domains))
    if domain_penalty:
        total -= domain_penalty
    details["hard_requirements"] = {
        "penalty": domain_penalty,
        "findings": hard_domains,
    }

    total = max(0, min(100, int(round(total))))

    if total >= 80:
        verdict = "APPLY"
    elif total >= 65:
        verdict = "STRONG CONSIDER"
    elif total >= 50:
        verdict = "STRETCH"
    else:
        verdict = "SKIP"

    details["verdict"] = verdict
    return total, details
