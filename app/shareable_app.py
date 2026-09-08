from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from data.db import list_jobs, update_status
from matching.application_history import load_history, match_history, save_history
from matching.scorer import score_job
from profile_config import load_profile, load_profile_template, save_user_profile
from run_collectors import run as run_collectors

HISTORY_PATH = ROOT / "data" / "application_history.json"

st.set_page_config(page_title="Opportunity Intelligence", page_icon="🪟", layout="wide")

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
div[data-testid="stExpander"]{background:#fff!important;border:1px solid var(--border)!important;border-radius:2px!important;max-width:420px}div[data-testid="stExpander"] summary{background:linear-gradient(#f7fbff,#dceaf8)!important}div[data-testid="stExpander"] summary p{color:var(--link)!important;font-weight:700}.taskbar{position:fixed;left:0;right:0;bottom:0;height:35px;background:linear-gradient(#2e7df1,#0757c8);z-index:9998;color:#fff;padding:.35rem .5rem}.start{background:linear-gradient(#6bc65c,#2e9a2e);border:1px solid #1d7d1d;border-radius:0 14px 14px 0;padding:.27rem 1rem;font-weight:700;font-style:italic}.task{margin-left:.55rem;background:#1e66c9;border:1px solid #0e4fae;padding:.23rem .7rem;display:inline-block}
@media(max-width:1000px){:root{--window:calc(100vw - 16px)}[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important}[data-testid="stColumn"]{min-width:min(100%,270px)!important;flex:1 1 270px!important}}
@media(max-width:650px){:root{--window:calc(100vw - 6px)}.block-container,[data-testid="stMainBlockContainer"]{padding-inline:.4rem!important}.task{display:none}.titlebar{flex-wrap:wrap}}
</style>
""",
    unsafe_allow_html=True,
)


def split_terms(text: str) -> list[str]:
    return [x.strip().lower() for x in text.replace("\n", ",").split(",") if x.strip()]


def join_terms(values) -> str:
    return ", ".join(values or [])


profile = load_profile()
template = load_profile_template()
profile_name = profile.get("name") or "Job Seeker"

st.markdown(
    f'<div class="menu">File &nbsp; View &nbsp; Favorites &nbsp; Tools &nbsp; Help'
    f'<span style="float:right;color:#16418a"><b>{profile_name}</b></span></div>',
    unsafe_allow_html=True,
)

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
statuses = ["new", "saved", "applied", "screen", "interview", "final", "offer", "rejected", "withdrawn"]


def money(value):
    if value is None or pd.isna(value):
        return None
    value = float(value)
    return f"${value/1000:.0f}K" if value >= 1000 else f"${value:,.0f}"


def pay_label(row):
    lo, hi = money(row.get("salary_min")), money(row.get("salary_max"))
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
            ("Title fit", "title"), ("Skills", "skills"), ("Seniority", "seniority"),
            ("Work themes", "process_ops"), ("Bonus skills", "crm_power_platform"),
            ("Location", "location"), ("Compensation", "salary"),
        ]:
            st.write(f"**{label}:** {d[key]['score']}/{d[key]['max']}")
        for finding in d.get("hard_requirements", {}).get("findings", []):
            years = f"{finding.get('years')}+ years" if finding.get("years") else "direct experience"
            st.error(f"Hard requirement gap: {years} in {finding['domain']}.")


if section == "🏠 Job Market":
    left, right = st.columns([1, 4])
    with left:
        if st.button("🔄 Refresh Market", use_container_width=True):
            with st.spinner("Checking job sources for your market..."):
                run_collectors()
            st.rerun()
    with right:
        market = ", ".join(profile.get("preferred_location_terms", [])[:4]) or "not configured"
        remote = " + U.S. remote" if profile.get("remote_ok", True) else ""
        st.caption(f"Current market: {market}{remote}")

    if df.empty:
        st.info("No jobs loaded yet. Open Control Panel, set your profile, then click Refresh Market.")
    else:
        active = df[(df["status"].isin(["new", "saved"])) & (df["history_match"] != "exact")]
        st.markdown('<div class="section">📊 Market Pulse</div>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Market Watch", len(df))
        m2.metric("Apply Now", int((active["verdict"] == "APPLY").sum()))
        m3.metric("Strong Matches", int((active["verdict"] == "STRONG CONSIDER").sum()))
        m4.metric("Previous Applications", int((df["history_match"] == "exact").sum()))

        st.markdown('<div class="section">📂 Today’s Shortlist</div>', unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        with f1:
            verdicts = st.multiselect("Verdict", ["APPLY", "STRONG CONSIDER", "STRETCH", "SKIP"], default=["APPLY", "STRONG CONSIDER", "STRETCH"])
        with f2:
            companies = st.multiselect("Company", sorted(df["company"].dropna().unique()))
        with f3:
            show_handled = st.checkbox("Show already handled", value=False)

        view = df[df["verdict"].isin(verdicts)].copy()
        if not show_handled:
            view = view[view["status"].isin(["new", "saved"])]
        view = view[view["history_match"] != "exact"]
        if companies:
            view = view[view["company"].isin(companies)]
        view = view.sort_values(["score", "date_found"], ascending=[False, False])

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
                    st.markdown(f'<div class="meta"><b>{row["company"]}</b> · {row["location"] or "Location not listed"}</div>', unsafe_allow_html=True)
                    match = history_matches.get(row["id"])
                    if match and match["match_type"] == "possible":
                        prior = match["prior"]
                        st.markdown(f'<div class="dupe">⚠ Possible previous application: {prior.get("title") or "another role"} at {prior.get("company", row["company"])}</div>', unsafe_allow_html=True)
                    cls = "apply" if row["verdict"] == "APPLY" else "strong" if row["verdict"] == "STRONG CONSIDER" else "stretch" if row["verdict"] == "STRETCH" else "skip"
                    st.markdown(f'<span class="badge {cls}">{row["verdict"]}</span><span class="badge">{row.get("source") or "unknown"}</span>', unsafe_allow_html=True)
                    a, b = st.columns([1, 3])
                    with a:
                        if row.get("url"):
                            st.link_button("Open Posting", row["url"])
                    with b:
                        score_explanation(row)
                with status_col:
                    current = row["status"] if row["status"] in statuses else "new"
                    new_status = st.selectbox("Status", statuses, index=statuses.index(current), key=f"status-{row['id']}")
                    if new_status != row["status"]:
                        update_status(int(row["id"]), new_status)
                        st.rerun()

elif section == "📂 My Applications":
    st.markdown('<div class="section">📂 My Applications</div>', unsafe_allow_html=True)
    st.caption("This history is private to this installation.")
    uploaded = st.file_uploader("Import application history (optional)", type=["json"])
    if uploaded is not None:
        try:
            payload = json.loads(uploaded.getvalue().decode("utf-8"))
            items = payload.get("applications", []) if isinstance(payload, dict) else payload
            save_history(HISTORY_PATH, [x for x in items if isinstance(x, dict)])
            st.success("Application history imported.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not import that file: {exc}")
    if history:
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
    if not df.empty:
        handled = df[~df["status"].isin(["new", "saved"])]
        if not handled.empty:
            st.markdown("### Tracked in this app")
            st.dataframe(handled[["company", "title", "score", "verdict", "status", "date_found"]], use_container_width=True, hide_index=True)

else:
    st.markdown('<div class="section">🛠 Control Panel · Job Search Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="help"><b>No coding required.</b> Fill this out once, click <b>Save Profile</b>, then return to Job Market and click Refresh Market.</div>', unsafe_allow_html=True)

    locations = profile.get("preferred_location_terms", [])
    home_city = profile.get("home_city", locations[0] if locations else "")
    home_state = profile.get("home_state", "")
    nearby_default = [x for x in locations if x not in {home_city.lower(), home_state.lower()}]

    with st.form("profile_form"):
        st.markdown("### 👤 About you")
        name = st.text_input("Your name", value=profile.get("name", "Job Seeker"))
        c1, c2, c3 = st.columns(3)
        with c1:
            city = st.text_input("Home city", value=home_city)
        with c2:
            state = st.text_input("State", value=home_state)
        with c3:
            remote_ok = st.checkbox("Include U.S. remote jobs", value=bool(profile.get("remote_ok", True)))
        nearby = st.text_input("Nearby cities / areas", value=join_terms(nearby_default), help="Comma separated")

        st.markdown("### 💼 Roles")
        target_titles = st.text_area("Target job titles", value=join_terms(profile.get("target_titles", template.get("target_titles", []))), height=80, help="Comma separated")
        seniority = st.text_input("Preferred levels / title words", value=join_terms(profile.get("seniority_preferences", template.get("seniority_preferences", []))))
        avoid_seniority = st.text_input("Titles to de-prioritize", value=join_terms(profile.get("deprioritize_seniority", template.get("deprioritize_seniority", []))))

        st.markdown("### 🧰 Skills")
        strong_skills = st.text_area("Strong skills", value=join_terms(profile.get("strong_skills", template.get("strong_skills", []))), height=90)
        secondary_skills = st.text_area("Secondary skills", value=join_terms(profile.get("secondary_skills", template.get("secondary_skills", []))), height=75)
        focus_terms = st.text_area("Work themes you enjoy", value=join_terms(profile.get("focus_terms", template.get("focus_terms", []))), height=75)
        bonus_terms = st.text_input("Bonus keywords / tools", value=join_terms(profile.get("bonus_terms", template.get("bonus_terms", []))))

        st.markdown("### 🏢 Domain experience")
        domains = ["HR / People Operations", "Healthcare / Clinical", "Finance / Accounting", "Insurance", "Legal / Compliance", "Supply Chain / Procurement"]
        domain_strengths = st.multiselect("Areas where you have meaningful professional experience", domains, default=[x for x in profile.get("domain_strengths", []) if x in domains])

        st.markdown("### 💰 Compensation")
        s1, s2 = st.columns(2)
        with s1:
            salary_floor = st.number_input("Minimum salary", min_value=0, step=5000, value=int(profile.get("salary_floor", template.get("salary_floor", 0)) or 0))
        with s2:
            salary_target = st.number_input("Target salary", min_value=0, step=5000, value=int(profile.get("salary_target", template.get("salary_target", 0)) or 0))
        avoid_terms = st.text_input("Dealbreakers / avoid terms", value=join_terms(profile.get("avoid_terms", template.get("avoid_terms", []))))

        save = st.form_submit_button("💾 Save Profile", use_container_width=True)

    if save:
        market_terms = []
        if city.strip():
            market_terms.append(city.strip().lower())
        if state.strip():
            market_terms.append(state.strip().lower())
        market_terms.extend(split_terms(nearby))
        market_terms = list(dict.fromkeys(market_terms))
        targets = split_terms(target_titles)
        strong = split_terms(strong_skills)
        new_profile = dict(template)
        new_profile.update({
            "name": name.strip() or "Job Seeker",
            "home_city": city.strip(),
            "home_state": state.strip(),
            "preferred_location_terms": market_terms,
            "remote_ok": remote_ok,
            "target_titles": targets,
            "title_family_terms": targets,
            "seniority_preferences": split_terms(seniority),
            "deprioritize_seniority": split_terms(avoid_seniority),
            "strong_skills": strong,
            "secondary_skills": split_terms(secondary_skills),
            "focus_terms": split_terms(focus_terms) or strong,
            "bonus_terms": split_terms(bonus_terms),
            "domain_strengths": domain_strengths,
            "salary_floor": int(salary_floor),
            "salary_target": int(salary_target),
            "avoid_terms": split_terms(avoid_terms),
        })
        save_user_profile(new_profile)
        st.success("Profile saved. Your jobs will now be scored for you.")
        st.rerun()

st.markdown(f'<div class="taskbar"><span class="start">🪟 start</span><span class="task">📁 Opportunity Intelligence · {profile_name}</span></div>', unsafe_allow_html=True)
