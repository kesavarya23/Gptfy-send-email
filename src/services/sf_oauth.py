"""
Salesforce OAuth 2.0 Web Server flow: token exchange and refresh.
Uses the same session-backed pattern as Gmail / Outlook in app.py.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

import requests
from simple_salesforce import Salesforce

logger = logging.getLogger(__name__)

# Access tokens last ~2h in many orgs; refresh before typical expiry.
_ACCESS_TOKEN_MAX_AGE_SEC = 50 * 60


def salesforce_login_base() -> str:
    return (os.getenv("SALESFORCE_LOGIN_URL") or "https://login.salesforce.com").rstrip("/")


def salesforce_token_url() -> str:
    return salesforce_login_base() + "/services/oauth2/token"


def salesforce_authorize_url() -> str:
    return salesforce_login_base() + "/services/oauth2/authorize"


def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
    cid = os.getenv("SALESFORCE_CLIENT_ID", "")
    cs = os.getenv("SALESFORCE_CLIENT_SECRET", "")
    r = requests.post(
        salesforce_token_url(),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": cid,
            "client_secret": cs,
            "redirect_uri": redirect_uri,
        },
        timeout=45,
    )
    if r.status_code != 200:
        logger.warning("Salesforce token exchange failed: %s %s", r.status_code, r.text[:500])
        raise RuntimeError("Salesforce token exchange failed")
    return r.json()


def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    cid = os.getenv("SALESFORCE_CLIENT_ID", "")
    cs = os.getenv("SALESFORCE_CLIENT_SECRET", "")
    r = requests.post(
        salesforce_token_url(),
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": cid,
            "client_secret": cs,
        },
        timeout=45,
    )
    if r.status_code != 200:
        logger.warning("Salesforce refresh failed: %s %s", r.status_code, r.text[:500])
        raise RuntimeError("Salesforce token refresh failed")
    return r.json()


def salesforce_client_from_token(instance_url: str, access_token: str) -> Salesforce:
    return Salesforce(instance_url=instance_url, session_id=access_token)


def session_apply_token_response(session: dict, j: Dict[str, Any]) -> None:
    """Write OAuth fields into Flask session dict (caller passes session)."""
    if j.get("access_token"):
        session["salesforce_access_token"] = j["access_token"]
        session["salesforce_token_at"] = time.time()
    if j.get("refresh_token"):
        session["salesforce_refresh_token"] = j["refresh_token"]
    if j.get("instance_url"):
        session["salesforce_instance_url"] = j["instance_url"]
    # Identity URL (same for refresh until reconnect)
    if j.get("id"):
        session["salesforce_identity_url"] = j["id"]


def fetch_identity(access_token: str, identity_url: str) -> Dict[str, Any]:
    """GET Salesforce identity for the authorized user (username, org id, display name)."""
    r = requests.get(
        identity_url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    if r.status_code != 200:
        logger.warning("Salesforce identity GET failed: %s", r.status_code)
        return {}
    return r.json() if r.content else {}


def enrich_session_from_identity(session: dict, access_token: str, identity_url: str) -> None:
    """Store username, org id, display name; optionally org record Name query."""
    session.pop("salesforce_org_name", None)
    ident = fetch_identity(access_token, identity_url)
    if not ident:
        return
    session["salesforce_username"] = ident.get("username") or ""
    session["salesforce_org_id"] = ident.get("organization_id") or ""
    session["salesforce_display_name"] = ident.get("display_name") or ""
    try:
        inst = (session.get("salesforce_instance_url") or "").rstrip("/")
        if inst and access_token:
            sf = salesforce_client_from_token(inst, access_token)
            q = sf.query("SELECT Name FROM Organization LIMIT 1")
            recs = q.get("records") or []
            if recs and recs[0].get("Name"):
                session["salesforce_org_name"] = recs[0]["Name"]
    except Exception as e:
        logger.info("Organization name query skipped: %s", e)


def ensure_salesforce_client(session: dict) -> Tuple[Optional[Salesforce], Optional[str]]:
    """
    Return (Salesforce client, error_message). Refreshes access token when stale.
    """
    rt = session.get("salesforce_refresh_token")
    inst = (session.get("salesforce_instance_url") or "").rstrip("/")
    at = session.get("salesforce_access_token")
    stored_at = float(session.get("salesforce_token_at") or 0)

    if not rt or not inst:
        return None, "Not connected to Salesforce. Use Connect Salesforce first."

    need_refresh = not at or (time.time() - stored_at > _ACCESS_TOKEN_MAX_AGE_SEC)
    if need_refresh:
        try:
            j = refresh_access_token(rt)
        except RuntimeError:
            return None, "Salesforce session expired. Connect Salesforce again."
        if not j.get("access_token"):
            return None, "Salesforce did not return an access token. Connect again."
        session_apply_token_response(session, j)
        at = session["salesforce_access_token"]
        inst = (session.get("salesforce_instance_url") or inst).rstrip("/")

    try:
        return salesforce_client_from_token(inst, at), None
    except Exception as e:
        logger.exception("Salesforce client init failed")
        return None, str(e)
