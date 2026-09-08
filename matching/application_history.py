from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from auth_user import database_configured, is_logged_in


def _clean(text: str | None) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _company_key(text: str | None) -> str:
    value = _clean(text)
    drop = {"inc", "llc", "corp", "corporation", "company", "co", "group", "holdings"}
    return " ".join(tok for tok in value.split() if tok not in drop)


def _title_key(text: str | None) -> str:
    value = _clean(text)
    replacements = {
        "sr": "senior",
        "jr": "junior",
        "bi": "business intelligence",
        "ops": "operations",
    }
    return " ".join(replacements.get(tok, tok) for tok in value.split())


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _persistent_mode() -> bool:
    return database_configured() and is_logged_in()


def load_history(path: Path) -> list[dict[str, Any]]:
    if _persistent_mode():
        from persistent_store import load_history as load_persistent_history

        return load_persistent_history()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(payload, dict):
        rows = payload.get("applications", [])
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []
    return [row for row in rows if isinstance(row, dict)]


def save_history(path: Path, rows: list[dict[str, Any]]) -> None:
    if _persistent_mode():
        from persistent_store import save_history as save_persistent_history

        save_persistent_history(rows)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"applications": rows}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def match_history(job: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Returns the best prior-application match.

    match_type values:
      - exact: safe to suppress from the new-job queue
      - possible: warn the user, but do not suppress automatically

    Company-only history rows are intentionally never treated as exact. They
    produce a warning only, which protects against LinkedIn confirmations that
    identify the employer but omit the role title.
    """
    job_company = _company_key(job.get("company"))
    job_title = _title_key(job.get("title"))
    job_req = _clean(str(job.get("external_id") or ""))

    best: dict[str, Any] | None = None
    best_score = 0.0

    for prior in history:
        prior_company = _company_key(prior.get("company"))
        prior_title = _title_key(prior.get("title"))
        prior_req = _clean(str(prior.get("requisition_id") or prior.get("external_id") or ""))

        if not job_company or not prior_company:
            continue

        company_score = _similarity(job_company, prior_company)
        if company_score < 0.72:
            continue

        req_exact = bool(job_req and prior_req and job_req == prior_req)
        title_score = _similarity(job_title, prior_title)

        if req_exact:
            match_type = "exact"
            score = 1.0
        elif prior_title and company_score >= 0.88 and title_score >= 0.86:
            match_type = "exact"
            score = (company_score + title_score) / 2
        elif prior_title and company_score >= 0.84 and title_score >= 0.68:
            match_type = "possible"
            score = (company_score + title_score) / 2
        elif not prior_title and company_score >= 0.90:
            match_type = "possible"
            score = company_score * 0.80
        else:
            continue

        if score > best_score:
            best_score = score
            best = {
                "match_type": match_type,
                "confidence": round(score, 3),
                "prior": prior,
            }

    return best
