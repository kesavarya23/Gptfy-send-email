"""
AI email writer (OpenAI).

When OPENAI_API_KEY is configured, every outgoing email's subject and body are
written by the LLM, using the Salesforce account / opportunity / case context
supplied in the UI. If the key is missing or the API call fails for any reason,
``compose_email`` returns ``None`` so the caller can fall back to legacy
template-based generation.
"""

from __future__ import annotations

import html
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_TEMPERATURE = 0.4
_DEFAULT_TIMEOUT = 30
_MAX_PARAGRAPHS = 6
_MAX_PARAGRAPH_LEN = 1200
_MAX_SUBJECT_LEN = 200
_MAX_CUSTOM_PROMPT_LEN = 16000

# Default location: <project_root>/prompts/email_system_prompt.md
# (project_root = parent of /src)
_DEFAULT_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "email_system_prompt.md"
)


def _custom_system_prompt_path() -> Path:
    """Path to the editable system-prompt file. Override with $EMAIL_SYSTEM_PROMPT_PATH."""
    env_path = (os.getenv("EMAIL_SYSTEM_PROMPT_PATH") or "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    return _DEFAULT_PROMPT_PATH


def _load_custom_system_prompt() -> str:
    """
    Read the team-editable system prompt fresh on every call so edits take
    effect without restarting the server. Returns '' if the file is missing
    or contains only the default template instructions.
    """
    path = _custom_system_prompt_path()
    try:
        if not path.is_file():
            return ""
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.warning("Could not read custom system prompt at %s: %s", path, e)
        return ""

    # The default template ships with a "Replace everything below this line"
    # marker; if the user only edited the part below it, take that part.
    marker = "Replace everything below this line with your own system prompt."
    if marker in text:
        text = text.split(marker, 1)[1]
        text = text.lstrip("\n -")

    text = text.strip()
    if not text:
        return ""
    if len(text) > _MAX_CUSTOM_PROMPT_LEN:
        text = text[: _MAX_CUSTOM_PROMPT_LEN - 1].rstrip() + "…"
    return text


def is_ai_enabled() -> bool:
    """True when an OpenAI API key is configured."""
    return bool((os.getenv("OPENAI_API_KEY") or "").strip())


def _get_client():
    """Lazily import + construct the OpenAI client. Returns None if unusable."""
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        logger.warning(
            "openai package not installed — install with `pip install openai`"
        )
        return None
    try:
        timeout = float(os.getenv("OPENAI_TIMEOUT") or _DEFAULT_TIMEOUT)
    except (TypeError, ValueError):
        timeout = _DEFAULT_TIMEOUT
    try:
        return OpenAI(api_key=api_key, timeout=timeout)
    except Exception as e:
        logger.warning("Failed to construct OpenAI client: %s", e)
        return None


def _model() -> str:
    return (os.getenv("OPENAI_MODEL") or _DEFAULT_MODEL).strip() or _DEFAULT_MODEL


def _temperature() -> float:
    raw = (os.getenv("OPENAI_TEMPERATURE") or "").strip()
    if not raw:
        return _DEFAULT_TEMPERATURE
    try:
        return max(0.0, min(2.0, float(raw)))
    except ValueError:
        return _DEFAULT_TEMPERATURE


def _name_from_email(addr: str) -> str:
    """Best-effort first-name guess from an email like 'jane.doe@acme.com'.

    Returns '' when the local-part doesn't look like a real name (contains
    digits, is too short, etc.) so the caller can fall back to a generic
    greeting like 'Hi there,' instead of producing 'Hi Kesavcbe23,'.
    """
    a = (addr or "").strip()
    if "@" not in a:
        return ""
    local = a.split("@", 1)[0].split("+", 1)[0]
    parts = [p for p in local.replace("_", ".").replace("-", ".").split(".") if p]
    if not parts:
        return ""
    first = parts[0]
    if not first.isalpha() or len(first) < 2:
        return ""
    return first[:1].upper() + first[1:].lower()


def _format_dict_block(label: str, d: Dict[str, Any]) -> str:
    if not d:
        return ""
    lines = [f"{label}:"]
    for k, v in d.items():
        if v in (None, "", [], {}):
            continue
        if isinstance(v, (list, dict)):
            try:
                v = json.dumps(v, default=str)[:1500]
            except (TypeError, ValueError):
                v = str(v)[:1500]
        else:
            v = str(v)[:1500]
        lines.append(f"  - {k}: {v}")
    return "\n".join(lines) if len(lines) > 1 else ""


_PURPOSE_LABELS = {
    "meeting_invitation": "an invitation to a working meeting",
    "followup": "a polite follow-up after a previous interaction",
    "thank_you": "a sincere thank-you note",
    "project_update": "a clear project status update",
    "reminder": "a friendly reminder about a pending item",
    "trial_feedback": "a check-in regarding a product trial",
    "product_queries": "a response to product-related questions",
    "product_issues": "an update on reported product issues",
    "demo_enquiry": "a response to a product demo enquiry",
    "opportunity": "a Salesforce opportunity update tied to a real deal",
    "case": "a Salesforce case update keeping the customer informed",
}


def _build_messages(
    *,
    purpose: str,
    sender_name: str,
    recipient_name: str,
    subject_seed: str,
    user_message: str,
    account_name: str,
    account_details: str,
    opportunity_text: str,
    structured_record: Dict[str, Any],
    extra_notes: str,
    tone: str,
) -> List[Dict[str, str]]:
    purpose_label = _PURPOSE_LABELS.get(purpose, "a professional business email")

    base_system = (
        "You are an experienced B2B account executive who writes short, high-signal "
        "client emails. Hard rules you ALWAYS follow:\n"
        "1. Use ONLY the facts you are given. Never invent prices, dates, names, "
        "products, partnerships, or quotes.\n"
        "2. Output STRICTLY valid JSON with this exact shape:\n"
        '   {"subject": "string", "paragraphs": ["string", "string", ...]}\n'
        "3. The subject must be specific (<= 80 chars) and avoid clickbait or ALL CAPS.\n"
        "4. Each item in 'paragraphs' is one paragraph of the email body. The app will "
        "render them as separate paragraphs in the email.\n\n"
        "Soft defaults (overridable by the team system prompt below if one is present):\n"
        "- 3 to 5 short paragraphs, 2 to 4 sentences each.\n"
        "- You may include a greeting in the first paragraph (e.g. 'Hi Jane,') and a "
        "  sign-off in the last paragraph (e.g. 'Best regards,\\nKesav') if it improves "
        "  realism. The app auto-detects them and will not duplicate.\n"
        "- If a Salesforce opportunity is provided, ground the email in its specifics."
    )

    custom = _load_custom_system_prompt()
    if custom:
        system = (
            base_system
            + "\n\n"
            + "----- TEAM SYSTEM PROMPT (project-specific brand voice & rules) -----\n"
            + custom
            + "\n"
            + "----- END TEAM SYSTEM PROMPT -----\n"
            + "Conflict resolution: hard rules 1 to 4 above are absolute (factual accuracy + "
            + "parseable JSON output). EVERYTHING ELSE — voice, tone, structure, length, "
            + "greeting/sign-off style, taboos, examples — defers to the team system prompt."
        )
    else:
        system = base_system

    sections: List[str] = []
    sections.append(f"Email purpose: {purpose_label}.")
    sections.append(f"Tone: {tone}.")
    if sender_name:
        sections.append(f"Sender (writing the email): {sender_name}")
    if recipient_name:
        sections.append(f"Recipient (greeted as 'Hi {recipient_name},'): {recipient_name}")
    else:
        sections.append(
            "Recipient name is UNKNOWN. If you choose to include a greeting, "
            "use exactly 'Hi there,' — do NOT invent names like 'team', "
            "'customer', 'friend', or anything similar."
        )
    if subject_seed:
        sections.append(
            f"Suggested subject (you may keep, refine, or replace): {subject_seed}"
        )
    if account_name:
        sections.append(f"Salesforce account: {account_name}")
    if account_details:
        sections.append("Account details (from Salesforce):\n" + account_details)
    if opportunity_text:
        sections.append(
            "Opportunity / deal context (from Salesforce or user notes):\n"
            + opportunity_text[:8000]
        )
    record_block = _format_dict_block("Structured record fields", structured_record)
    if record_block:
        sections.append(record_block)
    if user_message and user_message.strip():
        sections.append(
            "User's instruction / custom message (this is the most important "
            "intent — honour it):\n" + user_message.strip()[:4000]
        )
    if extra_notes:
        sections.append("Additional notes:\n" + extra_notes)

    user = "\n\n".join(sections) + (
        "\n\nReturn JSON only — no markdown, no commentary, just the JSON object."
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _safe_parse(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    raw = raw.strip()
    # Strip accidental markdown code fences.
    if raw.startswith("```"):
        raw = raw.split("```", 2)[-1]
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip("`\n ")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Last-ditch: try to find the first '{' ... last '}' substring.
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None


def _normalize_output(
    parsed: Dict[str, Any],
    *,
    fallback_subject: str,
) -> Optional[Dict[str, Any]]:
    if not isinstance(parsed, dict):
        return None
    subj = (parsed.get("subject") or "").strip()
    paras_raw = parsed.get("paragraphs") or parsed.get("body") or []
    if isinstance(paras_raw, str):
        paras_raw = [p.strip() for p in paras_raw.split("\n\n") if p.strip()]
    if not isinstance(paras_raw, list):
        return None

    paragraphs: List[str] = []
    for p in paras_raw:
        if not isinstance(p, str):
            continue
        cleaned = p.strip()
        if not cleaned:
            continue
        if len(cleaned) > _MAX_PARAGRAPH_LEN:
            cleaned = cleaned[: _MAX_PARAGRAPH_LEN - 1].rstrip() + "…"
        paragraphs.append(cleaned)
        if len(paragraphs) >= _MAX_PARAGRAPHS:
            break

    if not paragraphs:
        return None

    if not subj:
        subj = fallback_subject or "Update from your account team"
    if len(subj) > _MAX_SUBJECT_LEN:
        subj = subj[: _MAX_SUBJECT_LEN - 1].rstrip() + "…"

    return {"subject": subj, "paragraphs": paragraphs}


_GREETING_PREFIXES = (
    "hi ", "hi,", "hi.", "hello", "dear ", "dear,",
    "good morning", "good afternoon", "good evening",
    "hey ", "hey,", "greetings",
)

_SIGNOFF_TOKENS = (
    "best regards", "kind regards", "warm regards", "regards,", "regards\n",
    "best,", "best\n", "thanks,", "thanks\n", "thank you,", "thank you\n",
    "sincerely,", "sincerely\n", "cheers,", "cheers\n", "yours truly",
    "warmly,", "warmly\n", "with appreciation", "respectfully,",
    "talk soon,", "speak soon,",
)


def _starts_with_greeting(text: str) -> bool:
    if not text:
        return False
    s = text.lstrip().lower()
    return any(s.startswith(g) for g in _GREETING_PREFIXES)


def _has_signoff(text: str) -> bool:
    if not text:
        return False
    s = text.strip().lower() + "\n"
    return any(token in s for token in _SIGNOFF_TOKENS)


def _render_plain_text(
    *,
    subject: str,
    paragraphs: List[str],
    recipient_name: str,
    sender_name: str,
) -> str:
    has_greeting = bool(paragraphs) and _starts_with_greeting(paragraphs[0])
    has_signoff = bool(paragraphs) and _has_signoff(paragraphs[-1])

    # NOTE: Do NOT prepend "Subject: …" here. The subject is carried by the MIME
    # envelope (Gmail / Outlook display it as the message title). Repeating it
    # in the body shows up as a stray "Subject:" line for the recipient.
    _ = subject  # kept in signature for API stability / future use
    lines: List[str] = []
    if not has_greeting:
        greeting = f"Hi {recipient_name}," if recipient_name else "Hi there,"
        lines.extend([greeting, ""])
    for p in paragraphs:
        lines.append(p)
        lines.append("")
    if not has_signoff:
        # Trim the trailing blank line so the sign-off sits one line below the
        # last paragraph (standard email spacing) instead of two.
        if lines and lines[-1] == "":
            lines.pop()
        lines.append("")
        lines.append("Best regards,")
        # Only add a name line when we actually have a real sender name —
        # avoid the awkward "Your team" placeholder.
        if sender_name and sender_name.strip():
            lines.append(sender_name.strip())
    return "\n".join(lines).rstrip() + "\n"


def _render_html(
    *,
    subject: str,
    paragraphs: List[str],
    recipient_name: str,
    sender_name: str,
) -> str:
    """Minimal, email-client-friendly HTML wrapper."""
    has_greeting = bool(paragraphs) and _starts_with_greeting(paragraphs[0])
    has_signoff = bool(paragraphs) and _has_signoff(paragraphs[-1])

    safe_subj = html.escape(subject)
    safe_recipient = html.escape(recipient_name or "there")
    safe_sender = html.escape(sender_name or "Your team")

    body_paragraphs = "\n".join(
        f'      <p style="margin:0 0 14px 0;line-height:1.55;white-space:pre-wrap;">{html.escape(p)}</p>'
        for p in paragraphs
    )
    greeting_html = (
        ""
        if has_greeting
        else f'          <p style="margin:0 0 18px 0;font-size:15px;color:#1a1f2c;">Hi {safe_recipient},</p>\n'
    )
    signoff_html = (
        ""
        if has_signoff
        else f'\n          <p style="margin:24px 0 0 0;font-size:15px;color:#1a1f2c;">Best regards,<br>{safe_sender}</p>'
    )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{safe_subj}</title></head>
<body style="margin:0;padding:0;background:#f6f7f9;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1a1f2c;">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:#f6f7f9;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" cellpadding="0" cellspacing="0" width="640" style="max-width:640px;background:#ffffff;border-radius:10px;padding:28px 32px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <tr><td>
{greeting_html}{body_paragraphs}{signoff_html}
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def compose_email(
    *,
    purpose: str,
    recipient_email: str = "",
    recipient_name: str = "",
    sender_name: str = "",
    subject_seed: str = "",
    user_message: str = "",
    account_name: str = "",
    account_details: str = "",
    opportunity_text: str = "",
    structured_record: Optional[Dict[str, Any]] = None,
    extra_notes: str = "",
    tone: str = "warm, professional, concise",
) -> Optional[Dict[str, Any]]:
    """
    Generate a complete email (subject + body paragraphs + plain text + html)
    using the LLM.

    Returns a dict with keys: ``subject``, ``paragraphs``, ``plain_text``,
    ``html_content``. Returns ``None`` on any failure so the caller can fall
    back to legacy template-based generation.
    """
    client = _get_client()
    if client is None:
        return None

    rname = (recipient_name or "").strip() or _name_from_email(recipient_email)
    sname = (sender_name or "").strip()

    messages = _build_messages(
        purpose=purpose,
        sender_name=sname,
        recipient_name=rname,
        subject_seed=subject_seed.strip(),
        user_message=user_message,
        account_name=account_name.strip(),
        account_details=account_details.strip(),
        opportunity_text=opportunity_text.strip(),
        structured_record=structured_record or {},
        extra_notes=extra_notes.strip(),
        tone=tone,
    )

    raw: str = ""
    last_err: Optional[Exception] = None
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model=_model(),
                messages=messages,
                temperature=_temperature(),
                response_format={"type": "json_object"},
            )
            raw = (resp.choices[0].message.content or "").strip()
            if raw:
                break
        except Exception as e:
            last_err = e
            logger.warning(
                "OpenAI call failed (attempt %d/%d): %s", attempt + 1, 2, e
            )

    if not raw:
        if last_err is not None:
            logger.error("AI email generation failed: %s", last_err)
        return None

    parsed = _safe_parse(raw)
    if parsed is None:
        logger.warning("AI returned non-JSON output; ignoring")
        return None

    normalized = _normalize_output(parsed, fallback_subject=subject_seed)
    if normalized is None:
        logger.warning("AI output had no usable paragraphs; ignoring")
        return None

    plain = _render_plain_text(
        subject=normalized["subject"],
        paragraphs=normalized["paragraphs"],
        recipient_name=rname,
        sender_name=sname,
    )
    html_body = _render_html(
        subject=normalized["subject"],
        paragraphs=normalized["paragraphs"],
        recipient_name=rname,
        sender_name=sname,
    )

    return {
        "subject": normalized["subject"],
        "paragraphs": normalized["paragraphs"],
        "plain_text": plain,
        "html_content": html_body,
    }
