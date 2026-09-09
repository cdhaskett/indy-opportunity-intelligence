import json
from pathlib import Path

from data.discovery_enrichment import enrich_discovery_jobs


DISCOVERY_PATH = Path(__file__).parents[1] / "data" / "discovered_jobs.json"


def test_stale_discovery_row_uses_company_title_fallback():
    payload = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))
    expected = next(
        job for job in payload["jobs"]
        if job["company"] == "Federal Home Loan Bank of Indianapolis"
        and job["title"] == "CRM and Business Systems Analyst"
    )

    stale = {
        "id": 999,
        "external_id": "old-or-missing-id",
        "source": "discovery",
        "company": "Federal Home Loan Bank of Indianapolis",
        "title": "CRM and Business Systems Analyst",
        "description": "CRM and business systems analyst role supporting business systems and CRM ownership.",
        "salary_min": 74000,
        "salary_max": 87000,
        "status": "interview",
    }

    enriched = enrich_discovery_jobs([stale])[0]

    assert enriched["description"] == expected["description"]
    assert "Microsoft Dynamics 365 CRM" in enriched["description"]
    assert enriched["status"] == "interview"
