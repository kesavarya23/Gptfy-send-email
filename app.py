"""
Salesforce Email Sender - Web UI
Simple web interface for sending emails
"""

from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import sys
import secrets
import os
import time
import urllib.parse
import re
import requests
sys.path.append('src')

from agent import EmailAgent
from utils.data_generator import DataGenerator
from utils.email_generator import EmailGenerator
from services.oauth_send import (
    get_google_user_email,
    get_microsoft_access_token,
    get_microsoft_user_email,
    send_gmail,
    send_outlook,
)
from utils.context_extract import (
    build_salesforce_context,
    combined_opportunity_text,
    is_uploaded_file_without_extractable_text,
)

app = Flask(__name__)
# Use a stable secret in production (e.g. Vercel env) so OAuth sessions survive restarts
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
CORS(app)  # Enable CORS for all routes


def _do_send_email(
    send_method: str,
    agent,
    to_list: list,
    subject: str,
    html_content: str,
    plain_text: str,
    cc: list = None,
    bcc: list = None,
) -> bool:
    if not to_list:
        return False
    cc = list(cc or [])
    bcc = list(bcc or [])
    if send_method == "gmail":
        cid = os.getenv("GOOGLE_CLIENT_ID", "")
        cs = os.getenv("GOOGLE_CLIENT_SECRET", "")
        rt = session.get("google_refresh_token")
        from_addr = session.get("google_email", "")
        if not (cid and cs and rt and from_addr):
            return False
        return send_gmail(
            cid, cs, rt, from_addr, to_list, subject, plain_text, html_content,
            cc=cc, bcc=bcc,
        )
    if send_method == "outlook":
        rt = session.get("microsoft_refresh_token")
        if not rt:
            return False
        at = get_microsoft_access_token(rt)
        if not at:
            return False
        return send_outlook(
            at, to_list, subject, plain_text,
            html=html_content,
            cc=cc, bcc=bcc,
        )
    if agent is None:
        return False
    return agent.email_service.send_email(
        to_email=to_list,
        subject=subject,
        html_content=html_content,
        plain_text=plain_text,
        cc=cc,
        bcc=bcc,
    )


def _as_bool(v):
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).lower() in ("true", "1", "yes", "on")


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
            "strict_sf_context": str(f.get("strict_sf_context", "")).lower() in (
                "true", "1", "on", "yes",
            ),
            "account_name": f.get("account_name") or "",
            "opportunity_text": f.get("opportunity_text") or "",
        }
        return data, request.files.get("opportunity_file")
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
    data["strict_sf_context"] = _as_bool(data.get("strict_sf_context", False))
    data["account_name"] = data.get("account_name") or ""
    data["opportunity_text"] = data.get("opportunity_text") or ""
    return data, None


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/send_emails', methods=['POST'])
def send_emails():
    """Send emails endpoint"""
    try:
        # Get form data (JSON or multipart for file upload)
        data, opportunity_file = _parse_send_payload()

        sender_email = data.get("sender_email")
        sender_password = data.get("sender_password")
        sender_name = data.get("sender_name", sender_email)
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
        strict_sf = _as_bool(data.get("strict_sf_context")) and use_custom_context
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
                'error': 'Please specify at least 1 opportunity, case, or business email'
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
            opportunities = data_generator.generate_opportunities(num_opportunities)

            for i, opp in enumerate(opportunities, 1):
                try:
                    email_content = email_generator.generate_opportunity_email(
                        opportunity_data=opp,
                        custom_message=custom_message
                    )

                    success = _do_send_email(
                        send_method, agent, to_list,
                        email_content['subject'], email_content['html_content'],
                        email_content.get('plain_text') or '',
                        cc=cc_list, bcc=bcc_list,
                    )

                    all_emails.append({
                        'type': 'Opportunity',
                        'name': opp['opportunity_name'],
                        'status': 'Sent' if success else 'Failed',
                        'number': i
                    })

                except Exception as e:
                    all_emails.append({
                        'type': 'Opportunity',
                        'name': opp.get('opportunity_name', 'Unknown'),
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

            for i, case in enumerate(cases, 1):
                try:
                    email_content = email_generator.generate_case_email(
                        case_data=case,
                        custom_message=custom_message
                    )

                    success = _do_send_email(
                        send_method, agent, to_list,
                        email_content['subject'], email_content['html_content'],
                        email_content.get('plain_text') or '',
                        cc=cc_list, bcc=bcc_list,
                    )

                    all_emails.append({
                        'type': 'Case',
                        'name': f"Case {case['case_number']}",
                        'status': 'Sent' if success else 'Failed',
                        'number': i
                    })

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

            for i, business_email in enumerate(business_emails, 1):
                try:
                    email_content = email_generator.generate_business_email(business_email)

                    success = _do_send_email(
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

                    all_emails.append({
                        'type': type_names.get(business_email['type'], business_email['type']),
                        'name': email_content['subject'],
                        'status': 'Sent' if success else 'Failed',
                        'number': i
                    })

                except Exception as e:
                    all_emails.append({
                        'type': 'Business Email',
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
    return jsonify({
        "gmail_connected": g_ok,
        "gmail_email": session.get("google_email", ""),
        "outlook_connected": o_ok,
        "outlook_email": session.get("outlook_email", ""),
        "google_configured": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")),
        "microsoft_configured": bool(
            os.getenv("MICROSOFT_CLIENT_ID") and os.getenv("MICROSOFT_CLIENT_SECRET")
        ),
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
        email = get_google_user_email(at)
        if email:
            session["google_email"] = email
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
        em = get_microsoft_user_email(j["access_token"])
        if em:
            session["outlook_email"] = em
    return redirect("/?outlook=connected")


@app.route("/api/auth/disconnect", methods=["POST", "GET"])
def auth_disconnect():
    body = request.get_json(silent=True) or {}
    p = (body.get("provider") or request.args.get("provider", "")).lower()
    if p in ("gmail", "google"):
        session.pop("google_refresh_token", None)
        session.pop("google_email", None)
        session.pop("google_access_token", None)
    elif p in ("outlook", "microsoft"):
        session.pop("microsoft_refresh_token", None)
        session.pop("outlook_email", None)
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
