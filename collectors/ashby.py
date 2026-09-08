from __future__ import annotations
import requests
from .base import normalized_job

def fetch_ashby_jobs(board_name: str):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board_name}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()

    jobs = []
    for item in payload.get("jobs", []):
        location = item.get("location") or ""
        jobs.append(normalized_job(
            external_id=str(item.get("id") or item.get("jobUrl")),
            source="ashby",
            company=board_name,
            title=item.get("title") or "",
            location=location,
            remote=bool(item.get("isRemote")),
            url=item.get("jobUrl") or item.get("applyUrl") or "",
            posted_at=item.get("publishedAt") or "",
            description=item.get("descriptionPlain") or item.get("descriptionHtml") or "",
        ))
    return jobs
