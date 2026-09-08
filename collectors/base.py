from __future__ import annotations
from typing import Dict

def normalized_job(
    *,
    external_id: str,
    source: str,
    company: str,
    title: str,
    location: str = "",
    remote: bool = False,
    salary_min: int | None = None,
    salary_max: int | None = None,
    url: str = "",
    posted_at: str = "",
    description: str = "",
) -> Dict:
    return {
        "external_id": external_id,
        "source": source,
        "company": company,
        "title": title,
        "location": location,
        "remote": remote,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "url": url,
        "posted_at": posted_at,
        "description": description,
    }
