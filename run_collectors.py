from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from collectors.ashby import fetch_ashby_jobs
from collectors.greenhouse import fetch_greenhouse_jobs
from collectors.lever import fetch_lever_jobs
from data.db import upsert_jobs
from matching.scorer import score_job

ROOT = Path(__file__).resolve().parent
PROFILE = json.loads((ROOT / "data" / "candidate_profile.json").read_text())
REGISTRY = json.loads((ROOT / "data" / "employers.json").read_text())

LOCAL_MARKERS = [
    "indianapolis", "carmel", "fishers", "noblesville", "westfield",
    "greenwood", "plainfield", "avon", "anderson", "indiana",
]
US_REMOTE_MARKERS = [
    "united states", "usa", "u.s.", "us remote", "remote - us",
    "remote, us", "remote usa", "remote united states"
]
NON_US_MARKERS = [
    "india", "canada", "united kingdom", "uk", "australia", "singapore",
    "malaysia", "mexico", "brazil", "argentina", "china", "taiwan",
    "south korea"
]

COLLECTORS = {
    "greenhouse": fetch_greenhouse_jobs,
    "lever": fetch_lever_jobs,
    "ashby": fetch_ashby_jobs,
}

def is_indiana_location(location: str) -> bool:
    if any(x in location for x in LOCAL_MARKERS):
        return True
    return bool(re.search(r",\s*in(?:\s+\d{5})?(?:$|;)", location))

def market_eligible(job: dict) -> bool:
    location = (job.get("location") or "").lower().strip()
    if is_indiana_location(location):
        return True

    remote = bool(job.get("remote")) or "remote" in location
    if remote:
        if any(x in location for x in NON_US_MARKERS):
            return False
        if any(x in location for x in US_REMOTE_MARKERS):
            return True
        return location in {"remote", "remote - usa", "remote, usa"}

    return False

def run(priority: str | None = None):
    collected = []
    failures = []

    for employer in REGISTRY["employers"]:
        if priority and employer.get("priority") != priority:
            continue

        ats = employer["ats"]
        board = employer["board"]
        collector = COLLECTORS[ats]

        try:
            jobs = collector(board)
        except Exception as exc:
            failures.append((employer["name"], str(exc)))
            continue

        eligible = 0
        for job in jobs:
            if not market_eligible(job):
                continue
            eligible += 1
            job["company"] = employer["name"]
            score, detail = score_job(job, PROFILE)
            job["score"] = score
            job["verdict"] = detail["verdict"]
            collected.append(job)

        print(f"{employer['name']}: {len(jobs)} fetched / {eligible} in market")

    upsert_jobs(collected)
    print(f"\nSaved/updated {len(collected)} market-eligible jobs.")

    if failures:
        print("\nCollector failures:")
        for company, error in failures:
            print(f"- {company}: {error}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        help="Only run employers at one priority tier.",
    )
    args = parser.parse_args()
    run(args.priority)
