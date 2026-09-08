# Opportunity Intelligence — Shareable Build

A no-code, explainable job-search dashboard that turns a person's own skills, target roles, location, salary needs, and application history into a personalized shortlist.

This branch is the **friend-ready / multi-user product build**. Ciara's personal working version remains protected on `main` and `ciara-personal-safe`.

## Intended user experience

The job seeker should not need Python, PowerShell, GitHub Desktop, or JSON editing.

1. Open the hosted web app.
2. Go to **🛠 Control Panel**.
3. Enter city/state, remote preference, target roles, skills, salary range, domain experience, and dealbreakers.
4. Click **Save Profile**.
5. Open **🏠 Job Market** and click **Refresh Market**.
6. Review the personalized shortlist, open postings, and update application status.

## Shareable Streamlit entrypoint

`app/shareable_app.py`

The XP-inspired interface includes a Windows-style desktop, job cards, Market Pulse, application tracking, and a no-code profile form.

## Personalization

The scoring engine uses the current user's profile rather than hardcoded Indianapolis/Power BI assumptions. Profile fields include:

- Home city/state and nearby markets
- U.S. remote preference
- Target job titles
- Preferred seniority
- Strong and secondary skills
- Work themes and bonus keywords
- Domain experience
- Salary floor and target
- Dealbreakers

The collector also uses the active profile's market terms when deciding which jobs are locally relevant.

## Privacy during local testing

Private files are Git-ignored:

- `data/user_profile.json`
- `data/application_history.json`
- `data/jobs.db`

For a real hosted multi-user deployment, local files are only a prototype. The next production step is authenticated users plus persistent per-user profile/application storage in a hosted database.

## Current job-source support

The engine currently supports employer feeds from Greenhouse, Lever, Ashby, Workday, and SmartRecruiters, plus a verified discovery layer.

## Product principle

> Find fewer jobs. Find better jobs. Learn from the outcomes.
