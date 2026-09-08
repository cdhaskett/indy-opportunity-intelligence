from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from data.db import count_today_status, list_jobs, update_status
from matching.application_history import load_history, match_history, save_history
from matching.scorer import score_job
from market_state import load_market_state, save_refresh_result
from profile_config import (
    has_user_profile,
    load_profile,
    load_profile_template,
    profile_source,
    reset_user_profile,
    save_user_profile,
)
from run_collectors import run as run_collectors

HISTORY_PATH = ROOT / "data" / "application_history.json"

st.set_page_config(
    page_title="Opportunity Intelligence",
    page_icon="🪟",
    layout="wide",
)

st.markdown(
    """
<style>
:root {
  --blue:#0a5bd8; --blue-dark:#0753c7; --ivory:#ece9d8; --card:#fffef5;
  --border:#7f9db9; --text:#111; --link:#10479d;
  --window:min(1500px, calc(100vw - 36px));
}
html,body,[class*="css"]{font-family:Tahoma,Arial,sans-serif}
html,body,.stApp{overflow-x:hidden!important}
.stApp{color:var(--text);background:linear-gradient(#4b9df4 0 42%,#bfe4ff 59%,#79cf5c 60%,#3d9d34 100%)}
.stApp:before{content:"";position:fixed;inset:0;pointer-events:none;background:
 radial-gradient(ellipse at 12% 18%,rgba(255,255,255,.9) 0 2.5%,transparent 2.9%),
 radial-gradient(ellipse at 18% 17%,rgba(255,255,255,.74) 0 3.2%,transparent 3.6%),
 radial-gradient(ellipse at 76% 19%,rgba(255,255,255,.86) 0 2.4%,transparent 2.8%),
 radial-gradient(ellipse at 82% 19%,rgba(255,255,255,.70) 0 3.2%,transparent 3.6%),
 radial-gradient(ellipse at 20% 105%,#318c2c 0 34%,transparent 34.4%),
 radial-gradient(ellipse at 55% 110%,#68c94e 0 44%,transparent 44.4%),
 radial-gradient(ellipse at 92% 108%,#45a83b 0 38%,transparent 38.4%)}
.stApp:after{content:"";position:fixed;inset-block:0;left:50%;transform:translateX(-50%);width:var(--window);background:var(--ivory);border-inline:1px solid #7697bd;box-shadow:0 0 25px #285b8a88;pointer-events:none}
.block-container,[data-testid="stMainBlockContainer"]{position:relative;z-index:1;width:var(--window)!important;max-width:var(--window)!important;margin:auto!important;padding:.65rem 1.1rem 4rem!important;background:transparent!important;box-sizing:border-box;overflow-x:hidden!important}
.menu{background:#f5f3eb;border:1px solid #aca899;box-shadow:inset 1px 1px #fff;padding:.32rem .55rem;margin-bottom:.35rem;font-size:.78rem;color:#111}
.section{background:linear-gradient(#3f93ff,var(--blue-dark));color:#fff;border:1px solid #06459e;border-radius:5px 5px 0 0;padding:.38rem .58rem;font-weight:700;text-shadow:1px 1px #16448a;margin-top:.45rem}
.help{background:#fff7a8;border:1px solid #d0bd3e;color:#4c4314;padding:.55rem .65rem;margin:.35rem 0 .6rem;font-size:.82rem}
.welcome{background:#fffef5;border:1px solid #7f9db9;box-shadow:inset 1px 1px #fff;padding:1rem 1.15rem;margin:.4rem 0 .7rem}
.welcome h2{color:#10479d;margin:.05rem 0 .35rem;font-size:1.35rem}.welcome p{color:#333;margin:.2rem 0}
.steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.35rem;margin:.55rem 0 .8rem}
.step{background:#dbe8f7;border:1px solid #7f9db9;color:#284b77;padding:.45rem .5rem;font-size:.78rem;font-weight:700;text-align:center}
.summary{background:#fffef5;border:1px solid #aca899;padding:.55rem .7rem;margin:.35rem 0;color:#222;font-size:.82rem}
div[role="radiogroup"]{background:#ece9d8;border:1px solid #aca899;padding:.22rem;width:fit-content;max-width:100%;margin:.25rem 0 .55rem;box-shadow:inset 1px 1px #fff;flex-wrap:wrap!important}
div[role="radiogroup"] p{color:#111!important;font-weight:700}
div[data-testid="stMetric"]{background:var(--card)!important;border:1px solid #888;border-top-color:#fff;border-left-color:#fff;padding:.52rem .68rem;min-height:78px;box-shadow:1px 1px #777}
[data-testid="stMetricLabel"] *,[data-testid="stMetricLabel"]{color:#0b3d91!important;opacity:1!important;font-weight:700!important}
[data-testid="stMetricValue"] *{color:#111!important}
div[data-testid="stVerticalBlockBorderWrapper"]{background:var(--card)!important;border:1px solid var(--border)!important;border-radius:4px!important;overflow:hidden!important;margin-bottom:.45rem}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"],div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stColumn"]{background:var(--card)!important}
.titlebar{display:flex;align-items:center;gap:.45rem;background:linear-gradient(#3f93ff,#0753c7);border:1px solid #06459e;color:#fff;padding:.34rem .48rem;margin:0 0 .34rem;box-sizing:border-box;width:100%}
.titletext{font-weight:700;flex:1;min-width:0;overflow-wrap:anywhere}.score{background:linear-gradient(#72d377,#33a542);border:1px solid #176f27;border-radius:3px;color:#fff;padding:.13rem .33rem;font-weight:700}.salary{background:#ffdf57;border:1px solid #a47b00;color:#493900;padding:.13rem .34rem;border-radius:3px;font-weight:700;font-size:.75rem}.meta{color:#333;font-size:.82rem}.badge{display:inline-block;background:#dbe8f7;border:1px solid var(--border);color:#284b77;padding:.13rem .34rem;margin:.18rem .2rem .18rem 0;font-size:.67rem;font-weight:700;text-transform:uppercase}.apply{background:#39b54a;color:#fff;border-color:#1c7d2b}.strong{background:#ffd65a;color:#4e3900;border-color:#a87800}.stretch{background:#e2eaf3;color:#274a75}.skip{background:#efc2bd;color:#721b14}.dupe{background:#fff7a8;border:1px solid #d0bd3e;color:#4c4314;padding:.38rem .48rem;margin:.25rem 0;font-size:.78rem}
.stButton>button,.stLinkButton>a{background:linear-gradient(#fff,#e5e5df)!important;border:1px solid #003c74!important;color:#111!important;border-radius:3px!important;font-weight:700!important;box-shadow:inset 1px 1px #fff!important}
input,textarea,[role="combobox"],div[data-baseweb="select"]>div{background:#fff!important;color:#111!important;border-color:var(--border)!important}
[data-baseweb="tag"]{background:#dbe8f7!important;border:1px solid var(--border)!important}[data-baseweb="tag"] *{color:var(--link)!important;background:transparent!important}
div[data-testid="stExpander"]{background:#fff!important;border:1px solid var(--border)!important;border-radius:2px!important;max-width:420px}
div[data-testid="stExpander"] summary{background:linear-gradient(#f7fbff,#dceaf8)!important}
div[data-testid="stExpander"] summary p{color:var(--link)!important;font-weight:700}
.taskbar{position:fixed;left:0;right:0;bottom:0;height:35px;background:linear-gradient(#2e7df1,#0757c8);z-index:9998;color:#fff;padding:.35rem .5rem}
.start{background:linear-gradient(#6bc65c,#2e9a2e);border:1px solid #1d7d1d;border-radius:0 14px 14px 0;padding:.27rem 1rem;font-weight:700;font-style:italic}
.task{margin-left:.55rem;background:#1e66c9;border:1px solid #0e4fae;padding:.23rem .7rem;display:inline-block}
@media(max-width:1000px){:root{--window:calc(100vw - 16px)}[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important}[data-testid="stColumn"]{min-width:min(100%,270px)!important;flex:1 1 270px!important}.steps{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:650px){:root{--window:calc(100vw - 6px)}.block-container,[data-testid="stMainBlockContainer"]{padding-inline:.4rem!important}.task{display:none}.titlebar{flex-wrap:wrap}.steps{grid-template-columns:1fr}}
</style>
""",
    unsafe_allow_html=True,
)


def split_terms(text: str) -> list[str]:
    return [x.strip().lower() for x in text.replace("\n", ",").split(",") if x.strip()]


def join_terms(values) -> str:
    return ", ".join(values or [])


def build_profile(
    base: dict,
    *,
    name: str,
    city: str,
    state: str,
    nearby: str,
    remote_ok: bool,
    target_titles: str,
    seniority: str,
    avoid_seniority: str,
    strong_skills: str,
    secondary_skills: str,
    focus_terms: str,
    bonus_terms: str,
    domain_strengths: list[str],
    salary_floor: int,
    salary_target: int,
    daily_application_goal: int,
    avoid_terms: str,
) -> dict:
    locations: list[str] = []
    if city.strip():
        locations.append(city.strip().lower())
    if state.strip():
        locations.append(state.strip().lower())
    locations.extend(split_terms(nearby))
    locations = list(dict.fromkeys(locations))

    targets = split_terms(target_titles)
    strong = split_terms(strong_skills)

    profile = dict(base)
    profile.update(
        {
            "name": name.strip() or "Job Seeker",
            "home_city": city.strip(),
            "home_state": state.strip(),
            "preferred_location_terms": locations,
            "remote_ok": bool(remote_ok),
            "target_titles": targets,
            "title_family_terms": targets,
            "seniority_preferences": split_terms(seniority),
            "deprioritize_seniority": split_terms(avoid_seniority),
            "strong_skills": strong,
            "secondary_skills": split_terms(secondary_skills),
            "focus_terms": split_terms(focus_terms) or strong,
            "bonus_terms": split_terms(bonus_terms),
            "domain_strengths": list(domain_strengths),
            "salary_floor": int(salary_floor),
            "salary_target": int(salary_target),
            "daily_application_goal": int(daily_application_goal),
            "avoid_terms": split_terms(avoid_terms),
        }
    )
    return profile


def profile_form(current: dict, template: dict, form_key: str, onboarding: bool = False) -> dict | None:
    locations = current.get("preferred_location_terms", [])
    home_city = current.get("home_city", "")
    home_state = current.get("home_state", "")
    nearby_default = [
        x for x in locations
        if x not in {home_city.lower(), home_state.lower()}
    ]

    with st.form(form_key):
        st.markdown("### 👤 About you")
        name = st.text_input(
            "Your name",
            value="" if onboarding else current.get("name", ""),
            placeholder="Example: Alex",
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            city = st.text_input(
                "Home city",
                value="" if onboarding else home_city,
                placeholder="Louisville",
            )
        with c2:
            state = st.text_input(
                "State",
                value="" if onboarding else home_state,
                placeholder="Kentucky",
            )
        with c3:
            remote_ok = st.checkbox(
                "Include U.S. remote jobs",
                value=bool(current.get("remote_ok", True)),
            )

        nearby = st.text_input(
            "Nearby cities / areas to include",
            value="" if onboarding else join_terms(nearby_default),
            placeholder="Jeffersonville, New Albany",
            help="Optional. Separate multiple areas with commas.",
        )

        st.markdown("### 💼 What work are you looking for?")
        target_titles = st.text_area(
            "Target job titles",
            value="" if onboarding else join_terms(current.get("target_titles", [])),
            placeholder="Project Manager, Operations Manager, Logistics Analyst",
            height=80,
            help="Use the titles you would actually search for. Separate them with commas.",
        )
        seniority = st.text_input(
            "Preferred levels / title words",
            value="" if onboarding else join_terms(current.get("seniority_preferences", [])),
            placeholder="analyst, senior analyst, specialist, manager",
        )
        avoid_seniority = st.text_input(
            "Titles to de-prioritize",
            value="" if onboarding else join_terms(current.get("deprioritize_seniority", [])),
            placeholder="director, vice president, chief",
        )

        st.markdown("### 🧰 What are you good at?")
        strong_skills = st.text_area(
            "Strong skills",
            value="" if onboarding else join_terms(current.get("strong_skills", [])),
            placeholder="Excel, SAP, scheduling, team leadership, warehouse operations",
            height=90,
        )
        secondary_skills = st.text_area(
            "Other useful skills",
            value="" if onboarding else join_terms(current.get("secondary_skills", [])),
            placeholder="Power BI, SQL, reporting",
            height=70,
        )
        focus_terms = st.text_area(
            "Work themes you enjoy",
            value="" if onboarding else join_terms(current.get("focus_terms", [])),
            placeholder="project management, process improvement, operations, customer success",
            height=70,
        )
        bonus_terms = st.text_input(
            "Bonus tools / keywords",
            value="" if onboarding else join_terms(current.get("bonus_terms", [])),
            placeholder="Salesforce, Jira, Tableau",
        )

        st.markdown("### 🏢 Professional domains")
        domains = [
            "HR / People Operations",
            "Healthcare / Clinical",
            "Finance / Accounting",
            "Insurance",
            "Legal / Compliance",
            "Supply Chain / Procurement",
        ]
        domain_strengths = st.multiselect(
            "Areas where you have meaningful professional experience",
            domains,
            default=[] if onboarding else [
                x for x in current.get("domain_strengths", []) if x in domains
            ],
            help="This keeps legitimate domain requirements from being treated as a gap.",
        )

        st.markdown("### 💰 Compensation & dealbreakers")
        s1, s2 = st.columns(2)
        with s1:
            salary_floor = st.number_input(
                "Minimum salary",
                min_value=0,
                step=5000,
                value=0 if onboarding else int(current.get("salary_floor", 0) or 0),
            )
        with s2:
            salary_target = st.number_input(
                "Target salary",
                min_value=0,
                step=5000,
                value=0 if onboarding else int(current.get("salary_target", 0) or 0),
            )
        avoid_terms = st.text_input(
            "Dealbreakers / avoid terms",
            value="" if onboarding else join_terms(current.get("avoid_terms", [])),
            placeholder="commission only, contract only, night shift",
        )

        daily_application_goal = st.number_input(
            "Daily application goal",
            min_value=1,
            max_value=10,
            step=1,
            value=3 if onboarding else int(current.get("daily_application_goal", 3) or 3),
            help="A small daily target keeps the search moving without turning it into endless scrolling.",
        )

        button_text = "🚀 Save & Find My Jobs" if onboarding else "💾 Save Profile"
        submitted = st.form_submit_button(button_text, use_container_width=True)

    if not submitted:
        return None

    errors: list[str] = []
    if not city.strip():
        errors.append("home city")
    if not state.strip():
        errors.append("state")
    if not split_terms(target_titles):
        errors.append("at least one target job title")
    if not split_terms(strong_skills):
        errors.append("at least one strong skill")

    if errors:
        st.error("Please add " + ", ".join(errors) + " before continuing.")
        return None

    return build_profile(
        template,
        name=name,
        city=city,
        state=state,
        nearby=nearby,
        remote_ok=remote_ok,
        target_titles=target_titles,
        seniority=seniority,
        avoid_seniority=avoid_seniority,
        strong_skills=strong_skills,
        secondary_skills=secondary_skills,
        focus_terms=focus_terms,
        bonus_terms=bonus_terms,
        domain_strengths=domain_strengths,
        salary_floor=salary_floor,
        salary_target=salary_target,
        daily_application_goal=daily_application_goal,
        avoid_terms=avoid_terms,
    )


template = load_profile_template()
first_run = not has_user_profile()

if first_run:
    st.markdown(
        '<div class="menu">File &nbsp; View &nbsp; Help'
        '<span style="float:right;color:#16418a"><b>First-time setup</b></span></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section">🪟 Welcome to Opportunity Intelligence</div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="welcome">
<h2>Your job search, ranked around you.</h2>
<p>Instead of showing every opening, Opportunity Intelligence uses your location,
skills, target roles and dealbreakers to build a shortlist worth your time.</p>
</div>
<div class="steps">
  <div class="step">1 · Your market</div>
  <div class="step">2 · Your roles</div>
  <div class="step">3 · Your skills</div>
  <div class="step">4 · Your dealbreakers</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="help"><b>About 2 minutes.</b> Nothing here requires coding. '
        'Your answers create your private scoring profile.</div>',
        unsafe_allow_html=True,
    )

    new_profile = profile_form(template, template, "first_run_profile", onboarding=True)
    if new_profile is not None:
        save_user_profile(new_profile)
        st.session_state["welcome_complete"] = new_profile.get("name", "Job Seeker")
        st.rerun()

    st.markdown(
        '<div class="taskbar"><span class="start">🪟 start</span>'
        '<span class="task">📁 Opportunity Intelligence · Setup</span></div>',
        unsafe_allow_html=True,
    )
    st.stop()


profile = load_profile()
profile_name = profile.get("name") or "Job Seeker"
market_state = load_market_state()
new_refresh_ids = {int(job_id) for job_id in market_state.get("new_job_ids", [])}
applied_today = count_today_status("applied")
daily_goal = max(1, int(profile.get("daily_application_goal", 3) or 3))

st.markdown(
    f'<div class="menu">File &nbsp; View &nbsp; Favorites &nbsp; Tools &nbsp; Help'
    f'<span style="float:right;color:#16418a"><b>{profile_name}</b></span></div>',
    unsafe_allow_html=True,
)

if "welcome_complete" in st.session_state:
    completed_name = st.session_state.pop("welcome_complete")
    st.success(f"Welcome, {completed_name}. Your profile is ready — refresh the market to build your shortlist.")

section = st.radio(
    "Navigation",
    ["🏠 Job Market", "📂 My Applications", "🛠 Control Panel"],
    horizontal=True,
    label_visibility="collapsed",
)

history = load_history(HISTORY_PATH)
rows: list[dict] = []
details_by_id: dict[int, dict] = {}
history_matches: dict[int, dict] = {}

for raw in list_jobs():
    score, details = score_job(raw, profile)
    job = dict(raw)
    job["score"] = score
    job["verdict"] = details["verdict"]
    match = match_history(job, history)
    job["history_match"] = match["match_type"] if match else None
    if match:
        history_matches[job["id"]] = match
    details_by_id[job["id"]] = details
    rows.append(job)

df = pd.DataFrame(rows) if rows else pd.DataFrame()
if not df.empty:
    df["is_new_refresh"] = df["id"].isin(new_refresh_ids)
statuses = [
    "new", "saved", "applied", "screen", "interview",
    "final", "offer", "rejected", "withdrawn",
]


def money(value):
    if value is None or pd.isna(value):
        return None
    value = float(value)
    return f"${value/1000:.0f}K" if value >= 1000 else f"${value:,.0f}"


def pay_label(row):
    lo = money(row.get("salary_min"))
    hi = money(row.get("salary_max"))
    if lo and hi:
        return f"{lo}–{hi}"
    if lo:
        return f"{lo}+"
    if hi:
        return f"Up to {hi}"
    return None


def score_explanation(row):
    d = details_by_id[row["id"]]
    with st.expander(f"Why {int(row['score'])}?"):
        for label, key in [
            ("Title fit", "title"),
            ("Skills", "skills"),
            ("Seniority", "seniority"),
            ("Work themes", "process_ops"),
            ("Bonus skills", "crm_power_platform"),
            ("Location", "location"),
            ("Compensation", "salary"),
        ]:
            st.write(f"**{label}:** {d[key]['score']}/{d[key]['max']}")
        matched = list(
            dict.fromkeys(
                d["skills"].get("strong_matches", [])
                + d["skills"].get("secondary_matches", [])
                + d["process_ops"].get("matches", [])
                + d["crm_power_platform"].get("matches", [])
            )
        )
        if matched:
            st.write("**Matched signals:** " + ", ".join(matched[:14]))
        for finding in d.get("hard_requirements", {}).get("findings", []):
            years = (
                f"{finding.get('years')}+ years"
                if finding.get("years")
                else "direct experience"
            )
            st.error(f"Hard requirement gap: {years} in {finding['domain']}.")


if section == "🏠 Job Market":
    left, right = st.columns([1, 4])
    with left:
        if st.button("🔄 Refresh Market", use_container_width=True):
            before_ids = {int(job["id"]) for job in list_jobs()}
            with st.spinner("Checking job sources for your market..."):
                run_collectors()
            after_ids = {int(job["id"]) for job in list_jobs()}
            save_refresh_result(after_ids - before_ids)
            st.rerun()
    with right:
        market = ", ".join(profile.get("preferred_location_terms", [])[:4]) or "not configured"
        remote = " + U.S. remote" if profile.get("remote_ok", True) else ""
        st.caption(f"Current market: {market}{remote}")

    if df.empty:
        st.info("Your profile is ready. Click Refresh Market to build your first shortlist.")
    else:
        active = df[
            (df["status"].isin(["new", "saved"]))
            & (df["history_match"] != "exact")
        ]

        st.markdown('<div class="section">📊 Market Pulse</div>', unsafe_allow_html=True)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Market Watch", len(df))
        m2.metric("New This Refresh", int(df["is_new_refresh"].sum()))
        m3.metric("Apply Now", int((active["verdict"] == "APPLY").sum()))
        m4.metric("Strong Matches", int((active["verdict"] == "STRONG CONSIDER").sum()))
        m5.metric("Previous Applications", int((df["history_match"] == "exact").sum()))

        st.markdown('<div class="section">🎯 Today’s Goal</div>', unsafe_allow_html=True)
        progress = min(1.0, applied_today / daily_goal)
        st.progress(progress)
        if applied_today >= daily_goal:
            st.success(f"{applied_today}/{daily_goal} applications today — goal complete.")
        else:
            remaining = daily_goal - applied_today
            st.caption(f"{applied_today}/{daily_goal} applications today · {remaining} to go")

        st.markdown('<div class="section">📂 Today’s Shortlist</div>', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            verdicts = st.multiselect(
                "Verdict",
                ["APPLY", "STRONG CONSIDER", "STRETCH", "SKIP"],
                default=["APPLY", "STRONG CONSIDER", "STRETCH"],
            )
        with f2:
            companies = st.multiselect(
                "Company",
                sorted(df["company"].dropna().unique()),
            )
        with f3:
            only_new = st.checkbox("Only new this refresh", value=False)
        with f4:
            show_handled = st.checkbox("Show already handled", value=False)

        view = df[df["verdict"].isin(verdicts)].copy()
        if not show_handled:
            view = view[view["status"].isin(["new", "saved"])]
        view = view[view["history_match"] != "exact"]
        if only_new:
            view = view[view["is_new_refresh"]]
        if companies:
            view = view[view["company"].isin(companies)]
        view = view.sort_values(
            ["score", "date_found"],
            ascending=[False, False],
        )

        for _, row in view.iterrows():
            with st.container(border=True):
                pay = pay_label(row)
                pay_html = f'<span class="salary">💵 {pay}</span>' if pay else ""
                st.markdown(
                    f'<div class="titlebar"><span class="score">{int(row["score"])}</span>'
                    f'<span class="titletext">{row["title"]}</span>{pay_html}</div>',
                    unsafe_allow_html=True,
                )

                body, status_col = st.columns([5.5, 1])
                with body:
                    st.markdown(
                        f'<div class="meta"><b>{row["company"]}</b> · '
                        f'{row["location"] or "Location not listed"}</div>',
                        unsafe_allow_html=True,
                    )
                    match = history_matches.get(row["id"])
                    if match and match["match_type"] == "possible":
                        prior = match["prior"]
                        st.markdown(
                            f'<div class="dupe">⚠ Possible previous application: '
                            f'{prior.get("title") or "another role"} at '
                            f'{prior.get("company", row["company"])}</div>',
                            unsafe_allow_html=True,
                        )

                    cls = (
                        "apply"
                        if row["verdict"] == "APPLY"
                        else "strong"
                        if row["verdict"] == "STRONG CONSIDER"
                        else "stretch"
                        if row["verdict"] == "STRETCH"
                        else "skip"
                    )
                    st.markdown(
                        f'<span class="badge {cls}">{row["verdict"]}</span>'
                        f'<span class="badge">{row.get("source") or "unknown"}</span>',
                        unsafe_allow_html=True,
                    )
                    a, b = st.columns([1, 3])
                    with a:
                        if row.get("url"):
                            st.link_button("Open Posting", row["url"])
                    with b:
                        score_explanation(row)

                with status_col:
                    current = row["status"] if row["status"] in statuses else "new"
                    new_status = st.selectbox(
                        "Status",
                        statuses,
                        index=statuses.index(current),
                        key=f"status-{row['id']}",
                    )
                    if new_status != row["status"]:
                        update_status(int(row["id"]), new_status)
                        st.rerun()

elif section == "📂 My Applications":
    st.markdown('<div class="section">📂 My Applications</div>', unsafe_allow_html=True)
    st.caption("This history is private to this user profile.")

    uploaded = st.file_uploader(
        "Import application history (optional)",
        type=["json"],
    )
    if uploaded is not None:
        try:
            payload = json.loads(uploaded.getvalue().decode("utf-8"))
            items = (
                payload.get("applications", [])
                if isinstance(payload, dict)
                else payload
            )
            save_history(HISTORY_PATH, [x for x in items if isinstance(x, dict)])
            st.success("Application history imported.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not import that file: {exc}")

    if history:
        st.dataframe(
            pd.DataFrame(history),
            use_container_width=True,
            hide_index=True,
        )

    if not df.empty:
        handled = df[~df["status"].isin(["new", "saved"])]
        if not handled.empty:
            st.markdown("### Tracked in this app")
            visible_cols = [
                col
                for col in ["company", "title", "score", "verdict", "status", "date_found"]
                if col in handled.columns
            ]
            st.dataframe(
                handled[visible_cols],
                use_container_width=True,
                hide_index=True,
            )

else:
    st.markdown(
        '<div class="section">🛠 Control Panel · Job Search Profile</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="help"><b>No coding required.</b> Update anything below and '
        'click <b>Save Profile</b>. Existing jobs rescore immediately; use Refresh '
        'Market when you change your location or remote preference.</div>',
        unsafe_allow_html=True,
    )

    edited = profile_form(profile, template, "edit_profile", onboarding=False)
    if edited is not None:
        save_user_profile(edited)
        st.success("Profile saved. Your existing jobs have been rescored.")
        st.rerun()

    st.markdown('<div class="section">ℹ Current Profile</div>', unsafe_allow_html=True)
    market = join_terms(profile.get("preferred_location_terms", [])) or "not configured"
    roles = join_terms(profile.get("target_titles", [])) or "not configured"
    st.markdown(
        f'<div class="summary"><b>{profile_name}</b><br>'
        f'Market: {market}<br>'
        f'Remote: {"Yes" if profile.get("remote_ok", True) else "No"}<br>'
        f'Target roles: {roles}<br>'
        f'Daily goal: {daily_goal} applications<br>'
        f'Profile storage: {profile_source()}</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Start setup over"):
        st.caption("This removes only the private profile. It does not delete application history.")
        if st.button("Reset my profile"):
            reset_user_profile()
            st.rerun()

st.markdown(
    '<div class="taskbar"><span class="start">🪟 start</span>'
    f'<span class="task">📁 Opportunity Intelligence · {profile_name}</span></div>',
    unsafe_allow_html=True,
)
