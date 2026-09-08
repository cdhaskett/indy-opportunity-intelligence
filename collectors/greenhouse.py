from __future__ import annotations
import requests
from .base import normalized_job

def fetch_greenhouse_jobs(board_token: str):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()

    jobs = []
    for item in payload.get("jobs", []):
        location = ((item.get("location") or {}).get("name") or "")
        jobs.append(normalized_job(
            external_id=str(item.get("id")),
            source="greenhouse",
            company=board_token,
            title=item.get("title") or "",
            location=location,
            remote="remote" in location.lower(),
            url=item.get("absolute_url") or "",
            posted_at=item.get("updated_at") or "",
            description=item.get("content") or "",
        ))
    return jobs
