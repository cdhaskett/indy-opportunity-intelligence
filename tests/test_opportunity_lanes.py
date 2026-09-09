from matching.opportunity_lanes import classify_opportunity


def test_unfamiliar_title_can_be_hidden_fit_from_actual_work():
    profile = {
        "target_titles": ["business analyst", "data analyst"],
        "title_family_terms": ["business analyst", "data analyst", "analyst"],
    }
    job = {
        "title": "Revenue Enablement Specialist",
        "description": (
            "Own Salesforce pipeline data, sales process reporting, workflow improvement, "
            "go-to-market analytics, stakeholder requirements and user adoption."
        ),
    }
    result = classify_opportunity(
        job,
        profile,
        fit_score=86,
        fit_details={"verdict": "APPLY", "title": {"score": 4}},
    )

    assert result["lane"] == "Revenue Ops & Enablement"
    assert result["hidden_fit"] is True


def test_lane_is_driven_by_description_more_than_generic_title():
    profile = {"target_titles": ["analyst"], "title_family_terms": ["analyst"]}
    job = {
        "title": "Strategic Analyst",
        "description": (
            "Lead process improvement, process mapping, root cause analysis, standard work, "
            "workflow improvement and continuous improvement initiatives."
        ),
    }
    result = classify_opportunity(job, profile, fit_score=82, fit_details={"verdict": "APPLY"})

    assert result["lane"] == "Process & Continuous Improvement"
