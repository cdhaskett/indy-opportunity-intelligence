from __future__ import annotations

import html
import re

import requests

BASE = "https://api.smartrecruiters.com/v1/companies/{company}/postings"


def _plain(value: str | None) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_smartrecruiters_jobs(company_identifier: str) -> list[dict]:
    """Fetch public postings from a SmartRecruiters company career site."""
    jobs: list[dict] = []
    offset = 0
    limit = 100
    url = BASE.format(company=company_identifier)

    while True:
        response = requests.get(
            url,
            params={"limit": limit, "offset": offset, "destination": "PUBLIC"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("content", [])

        for row in rows:
            posting_id = row.get("id") or row.get("uuid")
            if not posting_id:
                continue

            detail_response = requests.get(f"{url}/{posting_id}", timeout=30)
            detail_response.raise_for_status()
            detail = detail_response.json()

            location_obj = detail.get("location") or row.get("location") or {}
            location_parts = [
                location_obj.get("city"),
                location_obj.get("region"),
                location_obj.get("country"),
            ]
            location = ", ".join(str(x) for x in location_parts if x)
            remote = bool(location_obj.get("remote")) or "remote" in location.lower()

            sections = detail.get("jobAd", {}).get("sections", {})
            description_parts = []
            for key in ["companyDescription", "jobDescription", "qualifications", "additionalInformation"]:
                section = sections.get(key) or {}
                if isinstance(section, dict):
                    description_parts.append(_plain(section.get("text")))
            description = " ".join(x for x in description_parts if x)

            jobs.append({
                "external_id": str(detail.get("id") or posting_id),
                "title": detail.get("name") or row.get("name") or "Untitled role",
                "location": location,
                "remote": remote,
                "description": description,
                "url": detail.get("applyUrl") or detail.get("jobAd", {}).get("jobAdUrl") or row.get("ref"),
                "source": "smartrecruiters",
                "salary_min": None,
                "salary_max": None,
            })

        offset += len(rows)
        total = int(payload.get("totalFound") or 0)
        if not rows or offset >= total:
            break

    return jobs
