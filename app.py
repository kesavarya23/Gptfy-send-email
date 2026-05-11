"""
Salesforce Email Sender - Web UI
Simple web interface for sending emails
"""

import logging

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import sys
import secrets
import os
import time
import urllib.parse
import re
import html as html_lib
import hashlib
import base64
import random
import requests
sys.path.append('src')

from agent import EmailAgent
from utils.data_generator import DataGenerator
from utils.email_generator import EmailGenerator
from services.oauth_send import (
    get_google_user_info,
    get_microsoft_access_token,
    get_microsoft_user_info,
    send_gmail,
    send_outlook,
)
from utils.context_extract import (
    build_salesforce_context,
    combined_opportunity_text,
    is_uploaded_file_without_extractable_text,
)
from services.sf_oauth import (
    clear_oauth_config as clear_sf_oauth_config,
    exchange_code_for_tokens,
    enrich_session_from_identity,
    ensure_salesforce_client,
    get_oauth_config as get_sf_oauth_config,
    salesforce_authorize_url,
    session_apply_token_response,
    store_oauth_config as store_sf_oauth_config,
)
from services.sf_live_account import resolve_account_bundle
from services.ai_writer import compose_email as ai_compose_email, is_ai_enabled

# Send INFO+ from our own modules to stderr so failures in OAuth / Graph / SMTP
# show up in the terminal during development. Werkzeug configures its own
# logger, but app-level loggers were silent before this.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
# Use a stable secret in production (e.g. Vercel env) so OAuth sessions survive restarts
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
CORS(app)  # Enable CORS for all routes


def _plain_text_to_minimal_html(plain_text: str) -> str:
    """Wrap paragraph-separated plain text in a tiny, unstyled HTML shell.

    Gmail's web UI renders ``text/plain`` bodies inside a narrow fixed-width
    column (~600px), which makes paragraphs look cramped and pre-wrapped
    compared with Outlook (which flows plain text across its full reading
    pane). Sending an HTML alternative tells Gmail to use its normal HTML
    email rendering, so the message looks the same in both clients.

    The HTML is deliberately minimal — system font, normal paragraph
    spacing, no card / background / border — so the email still reads like
    a "normally typed message" rather than marketing mail.
    """
    if not plain_text or not plain_text.strip():
        return ""
    paragraphs = [p for p in re.split(r"\n\s*\n", plain_text.strip()) if p.strip()]
    if not paragraphs:
        return ""
    parts = []
    for p in paragraphs:
        escaped = html_lib.escape(p.strip()).replace("\n", "<br>")
        parts.append(f'<p style="margin:0 0 14px 0;">{escaped}</p>')
    inner = "\n".join(parts)
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        '<body style="margin:0;padding:0;'
        'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,'
        'Helvetica,Arial,sans-serif;font-size:14px;line-height:1.5;'
        'color:#202124;">'
        f"{inner}"
        "</body></html>"
    )


def _do_send_email(
    send_method: str,
    agent,
    to_list: list,
    subject: str,
    html_content: str,
    plain_text: str,
    cc: list = None,
    bcc: list = None,
):
    """Send a single email. Returns ``(success: bool, error: str)``.

    ``error`` is empty on success; on failure it contains the most specific
    message we have (Graph error body, SMTP exception text, etc.) so the
    caller can show it in the UI.

    Both Gmail and Outlook receive a multipart message: the plain-text body
    (so it stays readable for clients that strip HTML) plus a minimal HTML
    body generated from that same plain text. The minimal HTML is what makes
    Gmail render with the same paragraph width / spacing as Outlook — Gmail
    otherwise displays plain-text emails in a narrow fixed-width column.
    We intentionally ignore the upstream AI writer's styled HTML "card" so
    the message still looks like a normally typed email, not marketing mail.
    """
    if not to_list:
        return False, "No recipient addresses"
    cc = list(cc or [])
    bcc = list(bcc or [])
    if not (plain_text and plain_text.strip()) and html_content:
        plain_text = re.sub(r"<[^>]+>", "", html_content)
        plain_text = re.sub(r"\n{3,}", "\n\n", plain_text).strip()
    html_content = _plain_text_to_minimal_html(plain_text)
    if send_method == "gmail":
        cid = os.getenv("GOOGLE_CLIENT_ID", "")
        cs = os.getenv("GOOGLE_CLIENT_SECRET", "")
        rt = session.get("google_refresh_token")
        from_addr = session.get("google_email", "")
        if not (cid and cs and rt and from_addr):
            return False, "Gmail not connected (missing client id/secret/refresh token)"
        ok = send_gmail(
            cid, cs, rt, from_addr, to_list, subject, plain_text, html_content,
            cc=cc, bcc=bcc,
        )
        return (True, "") if ok else (False, "Gmail send failed (see server logs)")
    if send_method == "outlook":
        rt = session.get("microsoft_refresh_token")
        if not rt:
            return False, "Outlook not connected (no refresh token in session)"
        at = get_microsoft_access_token(rt)
        if not at:
            return False, "Could not refresh Microsoft access token (re-connect Outlook)"
        ok = send_outlook(
            at, to_list, subject, plain_text,
            html=html_content,
            cc=cc, bcc=bcc,
        )
        if ok:
            return True, ""
        return False, getattr(send_outlook, "last_error", "") or "Graph send failed"
    if agent is None:
        return False, "SMTP agent not initialised"
    try:
        ok = agent.email_service.send_email(
            to_email=to_list,
            subject=subject,
            html_content=html_content,
            plain_text=plain_text,
            cc=cc,
            bcc=bcc,
        )
        return (True, "") if ok else (False, "SMTP send returned False")
    except Exception as e:  # noqa: BLE001
        return False, f"SMTP error: {e}"


def _as_bool(v):
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).lower() in ("true", "1", "yes", "on")


def _email_style_directives(
    *,
    one_opp_mode: bool,
    strict_sf: bool = False,
) -> str:
    """Build the ``extra_notes`` block we send to the AI writer.

    Centralises three requirements that the email-output had been missing:
      1. ONE-opportunity rule (only when ``one_opp_mode`` — i.e. the call is
         paired with a single real Salesforce opportunity record). Without
         this, the LLM tends to summarise every opp it sees in the context
         block, producing emails that name 2-3 deals at once.
      2. Personal / rapport-building tone — the previous output read like
         marketing boilerplate ("Thank you for reaching out … I appreciate
         your interest"). We ask for a warm, human opener that's grounded
         in real context, not invented personal life facts.
      3. Length floor — the base system prompt's "short, high-signal" + "3-5
         short paragraphs" defaults were producing ~600-800 char bodies. We
         explicitly request 1300–1700 chars across 5-7 substantive paragraphs.
    """
    blocks = []
    if one_opp_mode:
        blocks.append(
            "STRICT single-opportunity rule: this email is about EXACTLY ONE "
            "opportunity — the one described in the structured record and the "
            "opportunity context above. Do NOT name, list, summarise, or "
            "compare any other deals on this account, even if more opportunities "
            "are visible elsewhere. Keep the entire narrative focused on this "
            "one deal — its stage, value, next step, and what you need from "
            "the recipient to move it forward."
        )
    blocks.append(
        "Length: aim for 1300 to 1700 characters of body text (not counting "
        "the greeting and sign-off). Use 5 to 7 substantive paragraphs of "
        "2 to 4 sentences each. Do NOT default to the 'short' style — this "
        "is a relationship email, not a one-line ping."
    )
    blocks.append(
        "Personal touch / rapport: open the body with ONE warm, human sentence "
        "that acknowledges the working relationship or the recipient's likely "
        "context (e.g. 'I know things have been moving quickly on your side as "
        "we get closer to close…'). Sprinkle small humanising touches through "
        "the email — a courteous offer to make their week easier, a brief "
        "acknowledgement of their team's effort, a forward-looking line about "
        "working together. Do NOT invent personal-life facts (kids, vacation, "
        "weekend plans) and do NOT use generic marketing phrases like 'Thank "
        "you for reaching out' or 'I appreciate your interest'."
    )
    blocks.append(
        "Tone: warm, confident, relationship-building. Write like you are "
        "emailing a colleague you respect and have worked with for months — "
        "not a stranger on a marketing list."
    )
    if strict_sf:
        blocks.append(
            "Stay grounded in the user's Salesforce context and custom message "
            "above. Any 'personal touch' must be relational (about the working "
            "partnership), not invented facts about wellbeing, family, or "
            "weekends."
        )
    return "\n\n".join(blocks)


# Pool of "opening style" hints we rotate through per batch so a run of
# N emails doesn't collapse into N near-identical openers ("I hope this email
# finds you well…"). One of these is forwarded to the AI writer for each
# email; the writer treats it as authoritative for the OPENING SENTENCE and
# overall structure, while the body still respects the Salesforce context
# and the user's custom message.
_OPENING_STYLE_HINTS = (
    "Open with a concrete detail about THIS deal's current stage or momentum. "
    "The first sentence MUST lead with a specific fact pulled from the structured "
    "record (stage, milestone, timeline, amount, or owner) — never a hope/wellness "
    "filler line.",

    "Open with a forward-looking line tied to an upcoming step or window for "
    "this opportunity. Anchor the first sentence on a named next action or a "
    "date already present in the structured record / brief.",

    "Open by acknowledging, in one specific sentence, the recipient's or their "
    "team's recent contribution on THIS deal. Avoid generic 'thanks for your "
    "time' phrasing — name the actual thing they did or are doing.",

    "Open with a one-sentence status framing — where this deal stands right "
    "now, in plain language. Then transition into the reason for writing. "
    "Skip any 'hope you are well' opener.",

    "Open by surfacing the single decision or question the recipient currently "
    "owns on this opportunity. Make the first sentence land that question, "
    "conversationally, before any context.",

    "Open with a short, human note about pace or context (e.g. 'with the close "
    "date narrowing in' or 'now that the proposal is in front of your team'), "
    "grounded ONLY in the structured record. Do not invent personal-life facts.",

    "Open by referencing the most recent shared touchpoint (a meeting, working "
    "session, or previous thread) and pivot immediately — within the first two "
    "sentences — to today's reason for writing.",

    "Open by naming, in plain language, the one thing you need from the "
    "recipient to move this opportunity forward. The rest of the email then "
    "supports that single ask.",

    "Open with a brief observation about the broader account / industry context "
    "as it touches THIS deal (one sentence only), then immediately ground in a "
    "specific opportunity fact. No generic market commentary.",

    "Open by quickly recapping the most recent change on this deal (a stage "
    "advance, a new next step, a refreshed close date), in one sentence, before "
    "stating today's purpose. Use only facts from the structured record.",
)


def _build_opening_style_batch(n: int) -> list:
    """Return ``n`` opening-style hints with no two consecutive duplicates.

    Shuffled per request so emails in the SAME batch never share an opener,
    and successive batches don't always start on the same style.
    """
    if n <= 0:
        return []
    pool = list(_OPENING_STYLE_HINTS)
    random.shuffle(pool)
    if n <= len(pool):
        return pool[:n]
    out = list(pool)
    while len(out) < n:
        next_pool = list(_OPENING_STYLE_HINTS)
        random.shuffle(next_pool)
        # Avoid an immediate repeat at the boundary.
        if next_pool and out and next_pool[0] == out[-1] and len(next_pool) > 1:
            next_pool[0], next_pool[1] = next_pool[1], next_pool[0]
        out.extend(next_pool)
    return out[:n]


def _pick_opps_for_send(account_name_in_form: str, count: int):
    """Return ``count`` real Salesforce opps to use, one per email.

    Reads the structured opp list cached by ``/api/salesforce/account``.
    Only used when the account name in the form still matches the one we
    loaded against (so a manual edit invalidates the cache and we fall
    back to legacy random generation).

    Behaviour:
      * 6 opps + 6 requested  → all 6, randomised order, one per email.
      * 6 opps + 1 requested  → 1 randomly picked real opp.
      * 6 opps + 10 requested → all 6 once, then 4 cycled repeats.
      * No cache / no match   → returns ``([], None)`` so caller falls back.

    Returns ``(picked_opps, cached_account_name)`` — the second value is
    used by the result list to label rows like "Opportunity 3 of 6".
    """
    if count <= 0:
        return [], None
    cached_opps = session.get("sf_account_opportunities") or []
    cached_account = (session.get("sf_account_name_loaded") or "").strip()
    acc_in_form = (account_name_in_form or "").strip()
    if not (cached_opps and cached_account and acc_in_form):
        return [], None
    if cached_account.lower() != acc_in_form.lower():
        return [], None
    shuffled = list(cached_opps)
    random.shuffle(shuffled)
    picked = [shuffled[i % len(shuffled)] for i in range(count)]
    return picked, cached_account


def _maybe_ai_email(
    *,
    purpose: str,
    fallback,
    to_list,
    sender_name: str,
    subject_seed: str = "",
    user_message: str = "",
    account_name: str = "",
    account_details: str = "",
    opportunity_text: str = "",
    structured_record=None,
    extra_notes: str = "",
    variation_hint: str = "",
):
    """
    Produce a (subject, html, plain_text) email triple.

    When OPENAI_API_KEY is configured, the LLM writes the email using all
    available Salesforce / opportunity / case / user-supplied context. On any
    failure (no key, network error, malformed response) we fall back to the
    legacy template-based ``fallback()`` callable so sending never breaks.

    ``variation_hint`` is forwarded to the AI writer so a batch of N emails
    produces N distinct openers / structures instead of N near-duplicates.
    """
    if is_ai_enabled():
        recipient_email = (to_list[0] if to_list else "") or ""
        ai = ai_compose_email(
            purpose=purpose,
            recipient_email=recipient_email,
            sender_name=sender_name,
            subject_seed=subject_seed,
            user_message=user_message,
            account_name=account_name,
            account_details=account_details,
            opportunity_text=opportunity_text,
            structured_record=structured_record or {},
            extra_notes=extra_notes,
            variation_hint=variation_hint,
        )
        if ai:
            return {
                "subject": ai["subject"],
                "html_content": ai["html_content"],
                "plain_text": ai["plain_text"],
                "ai": True,
            }
    legacy = fallback()
    return {
        "subject": legacy["subject"],
        "html_content": legacy["html_content"],
        "plain_text": legacy.get("plain_text") or "",
        "ai": False,
    }


def _parse_email_list(value) -> list:
    """Parse comma, semicolon, or newline–separated addresses from a string or list."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(x).strip() for x in value if str(x).strip()]
    s = str(value).strip()
    if not s:
        return []
    return [p.strip() for p in re.split(r"[\s,;]+", s.replace("\r", "").replace("\n", " ")) if p.strip()]


def _parse_send_payload():
    """Parse JSON or multipart/form-data (file upload for opportunity context)."""
    if request.content_type and "multipart/form-data" in request.content_type:
        f = request.form
        data = {
            "sender_email": f.get("sender_email") or "",
            "sender_password": f.get("sender_password") or "",
            "sender_name": f.get("sender_name") or "",
            "recipient_email": f.get("recipient_email") or "",
            "to_emails": f.get("to_emails") or f.get("recipient_to") or "",
            "cc_emails": f.get("cc_emails") or "",
            "bcc_emails": f.get("bcc_emails") or "",
            "num_opportunities": f.get("num_opportunities", 0),
            "num_cases": f.get("num_cases", 0),
            "num_business": f.get("num_business", 0),
            "topic_mode": f.get("topic_mode", "default"),
            "custom_message": f.get("custom_message", "Please review this Salesforce data."),
            "send_method": f.get("send_method", "smtp"),
            "delay_seconds": f.get("delay_seconds", 0),
            "selected_topics": f.getlist("selected_topics"),
            "use_custom_context": str(f.get("use_custom_context", "")).lower() in (
                "true", "1", "on", "yes",
            ),
            # Per-field include toggles. Default to True when the field is missing
            # so older clients / API callers keep their previous behaviour.
            "include_account": str(f.get("include_account", "true")).lower() in (
                "true", "1", "on", "yes",
            ),
            "include_opportunity": str(f.get("include_opportunity", "true")).lower() in (
                "true", "1", "on", "yes",
            ),
            "account_name": f.get("account_name") or "",
            "opportunity_text": f.get("opportunity_text") or "",
        }
        opp_file = request.files.get("opportunity_file")
        # If the user unchecked the opportunity context box, ignore Account-side
        # values too only for the opp side: drop opp text and the uploaded file
        # so neither reaches the AI / data generator.
        if not data["include_opportunity"]:
            data["opportunity_text"] = ""
            opp_file = None
        if not data["include_account"]:
            data["account_name"] = ""
        return data, opp_file
    data = request.get_json() or {}
    data.setdefault("to_emails", data.get("recipient_to") or data.get("to_emails") or "")
    data.setdefault("cc_emails", data.get("cc_emails") or "")
    data.setdefault("bcc_emails", data.get("bcc_emails") or "")
    st = data.get("selected_topics")
    if st is None:
        data["selected_topics"] = []
    elif not isinstance(st, list):
        data["selected_topics"] = [st] if st else []
    data["use_custom_context"] = _as_bool(data.get("use_custom_context"))
    # Default include_* to True for JSON callers that don't send the flag.
    data["include_account"] = _as_bool(data.get("include_account", True))
    data["include_opportunity"] = _as_bool(data.get("include_opportunity", True))
    data["account_name"] = data.get("account_name") or ""
    data["opportunity_text"] = data.get("opportunity_text") or ""
    if not data["include_account"]:
        data["account_name"] = ""
    if not data["include_opportunity"]:
        data["opportunity_text"] = ""
    return data, None


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', ai_enabled=is_ai_enabled())


@app.route('/send_emails', methods=['POST'])
def send_emails():
    """Send emails endpoint"""
    try:
        # Get form data (JSON or multipart for file upload)
        data, opportunity_file = _parse_send_payload()

        sender_email = data.get("sender_email") or ""
        sender_password = data.get("sender_password")
        sender_name_raw = (data.get("sender_name") or "").strip()
        send_method_peek = (data.get("send_method") or "smtp").lower()
        oauth_email_for_name = ""
        if not sender_name_raw or sender_name_raw == sender_email:
            if send_method_peek == "gmail":
                sender_name_raw = (
                    session.get("google_name")
                    or session.get("google_given_name")
                    or ""
                ).strip()
                oauth_email_for_name = session.get("google_email", "")
            elif send_method_peek == "outlook":
                sender_name_raw = (
                    session.get("outlook_name")
                    or session.get("outlook_given_name")
                    or ""
                ).strip()
                oauth_email_for_name = session.get("outlook_email", "")
        if not sender_name_raw:
            # Last-ditch: derive a Title-Cased name from the connected email's
            # local-part (e.g. "jane.doe@acme.com" -> "Jane Doe"). Better than
            # leaving the "Best regards," line dangling.
            src_email = oauth_email_for_name or sender_email
            if "@" in src_email:
                local = src_email.split("@", 1)[0].split("+", 1)[0]
                tokens = [
                    t for t in re.split(r"[._\-]+", local)
                    if t and any(c.isalpha() for c in t)
                ]
                if tokens:
                    sender_name_raw = " ".join(
                        "".join(c for c in t if c.isalpha()).capitalize()
                        for t in tokens
                        if "".join(c for c in t if c.isalpha())
                    ).strip()
        sender_name = sender_name_raw or sender_email or ""
        to_list = _parse_email_list(
            data.get("to_emails")
            or data.get("recipient_to")
            or data.get("recipient_email")
            or "",
        )
        cc_list = _parse_email_list(data.get("cc_emails") or data.get("cc") or "")
        bcc_list = _parse_email_list(data.get("bcc_emails") or data.get("bcc") or "")
        num_opportunities = int(data.get("num_opportunities", 0) or 0)
        num_cases = int(data.get("num_cases", 0) or 0)
        num_business = int(data.get("num_business", 0) or 0)
        topic_mode = data.get("topic_mode", "default")
        selected_topics = data.get("selected_topics") or []
        custom_message = data.get("custom_message", "Please review this Salesforce data.")
        send_method = (data.get("send_method") or "smtp").lower()
        if send_method not in ("smtp", "gmail", "outlook"):
            send_method = "smtp"
        use_custom_context = _as_bool(data.get("use_custom_context"))
        # Strict context is now implicit: whenever the user supplies custom Salesforce
        # context, we always nudge the LLM (and the legacy template fallback) to stick
        # to that context only — no random "wellbeing" or product filler. The previous
        # user-facing checkbox was redundant with the system prompt; this keeps the
        # behaviour without the UI noise.
        strict_sf = use_custom_context
        salesforce_context = build_salesforce_context(
            use_custom_context,
            data.get("account_name") or "",
            data.get("opportunity_text") or "",
            opportunity_file,
        )
        # Delay between emails in seconds (0 = no delay)
        try:
            delay_seconds = int(data.get("delay_seconds", 0) or 0)
        except (TypeError, ValueError):
            delay_seconds = 0

        # Validation
        if not to_list:
            return jsonify({
                'success': False,
                'error': 'Please add at least one address in To (use comma, semicolon, or new lines between multiple emails)',
            })
        if send_method == 'smtp':
            if not sender_email or not sender_password:
                return jsonify({
                    'success': False,
                    'error': 'Please fill in sender email and app password for SMTP, or use Gmail/Outlook and connect first'
                })
        if send_method == 'gmail':
            if not session.get('google_refresh_token') or not session.get('google_email'):
                return jsonify({
                    'success': False,
                    'error': 'Please connect Google (Gmail) first using the button in Sender section'
                })
        if send_method == 'outlook':
            if not session.get('microsoft_refresh_token'):
                return jsonify({
                    'success': False,
                    'error': 'Please connect Microsoft (Outlook) first using the button in Sender section'
                })

        if num_opportunities == 0 and num_cases == 0 and num_business == 0:
            return jsonify({
                'success': False,
                'error': 'Please enter at least 1 in "No. of emails to send"'
            })

        if num_business > 0 and topic_mode == 'custom' and not selected_topics:
            return jsonify({
                'success': False,
                'error': 'Please select at least one topic when using Custom mode'
            })

        if use_custom_context and not salesforce_context and num_business > 0:
            if is_uploaded_file_without_extractable_text(
                opportunity_file,
                data.get("account_name") or "",
                data.get("opportunity_text") or "",
            ):
                return jsonify({
                    "success": False,
                    "error": (
                        "We could not read text from your image on this server (OCR is often unavailable in the cloud). "
                        "Please paste the Account, Opportunity, Stage, Amount, and Close date in the text box, then try again. "
                        "Or upload a .txt / .md file with the same information."
                    ),
                })
            return jsonify({
                "success": False,
                "error": (
                    "Custom Salesforce context is on but no content was found. "
                    "Add an account name, opportunity text, and/or a text or image file."
                ),
            })

        # Initialize services
        data_generator = DataGenerator()
        agent = None
        if send_method == 'smtp':
            # Use SMTP_HOST / SMTP_PORT so Microsoft 365 / Outlook.com can use the right server (not Gmail’s default).
            _smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            try:
                _smtp_port = int(os.getenv("SMTP_PORT", "587") or 587)
            except ValueError:
                _smtp_port = 587
            agent = EmailAgent(
                sender_email=sender_email,
                sender_password=sender_password,
                sender_name=sender_name,
                smtp_host=_smtp_host,
                smtp_port=_smtp_port,
            )
        email_generator = EmailGenerator()

        results = []
        all_emails = []

        # Generate and send opportunities
        if num_opportunities > 0:
            # Always forward whatever Salesforce context was loaded into the form
            # (via /api/salesforce/account) to the LLM, regardless of the
            # "use custom context" toggle. That toggle only controls the legacy
            # template-based generator; the AI writer should always ground its
            # output in real CRM data when it is available.
            sf_account_for_ai = (data.get("account_name") or "").strip()
            sf_opp_for_ai = (data.get("opportunity_text") or "").strip()

            # Prefer the real per-opportunity list cached by /api/salesforce/account
            # so we can send ONE email per real opp instead of a single context
            # blob duplicated across N emails.
            picked_real_opps, cached_account = _pick_opps_for_send(
                sf_account_for_ai, num_opportunities
            )
            use_real_opps = bool(picked_real_opps)

            if use_real_opps:
                opps_for_send = picked_real_opps
                source_index_by_name = {
                    o.get("name"): idx + 1
                    for idx, o in enumerate(session.get("sf_account_opportunities") or [])
                }
                total_real_opps = len(session.get("sf_account_opportunities") or [])
            else:
                opps_for_send = data_generator.generate_opportunities(num_opportunities)
                source_index_by_name = {}
                total_real_opps = 0

            # Per-batch shuffled list of opening-style hints — one per email — so
            # the first sentences across the batch are clearly different.
            opp_opening_styles = _build_opening_style_batch(len(opps_for_send))

            for i, opp in enumerate(opps_for_send, 1):
                try:
                    if use_real_opps:
                        opp_name = opp.get("name") or "Opportunity"
                        opp_account = opp.get("account_name") or sf_account_for_ai
                        # Per-opp brief: just THIS opp's facts, not the whole list.
                        per_opp_text = opp.get("brief_text") or ""
                        subject_seed = (
                            f"Salesforce Opportunity Update: {opp_name}".strip()
                        )
                        structured_record = {
                            "opportunity_name": opp_name,
                            "account_name": opp_account,
                            "stage": opp.get("stage"),
                            "amount": opp.get("amount"),
                            "amount_display": opp.get("amount_str"),
                            "close_date": opp.get("close_date"),
                            "probability": opp.get("probability"),
                            "next_step": opp.get("next_step"),
                        }
                        result_name = opp_name
                    else:
                        opp_name = opp.get("opportunity_name", "Unknown")
                        opp_account = opp.get("account_name") or sf_account_for_ai
                        per_opp_text = sf_opp_for_ai
                        subject_seed = (
                            f"Salesforce Opportunity Update: {opp_name}".strip()
                        )
                        structured_record = {
                            "opportunity_name": opp_name,
                            "account_name": opp_account,
                            "stage": opp.get("stage"),
                            "amount": opp.get("amount"),
                            "close_date": opp.get("close_date"),
                            "owner_name": opp.get("owner_name"),
                            "probability": opp.get("probability"),
                            "next_step": opp.get("next_step"),
                        }
                        result_name = opp_name

                    email_content = _maybe_ai_email(
                        purpose="opportunity",
                        fallback=lambda o=opp: email_generator.generate_opportunity_email(
                            opportunity_data=o,
                            custom_message=custom_message,
                        ),
                        to_list=to_list,
                        sender_name=sender_name,
                        subject_seed=subject_seed,
                        user_message=custom_message,
                        account_name=opp_account,
                        opportunity_text=per_opp_text,
                        structured_record=structured_record,
                        extra_notes=_email_style_directives(
                            one_opp_mode=use_real_opps,
                            strict_sf=strict_sf,
                        ),
                        variation_hint=(
                            opp_opening_styles[i - 1]
                            if i - 1 < len(opp_opening_styles) else ""
                        ),
                    )

                    success, send_err = _do_send_email(
                        send_method, agent, to_list,
                        email_content['subject'], email_content['html_content'],
                        email_content.get('plain_text') or '',
                        cc=cc_list, bcc=bcc_list,
                    )

                    entry = {
                        'type': 'Opportunity',
                        'name': result_name,
                        'status': 'Sent' if success else 'Failed',
                        'number': i,
                    }
                    if use_real_opps and source_index_by_name:
                        src_idx = source_index_by_name.get(result_name)
                        if src_idx:
                            entry['source'] = (
                                f"Opportunity {src_idx} of {total_real_opps} "
                                f"from {cached_account}"
                            )
                    if not success and send_err:
                        entry['error'] = send_err
                    all_emails.append(entry)

                except Exception as e:
                    all_emails.append({
                        'type': 'Opportunity',
                        'name': (
                            opp.get("name")
                            if use_real_opps
                            else opp.get('opportunity_name', 'Unknown')
                        ),
                        'status': 'Failed',
                        'error': str(e),
                        'number': i
                    })

                # Delay between emails if configured
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

        # Generate and send cases
        if num_cases > 0:
            cases = data_generator.generate_cases(num_cases)
            sf_account_for_ai = (data.get("account_name") or "").strip()
            sf_opp_for_ai = (data.get("opportunity_text") or "").strip()

            case_opening_styles = _build_opening_style_batch(len(cases))

            for i, case in enumerate(cases, 1):
                try:
                    email_content = _maybe_ai_email(
                        purpose="case",
                        fallback=lambda c=case: email_generator.generate_case_email(
                            case_data=c,
                            custom_message=custom_message,
                        ),
                        to_list=to_list,
                        sender_name=sender_name,
                        subject_seed=(
                            f"Case {case.get('case_number', '')} - {case.get('subject', '')}".strip(" -")
                        ),
                        user_message=custom_message,
                        account_name=sf_account_for_ai or (case.get("account_name") or ""),
                        opportunity_text=sf_opp_for_ai,
                        structured_record={
                            "case_number": case.get("case_number"),
                            "subject": case.get("subject"),
                            "status": case.get("status"),
                            "priority": case.get("priority"),
                            "case_type": case.get("case_type"),
                            "origin": case.get("origin"),
                            "contact_name": case.get("contact_name"),
                            "owner_name": case.get("owner_name"),
                            "description": case.get("description"),
                        },
                        variation_hint=(
                            case_opening_styles[i - 1]
                            if i - 1 < len(case_opening_styles) else ""
                        ),
                    )

                    success, send_err = _do_send_email(
                        send_method, agent, to_list,
                        email_content['subject'], email_content['html_content'],
                        email_content.get('plain_text') or '',
                        cc=cc_list, bcc=bcc_list,
                    )

                    entry = {
                        'type': 'Case',
                        'name': f"Case {case['case_number']}",
                        'status': 'Sent' if success else 'Failed',
                        'number': i,
                    }
                    if not success and send_err:
                        entry['error'] = send_err
                    all_emails.append(entry)

                except Exception as e:
                    all_emails.append({
                        'type': 'Case',
                        'name': f"Case {case.get('case_number', 'Unknown')}",
                        'status': 'Failed',
                        'error': str(e),
                        'number': i
                    })

                # Delay between emails if configured
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

        # Generate and send business emails
        if num_business > 0:
            topic_types = selected_topics if topic_mode == 'custom' and selected_topics else None
            acc_for_gen = (data.get("account_name") or "").strip() or None
            opp_combined = (
                combined_opportunity_text(data.get("opportunity_text") or "", opportunity_file)
                if use_custom_context
                else ""
            )
            business_emails = data_generator.generate_business_emails(
                num_business,
                topic_types=topic_types,
                salesforce_context=salesforce_context,
                account_name=acc_for_gen,
                opportunity_brief=opp_combined or None,
                strict_sf_context=strict_sf,
            )

            # AI writer always sees the Salesforce-loaded context plus any
            # uploaded file/text, regardless of the "use custom context" toggle.
            # The toggle still governs the legacy data generator above.
            sf_account_for_ai = (data.get("account_name") or "").strip()
            sf_opp_for_ai = combined_opportunity_text(
                data.get("opportunity_text") or "", opportunity_file
            )

            # Pair each business email with ONE real Salesforce opportunity so
            # the AI grounds the message in a single deal instead of listing
            # every open opp on the account. Same logic as the opportunity
            # loop: randomised, cycled if needed, falls back to the existing
            # "big blob" behaviour when the user hasn't loaded an SF account.
            picked_business_opps, cached_account_b = _pick_opps_for_send(
                sf_account_for_ai, num_business
            )
            business_one_opp_mode = bool(picked_business_opps)
            total_real_opps_b = (
                len(session.get("sf_account_opportunities") or [])
                if business_one_opp_mode
                else 0
            )
            source_index_by_name_b = (
                {
                    o.get("name"): idx + 1
                    for idx, o in enumerate(session.get("sf_account_opportunities") or [])
                }
                if business_one_opp_mode
                else {}
            )

            business_opening_styles = _build_opening_style_batch(len(business_emails))

            for i, business_email in enumerate(business_emails, 1):
                try:
                    bet = business_email.get("type") or "business"

                    # Compute per-email account / opp context:
                    #  - one-opp mode: feed ONLY this opp's brief, not the
                    #    full list. That is the actual fix for "the email
                    #    talks about 2-3 opportunities at once".
                    #  - legacy mode: keep the previous wider context blob.
                    if business_one_opp_mode:
                        picked_opp = picked_business_opps[i - 1]
                        per_email_account = (
                            picked_opp.get("account_name") or sf_account_for_ai
                        )
                        per_email_opp_text = picked_opp.get("brief_text") or ""
                        picked_opp_name = picked_opp.get("name") or ""
                    else:
                        picked_opp = None
                        per_email_account = sf_account_for_ai
                        per_email_opp_text = sf_opp_for_ai
                        picked_opp_name = ""

                    structured_record = {
                        "type": bet,
                        "meeting_title": business_email.get("meeting_title"),
                        "agenda": business_email.get("agenda"),
                        "date": business_email.get("date"),
                        "time": business_email.get("time"),
                        "location": business_email.get("location"),
                        "context": business_email.get("context"),
                        "reason": business_email.get("reason"),
                        "company": business_email.get("company"),
                        "project_name": business_email.get("project_name"),
                        "milestone": business_email.get("milestone"),
                        "completion": business_email.get("completion"),
                        "status": business_email.get("status"),
                        "reminder_about": business_email.get("reminder_about"),
                        "due_date": business_email.get("due_date"),
                    }
                    if picked_opp is not None:
                        # Surface the chosen opp's fields so the LLM can quote
                        # specifics (stage, amount, close date) for this single
                        # deal — and nothing else.
                        structured_record.update({
                            "focus_opportunity_name": picked_opp.get("name"),
                            "focus_opportunity_stage": picked_opp.get("stage"),
                            "focus_opportunity_amount": picked_opp.get("amount"),
                            "focus_opportunity_amount_display": picked_opp.get("amount_str"),
                            "focus_opportunity_close_date": picked_opp.get("close_date"),
                            "focus_opportunity_probability": picked_opp.get("probability"),
                            "focus_opportunity_next_step": picked_opp.get("next_step"),
                        })

                    email_content = _maybe_ai_email(
                        purpose=bet,
                        fallback=lambda be=business_email: email_generator.generate_business_email(be),
                        to_list=to_list,
                        sender_name=sender_name,
                        subject_seed=business_email.get("subject", "") or "",
                        user_message=custom_message,
                        account_name=per_email_account,
                        opportunity_text=per_email_opp_text,
                        structured_record=structured_record,
                        extra_notes=_email_style_directives(
                            one_opp_mode=business_one_opp_mode,
                            strict_sf=strict_sf,
                        ),
                        variation_hint=(
                            business_opening_styles[i - 1]
                            if i - 1 < len(business_opening_styles) else ""
                        ),
                    )

                    success, send_err = _do_send_email(
                        send_method, agent, to_list,
                        email_content['subject'], email_content['html_content'],
                        email_content.get('plain_text') or '',
                        cc=cc_list, bcc=bcc_list,
                    )

                    # Friendly type names
                    type_names = {
                        'meeting_invitation': 'Meeting Invitation',
                        'followup': 'Follow-up',
                        'thank_you': 'Thank You',
                        'project_update': 'Project Update',
                        'reminder': 'Reminder',
                        'trial_feedback': 'Product Trial Feedback',
                        'product_queries': 'Product Queries',
                        'product_issues': 'Product Issues',
                        'demo_enquiry': 'Demo Enquiry',
                    }

                    entry = {
                        'type': type_names.get(business_email['type'], business_email['type']),
                        'name': email_content['subject'],
                        'status': 'Sent' if success else 'Failed',
                        'number': i,
                    }
                    if business_one_opp_mode and picked_opp_name:
                        src_idx = source_index_by_name_b.get(picked_opp_name)
                        if src_idx:
                            entry['source'] = (
                                f"Grounded in Opportunity {src_idx} of "
                                f"{total_real_opps_b} ({picked_opp_name}) "
                                f"from {cached_account_b}"
                            )
                    if not success and send_err:
                        entry['error'] = send_err
                    all_emails.append(entry)

                except Exception as e:
                    all_emails.append({
                        'type': 'Email',
                        'name': business_email.get('subject', 'Unknown'),
                        'status': 'Failed',
                        'error': str(e),
                        'number': i
                    })

                # Delay between emails if configured
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

        # Calculate summary
        total_sent = sum(1 for email in all_emails if email['status'] == 'Sent')
        total_failed = len(all_emails) - total_sent

        return jsonify({
            'success': True,
            'summary': {
                'total': len(all_emails),
                'sent': total_sent,
                'failed': total_failed,
                'success_rate': round((total_sent / len(all_emails) * 100), 1) if all_emails else 0
            },
            'emails': all_emails
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


def _public_base_url():
    u = (os.getenv("PUBLIC_BASE_URL") or request.url_root or "").rstrip("/")
    return u if u else f"{request.scheme}://{request.host}"


@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    g_ok = bool(session.get("google_refresh_token") and session.get("google_email"))
    o_ok = bool(session.get("microsoft_refresh_token") and session.get("outlook_email"))
    sf_ok = bool(session.get("salesforce_refresh_token") and session.get("salesforce_instance_url"))
    sf_cfg = get_sf_oauth_config(session)
    return jsonify({
        "gmail_connected": g_ok,
        "gmail_email": session.get("google_email", ""),
        "outlook_connected": o_ok,
        "outlook_email": session.get("outlook_email", ""),
        "google_configured": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")),
        "microsoft_configured": bool(
            os.getenv("MICROSOFT_CLIENT_ID") and os.getenv("MICROSOFT_CLIENT_SECRET")
        ),
        "salesforce_connected": sf_ok,
        "salesforce_instance_url": session.get("salesforce_instance_url", ""),
        "salesforce_username": session.get("salesforce_username", ""),
        "salesforce_org_id": session.get("salesforce_org_id", ""),
        "salesforce_org_name": session.get("salesforce_org_name", ""),
        "salesforce_display_name": session.get("salesforce_display_name", ""),
        # True when the user has saved Connected App creds in this session OR via .env.
        "salesforce_configured": bool(sf_cfg["client_id"] and sf_cfg["client_secret"]),
        "salesforce_login_url": sf_cfg["login_url"],
    })


@app.route("/api/auth/google", methods=["GET"])
def auth_google_start():
    cid = os.getenv("GOOGLE_CLIENT_ID", "")
    if not cid or not os.getenv("GOOGLE_CLIENT_SECRET"):
        return "Google OAuth is not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_OAUTH_REDIRECT in the server environment.", 503
    state = secrets.token_urlsafe(32)
    session["oauth_state_g"] = state
    redir = os.getenv("GOOGLE_OAUTH_REDIRECT") or (_public_base_url() + "/api/auth/google/callback")
    params = {
        "client_id": cid,
        "redirect_uri": redir,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/userinfo.email openid",
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return redirect("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params))


@app.route("/api/auth/google/callback", methods=["GET"])
def auth_google_callback():
    if request.args.get("error"):
        return redirect("/?gmail_error=access_denied")
    if request.args.get("state") != session.get("oauth_state_g"):
        return redirect("/?gmail_error=state")
    code = request.args.get("code")
    if not code:
        return redirect("/?gmail_error=no_code")
    redir = os.getenv("GOOGLE_OAUTH_REDIRECT") or (_public_base_url() + "/api/auth/google/callback")
    data = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": redir,
        "grant_type": "authorization_code",
    }
    r = requests.post("https://oauth2.googleapis.com/token", data=data, timeout=30)
    if r.status_code != 200:
        return redirect("/?gmail_error=token")
    j = r.json()
    if j.get("refresh_token"):
        session["google_refresh_token"] = j["refresh_token"]
    at = j.get("access_token")
    if at:
        session["google_access_token"] = at
        info = get_google_user_info(at)
        if info.get("email"):
            session["google_email"] = info["email"]
        if info.get("name"):
            session["google_name"] = info["name"]
        if info.get("given_name"):
            session["google_given_name"] = info["given_name"]
    return redirect("/?gmail=connected")


@app.route("/api/auth/outlook", methods=["GET"])
def auth_outlook_start():
    cid = os.getenv("MICROSOFT_CLIENT_ID", "")
    if not cid or not os.getenv("MICROSOFT_CLIENT_SECRET"):
        return "Microsoft OAuth is not configured. Set MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, and MICROSOFT_OAUTH_REDIRECT on the server.", 503
    state = secrets.token_urlsafe(32)
    session["oauth_state_ms"] = state
    tenant = os.getenv("MICROSOFT_TENANT", "common")
    redir = os.getenv("MICROSOFT_OAUTH_REDIRECT") or (_public_base_url() + "/api/auth/outlook/callback")
    params = {
        "client_id": cid,
        "response_type": "code",
        "redirect_uri": redir,
        "response_mode": "query",
        "scope": "offline_access User.Read openid email https://graph.microsoft.com/Mail.Send",
        "state": state,
    }
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}"
    return redirect(url)


@app.route("/api/auth/outlook/callback", methods=["GET"])
def auth_outlook_callback():
    if request.args.get("error"):
        return redirect("/?outlook_error=access_denied")
    if request.args.get("state") != session.get("oauth_state_ms"):
        return redirect("/?outlook_error=state")
    code = request.args.get("code")
    if not code:
        return redirect("/?outlook_error=no_code")
    tenant = os.getenv("MICROSOFT_TENANT", "common")
    redir = os.getenv("MICROSOFT_OAUTH_REDIRECT") or (_public_base_url() + "/api/auth/outlook/callback")
    data = {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET", ""),
        "code": code,
        "redirect_uri": redir,
        "grant_type": "authorization_code",
    }
    r = requests.post(
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        data=data,
        timeout=30,
    )
    if r.status_code != 200:
        return redirect("/?outlook_error=token")
    j = r.json()
    if j.get("refresh_token"):
        session["microsoft_refresh_token"] = j["refresh_token"]
    if j.get("access_token"):
        info = get_microsoft_user_info(j["access_token"])
        if info.get("email"):
            session["outlook_email"] = info["email"]
        if info.get("name"):
            session["outlook_name"] = info["name"]
        if info.get("given_name"):
            session["outlook_given_name"] = info["given_name"]
    return redirect("/?outlook=connected")


def _sf_callback_url() -> str:
    """Resolve the Salesforce OAuth callback URL the running app will use."""
    cfg = get_sf_oauth_config(session)
    return cfg["redirect_uri"] or (_public_base_url() + "/api/auth/salesforce/callback")


@app.route("/salesforce/setup", methods=["GET", "POST"])
def salesforce_setup():
    """
    In-app setup page for the user's own Salesforce Connected App.
    GET  → render the form (pre-filled from session/.env if present).
    POST → save credentials in the session and continue to the OAuth flow.
    """
    callback_url = _sf_callback_url()
    if request.method == "POST":
        client_id = (request.form.get("client_id") or "").strip()
        client_secret = (request.form.get("client_secret") or "").strip()
        login_url = (request.form.get("login_url") or "").strip() or "https://login.salesforce.com"
        redirect_uri = (request.form.get("redirect_uri") or "").strip() or callback_url
        if not client_id or not client_secret:
            cfg = get_sf_oauth_config(session)
            return render_template(
                "salesforce_setup.html",
                cfg=cfg,
                callback_url=callback_url,
                error="Consumer Key and Consumer Secret are required.",
            )
        store_sf_oauth_config(
            session,
            client_id=client_id,
            client_secret=client_secret,
            login_url=login_url,
            redirect_uri=redirect_uri,
        )
        return redirect("/api/auth/salesforce")

    cfg = get_sf_oauth_config(session)
    return render_template(
        "salesforce_setup.html",
        cfg=cfg,
        callback_url=callback_url,
        error=None,
    )


@app.route("/api/auth/salesforce", methods=["GET"])
def auth_salesforce_start():
    cfg = get_sf_oauth_config(session)
    if not cfg["client_id"] or not cfg["client_secret"]:
        return redirect("/salesforce/setup")
    state = secrets.token_urlsafe(32)
    session["oauth_state_sf"] = state
    # PKCE: generate verifier, store in session; send SHA-256 challenge to Salesforce.
    code_verifier = secrets.token_urlsafe(64)
    session["oauth_pkce_verifier_sf"] = code_verifier
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")
    redir = cfg["redirect_uri"] or (_public_base_url() + "/api/auth/salesforce/callback")
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": redir,
        "response_type": "code",
        "scope": "api refresh_token",
        "state": state,
        "prompt": "consent",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return redirect(salesforce_authorize_url(session) + "?" + urllib.parse.urlencode(params))


@app.route("/api/auth/salesforce/callback", methods=["GET"])
def auth_salesforce_callback():
    if request.args.get("error"):
        return redirect("/?sf_error=access_denied")
    if request.args.get("state") != session.get("oauth_state_sf"):
        return redirect("/?sf_error=state")
    code = request.args.get("code")
    if not code:
        return redirect("/?sf_error=no_code")
    cfg = get_sf_oauth_config(session)
    redir = cfg["redirect_uri"] or (_public_base_url() + "/api/auth/salesforce/callback")
    code_verifier = session.pop("oauth_pkce_verifier_sf", None)
    try:
        j = exchange_code_for_tokens(
            code, redir, code_verifier=code_verifier, session=session
        )
        session_apply_token_response(session, j)
        id_url = j.get("id") or session.get("salesforce_identity_url")
        at = j.get("access_token") or session.get("salesforce_access_token")
        if id_url and at:
            enrich_session_from_identity(session, at, id_url)
    except RuntimeError:
        return redirect("/?sf_error=token")
    return redirect("/?sf=connected")


@app.route("/api/salesforce/account", methods=["POST"])
def salesforce_fetch_account():
    """Load Account + Opportunity summary from the connected org (Account name or Id)."""
    body = request.get_json(silent=True) or {}
    lookup = (body.get("account_lookup") or body.get("lookup") or "").strip()
    sf_client, err = ensure_salesforce_client(session)
    if err:
        return jsonify({"success": False, "error": err}), 401
    try:
        result = resolve_account_bundle(sf_client, lookup)
    except Exception as e:
        logger.exception("Salesforce account fetch failed")
        return jsonify({"success": False, "error": str(e)}), 500

    if result.get("needs_pick"):
        return jsonify({
            "success": False,
            "needs_pick": True,
            "matches": result.get("matches") or [],
            "message": result.get("error") or "Multiple matches.",
        })

    if not result.get("ok"):
        # On any failure, drop any stale cached opps so we never use them
        # against the wrong account.
        session.pop("sf_account_opportunities", None)
        session.pop("sf_account_name_loaded", None)
        return jsonify({"success": False, "error": result.get("error") or "Lookup failed."}), 400

    # Persist the structured per-opp list in the session so /send_emails can
    # iterate one-email-per-opportunity. We also remember the account name we
    # loaded against, so we only use these opps when the user keeps that same
    # account in the form (a manual edit invalidates the cache).
    opportunities = result.get("opportunities") or []
    aname = result.get("account_name") or ""
    session["sf_account_opportunities"] = opportunities
    session["sf_account_name_loaded"] = aname

    return jsonify({
        "success": True,
        "account_id": result.get("account_id"),
        "account_name": aname,
        "opportunity_text": result.get("opportunity_text"),
        "opportunity_count": len(opportunities),
    })


@app.route("/api/auth/disconnect", methods=["POST", "GET"])
def auth_disconnect():
    body = request.get_json(silent=True) or {}
    p = (body.get("provider") or request.args.get("provider", "")).lower()
    if p in ("gmail", "google"):
        session.pop("google_refresh_token", None)
        session.pop("google_email", None)
        session.pop("google_access_token", None)
        session.pop("google_name", None)
        session.pop("google_given_name", None)
    elif p in ("outlook", "microsoft"):
        session.pop("microsoft_refresh_token", None)
        session.pop("outlook_email", None)
        session.pop("outlook_name", None)
        session.pop("outlook_given_name", None)
    elif p in ("salesforce", "sf"):
        session.pop("salesforce_refresh_token", None)
        session.pop("salesforce_access_token", None)
        session.pop("salesforce_instance_url", None)
        session.pop("salesforce_token_at", None)
        session.pop("salesforce_identity_url", None)
        session.pop("salesforce_username", None)
        session.pop("salesforce_org_id", None)
        session.pop("salesforce_org_name", None)
        session.pop("salesforce_display_name", None)
        # Drop the cached per-account opportunity list — it belongs to the
        # disconnected org and must never leak into a different connection.
        session.pop("sf_account_opportunities", None)
        session.pop("sf_account_name_loaded", None)
        # Also drop saved Connected App credentials so the user can paste a new org.
        clear_sf_oauth_config(session)
    if request.is_json or request.path.endswith("disconnect"):
        return jsonify({"success": True})
    return redirect("/")


if __name__ == '__main__':
    print("="*70)
    print("SALESFORCE EMAIL SENDER - WEB UI")
    print("="*70)
    print()
    print("Starting web server...")
    print("Open your browser and go to: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("="*70)

    app.run(debug=True, host='0.0.0.0', port=5000)
