from __future__ import annotations

import hashlib
from typing import Any

import streamlit as st


def auth_configured() -> bool:
    try:
        auth = st.secrets.get("auth", {})
    except Exception:
        return False
    return bool(auth)


def database_configured() -> bool:
    try:
        database = st.secrets.get("database", {})
    except Exception:
        return False
    return bool(database.get("url"))


def is_logged_in() -> bool:
    try:
        return bool(st.user.is_logged_in)
    except Exception:
        return False


def current_identity() -> dict[str, Any] | None:
    if not is_logged_in():
        return None
    try:
        claims = st.user.to_dict()
    except Exception:
        claims = dict(st.user)

    subject = str(claims.get("sub") or claims.get("email") or "").strip()
    issuer = str(claims.get("iss") or "streamlit-oidc").strip()
    if not subject:
        return None

    user_id = hashlib.sha256(f"{issuer}|{subject}".encode("utf-8")).hexdigest()
    return {
        "user_id": user_id,
        "subject": subject,
        "issuer": issuer,
        "email": str(claims.get("email") or claims.get("preferred_username") or "").strip(),
        "name": str(claims.get("name") or claims.get("given_name") or "").strip(),
        "claims": claims,
    }


def current_user_id() -> str | None:
    identity = current_identity()
    return identity["user_id"] if identity else None


def require_login() -> dict[str, Any]:
    if not auth_configured():
        st.error("Sign-in is not configured for this beta yet.")
        st.caption("The app owner needs to add the OIDC settings in Streamlit Secrets.")
        st.stop()

    if not is_logged_in():
        st.markdown("## 🪟 Opportunity Intelligence")
        st.write("Sign in to keep your job-search profile, application history, and statuses private.")
        if st.button("🔐 Sign in with Google", use_container_width=True):
            st.login()
        st.stop()

    identity = current_identity()
    if not identity:
        st.error("Your sign-in succeeded, but no stable user identifier was returned.")
        if st.button("Sign out"):
            st.logout()
        st.stop()
    return identity
