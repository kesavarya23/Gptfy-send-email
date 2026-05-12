"""
Thin Postgres wrapper (Neon) for the reply-testing feature.

Persists three things the rest of the app needs:
  * ``reply_mailboxes`` — OAuth refresh tokens for each test-contact mailbox
    that has been onboarded, keyed by email address.
  * ``sends`` + ``send_recipients`` — one row per outgoing message so that
    later the "Get reply" UI can look up the original subject, message-id
    and recipient list.
  * ``replies`` — one row per AI-generated reply that we fired from a
    contact's mailbox, including ``parent_reply_id`` for multi-turn chains.

The connection string lives in the ``DATABASE_URL`` env var. When it is
absent the helpers degrade to no-ops + ``None`` so the rest of the app
keeps working — the reply-testing feature simply turns off.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # noqa: BLE001
    psycopg = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]


def is_db_enabled() -> bool:
    """True when ``DATABASE_URL`` is set and the driver imported successfully."""
    return bool(psycopg is not None and (os.getenv("DATABASE_URL") or "").strip())


@contextmanager
def _conn():
    """Yield a short-lived autocommit connection.

    We open per-call rather than holding a long-lived pool because the app
    is targeted at Vercel serverless — each request is a fresh process and a
    pool wouldn't survive anyway. Neon's connection pooler endpoint handles
    the actual pool on the server side.
    """
    if not is_db_enabled():
        raise RuntimeError("DATABASE_URL is not configured")
    url = os.getenv("DATABASE_URL", "")
    conn = psycopg.connect(url, autocommit=True, row_factory=dict_row)  # type: ignore[arg-type]
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# reply_mailboxes
# ---------------------------------------------------------------------------


def upsert_reply_mailbox(
    *,
    email: str,
    provider: str,
    refresh_token: str,
    scopes: str = "",
    display_name: str = "",
) -> bool:
    """Insert or update a contact mailbox's OAuth refresh token."""
    if not is_db_enabled():
        logger.warning("DATABASE_URL not set — reply mailbox not persisted")
        return False
    if not (email and provider and refresh_token):
        return False
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reply_mailboxes
                    (email, provider, refresh_token, scopes, display_name, connected_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (email) DO UPDATE SET
                    provider = EXCLUDED.provider,
                    refresh_token = EXCLUDED.refresh_token,
                    scopes = EXCLUDED.scopes,
                    display_name = COALESCE(NULLIF(EXCLUDED.display_name, ''), reply_mailboxes.display_name),
                    connected_at = NOW()
                """,
                (email.lower().strip(), provider, refresh_token, scopes, display_name),
            )
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("upsert_reply_mailbox failed: %s", e)
        return False


def get_reply_mailbox(email: str) -> Optional[Dict[str, Any]]:
    if not is_db_enabled() or not email:
        return None
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                "SELECT email, provider, refresh_token, scopes, display_name, connected_at, last_used_at FROM reply_mailboxes WHERE email = %s",
                (email.lower().strip(),),
            )
            return cur.fetchone()
    except Exception as e:  # noqa: BLE001
        logger.error("get_reply_mailbox failed: %s", e)
        return None


def list_reply_mailboxes() -> List[Dict[str, Any]]:
    if not is_db_enabled():
        return []
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                "SELECT email, provider, display_name, connected_at, last_used_at FROM reply_mailboxes ORDER BY connected_at DESC"
            )
            return list(cur.fetchall() or [])
    except Exception as e:  # noqa: BLE001
        logger.error("list_reply_mailboxes failed: %s", e)
        return []


def delete_reply_mailbox(email: str) -> bool:
    if not is_db_enabled() or not email:
        return False
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                "DELETE FROM reply_mailboxes WHERE email = %s",
                (email.lower().strip(),),
            )
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("delete_reply_mailbox failed: %s", e)
        return False


def mark_reply_mailbox_used(email: str) -> None:
    if not is_db_enabled() or not email:
        return
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                "UPDATE reply_mailboxes SET last_used_at = NOW() WHERE email = %s",
                (email.lower().strip(),),
            )
    except Exception as e:  # noqa: BLE001
        logger.error("mark_reply_mailbox_used failed: %s", e)


# ---------------------------------------------------------------------------
# sends + send_recipients
# ---------------------------------------------------------------------------


def record_send(
    *,
    send_id: str,
    sender_email: str,
    sender_provider: str,
    subject: str,
    body_plain: str,
    body_html: str,
    message_id: str,
    thread_id: str = "",
    conversation_id: str = "",
    recipients: Iterable[Tuple[str, str]] = (),
) -> bool:
    """Persist one outgoing message + its recipients.

    ``recipients`` is an iterable of ``(email, role)`` tuples where role is
    one of ``'to' | 'cc' | 'bcc'``.
    """
    if not is_db_enabled():
        return False
    if not send_id or not sender_email:
        return False
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sends
                    (send_id, sender_email, sender_provider, subject, body_plain,
                     body_html, message_id, thread_id, conversation_id, sent_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (send_id) DO NOTHING
                """,
                (
                    send_id,
                    sender_email.lower().strip(),
                    sender_provider,
                    subject[:2000],
                    body_plain[:64000],
                    body_html[:200000] if body_html else "",
                    message_id,
                    thread_id or "",
                    conversation_id or "",
                ),
            )
            seen = set()
            for email, role in recipients:
                e = (email or "").strip().lower()
                r = (role or "").strip().lower()
                if not e or r not in ("to", "cc", "bcc"):
                    continue
                key = (e, r)
                if key in seen:
                    continue
                seen.add(key)
                cur.execute(
                    "INSERT INTO send_recipients (send_id, email, role) VALUES (%s, %s, %s)",
                    (send_id, e, r),
                )
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("record_send failed: %s", e)
        return False


def get_send(send_id: str) -> Optional[Dict[str, Any]]:
    """Return the full send record + recipients, or ``None`` if not found."""
    if not is_db_enabled() or not send_id:
        return None
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                "SELECT * FROM sends WHERE send_id = %s",
                (send_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            cur.execute(
                "SELECT email, role FROM send_recipients WHERE send_id = %s",
                (send_id,),
            )
            row["recipients"] = list(cur.fetchall() or [])
        return row
    except Exception as e:  # noqa: BLE001
        logger.error("get_send failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# replies
# ---------------------------------------------------------------------------


def record_reply(
    *,
    reply_id: str,
    send_id: str,
    replier_email: str,
    mode: str,
    intent: str,
    subject: str,
    body_plain: str,
    message_id: str,
    to_emails: str,
    cc_emails: str,
    parent_reply_id: Optional[str] = None,
    status: str = "sent",
    error: str = "",
) -> bool:
    if not is_db_enabled():
        return False
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO replies
                    (reply_id, send_id, parent_reply_id, replier_email, mode, intent,
                     subject, body_plain, message_id, to_emails, cc_emails, sent_at,
                     status, error)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
                """,
                (
                    reply_id,
                    send_id,
                    parent_reply_id,
                    replier_email.lower().strip(),
                    mode,
                    intent,
                    subject[:2000],
                    body_plain[:64000],
                    message_id,
                    to_emails,
                    cc_emails,
                    status,
                    error[:2000] if error else "",
                ),
            )
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("record_reply failed: %s", e)
        return False


def get_reply(reply_id: str) -> Optional[Dict[str, Any]]:
    if not is_db_enabled() or not reply_id:
        return None
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute("SELECT * FROM replies WHERE reply_id = %s", (reply_id,))
            return cur.fetchone()
    except Exception as e:  # noqa: BLE001
        logger.error("get_reply failed: %s", e)
        return None


def list_replies_for_send(send_id: str) -> List[Dict[str, Any]]:
    if not is_db_enabled() or not send_id:
        return []
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                "SELECT reply_id, send_id, parent_reply_id, replier_email, mode, intent, subject, body_plain, message_id, sent_at, status, error FROM replies WHERE send_id = %s ORDER BY sent_at ASC",
                (send_id,),
            )
            return list(cur.fetchall() or [])
    except Exception as e:  # noqa: BLE001
        logger.error("list_replies_for_send failed: %s", e)
        return []
