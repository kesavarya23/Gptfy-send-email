"""
Send email via Google Gmail API and Microsoft Graph (no SMTP app password).
"""
import base64
import logging
import os
from email.message import EmailMessage
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def get_google_user_email(access_token: str) -> str:
    r = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("email", "")


def get_microsoft_access_token(refresh_token: str) -> Optional[str]:
    try:
        from msal import ConfidentialClientApplication
    except ImportError:
        logger.error("msal is not installed")
        return None
    cid = os.getenv("MICROSOFT_CLIENT_ID", "")
    csec = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    tenant = os.getenv("MICROSOFT_TENANT", "common")
    if not (cid and csec and refresh_token):
        return None
    app_ms = ConfidentialClientApplication(
        cid, authority=f"https://login.microsoftonline.com/{tenant}", client_credential=csec
    )
    tr = app_ms.acquire_token_by_refresh_token(
        refresh_token, scopes=["https://graph.microsoft.com/Mail.Send", "https://graph.microsoft.com/User.Read"]
    )
    if "access_token" not in tr:
        logger.error("Microsoft token refresh failed: %s", tr)
        return None
    return tr["access_token"]


def get_microsoft_user_email(access_token: str) -> str:
    r = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if not r.ok:
        return ""
    d = r.json()
    return d.get("userPrincipalName") or d.get("mail") or d.get("email", "")


def send_gmail(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    from_addr: str,
    to: str,
    subject: str,
    plain: str,
    html: Optional[str] = None,
) -> bool:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token=None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )
    creds.refresh(Request())
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    msg = EmailMessage()
    msg["To"] = to
    msg["From"] = from_addr
    msg["Subject"] = subject
    if html:
        msg.set_content(plain, subtype="plain", charset="utf-8")
        msg.add_alternative(html, subtype="html", charset="utf-8")
    else:
        msg.set_content(plain, charset="utf-8")
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    try:
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception as e:
        logger.error("Gmail send failed: %s", e)
        return False


def send_outlook(access_token: str, to: str, subject: str, plain: str) -> bool:
    url = "https://graph.microsoft.com/v1.0/me/sendMail"
    body = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": plain},
            "toRecipients": [{"emailAddress": {"address": to}}],
        }
    }
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json=body,
        timeout=60,
    )
    if r.status_code not in (200, 202, 204):
        logger.error("Graph send failed: %s %s", r.status_code, r.text)
        return False
    return True
