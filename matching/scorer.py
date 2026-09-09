from __future__ import annotations

import re
from typing import Dict, List, Tuple

# Titles and compensation are not the job. Fit is driven by evidence in the
# posting: skills, process/operations work, systems, level and location.
# Compensation remains visible and can enforce a clear user floor, but it does
# not add or subtract fit points.
WEIGHTS = {
    "title": 8,
    "skills": 34,
    "seniority": 10,
    "focus": 28,
    "bonus": 10,
    "location": 10,
    "salary": 0,
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
        "pharmaceutical experience", "pharma experience", "life sciences experience",
        "pharmaceutical media and marketing experience", "pharmaceutical media experience",
        "pharmaceutical marketing experience", "pharma media experience",
        "pharma marketing experience", "hcp omnichannel", "consumer omnichannel campaigns",
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

PREFERENCE_CUES = [
    "preferred", "nice to have", "nice-to-have", "bonus", "a plus", "plus if",
]


def normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def contains_any(text: str, terms: List[str]) -> List[str]:
    return [term for term in terms if term and normalize(term) in text]


def _money_value(token: str) -> int | None:
    raw = token.lower().replace("$", "").replace(",", "").strip()
    multiplier = 1
    if raw.endswith("k"):
        multiplier = 1000
        raw = raw[:-1].strip()
    try:
        value = float(raw) * multiplier
    except ValueError:
        return None
    if value < 10000:
        return None
    return int(round(value))


def extract_salary_range(description: str | None) -> Tuple[int | None, int | None]:
    """Extract a clearly stated annual salary range when the ATS omits structured pay fields."""
    text = normalize(description)
    if not text:
        return None, None

    money = r"(?:\$\s*)?(?:\d{2,3}(?:,\d{3})+|\d{2,3}(?:\.\d+)?\s*[kK])"
    range_pattern = re.compile(
        rf"(?P<low>{money})\s*(?:-|–|—|to)\s*(?P<high>{money})",
        re.IGNORECASE,
    )

    for match in range_pattern.finditer(text):
        low = _money_value(match.group("low"))
        high = _money_value(match.group("high"))
        if low is None or high is None:
            continue
        if low > high:
            low, high = high, low
        if 20000 <= low <= 500000 and 20000 <= high <= 750000:
            return low, high

    return None, None


def _requirement_chunks(description: str | None) -> List[str]:
    """Split job-description HTML/text into qualification-sized chunks."""
    text = description or ""
    text = re.sub(
        r"</?(?:li|p|br|div|ul|ol|h[1-6])[^>]*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    chunks = [
        normalize(c)
        for c in re.split(r"[\n\r•]|(?<=[.!?])\s+", text)
        if normalize(c)
    ]
    return chunks


def detect_hard_domain_requirements(description: str | None, profile: Dict) -> List[Dict]:
    """Find explicit domain-experience gates the current user does not claim as a strength."""
    findings: List[Dict] = []
    domain_strengths = set(profile.get("domain_strengths", []))
    chunks = _requirement_chunks(description)

    for domain, terms in DOMAIN_TERMS.items():
        if domain in domain_strengths:
            continue
        for chunk in chunks:
            domain_hits = contains_any(chunk, terms)
            if not domain_hits:
                continue

            cue_hits = contains_any(chunk, REQUIREMENT_CUES)
            preference_hits = contains_any(chunk, PREFERENCE_CUES)
            years_match = re.search(r"\b(\d+)\s*\+?\s*(?:years?|yrs?)\b", chunk)
            explicit_domain_experience = any(
                "experience" in normalize(hit) for hit in domain_hits
            )

            if not cue_hits and not years_match and not explicit_domain_experience:
                continue

            years = int(years_match.group(1)) if years_match else None

            if preference_hits:
                penalty, severity, gate = 8, "low", "soft"
            elif years is not None and years >= 4:
                penalty, severity, gate = 24, "high", "hard"
            elif explicit_domain_experience:
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
    raw_description = job.get("description") or ""
    description = normalize(raw_description)
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
        title_score = 6
    else:
        title_score = 4
    total += title_score
    details["title"] = {
        "score": title_score,
        "max": WEIGHTS["title"],
        "matches": title_matches or family_matches,
    }

    strong = contains_any(combined, profile.get("strong_skills", []))
    secondary = contains_any(combined, profile.get("secondary_skills", []))
    raw = min(1.0, (len(strong) + len(secondary) * 0.5) / 5.0)
    skill_score = round(WEIGHTS["skills"] * raw)
    total += skill_score
    details["skills"] = {
        "score": skill_score,
        "max": WEIGHTS["skills"],
        "strong_matches": strong,
        "secondary_matches": secondary,
    }

    bad_seniority = contains_any(title, profile.get("deprioritize_seniority", []))
    seniority_preferences = profile.get("seniority_preferences", [])
    if bad_seniority:
        seniority_score = 1
    elif contains_any(title, seniority_preferences):
        seniority_score = WEIGHTS["seniority"]
    elif family_matches:
        seniority_score = 8
    else:
        seniority_score = 6
    total += seniority_score
    details["seniority"] = {
        "score": seniority_score,
        "max": WEIGHTS["seniority"],
        "warnings": bad_seniority,
    }

    focus_terms = profile.get("focus_terms", DEFAULT_FOCUS_TERMS)
    focus_matches = contains_any(combined, focus_terms)
    focus_score = min(WEIGHTS["focus"], len(set(focus_matches)) * 4)
    total += focus_score
    details["process_ops"] = {
        "score": focus_score,
        "max": WEIGHTS["focus"],
        "matches": focus_matches,
    }

    bonus_terms = profile.get("bonus_terms", DEFAULT_BONUS_TERMS)
    bonus_matches = contains_any(combined, bonus_terms)
    bonus_score = min(WEIGHTS["bonus"], len(set(bonus_matches)) * 3)
    total += bonus_score
    details["crm_power_platform"] = {
        "score": bonus_score,
        "max": WEIGHTS["bonus"],
        "matches": bonus_matches,
    }

    preferred_locations = contains_any(location, profile.get("preferred_location_terms", []))
    remote = bool(job.get("remote")) or "remote" in combined
    remote_ok = bool(profile.get("remote_ok", True))
    location_score = WEIGHTS["location"] if (preferred_locations or (remote and remote_ok)) else 3
    total += location_score
    details["location"] = {
        "score": location_score,
        "max": WEIGHTS["location"],
        "matches": preferred_locations,
        "remote": remote,
        "remote_ok": remote_ok,
    }

    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    inferred_salary = False
    if salary_min is None or salary_max is None:
        inferred_min, inferred_max = extract_salary_range(raw_description)
        if salary_min is None and inferred_min is not None:
            salary_min = inferred_min
            inferred_salary = True
        if salary_max is None and inferred_max is not None:
            salary_max = inferred_max
            inferred_salary = True

    salary_floor = int(profile.get("salary_floor", 0) or 0)
    salary_below_floor = bool(
        salary_floor
        and salary_max is not None
        and float(salary_max) < salary_floor
    )

    # Compensation is display/eligibility metadata, not part of Job Fit.
    salary_score = 0
    details["salary"] = {
        "score": 0,
        "max": 0,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_floor": salary_floor,
        "below_floor": salary_below_floor,
        "inferred_from_description": inferred_salary,
        "scored": False,
    }

    avoid = contains_any(combined, profile.get("avoid_terms", []))
    if avoid:
        total -= 20
        details["avoid"] = avoid

    hard_domains = detect_hard_domain_requirements(raw_description, profile)
    domain_penalty = min(30, sum(item["penalty"] for item in hard_domains))
    if domain_penalty:
        total -= domain_penalty

    has_hard_gate = any(item.get("gate") == "hard" for item in hard_domains)
    has_soft_gate = any(item.get("gate") == "soft" for item in hard_domains)
    if has_hard_gate:
        total = min(total, 49)
    elif has_soft_gate:
        total = min(total, 64)

    # Only an explicit posted ceiling below the user's floor affects eligibility.
    # Unknown compensation or a range that reaches the floor does not reduce fit.
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
