from __future__ import annotations

import html
import re
import time
from typing import Dict, Iterable
from urllib.parse import urljoin

import requests

from .base import normalized_job

DEFAULT_SEARCH_TERMS = [
    "analyst",
    "business systems",
    "business intelligence",
    "operations",
    "crm",
    "power bi",
    "data",
]


def _plain_text(value: str | None) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _salary_min(text: str) -> int | None:
    """Best-effort annual salary floor extraction from public job text."""
    patterns = [
        r"\$\s*([0-9]{2,3}(?:,[0-9]{3})+)\s*(?:-|to|–)",
        r"pay range[^$]{0,80}\$\s*([0-9]{2,3}(?:,[0-9]{3})+)",
    ]
    lowered = text.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                pass
    return None


def fetch_workday_jobs(config: Dict) -> list[Dict]:
    """Fetch public postings from a configured Workday career site.

    Required config keys:
      host   e.g. https://rollsroyce.wd3.myworkdayjobs.com
      tenant e.g. rollsroyce
      site   e.g. professional

    Optional:
      locale e.g. en-US
      search_terms list[str]
    """
    host = config["host"].rstrip("/")
    tenant = config["tenant"]
    site = config["site"]
    locale = config.get("locale", "en-US")
    search_terms: Iterable[str] = config.get("search_terms") or DEFAULT_SEARCH_TERMS

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 IndyOpportunityIntelligence/0.2",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    })

    search_url = f"{host}/wday/cxs/{tenant}/{site}/jobs"
    postings: dict[str, dict] = {}

    for term in search_terms:
        offset = 0
        while True:
            payload = {
                "appliedFacets": {},
                "limit": 20,
                "offset": offset,
                "searchText": term,
            }
            response = session.post(search_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            rows = data.get("jobPostings") or []
            total = int(data.get("total") or 0)

            for row in rows:
                path = row.get("externalPath") or ""
                if path:
                    postings[path] = row

            offset += len(rows)
            if not rows or offset >= total:
                break
            time.sleep(0.05)

    jobs = []
    for path, row in postings.items():
        detail_url = f"{host}/wday/cxs/{tenant}/{site}{path}"
        description = ""
        location = row.get("locationsText") or ""
        salary_min = None
        external_id = path.rstrip("/").split("_")[-1] or path

        try:
            detail_response = session.get(detail_url, timeout=30)
            detail_response.raise_for_status()
            info = (detail_response.json().get("jobPostingInfo") or {})
            description = _plain_text(info.get("jobDescription"))
            location = info.get("location") or location
            external_id = str(info.get("jobReqId") or external_id)
            salary_min = _salary_min(description)
        except Exception:
            # Search results still provide enough information to keep the role.
            pass

        public_url = urljoin(f"{host}/{locale}/{site}/", path.lstrip("/"))
        remote = "remote" in (location or "").lower() or "working from home" in (location or "").lower()

        jobs.append(normalized_job(
            external_id=external_id,
            source="workday",
            company=config.get("company", tenant),
            title=row.get("title") or "",
            location=location,
            remote=remote,
            salary_min=salary_min,
            url=public_url,
            posted_at=row.get("postedOn") or "",
            description=description,
        ))

    return jobs
