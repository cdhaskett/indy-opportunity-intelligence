from __future__ import annotations

import html

import streamlit as st


def show_xp_loader(message: str = "Opening Opportunity Intelligence…"):
    """Render a lightweight XP-style animated loading card and return its placeholder."""
    placeholder = st.empty()
    safe_message = html.escape(message)
    placeholder.markdown(
        f"""
<style>
@keyframes oi-folder-bob {{
  0%, 100% {{ transform: translateY(0) rotate(-2deg); }}
  50% {{ transform: translateY(-5px) rotate(2deg); }}
}}
@keyframes oi-search-scan {{
  0% {{ transform: translate(-4px, 4px) rotate(-12deg); }}
  50% {{ transform: translate(14px, -2px) rotate(8deg); }}
  100% {{ transform: translate(-4px, 4px) rotate(-12deg); }}
}}
@keyframes oi-dot-pulse {{
  0%, 80%, 100% {{ opacity: .25; transform: translateY(0); }}
  40% {{ opacity: 1; transform: translateY(-2px); }}
}}
.oi-xp-loader {{
  display: flex;
  align-items: center;
  gap: .75rem;
  width: min(520px, 100%);
  box-sizing: border-box;
  margin: .35rem auto .55rem;
  padding: .62rem .78rem;
  background: #fffef5;
  border: 1px solid #7f9db9;
  border-top-color: #ffffff;
  border-left-color: #ffffff;
  box-shadow: 1px 1px 0 #777;
  color: #111;
  font-family: Tahoma, Arial, sans-serif;
}}
.oi-xp-loader-icons {{
  position: relative;
  width: 52px;
  height: 42px;
  flex: 0 0 52px;
}}
.oi-xp-loader-folder {{
  position: absolute;
  left: 2px;
  top: 5px;
  font-size: 29px;
  line-height: 1;
  animation: oi-folder-bob 1.15s ease-in-out infinite;
}}
.oi-xp-loader-search {{
  position: absolute;
  left: 24px;
  top: 14px;
  font-size: 20px;
  line-height: 1;
  animation: oi-search-scan 1.15s ease-in-out infinite;
}}
.oi-xp-loader-title {{
  color: #0b3d91;
  font-size: .84rem;
  font-weight: 700;
  margin-bottom: .12rem;
}}
.oi-xp-loader-message {{
  color: #333;
  font-size: .78rem;
}}
.oi-xp-loader-dots span {{
  display: inline-block;
  margin-left: 2px;
  color: #0a5bd8;
  font-weight: 700;
  animation: oi-dot-pulse 1.1s infinite ease-in-out;
}}
.oi-xp-loader-dots span:nth-child(2) {{ animation-delay: .14s; }}
.oi-xp-loader-dots span:nth-child(3) {{ animation-delay: .28s; }}
</style>
<div class="oi-xp-loader">
  <div class="oi-xp-loader-icons" aria-hidden="true">
    <span class="oi-xp-loader-folder">📁</span>
    <span class="oi-xp-loader-search">🔎</span>
  </div>
  <div>
    <div class="oi-xp-loader-title">Opportunity Intelligence</div>
    <div class="oi-xp-loader-message">{safe_message}<span class="oi-xp-loader-dots"><span>.</span><span>.</span><span>.</span></span></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    return placeholder
