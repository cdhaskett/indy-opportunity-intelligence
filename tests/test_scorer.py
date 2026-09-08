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
    }
    bad = {
        "title": "Principal Machine Learning Engineer",
        "description": "distributed ML kubernetes model serving",
        "location": "San Francisco, CA",
        "remote": False,
        "salary_min": 200000,
    }

    good_score, _ = score_job(good, PROFILE)
    bad_score, _ = score_job(bad, PROFILE)

    assert good_score > bad_score
    assert good_score >= 70
