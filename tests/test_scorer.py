import json
from pathlib import Path
from matching.scorer import score_job

PROFILE = json.loads(
    (Path(__file__).parents[1] / "data" / "candidate_profile.json").read_text()
)


def test_good_business_systems_role_scores_above_bad_engineering_role():
    good = {
        "title": "Business Systems Analyst",
        "description": "Dynamics 365 CRM Power BI process improvement stakeholders SQL",
        "location": "Indianapolis, IN",
        "remote": False,
        "salary_min": 90000,
        "salary_max": 105000,
    }
    bad = {
        "title": "Principal Machine Learning Engineer",
        "description": "distributed ML kubernetes model serving",
        "location": "San Francisco, CA",
        "remote": False,
        "salary_min": 200000,
        "salary_max": 240000,
    }

    good_score, _ = score_job(good, PROFILE)
    bad_score, _ = score_job(bad, PROFILE)

    assert good_score > bad_score
    assert good_score >= 70


def test_strong_fit_below_salary_floor_is_skip():
    job = {
        "title": "Business Analyst",
        "description": (
            "Power BI DAX Power Query Salesforce CRM process improvement "
            "business requirements stakeholder management SQL data visualization"
        ),
        "location": "Carmel, IN / Remote",
        "remote": True,
        "salary_min": 55000,
        "salary_max": 65000,
    }

    score, details = score_job(job, PROFILE)

    assert details["salary"]["below_floor"] is True
    assert details["hard_requirements"]["salary_gate"] is True
    assert details["verdict"] == "SKIP"
    assert score <= 49


def test_salary_range_that_reaches_floor_is_not_hard_gated():
    job = {
        "title": "Business Systems Analyst",
        "description": "Power BI Dynamics 365 CRM process improvement stakeholders SQL",
        "location": "Indianapolis, IN",
        "remote": False,
        "salary_min": 70000,
        "salary_max": 85000,
    }

    _, details = score_job(job, PROFILE)

    assert details["salary"]["below_floor"] is False
    assert details["hard_requirements"]["salary_gate"] is False
