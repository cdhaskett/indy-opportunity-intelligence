import json
from pathlib import Path

from matching.resume_helper import analyze_resume_for_job
from matching.scorer import score_job

PROFILE = json.loads(
    (Path(__file__).parents[1] / "data" / "candidate_profile.json").read_text()
)


def test_strong_candidate_can_have_weaker_resume_match():
    job = {
        "title": "CRM and Business Systems Analyst",
        "description": (
            "Administer Microsoft Dynamics 365 CRM, configure workflows and automation, "
            "manage security roles and Dataverse data, translate business requirements, "
            "partner with stakeholders, build Power BI reporting, support data governance, "
            "and identify continuous improvement opportunities."
        ),
        "location": "Indianapolis, IN",
        "remote": False,
        "salary_min": 74000,
        "salary_max": 87000,
    }
    fit_score, fit_details = score_job(job, PROFILE)

    weak_resume = """
    Ciara Haskett
    Business Development Analyst
    Created reports and helped teams with data.
    Worked with CRM systems and Excel.
    Helped improve processes.
    """

    analysis = analyze_resume_for_job(weak_resume, job, PROFILE, fit_score, fit_details)

    assert analysis["job_fit_score"] == fit_score
    assert fit_score > analysis["resume_match_score"]
    assert analysis["resume_health"]["issues"]
    assert analysis["missing_signals"]


def test_resume_helper_never_turns_hard_domain_gap_into_keyword_advice():
    job = {
        "title": "Senior Analyst, Pharma Insights",
        "description": (
            "Pharmaceutical media and marketing experience required. "
            "Hands-on HCP omnichannel campaign experience. Power BI and SQL."
        ),
        "location": "Remote - USA",
        "remote": True,
        "salary_min": 90000,
        "salary_max": 110000,
    }
    fit_score, fit_details = score_job(job, PROFILE)
    resume = "Power BI analyst with SQL, reporting, stakeholder management, and process improvement experience."

    analysis = analyze_resume_for_job(resume, job, PROFILE, fit_score, fit_details)

    assert fit_score <= 49
    assert analysis["dont_claim"]
    assert any(item["domain"] == "Healthcare / Clinical" for item in analysis["dont_claim"])
