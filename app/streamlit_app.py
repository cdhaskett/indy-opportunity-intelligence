from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pandas as pd
import streamlit as st
from data.db import list_jobs,update_status
from matching.application_history import load_history,match_history,save_history
from matching.scorer import score_job
from run_collectors import run as run_collectors
PROFILE=json.loads((ROOT/'data'/'candidate_profile.json').read_text());WATCHLIST=json.loads((ROOT/'data'/'market_watchlist.json').read_text());LIVE_REGISTRY=json.loads((ROOT/'data'/'employers.json').read_text());HISTORY_PATH=ROOT/'data'/'application_history.json'
st.set_page_config(page_title='Indy Opportunity Intelligence',page_icon='🪟',layout='wide')
st.markdown('''<style>
html,body,[class*="css"]{font-family:Tahoma,Arial,sans-serif}.stApp{background:linear-gradient(#4b9df4 0 42%,#bfe4ff 59%,#79cf5c 60%,#3d9d34 100%);color:#111}.stApp:before{content:"";position:fixed;inset:0;pointer-events:none;background:radial-gradient(ellipse at 12% 18%,rgba(255,255,255,.9) 0 2.4%,transparent 2.7%),radial-gradient(ellipse at 18% 17%,rgba(255,255,255,.75) 0 3.2%,transparent 3.5%),radial-gradient(ellipse at 74% 21%,rgba(255,255,255,.84) 0 2.5%,transparent 2.8%),radial-gradient(ellipse at 80% 20%,rgba(255,255,255,.7) 0 3.3%,transparent 3.6%),radial-gradient(ellipse at 20% 105%,#318c2c 0 34%,transparent 34.4%),radial-gradient(ellipse at 55% 110%,#68c94e 0 44%,transparent 44.4%),radial-gradient(ellipse at 92% 108%,#45a83b 0 38%,transparent 38.4%)}.block-container{position:relative;max-width:1540px;margin:auto;padding:.65rem 1.2rem 4rem;background:rgba(236,233,216,.975);min-height:100vh;border-left:1px solid #7697bd;border-right:1px solid #7697bd;box-shadow:0 0 25px #285b8a88}.xp-menubar{background:#f5f3eb;color:#111;padding:.30rem .60rem;border:1px solid #aca899;border-bottom-color:#777;margin-bottom:.35rem;font-size:.78rem;box-shadow:inset 1px 1px #fff}div[role="radiogroup"]{background:#ece9d8;border:1px solid #aca899;padding:.22rem;width:fit-content;margin:.25rem 0 .55rem;box-shadow:inset 1px 1px #fff}div[role="radiogroup"] label{padding:.28rem .48rem;border:1px solid transparent;border-radius:2px}div[role="radiogroup"] label:hover{background:#fff;border-color:#7f9db9}div[role="radiogroup"] p{color:#111!important;font-weight:bold;font-size:.84rem}.xp-section{background:linear-gradient(#3f93ff,#0753c7);color:white;font-weight:bold;padding:.36rem .56rem;border:1px solid #06459e;border-radius:5px 5px 0 0;margin-top:.45rem;text-shadow:1px 1px #16448a}div[data-testid="stMetric"]{background:#fffef5;border:1px solid #999;border-top-color:#fff;border-left-color:#fff;padding:.48rem .62rem;min-height:74px;box-shadow:1px 1px 0 #777}div[data-testid="stMetricLabel"] p{color:#1f3e72!important;font-size:.72rem;font-weight:bold}div[data-testid="stMetricValue"]{color:#111!important;font-size:1.52rem}div[data-testid="stVerticalBlockBorderWrapper"]{background:#fff!important;border:1px solid #9eb6cf!important;border-radius:0!important;box-shadow:inset 1px 1px #fff!important;margin-bottom:.38rem}div[data-testid="stVerticalBlockBorderWrapper"]>div{padding-top:.28rem!important;padding-bottom:.28rem!important}.job-title{color:#10479d;font-size:1.02rem;line-height:1.2;font-weight:bold;margin-bottom:.10rem}.score{display:inline-block;min-width:2.05rem;text-align:center;background:linear-gradient(#66c96d,#32a342);color:white;border:1px solid #18752a;padding:.16rem .34rem;margin-right:.42rem;border-radius:3px;text-shadow:1px 1px #287332}.salary{display:inline-block;background:#ffdf57;color:#493900;border:1px solid #a47b00;padding:.14rem .34rem;margin-left:.40rem;border-radius:3px;font-size:.75rem}.meta{font-size:.80rem;color:#444;margin:.12rem 0 .30rem}.badge{display:inline-block;padding:.13rem .34rem;margin:0 .22rem .20rem 0;font-size:.66rem;font-weight:bold;border:1px solid #7f9db9;background:#dbe8f7;color:#284b77;text-transform:uppercase}.apply{background:#39b54a;color:#fff;border-color:#1c7d2b}.strong{background:#ffd65a;color:#4e3900;border-color:#a87800}.stretch{background:#e2eaf3;color:#274a75;border-color:#7f9db9}.skip{background:#efc2bd;color:#721b14;border-color:#b25349}.dup{background:#fff7a8;border:1px solid #d0bd3e;color:#4c4314;padding:.34rem .46rem;margin:.24rem 0 .34rem;font-size:.76rem}.stButton>button,.stLinkButton>a{background:linear-gradient(#fff,#e5e5df)!important;border:1px solid #003c74!important;box-shadow:inset 1px 1px #fff!important;color:#111!important;border-radius:3px!important;font-weight:700!important;min-height:1.95rem!important;padding-top:.15rem!important;padding-bottom:.15rem!important}.stButton>button:hover,.stLinkButton>a:hover{background:linear-gradient(#fffef0,#f2e7ad)!important}div[data-testid="stSelectbox"] div[data-baseweb="select"]>div,div[data-testid="stMultiSelect"] div[data-baseweb="select"]>div,div[data-baseweb="select"]>div,[role="combobox"]{background:#fff!important;color:#111!important;border-color:#7f9db9!important;border-radius:2px!important}div[data-testid="stSelectbox"] *,div[data-testid="stMultiSelect"] *,div[data-baseweb="select"] *{color:#111!important}[data-baseweb="tag"]{background:#dbe8f7!important;border:1px solid #7f9db9!important;border-radius:2px!important}[data-baseweb="tag"] *,[data-baseweb="tag"] span{color:#10479d!important}div[data-testid="stExpander"]{border:1px solid #9eb6cf!important;background:#fff!important;border-radius:0!important;max-width:430px}div[data-testid="stExpander"] summary{background:linear-gradient(#f7fbff,#dceaf8)!important;min-height:1.85rem}div[data-testid="stExpander"] summary p{color:#10479d!important;font-size:.78rem;font-weight:700}div[data-testid="stExpander"] p,div[data-testid="stExpander"] li,div[data-testid="stExpander"] strong{color:#111!important}[data-testid="stToggle"] p,.stMultiSelect label p,.stSelectbox label p,.stFileUploader label p{color:#111!important}.stCaption p,[data-testid="stCaptionContainer"] p{color:#4e5f6f!important}div[data-testid="stDataFrame"]{border:1px solid #7f9db9;border-radius:0;overflow:hidden}.taskbar{position:fixed;bottom:0;left:0;right:0;height:35px;background:linear-gradient(#2e7df1,#0757c8);z-index:9998;color:white;padding:.35rem .5rem;box-shadow:0 -1px 4px #0005}.start{background:linear-gradient(#6bc65c,#2e9a2e);border:1px solid #1d7d1d;border-radius:0 14px 14px 0;padding:.27rem 1rem;font-weight:bold;font-style:italic;text-shadow:1px 1px #1c681d}.task-name{margin-left:.55rem;background:#1e66c9;border:1px solid #0e4fae;padding:.23rem .7rem;min-width:220px;display:inline-block}@media(max-width:850px){.block-container{padding-left:.5rem;padding-right:.5rem}.task-name{display:none}.salary{margin-left:.1rem}}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="xp-menubar">File &nbsp; View &nbsp; Tools &nbsp; Help</div>',unsafe_allow_html=True)
section=st.radio('Navigation',['🏠 Job Market','🌐 Market Coverage','📂 My Applications'],horizontal=True,label_visibility='collapsed')
history=load_history(HISTORY_PATH);score_details={};history_matches={};rows=[]
for raw in list_jobs():
 score,detail=score_job(raw,PROFILE);job=dict(raw);job['score']=score;job['verdict']=detail['verdict'];m=match_history(job,history);job['history_match']=m['match_type'] if m else None
 if m:history_matches[job['id']]=m
 score_details[job['id']]=detail;rows.append(job)
df=pd.DataFrame(rows) if rows else pd.DataFrame();statuses=['new','saved','applied','screen','interview','final','offer','rejected','withdrawn']
def money(v):
 if v is None or pd.isna(v):return None
 v=float(v);return f'${v/1000:.0f}K' if v>=1000 else f'${v:,.0f}'
def salary(row):
 lo,hi=money(row.get('salary_min')),money(row.get('salary_max'))
 return f'{lo}–{hi}' if lo and hi else f'{lo}+' if lo else f'Up to {hi}' if hi else None
def explain(row):
 d=score_details[row['id']]
 with st.expander(f"Why {int(row['score'])}?"):
  for label,key in [('Title / job family','title'),('Skills','skills'),('Seniority','seniority'),('Process / operations','process_ops'),('CRM / Power Platform','crm_power_platform'),('Location / remote','location'),('Compensation','salary')]:st.write(f"**{label}:** {d[key]['score']}/{d[key]['max']}")
  matched=list(dict.fromkeys(d['skills'].get('strong_matches',[])+d['skills'].get('secondary_matches',[])+d['process_ops'].get('matches',[])+d['crm_power_platform'].get('matches',[])));st.write('**Matched signals:** '+(', '.join(matched[:14]) if matched else 'No strong signals yet.'))
  for f in d.get('hard_requirements',{}).get('findings',[]):st.error(f"Hard requirement gap: {str(f.get('years'))+'+ years' if f.get('years') else 'direct experience'} in {f['domain']}.")
if section=='🏠 Job Market':
 a,b=st.columns([1,4])
 with a:
  if st.button('🔄 Refresh Market',width='stretch'):
   with st.spinner('Checking employer career systems...'):run_collectors()
   st.rerun()
 with b:st.caption('Live ATS feeds + verified discovery sources')
 if df.empty:st.info('No jobs loaded yet. Click Refresh Market.');st.stop()
 active=df[(df.status.isin(['new','saved']))&(df.history_match!='exact')]
 st.markdown('<div class="xp-section">📊 Market Pulse</div>',unsafe_allow_html=True);c1,c2,c3,c4,c5=st.columns(5);c1.metric('Market Watch',len(df));c2.metric('Apply Now',int((active.verdict=='APPLY').sum()));c3.metric('Strong Matches',int((active.verdict=='STRONG CONSIDER').sum()));c4.metric('Already Applied',int((df.history_match=='exact').sum()));c5.metric('Review Duplicates',int((df.history_match=='possible').sum()))
 st.markdown('<div class="xp-section">📂 Today’s Shortlist</div>',unsafe_allow_html=True);st.caption(f'Duplicate guard active · {len(history)} private application-history records loaded')
 processed=st.toggle("Show jobs I've already handled");exact=st.toggle('Show jobs matched to a previous application');f1,f2,f3=st.columns(3)
 with f1:vf=st.multiselect('Verdict',['APPLY','STRONG CONSIDER','STRETCH','SKIP'],default=['APPLY','STRONG CONSIDER','STRETCH'])
 with f2:cf=st.multiselect('Company',sorted(df.company.dropna().unique()))
 with f3:sf=st.multiselect('Status',statuses)
 view=df[df.verdict.isin(vf)].copy()
 if not processed and not sf:view=view[view.status.isin(['new','saved'])]
 if not exact:view=view[view.history_match!='exact']
 if cf:view=view[view.company.isin(cf)]
 if sf:view=view[view.status.isin(sf)]
 view=view.sort_values(['score','date_found'],ascending=[False,False])
 for _,r in view.iterrows():
  with st.container(border=True):
   left,right=st.columns([5.5,1]);s=salary(r)
   with left:
    st.markdown(f'<div class="job-title"><span class="score">{int(r.score)}</span>{r.title}{f"<span class=salary>💵 {s}</span>" if s else ""}</div><div class="meta"><b>{r.company}</b> · {r.location or "Location not listed"}</div>',unsafe_allow_html=True)
    m=history_matches.get(r.id)
    if m and m['match_type']=='possible':
     p=m['prior'];st.markdown(f'<div class="dup">⚠ Possible duplicate · Previously applied to <b>{p.get("title") or "another role"}</b> at {p.get("company",r.company)}</div>',unsafe_allow_html=True)
    cls='apply' if r.verdict=='APPLY' else 'strong' if r.verdict=='STRONG CONSIDER' else 'stretch' if r.verdict=='STRETCH' else 'skip';st.markdown(f'<span class="badge {cls}">{r.verdict}</span><span class="badge">{r.status}</span><span class="badge">{r.get("source") or "unknown"}</span>',unsafe_allow_html=True);x,y=st.columns([1,3])
    with x:
     if r.get('url'):st.link_button('Open Posting',r.url)
    with y:explain(r)
   with right:
    cur=r.status if r.status in statuses else 'new';new=st.selectbox('Status',statuses,index=statuses.index(cur),key=f's-{r.id}')
    if new!=r.status:update_status(int(r.id),new);st.rerun()
elif section=='🌐 Market Coverage':
 st.markdown('<div class="xp-section">🌐 Market Coverage</div>',unsafe_allow_html=True);live=pd.DataFrame(LIVE_REGISTRY['employers']);watch=pd.DataFrame(WATCHLIST['employers']);c1,c2,c3=st.columns(3);c1.metric('Connected Employers',len(live));c2.metric('Expansion Watchlist',len(watch));c3.metric('High Priority Gaps',int((watch.priority=='high').sum()));st.dataframe(live,width='stretch',hide_index=True);st.dataframe(watch,width='stretch',hide_index=True)
else:
 st.markdown('<div class="xp-section">📂 My Applications</div>',unsafe_allow_html=True);up=st.file_uploader('Import application history',type=['json'])
 if up:
  try:
   payload=json.loads(up.getvalue().decode());items=payload.get('applications',[]) if isinstance(payload,dict) else payload;save_history(HISTORY_PATH,[x for x in items if isinstance(x,dict)]);st.success('History imported.');st.rerun()
  except Exception as e:st.error(str(e))
 if history:st.dataframe(pd.DataFrame(history),width='stretch',hide_index=True)
 if not df.empty:
  handled=df[~df.status.isin(['new','saved'])];st.dataframe(handled,width='stretch',hide_index=True)
st.markdown('<div class="taskbar"><span class="start">🪟 start</span><span class="task-name">📁 Indy Opportunity Intelligence</span></div>',unsafe_allow_html=True)
