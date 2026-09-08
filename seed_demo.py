import json
from pathlib import Path
from matching.scorer import score_job
from data.db import upsert_jobs

PROFILE = json.loads(
    (Path(__file__).parent / "data" / "candidate_profile.json").read_text()
)

DEMO_JOBS = [
    {
        "external_id": "demo-1",
        "source": "demo",
        "company": "Example Manufacturing",
        "title": "CRM & Business Systems Analyst",
        "location": "Indianapolis, IN",
        "remote": False,
        "salary_min": 88000,
        "salary_max": 105000,
        "url": "https://example.com/job/1",
        "description": "Own Dynamics 365 CRM improvements, gather requirements from business stakeholders, improve workflows, support Power Platform solutions, build Power BI reporting, and partner with operations on process improvement. SQL experience preferred."
    },
    {
        "external_id": "demo-2",
        "source": "demo",
        "company": "Example Health",
        "title": "Business Intelligence Analyst",
        "location": "Remote - United States",
        "remote": True,
        "salary_min": 82000,
        "salary_max": 98000,
        "url": "https://example.com/job/2",
        "description": "Build Power BI dashboards, write SQL, partner with stakeholders, document requirements, and improve analytics processes. Experience with Snowflake and data governance is helpful."
    },
    {
        "external_id": "demo-3",
        "source": "demo",
        "company": "Example AI",
        "title": "Principal Machine Learning Engineer",
        "location": "San Francisco, CA",
        "remote": False,
        "salary_min": 190000,
        "salary_max": 240000,
        "url": "https://example.com/job/3",
        "description": "Lead production ML architecture, distributed training, Kubernetes, model serving, and a team of senior engineers. 10+ years required."
    },
]

for job in DEMO_JOBS:
    score, detail = score_job(job, PROFILE)
    job["score"] = score
    job["verdict"] = detail["verdict"]

upsert_jobs(DEMO_JOBS)
print("Seeded demo jobs.")
