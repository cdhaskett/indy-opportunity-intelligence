from matching.resume_parser import parse_resume_text


def test_resume_parser_extracts_profile_signals():
    text = """
    Jordan Rivera
    Louisville, KY
    Operations Manager
    Acme Distribution | 2021 - Present
    Led warehouse operations, logistics, scheduling, team leadership, process improvement and SAP reporting.
    Senior Logistics Analyst
    Previous Company | 2018 - 2021
    Built Excel reporting and Power BI dashboards for supply chain and procurement teams.
    University of Louisville - Bachelor of Science
    """

    result = parse_resume_text(text)
    profile = result["profile"]

    assert profile["name"] == "Jordan Rivera"
    assert profile["home_city"] == "Louisville"
    assert profile["home_state"] == "KY"
    assert any("Operations Manager" == title for title in profile["target_titles"])
    assert "excel" in [skill.lower() for skill in profile["strong_skills"]]
    assert "Supply Chain / Procurement" in profile["domain_strengths"]


def test_resume_parser_does_not_infer_salary_or_remote_preferences():
    text = """
    Taylor Morgan
    Columbus, OH
    Project Manager
    Managed Jira projects, stakeholder management, Agile delivery and reporting.
    """

    profile = parse_resume_text(text)["profile"]

    assert "salary_floor" not in profile
    assert "salary_target" not in profile
    assert "remote_ok" not in profile
    assert "avoid_terms" not in profile
