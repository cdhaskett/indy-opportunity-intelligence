# Indy Opportunity Intelligence

An explainable job-discovery and application-outcome analytics project focused on finding high-value opportunities instead of maximizing job-board scrolling.

## Alpha goals

1. Collect jobs from employer ATS/job-board sources.
2. Normalize them into one schema.
3. Score each opening against a candidate profile.
4. Explain why a role is a fit or mismatch.
5. Track application outcomes.
6. Later add a Central Indiana company map and market analytics.

## Current alpha

This starter version includes:

- Candidate profile and job-search preferences
- Explainable 0–100 scoring engine
- SQLite job + outcome tracker
- Minimal Ashby, Greenhouse, and Lever collectors
- Streamlit "Today's Market" dashboard
- Demo data
- Starter unit test

## Quick start

```bash
python -m venv .venv
```

Activate the environment.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Load the demo jobs:

```bash
python seed_demo.py
```

Run the app:

```bash
streamlit run app/streamlit_app.py
```

Run tests:

```bash
pytest
```

## Scoring philosophy

The score is deliberately explainable. It rewards:

- Target job-family/title fit
- Relevant skills
- Appropriate seniority
- Process/operations work
- CRM/Power Platform relevance
- Preferred geography or remote work
- Compensation alignment

AI can later help summarize or classify postings, but the core score remains inspectable.

## Planned roadmap

### v0.2 — Real employer feeds
Maintain a curated employer registry with ATS provider + board identifier. Pull jobs on demand and score them.

### v0.3 — Application intelligence
Track application, screen, interview, final-round, offer, rejection, and withdrawal outcomes. Calculate interview rates by role family, source, score band, and employer type.

### v0.4 — Central Indiana map
Join employers to coordinates and display matching roles geographically with filters for radius, score, role family, remote/hybrid/on-site, and application status.

### v0.5 — Automation
Run collectors on a schedule, deduplicate postings, score new roles, and surface only high-value changes.

## Project principle

> Find fewer jobs. Find better jobs. Learn from the outcomes.
