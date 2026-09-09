import json
from pathlib import Path
from matching.scorer import score_job

PROFILE = json.loads(
    (Path(__file__).parents[1] / "data" / "candidate_profile.json").read_text()
)


def test_good_business_systems_role_scores_above_bad_engineering_role():
    good = {"title":"Business Systems Analyst","description":"Dynamics 365 CRM Power BI process improvement stakeholders SQL","location":"Indianapolis, IN","remote":False,"salary_min":90000,"salary_max":105000}
    bad = {"title":"Principal Machine Learning Engineer","description":"distributed ML kubernetes model serving","location":"San Francisco, CA","remote":False,"salary_min":200000,"salary_max":240000}
    good_score, _ = score_job(good, PROFILE)
    bad_score, _ = score_job(bad, PROFILE)
    assert good_score > bad_score
    assert good_score >= 70


def test_strong_fit_below_salary_floor_is_skip():
    job = {"title":"Business Analyst","description":"Power BI DAX Power Query Salesforce CRM process improvement business requirements stakeholder management SQL data visualization","location":"Carmel, IN / Remote","remote":True,"salary_min":55000,"salary_max":65000}
    score, details = score_job(job, PROFILE)
    assert details["salary"]["below_floor"] is True
    assert details["hard_requirements"]["salary_gate"] is True
    assert details["verdict"] == "SKIP"
    assert score <= 49


def test_description_salary_range_below_floor_is_skip():
    job = {"title":"Business Analyst","description":"Power BI Power Query Salesforce CRM analytics process improvement stakeholder work. The anticipated salary range for this position is $55,000 - $65,000 annually.","location":"Remote, US","remote":True,"salary_min":None,"salary_max":None}
    score, details = score_job(job, PROFILE)
    assert details["salary"]["salary_min"] == 55000
    assert details["salary"]["salary_max"] == 65000
    assert details["salary"]["inferred_from_description"] is True
    assert details["salary"]["below_floor"] is True
    assert details["verdict"] == "SKIP"
    assert score <= 49


def test_salary_range_that_reaches_floor_is_not_hard_gated():
    job = {"title":"Business Systems Analyst","description":"Power BI Dynamics 365 CRM process improvement stakeholders SQL","location":"Indianapolis, IN","remote":False,"salary_min":70000,"salary_max":85000}
    _, details = score_job(job, PROFILE)
    assert details["salary"]["below_floor"] is False
    assert details["hard_requirements"]["salary_gate"] is False


def test_acceptable_compensation_does_not_change_fit_score():
    base = {"title":"Revenue Enablement Specialist","description":"Own Salesforce reporting, pipeline data, workflow improvement, stakeholder requirements, Power BI dashboards, SQL analysis, process improvement and user adoption.","location":"Indianapolis, IN","remote":False}
    lower_range = {**base, "salary_min":75000, "salary_max":90000}
    higher_range = {**base, "salary_min":105000, "salary_max":125000}
    unknown_range = {**base, "salary_min":None, "salary_max":None}
    lower_score, lower_details = score_job(lower_range, PROFILE)
    higher_score, higher_details = score_job(higher_range, PROFILE)
    unknown_score, unknown_details = score_job(unknown_range, PROFILE)
    assert lower_score == higher_score == unknown_score
    assert lower_details["salary"]["scored"] is False
    assert higher_details["salary"]["scored"] is False
    assert unknown_details["salary"]["scored"] is False


def test_explicit_pharma_media_experience_is_hard_gate():
    job = {"title":"Senior Analyst, Beyond Insights","description":"<ul><li>5+ years of experience in business intelligence/advanced analytics/data analytics working closely with data</li><li>Pharmaceutical media and marketing experience, with hands-on exposure to HCP and/or consumer omnichannel campaigns</li><li>Experience with SQL, Python, Snowflake, Databricks, Tableau and Power BI</li></ul><p>Pay Range: $70,000-$85,000</p>","location":"Remote - USA","remote":True,"salary_min":None,"salary_max":None}
    score, details = score_job(job, PROFILE)
    findings = details["hard_requirements"]["findings"]
    assert any(f["domain"] == "Healthcare / Clinical" and f["gate"] == "hard" for f in findings)
    assert details["hard_requirements"]["hard_gate"] is True
    assert details["verdict"] == "SKIP"
    assert score <= 49
