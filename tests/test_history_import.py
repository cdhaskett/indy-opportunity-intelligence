from __future__ import annotations

from io import BytesIO

import pandas as pd

from matching.history_import import merge_application_history, read_application_file


def test_csv_alias_columns_are_normalized():
    data = (
        "Employer,Role,Applied Date,Application Status,Req ID\n"
        "Acme Corp,Operations Analyst,2026-09-01,Applied,REQ-123\n"
    ).encode("utf-8")

    rows, mapping, skipped = read_application_file(data, "applications.csv")

    assert skipped == []
    assert mapping["company"] == "Employer"
    assert mapping["title"] == "Role"
    assert rows == [
        {
            "company": "Acme Corp",
            "title": "Operations Analyst",
            "status": "Applied",
            "requisition_id": "REQ-123",
            "date_applied": "2026-09-01",
        }
    ]


def test_xlsx_import_works():
    frame = pd.DataFrame(
        [{"Company": "Example Co", "Job Title": "Project Manager", "Status": "Interview"}]
    )
    buffer = BytesIO()
    frame.to_excel(buffer, index=False, engine="openpyxl")

    rows, mapping, skipped = read_application_file(buffer.getvalue(), "tracker.xlsx")

    assert skipped == []
    assert mapping["company"] == "Company"
    assert rows[0]["company"] == "Example Co"
    assert rows[0]["title"] == "Project Manager"


def test_merge_deduplicates_same_company_title_and_req():
    existing = [
        {"company": "Acme, Inc.", "title": "Data Analyst", "requisition_id": "123"}
    ]
    incoming = [
        {"company": "Acme Inc", "title": "Data Analyst", "requisition_id": "123"},
        {"company": "Acme Inc", "title": "Business Analyst", "requisition_id": "456"},
    ]

    merged, added = merge_application_history(existing, incoming)

    assert added == 1
    assert len(merged) == 2
