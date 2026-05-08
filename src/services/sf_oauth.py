"""
Salesforce OAuth 2.0 Web Server flow: token exchange and refresh.
Uses the same session-backed pattern as Gmail / Outlook in app.py.

OAuth credentials (client id / secret / login url / redirect uri) are read
from the Flask session first (set via the in-app "Connect Salesforce Org"
setup page), and fall back to environment variables for backward compatibility.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Mapping, Optional, Tuple

import requests
from simple_salesforce import Salesforce

logger = logging.getLogger(__name__)

# Access tokens last ~2h in many orgs; refresh before typical expiry.
_ACCESS_TOKEN_MAX_AGE_SEC = 50 * 60

# Session keys for the per-user Connected App settings.
SESSION_KEY_CLIENT_ID = "sf_oauth_client_id"
SESSION_KEY_CLIENT_SECRET = "sf_oauth_client_secret"
SESSION_KEY_LOGIN_URL = "sf_oauth_login_url"
SESSION_KEY_REDIRECT_URI = "sf_oauth_redirect_uri"


def _clean(s: Optional[str]) -> str:
    return (s or "").strip()


def get_oauth_config(session: Optional[Mapping[str, Any]] = None) -> Dict[str, str]:
    """
    Resolve the Salesforce OAuth config used for authorize / token / refresh.

    Lookup order per field:
      1. Flask session (filled in via /salesforce/setup)
      2. Environment variable (legacy .env support)
      3. Sensible default for login_url

    Returns dict with: client_id, client_secret, login_url, redirect_uri.
    Empty strings indicate the field is not yet configured.
    """
    sess = session or {}
    client_id = _clean(sess.get(SESSION_KEY_CLIENT_ID)) or _clean(os.getenv("SALESFORCE_CLIENT_ID"))
    client_secret = _clean(sess.get(SESSION_KEY_CLIENT_SECRET)) or _clean(
        os.getenv("SALESFORCE_CLIENT_SECRET")
    )
    login_url = (
        _clean(sess.get(SESSION_KEY_LOGIN_URL))
        or _clean(os.getenv("SALESFORCE_LOGIN_URL"))
        or "https://login.salesforce.com"
    ).rstrip("/")
    redirect_uri = _clean(sess.get(SESSION_KEY_REDIRECT_URI)) or _clean(
        os.getenv("SALESFORCE_OAUTH_REDIRECT")
    )
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "login_url": login_url,
        "redirect_uri": redirect_uri,
    }


def store_oauth_config(
    session: dict,
    client_id: str,
    client_secret: str,
    login_url: str,
    redirect_uri: str = "",
) -> None:
    """Persist the user's Connected App settings on the Flask session."""
    session[SESSION_KEY_CLIENT_ID] = _clean(client_id)
    session[SESSION_KEY_CLIENT_SECRET] = _clean(client_secret)
    lu = _clean(login_url) or "https://login.salesforce.com"
    if not lu.startswith(("http://", "https://")):
        lu = "https://" + lu
    session[SESSION_KEY_LOGIN_URL] = lu.rstrip("/")
    if redirect_uri:
        session[SESSION_KEY_REDIRECT_URI] = _clean(redirect_uri)


def clear_oauth_config(session: dict) -> None:
    for k in (
        SESSION_KEY_CLIENT_ID,
        SESSION_KEY_CLIENT_SECRET,
        SESSION_KEY_LOGIN_URL,
        SESSION_KEY_REDIRECT_URI,
    ):
        session.pop(k, None)


def has_oauth_config(session: Optional[Mapping[str, Any]] = None) -> bool:
    cfg = get_oauth_config(session)
    return bool(cfg["client_id"] and cfg["client_secret"])


def salesforce_login_base(session: Optional[Mapping[str, Any]] = None) -> str:
    return get_oauth_config(session)["login_url"]


def salesforce_token_url(session: Optional[Mapping[str, Any]] = None) -> str:
    return salesforce_login_base(session) + "/services/oauth2/token"


def salesforce_authorize_url(session: Optional[Mapping[str, Any]] = None) -> str:
    return salesforce_login_base(session) + "/services/oauth2/authorize"


def exchange_code_for_tokens(
    code: str,
    redirect_uri: str,
    code_verifier: Optional[str] = None,
    session: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = get_oauth_config(session)
    if not (cfg["client_id"] and cfg["client_secret"]):
        raise RuntimeError("Salesforce OAuth client id/secret are not configured")
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri": redirect_uri,
    }
    if code_verifier:
        data["code_verifier"] = code_verifier
    r = requests.post(salesforce_token_url(session), data=data, timeout=45)
    if r.status_code != 200:
        logger.warning("Salesforce token exchange failed: %s %s", r.status_code, r.text[:500])
        raise RuntimeError("Salesforce token exchange failed")
    return r.json()


def refresh_access_token(
    refresh_token: str, session: Optional[Mapping[str, Any]] = None
) -> Dict[str, Any]:
    cfg = get_oauth_config(session)
    if not (cfg["client_id"] and cfg["client_secret"]):
        raise RuntimeError("Salesforce OAuth client id/secret are not configured")
    r = requests.post(
        salesforce_token_url(session),
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
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
            j = refresh_access_token(rt, session=session)
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
