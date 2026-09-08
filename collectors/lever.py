from __future__ import annotations
import requests
from .base import normalized_job

def fetch_lever_jobs(site_name: str):
    url = f"https://api.lever.co/v0/postings/{site_name}?mode=json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()

    jobs = []
    for item in payload:
        categories = item.get("categories") or {}
        location = categories.get("location") or ""
        jobs.append(normalized_job(
            external_id=str(item.get("id")),
            source="lever",
            company=site_name,
            title=item.get("text") or "",
            location=location,
            remote="remote" in location.lower(),
            url=item.get("hostedUrl") or item.get("applyUrl") or "",
            description="\n".join([
                item.get("descriptionPlain") or "",
                item.get("additionalPlain") or "",
            ]),
        ))
    return jobs
