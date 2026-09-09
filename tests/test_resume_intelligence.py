from matching.resume_intelligence import infer_profile_from_resume, resume_health, resume_match_score


def test_resume_health_flags_sparse_resume():
    text = "Business Analyst\nWorked with reports and customers."
    result = resume_health(text)
    assert result["score"] < 70
    assert result["notes"]


def test_infer_profile_uses_resume_evidence_not_template_skills():
    template = {
        "name": "Job Seeker",
        "target_titles": ["operations analyst"],
        "title_family_terms": ["analyst"],
        "strong_skills": ["excel", "sql", "power bi"],
        "secondary_skills": [],
        "focus_terms": ["process improvement"],
    }
    text = "Senior Business Analyst\nPower BI dashboards and SQL reporting"
    profile = infer_profile_from_resume(text, template)
    assert "power bi" in profile["strong_skills"]
    assert "sql" in profile["strong_skills"]
    assert "excel" not in profile["strong_skills"]


def test_resume_match_exposes_hidden_skill_gap():
    profile = {
        "target_titles": ["business analyst"],
        "strong_skills": ["power bi", "sql", "salesforce"],
        "secondary_skills": [],
        "focus_terms": ["process improvement"],
    }
    job = {
        "title": "Business Analyst",
        "description": "Power BI SQL Salesforce process improvement",
    }
    resume_text = "Business Analyst with SQL reporting experience"
    result = resume_match_score(job, resume_text, profile)
    assert result["score"] < 100
    assert "power bi" in result["missing_skills"]
    assert "salesforce" in result["missing_skills"]
