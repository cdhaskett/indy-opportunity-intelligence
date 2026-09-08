from __future__ import annotations
import requests
from .base import normalized_job


def _salary_range(item: dict):
    compensation = item.get("compensation") or {}
    components = compensation.get("summaryComponents") or []
    annual_salary = [
        c for c in components
        if c.get("compensationType") == "Salary"
        and c.get("currencyCode") == "USD"
        and c.get("interval") == "1 YEAR"
    ]
    if not annual_salary:
        return None, None

    lows = [c.get("minValue") for c in annual_salary if c.get("minValue") is not None]
    highs = [c.get("maxValue") for c in annual_salary if c.get("maxValue") is not None]
    salary_min = int(min(lows)) if lows else None
    salary_max = int(max(highs)) if highs else None
    return salary_min, salary_max


def fetch_ashby_jobs(board_name: str):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board_name}?includeCompensation=true"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()

    jobs = []
    for item in payload.get("jobs", []):
        if item.get("isListed") is False:
            continue
        location = item.get("location") or ""
        salary_min, salary_max = _salary_range(item)
        jobs.append(normalized_job(
            external_id=str(item.get("id") or item.get("jobUrl")),
            source="ashby",
            company=board_name,
            title=item.get("title") or "",
            location=location,
            remote=bool(item.get("isRemote")) or item.get("workplaceType") == "Remote",
            salary_min=salary_min,
            salary_max=salary_max,
            url=item.get("jobUrl") or item.get("applyUrl") or "",
            posted_at=item.get("publishedAt") or "",
            description=item.get("descriptionPlain") or item.get("descriptionHtml") or "",
        ))
    return jobs
