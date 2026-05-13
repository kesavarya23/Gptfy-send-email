"""
Send email via Google Gmail API and Microsoft Graph (no SMTP app password).
"""
import base64
import logging
import os
import re
import socket
import time
import uuid
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import requests

logger = logging.getLogger(__name__)


def generate_message_id(domain: Optional[str] = None) -> str:
    """Generate an RFC 5322 ``Message-ID`` we control.

    Setting our own ``Message-ID`` matters for the reply-testing flow: the
    contact mailbox replying back needs to set ``In-Reply-To`` to this exact
    value so the reply threads correctly in the original sender's inbox. We
    use the same value for outbound Gmail (which honours the MIME header
    directly) and as a custom ``X-Gptfy-Message-Id`` header for Outlook
    (since Graph generates its own internetMessageId).

    ``domain`` should be the sender's email domain when known. Gmail will
    rewrite a ``Message-ID`` whose host part does not match the sender's
    domain (or, in some cases, the receiving server will), and that rewrite
    silently breaks ``In-Reply-To`` matching for subsequent replies — which
    is why the first inbound reply doesn't thread with the original send.
    Passing the sender domain keeps the header intact end-to-end.
    """
    raw_host = (domain or socket.gethostname() or "gptfy.local").strip() or "gptfy.local"
    # Defensive: if a full email address slipped through, keep only the host.
    if "@" in raw_host:
        raw_host = raw_host.rsplit("@", 1)[-1].strip() or "gptfy.local"
    return f"<{uuid.uuid4().hex}.{int(time.time())}@{raw_host}>"


def get_google_user_email(access_token: str) -> str:
    info = get_google_user_info(access_token)
    return info.get("email", "")


def get_google_user_info(access_token: str) -> dict:
    """Return ``{'email', 'name', 'given_name', 'family_name'}`` for the user."""
    try:
        r = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
        r.raise_for_status()
        d = r.json() or {}
    except Exception as e:
        logger.warning("Google userinfo fetch failed: %s", e)
        return {}
    return {
        "email": d.get("email", ""),
        "name": d.get("name", ""),
        "given_name": d.get("given_name", ""),
        "family_name": d.get("family_name", ""),
    }


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
    info = get_microsoft_user_info(access_token)
    return info.get("email", "")


def get_microsoft_user_info(access_token: str) -> dict:
    """Return ``{'email', 'name', 'given_name', 'family_name'}`` for the user."""
    try:
        r = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
        if not r.ok:
            return {}
        d = r.json() or {}
    except Exception as e:
        logger.warning("Microsoft user fetch failed: %s", e)
        return {}
    return {
        "email": (
            d.get("userPrincipalName") or d.get("mail") or d.get("email", "")
        ),
        "name": d.get("displayName", ""),
        "given_name": d.get("givenName", ""),
        "family_name": d.get("surname", ""),
    }


def _addr_list(
    *parts: Optional[Union[str, Sequence[str]]]
) -> List[str]:
    out: List[str] = []
    for p in parts:
        if p is None:
            continue
        if isinstance(p, (list, tuple)):
            for x in p:
                # Pass `x` directly (not as a 1-tuple) so the recursive call
                # sees a string and exits via the else branch. Wrapping in
                # `(x,)` re-enters this same branch forever — RecursionError.
                out.extend(_addr_list(x))
        else:
            s = str(p).strip()
            if not s:
                continue
            for chunk in re.split(r"[\s,;]+", s.replace("\n", " ")):
                t = chunk.strip()
                if t:
                    out.append(t)
    return out


def send_gmail(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    from_addr: str,
    to: Union[str, List[str]],
    subject: str,
    plain: str,
    html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    *,
    message_id: Optional[str] = None,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
    thread_id: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Send a message via the Gmail API.

    Returns a dict ``{"success", "message_id", "thread_id", "in_reply_to",
    "references", "error"}`` so the caller can persist the threading
    metadata and verify the chain landed correctly. ``message_id`` is the
    *final* RFC Message-ID Gmail assigned (not the one we proposed) — see
    the polling logic below for why this matters for Workspace senders.

    When ``thread_id`` is supplied the API will append the message to that
    Gmail conversation; useful for reply-to-reply chains where the contact's
    mailbox already contains the original thread.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    result: Dict[str, Any] = {
        "success": False,
        "message_id": message_id or "",
        "thread_id": "",
        "in_reply_to": "",
        "references": "",
        "error": "",
    }

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )
    try:
        creds.refresh(Request())
    except Exception as e:  # noqa: BLE001
        result["error"] = f"Token refresh failed: {e}"
        return result
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    to_list = _addr_list(to)
    if not to_list:
        result["error"] = "No recipient addresses"
        return result
    cc = _addr_list(cc)
    bcc = _addr_list(bcc)
    msg = EmailMessage()
    msg["To"] = ", ".join(to_list)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg["From"] = from_addr
    msg["Subject"] = subject
    if message_id:
        msg["Message-ID"] = message_id
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    if extra_headers:
        for k, v in extra_headers.items():
            if not k or v is None:
                continue
            try:
                msg[k] = str(v)
            except Exception:  # noqa: BLE001
                pass
    if html:
        msg.set_content(plain, subtype="plain", charset="utf-8")
        msg.add_alternative(html, subtype="html", charset="utf-8")
    else:
        msg.set_content(plain, charset="utf-8")
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    body: Dict[str, Any] = {"raw": raw}
    if thread_id:
        body["threadId"] = thread_id
    try:
        resp = service.users().messages().send(userId="me", body=body).execute() or {}
        result["success"] = True
        result["thread_id"] = resp.get("threadId", "") or ""
        # ALWAYS read the actual Message-Id back from Gmail — even when we
        # pre-set it ourselves. Gmail rewrites the Message-Id of every
        # outbound message to its own ``@mail.gmail.com`` form. For regular
        # ``@gmail.com`` senders the rewrite happens BEFORE our read-back,
        # so a single ``messages.get`` is enough. For Google Workspace
        # senders (custom domains) the rewrite is deferred behind DKIM
        # signing / relay processing — an immediate read-back returns the
        # transient pre-rewrite value, which then becomes stale a moment
        # later. A stale ``message_id`` silently breaks ``In-Reply-To``
        # threading on every subsequent reply (recipient mailboxes look up
        # the value we claim and can't find it).
        #
        # We therefore POLL ``messages.get`` until the value stabilises in
        # Gmail's final ``@mail.gmail.com`` form (or we exhaust the budget).
        # We also capture ``In-Reply-To`` / ``References`` so the caller can
        # confirm the thread chain landed correctly without a Show-Original
        # round-trip in Gmail.
        if resp.get("id"):
            # Build the "values that would mean we read the WRONG message
            # back" set. Gmail has a documented stale-read race when a
            # ``messages.get`` lands immediately after a ``messages.send``
            # into an existing thread: the metadata index can briefly serve
            # the PARENT's headers under the new message's id. The only
            # reliable way to detect that case from here is to notice that
            # the returned Message-Id collides with a value the caller
            # already knew about (the In-Reply-To target, or anything the
            # References chain quotes) — those are guaranteed to be NOT
            # this new message's Message-Id.
            poison_mids = set()
            if in_reply_to:
                poison_mids.add(in_reply_to.strip())
            if references:
                for tok in str(references).split():
                    tok = tok.strip()
                    if tok:
                        poison_mids.add(tok)

            # Marker we'll use as a last-resort lookup if the indexed read
            # keeps returning a stale/poisoned value. Pulled from
            # ``extra_headers`` so the caller stays in control of which
            # custom header carries the unique id.
            marker_header_name = ""
            marker_header_value = ""
            for k, v in (extra_headers or {}).items():
                if not k or not v:
                    continue
                if k.lower().startswith("x-gptfy-"):
                    marker_header_name = k
                    marker_header_value = str(v)
                    break

            final_mid = ""
            final_irt = ""
            final_refs = ""

            # Schedule starts with a non-zero wait: Workspace's Sent-folder
            # commit is not instant, and on a thread append the metadata
            # index races the body. 0.8s is enough to clear the race in
            # practice while keeping the worst-case latency bounded.
            delays = (0.8, 1.0, 1.4, 2.0)
            for attempt, delay in enumerate(delays):
                time.sleep(delay)
                try:
                    msg_meta = (
                        service.users()
                        .messages()
                        .get(
                            userId="me",
                            id=resp["id"],
                            # ``full`` bypasses the metadata-only cache that
                            # caused the poisoned read above; we still only
                            # look at headers, so the extra payload bytes
                            # are negligible.
                            format="full",
                        )
                        .execute()
                        or {}
                    )
                except Exception as poll_err:  # noqa: BLE001
                    logger.warning(
                        "Gmail message read failed (attempt=%d delay=%ss): %s",
                        attempt, delay, poll_err,
                    )
                    continue

                cur_mid = ""
                cur_irt = ""
                cur_refs = ""
                for h in (msg_meta.get("payload") or {}).get("headers") or []:
                    name = (h.get("name") or "").lower()
                    value = h.get("value") or ""
                    if name == "message-id":
                        cur_mid = value
                    elif name == "in-reply-to":
                        cur_irt = value
                    elif name == "references":
                        cur_refs = value

                # Reject the read if it collides with a known parent — that
                # means we hit the stale-read race and need to wait longer.
                if cur_mid and cur_mid.strip() in poison_mids:
                    logger.warning(
                        "Gmail returned stale parent headers for new message "
                        "(attempt=%d, message_id=%s collides with In-Reply-To/References) — retrying",
                        attempt, cur_mid,
                    )
                    continue

                if cur_mid:
                    final_mid = cur_mid
                if cur_irt:
                    final_irt = cur_irt
                if cur_refs:
                    final_refs = cur_refs

                # Gmail's authoritative final form always uses the
                # ``@mail.gmail.com`` host. As soon as we see that AND it
                # doesn't collide with anything in the chain, we know
                # no more rewrites are coming and we can stop polling.
                if final_mid and "@mail.gmail.com" in final_mid.lower():
                    break

            # Last-resort fallback: if the indexed read kept giving us a
            # poisoned value, look the message up via our unique marker
            # header. ``messages.list`` with a full-text query for the
            # marker value will find the just-sent message regardless of
            # which read replica answers, then a fresh ``messages.get``
            # against THAT id returns the correct headers.
            if (not final_mid or final_mid.strip() in poison_mids) and marker_header_value:
                try:
                    list_resp = (
                        service.users()
                        .messages()
                        .list(
                            userId="me",
                            q=f'"{marker_header_value}" newer_than:1h',
                            maxResults=3,
                        )
                        .execute()
                        or {}
                    )
                    for cand in list_resp.get("messages") or []:
                        cand_id = cand.get("id") or ""
                        if not cand_id or cand_id == resp["id"]:
                            # Skip the poisoned-id read entirely; only
                            # trust matches from a different gmail-id
                            # because that proves the marker resolved to
                            # the right MIME body, not the racing index.
                            if cand_id == resp["id"]:
                                continue
                        try:
                            cand_meta = (
                                service.users()
                                .messages()
                                .get(userId="me", id=cand_id, format="full")
                                .execute()
                                or {}
                            )
                        except Exception:  # noqa: BLE001
                            continue
                        cand_mid = ""
                        cand_marker = ""
                        for h in (cand_meta.get("payload") or {}).get("headers") or []:
                            n = (h.get("name") or "").lower()
                            v = h.get("value") or ""
                            if n == "message-id":
                                cand_mid = v
                            elif n == marker_header_name.lower():
                                cand_marker = v
                        if cand_marker == marker_header_value and cand_mid \
                                and cand_mid.strip() not in poison_mids:
                            final_mid = cand_mid
                            logger.info(
                                "Recovered final Message-Id via marker fallback: %s",
                                final_mid,
                            )
                            break
                except Exception as marker_err:  # noqa: BLE001
                    logger.warning(
                        "Marker-based recovery failed: %s", marker_err,
                    )

            if final_mid and final_mid.strip() not in poison_mids:
                result["message_id"] = final_mid
            else:
                # Refuse to store a known-bad value. Better to leave the
                # field empty so the caller surfaces the failure than to
                # poison the DB and silently break threading downstream.
                logger.error(
                    "Could not capture a unique Message-Id for Gmail send "
                    "(polled=%s, poison=%s). Caller will see empty message_id.",
                    final_mid, sorted(poison_mids),
                )
                result["message_id"] = ""
                result["error"] = (
                    "Gmail returned poisoned/parent Message-Id for the new "
                    "message after polling+marker fallback — see logs."
                )
            result["in_reply_to"] = final_irt
            result["references"] = final_refs
            logger.info(
                "Gmail send finalised: from=%s message_id=%s in_reply_to=%s references=%s",
                from_addr, result["message_id"], final_irt, final_refs,
            )
            if result["message_id"] and "@mail.gmail.com" not in result["message_id"].lower():
                logger.warning(
                    "Gmail did not rewrite Message-Id to @mail.gmail.com after polling "
                    "(value=%s). Threading on inbound replies may break — investigate "
                    "Workspace DKIM / outbound relay config.",
                    result["message_id"],
                )
        return result
    except Exception as e:  # noqa: BLE001
        logger.error("Gmail send failed: %s", e)
        result["error"] = f"Gmail send failed: {e}"
        return result


def send_outlook(
    access_token: str,
    to: Union[str, List[str]],
    subject: str,
    plain: str,
    html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    *,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    capture_metadata: bool = False,
) -> Dict[str, Any]:
    """Send via Microsoft Graph.

    Returns a dict ``{"success", "message_id", "conversation_id", "error"}``.

    When ``capture_metadata`` is True we use the "create draft → send draft"
    pattern so we can read back the ``internetMessageId`` and
    ``conversationId`` that Graph assigned (Graph's ``/me/sendMail`` endpoint
    is fire-and-forget and doesn't return that). The capture path is what
    enables the reply-testing flow to thread inbound replies correctly.

    Falls back to the legacy ``sendMail`` path when ``capture_metadata`` is
    False so existing callers keep their fast send behaviour.

    To preserve backward compatibility with code that still does
    ``if send_outlook(...): ...``, the returned dict is truthy on success
    via ``__bool__`` semantics — we also keep ``send_outlook.last_error``
    populated for older callers that read it directly.
    """
    send_outlook.last_error = ""  # type: ignore[attr-defined]
    result: Dict[str, Any] = {
        "success": False,
        "message_id": "",
        "conversation_id": "",
        "error": "",
    }
    to_list = _addr_list(to)
    if not to_list:
        result["error"] = "No recipient addresses"
        send_outlook.last_error = result["error"]  # type: ignore[attr-defined]
        return result
    cc = _addr_list(cc)
    bcc = _addr_list(bcc)
    use_html = bool(html and str(html).strip())
    message: Dict[str, Any] = {
        "subject": subject,
        "body": {
            "contentType": "HTML" if use_html else "Text",
            "content": (html if use_html else plain) or plain,
        },
        "toRecipients": [{"emailAddress": {"address": a}} for a in to_list],
    }
    if cc:
        message["ccRecipients"] = [{"emailAddress": {"address": a}} for a in cc]
    if bcc:
        message["bccRecipients"] = [{"emailAddress": {"address": a}} for a in bcc]

    # Custom MIME headers (must each start with "x-" per Graph contract; up to 5).
    headers_list = []
    if extra_headers:
        for k, v in extra_headers.items():
            if not k or v is None:
                continue
            name = str(k).strip()
            if not name.lower().startswith("x-"):
                continue
            headers_list.append({"name": name, "value": str(v)})
    # In-Reply-To / References cannot be expressed via internetMessageHeaders
    # (Graph reserves those names) — for replies from an Outlook contact we
    # use the dedicated /reply endpoint elsewhere. We still propagate them
    # as ``x-in-reply-to`` / ``x-references`` so the recipient mailbox at
    # least has a marker if the reply isn't going through Graph's reply API.
    if in_reply_to:
        headers_list.append({"name": "x-in-reply-to", "value": in_reply_to})
    if references:
        headers_list.append({"name": "x-references", "value": references})
    if headers_list:
        message["internetMessageHeaders"] = headers_list[:5]

    hdr = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    if not capture_metadata:
        # Fast path: fire-and-forget sendMail.
        try:
            r = requests.post(
                "https://graph.microsoft.com/v1.0/me/sendMail",
                headers=hdr,
                json={"message": message},
                timeout=60,
            )
        except requests.RequestException as e:
            result["error"] = f"network: {e}"
            send_outlook.last_error = result["error"]  # type: ignore[attr-defined]
            logger.error("Graph send network error: %s", e)
            return result
        if r.status_code not in (200, 202, 204):
            result["error"] = f"HTTP {r.status_code}: {r.text}"
            send_outlook.last_error = result["error"]  # type: ignore[attr-defined]
            logger.error("Graph send failed: %s %s", r.status_code, r.text)
            return result
        result["success"] = True
        return result

    # Capture path: create draft, read internetMessageId/conversationId, send draft.
    try:
        r = requests.post(
            "https://graph.microsoft.com/v1.0/me/messages",
            headers=hdr,
            json=message,
            timeout=60,
        )
    except requests.RequestException as e:
        result["error"] = f"network creating draft: {e}"
        send_outlook.last_error = result["error"]  # type: ignore[attr-defined]
        logger.error("Graph create draft network error: %s", e)
        return result
    # Graceful degradation: if the connected mailbox only granted Mail.Send
    # (e.g. token was issued before we widened the scope to Mail.ReadWrite),
    # POST /me/messages returns 403 ErrorAccessDenied. Fall back to the
    # fire-and-forget sendMail endpoint so the email still goes out — we
    # just won't be able to thread inbound replies for THIS particular
    # message until the user disconnects and reconnects Outlook to grant
    # the wider scope.
    if r.status_code == 403:
        logger.warning(
            "Graph create-draft returned 403 (likely missing Mail.ReadWrite). "
            "Falling back to sendMail without metadata capture."
        )
        try:
            f = requests.post(
                "https://graph.microsoft.com/v1.0/me/sendMail",
                headers=hdr,
                json={"message": message},
                timeout=60,
            )
        except requests.RequestException as e:
            result["error"] = f"network fallback sendMail: {e}"
            send_outlook.last_error = result["error"]  # type: ignore[attr-defined]
            return result
        if f.status_code not in (200, 202, 204):
            result["error"] = (
                f"create draft 403 (needs Mail.ReadWrite) and sendMail fallback "
                f"HTTP {f.status_code}: {f.text}"
            )
            send_outlook.last_error = result["error"]  # type: ignore[attr-defined]
            return result
        result["success"] = True
        # We don't populate message_id / conversation_id here — the caller
        # will simply have nothing to thread an inbound reply against on
        # this particular message. Surfacing this nicely in the UI is the
        # /api/get_reply endpoint's job (it returns "Original Message-Id
        # missing — reconnect Outlook to grant Mail.ReadWrite").
        return result
    if r.status_code not in (200, 201):
        result["error"] = f"create draft HTTP {r.status_code}: {r.text}"
        send_outlook.last_error = result["error"]  # type: ignore[attr-defined]
        logger.error("Graph create draft failed: %s %s", r.status_code, r.text)
        return result
    draft = r.json() or {}
    draft_id = draft.get("id") or ""
    result["message_id"] = draft.get("internetMessageId") or ""
    result["conversation_id"] = draft.get("conversationId") or ""
    if not draft_id:
        result["error"] = "Graph returned no draft id"
        send_outlook.last_error = result["error"]  # type: ignore[attr-defined]
        return result
    try:
        s = requests.post(
            f"https://graph.microsoft.com/v1.0/me/messages/{draft_id}/send",
            headers=hdr,
            timeout=60,
        )
    except requests.RequestException as e:
        result["error"] = f"network sending draft: {e}"
        send_outlook.last_error = result["error"]  # type: ignore[attr-defined]
        logger.error("Graph send draft network error: %s", e)
        return result
    if s.status_code not in (200, 202, 204):
        result["error"] = f"send draft HTTP {s.status_code}: {s.text}"
        send_outlook.last_error = result["error"]  # type: ignore[attr-defined]
        logger.error("Graph send draft failed: %s %s", s.status_code, s.text)
        return result
    result["success"] = True
    return result


send_outlook.last_error = ""  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Reply senders — used by /api/get_reply
# ---------------------------------------------------------------------------


def find_outlook_message_by_internet_id(
    access_token: str, internet_message_id: str
) -> Optional[Dict[str, Any]]:
    """Look up a message in the connected mailbox by its RFC Message-Id.

    Used so an Outlook contact mailbox can find the original we sent and
    reply via Graph's ``/reply`` endpoint (which auto-handles threading).
    Returns ``None`` if not found / on error.
    """
    if not (access_token and internet_message_id):
        return None
    try:
        r = requests.get(
            "https://graph.microsoft.com/v1.0/me/messages",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "$filter": f"internetMessageId eq '{internet_message_id}'",
                "$select": "id,subject,conversationId,internetMessageId",
                "$top": "1",
            },
            timeout=30,
        )
    except requests.RequestException as e:
        logger.warning("Graph lookup network error: %s", e)
        return None
    if r.status_code != 200:
        logger.warning("Graph lookup failed: %s %s", r.status_code, r.text[:200])
        return None
    items = (r.json() or {}).get("value") or []
    return items[0] if items else None


def reply_outlook(
    access_token: str,
    *,
    original_internet_message_id: str,
    reply_body_plain: str,
    reply_body_html: Optional[str] = None,
    additional_to: Optional[List[str]] = None,
    additional_cc: Optional[List[str]] = None,
    reply_all: bool = False,
) -> Dict[str, Any]:
    """Send a reply from a contact's Outlook mailbox.

    Looks up the original message by ``internetMessageId`` and then uses
    Graph's ``/createReply`` (or ``/createReplyAll``) to seed a draft with
    the right recipient list + threading metadata, patches the body, and
    sends. This is much more reliable than building the MIME ourselves
    because Graph won't let us set ``In-Reply-To`` directly.
    """
    result: Dict[str, Any] = {
        "success": False,
        "message_id": "",
        "conversation_id": "",
        "error": "",
    }
    if not access_token:
        result["error"] = "No access token"
        return result
    original = find_outlook_message_by_internet_id(
        access_token, original_internet_message_id
    )
    if not original:
        result["error"] = (
            "Original message not found in contact's Outlook mailbox "
            "(internetMessageId not visible — Graph may have stripped it)."
        )
        return result
    msg_id = original.get("id") or ""
    if not msg_id:
        result["error"] = "Original message missing Graph id"
        return result

    use_html = bool(reply_body_html and str(reply_body_html).strip())
    hdr = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    endpoint = "createReplyAll" if reply_all else "createReply"
    try:
        r = requests.post(
            f"https://graph.microsoft.com/v1.0/me/messages/{msg_id}/{endpoint}",
            headers=hdr,
            json={},
            timeout=30,
        )
    except requests.RequestException as e:
        result["error"] = f"network creating reply draft: {e}"
        return result
    if r.status_code not in (200, 201):
        result["error"] = f"createReply HTTP {r.status_code}: {r.text}"
        return result
    draft = r.json() or {}
    draft_id = draft.get("id") or ""
    if not draft_id:
        result["error"] = "Graph returned no reply draft id"
        return result
    result["conversation_id"] = draft.get("conversationId") or ""

    patch: Dict[str, Any] = {
        "body": {
            "contentType": "HTML" if use_html else "Text",
            "content": (reply_body_html if use_html else reply_body_plain) or reply_body_plain,
        }
    }
    extra_to = [a for a in (additional_to or []) if a]
    extra_cc = [a for a in (additional_cc or []) if a]
    if extra_to:
        patch["toRecipients"] = [
            {"emailAddress": {"address": a}} for a in extra_to
        ]
    if extra_cc:
        patch["ccRecipients"] = [
            {"emailAddress": {"address": a}} for a in extra_cc
        ]
    try:
        p = requests.patch(
            f"https://graph.microsoft.com/v1.0/me/messages/{draft_id}",
            headers=hdr,
            json=patch,
            timeout=30,
        )
    except requests.RequestException as e:
        result["error"] = f"network patching reply: {e}"
        return result
    if p.status_code not in (200, 204):
        result["error"] = f"patch reply HTTP {p.status_code}: {p.text}"
        return result

    if p.status_code == 200:
        patched = p.json() or {}
        result["message_id"] = patched.get("internetMessageId") or ""
        result["conversation_id"] = (
            patched.get("conversationId") or result["conversation_id"]
        )
    else:
        try:
            g = requests.get(
                f"https://graph.microsoft.com/v1.0/me/messages/{draft_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"$select": "internetMessageId,conversationId"},
                timeout=15,
            )
            if g.status_code == 200:
                gd = g.json() or {}
                result["message_id"] = gd.get("internetMessageId") or ""
                result["conversation_id"] = (
                    gd.get("conversationId") or result["conversation_id"]
                )
        except requests.RequestException:
            pass

    try:
        s = requests.post(
            f"https://graph.microsoft.com/v1.0/me/messages/{draft_id}/send",
            headers=hdr,
            timeout=30,
        )
    except requests.RequestException as e:
        result["error"] = f"network sending reply: {e}"
        return result
    if s.status_code not in (200, 202, 204):
        result["error"] = f"send reply HTTP {s.status_code}: {s.text}"
        return result
    result["success"] = True
    return result


def find_gmail_thread_id_by_message_id(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    rfc_message_id: str,
) -> Tuple[str, str]:
    """Search the connected Gmail mailbox for a message by its RFC Message-Id.

    Returns ``(gmail_message_id, thread_id)`` or ``("", "")`` if not found.
    The Gmail API supports the ``rfc822msgid:`` operator for this; we use it
    so a Gmail-based contact can pin their reply to the right Gmail thread
    via ``threadId`` (which is per-mailbox).
    """
    if not rfc_message_id:
        return "", ""
    try:
        service = _build_gmail_service(client_id, client_secret, refresh_token)
        bare = rfc_message_id.strip().lstrip("<").rstrip(">")
        query = f"rfc822msgid:{bare}"
        resp = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=1)
            .execute()
            or {}
        )
        msgs = resp.get("messages") or []
        if not msgs:
            return "", ""
        m = msgs[0]
        return m.get("id") or "", m.get("threadId") or ""
    except Exception as e:  # noqa: BLE001
        logger.warning("Gmail thread lookup failed: %s", e)
        return "", ""


def _build_gmail_service(client_id: str, client_secret: str, refresh_token: str):
    """Build an authenticated Gmail API client (refreshing the token first)."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )
    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def locate_gmail_message_for_reply(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    *,
    rfc_message_id: str,
    sender_email: str = "",
    subject: str = "",
) -> Dict[str, str]:
    """Self-healing lookup for the parent message in a contact's Gmail.

    Returns ``{"gmail_id", "thread_id", "actual_message_id"}``.

    Order of attempts:
      1. ``rfc822msgid:`` for the stored Message-Id (fast, exact).
      2. ``from:<sender> subject:"<subject>" newer_than:30d`` fallback —
         needed when the stored Message-Id is stale because Gmail did a
         delayed rewrite to its ``@mail.gmail.com`` form on the original
         send (a Workspace-sender quirk we can't avoid; we patch it on the
         send path going forward, but this fallback rescues older rows).

    ``actual_message_id`` is the Message-Id Gmail currently has on the
    located copy — caller should backfill any stale DB row with this value
    so future lookups are O(1) again.
    """
    out = {"gmail_id": "", "thread_id": "", "actual_message_id": ""}
    if not refresh_token:
        return out
    try:
        service = _build_gmail_service(client_id, client_secret, refresh_token)
    except Exception as e:  # noqa: BLE001
        logger.warning("Gmail service build failed: %s", e)
        return out

    candidate_id = ""
    candidate_thread = ""

    if rfc_message_id:
        bare = rfc_message_id.strip().lstrip("<").rstrip(">")
        try:
            resp = (
                service.users()
                .messages()
                .list(userId="me", q=f"rfc822msgid:{bare}", maxResults=1)
                .execute()
                or {}
            )
            msgs = resp.get("messages") or []
            if msgs:
                candidate_id = msgs[0].get("id") or ""
                candidate_thread = msgs[0].get("threadId") or ""
        except Exception as e:  # noqa: BLE001
            logger.warning("Gmail rfc822msgid lookup failed: %s", e)

    if not candidate_id and (sender_email or subject):
        # Quote the subject so spaces / colons don't get split into
        # separate Gmail search terms. Strip Re:/Fwd: so we match the
        # original even when our caller passed the reply subject.
        clean_subject = (subject or "").strip()
        for prefix in ("re:", "fwd:", "fw:"):
            while clean_subject.lower().startswith(prefix):
                clean_subject = clean_subject[len(prefix):].lstrip()
        parts = []
        if sender_email:
            parts.append(f"from:{sender_email}")
        if clean_subject:
            escaped = clean_subject.replace('"', "")
            parts.append(f'subject:"{escaped}"')
        parts.append("newer_than:30d")
        q = " ".join(parts)
        try:
            resp = (
                service.users()
                .messages()
                .list(userId="me", q=q, maxResults=5)
                .execute()
                or {}
            )
            msgs = resp.get("messages") or []
            if msgs:
                # Prefer the oldest matching message — that's the original,
                # not a later reply that happens to share the subject.
                candidate_id = (msgs[-1] or {}).get("id") or ""
                candidate_thread = (msgs[-1] or {}).get("threadId") or ""
        except Exception as e:  # noqa: BLE001
            logger.warning("Gmail subject/sender fallback lookup failed: %s", e)

    if not candidate_id:
        return out

    out["gmail_id"] = candidate_id
    out["thread_id"] = candidate_thread

    # Read the *current* Message-Id of the located copy. This is the value
    # the recipient mailbox actually has, and therefore the value we MUST
    # quote in In-Reply-To / References for threading to work.
    try:
        meta = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=candidate_id,
                format="metadata",
                metadataHeaders=["Message-Id"],
            )
            .execute()
            or {}
        )
        for h in (meta.get("payload") or {}).get("headers") or []:
            if (h.get("name") or "").lower() == "message-id":
                out["actual_message_id"] = h.get("value") or ""
                break
    except Exception as e:  # noqa: BLE001
        logger.warning("Gmail message metadata read for backfill failed: %s", e)

    return out


