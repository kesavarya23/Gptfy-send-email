# Gptfy Salesforce Email Sender

A Flask web app for composing and sending realistic, AI-styled business emails
generated from Salesforce-style data. Send via SMTP, Gmail (OAuth), or
Outlook / Microsoft 365 (OAuth), and optionally pull live Account /
Opportunity context from a connected Salesforce org.

## Features

- Web UI (`templates/index.html`) — no CLI required
- Three send methods:
  - **SMTP** (Gmail App Password, Outlook/Office 365, etc.)
  - **Gmail API** via Google OAuth
  - **Microsoft Graph** via Microsoft OAuth
- Salesforce OAuth — load Account + Opportunity summaries directly from your org
- Generators for opportunity, case, and business emails (meeting invites,
  follow-ups, project updates, reminders, etc.)
- Optional custom Salesforce context (paste text or upload a `.txt` / `.md`
  / image file; OCR via Tesseract if available)
- CC / BCC, multiple To addresses, configurable per-email delay

## Project layout

```
app.py                    Flask app, all HTTP routes, OAuth flows
Procfile                  gunicorn entry for Heroku-style hosts
vercel.json               Vercel deployment config
runtime.txt               Python version pin
requirements.txt          Python dependencies
templates/index.html      Web UI (single-page Flask template)

src/
  agent.py                Thin EmailAgent wrapper around EmailService (SMTP)
  services/
    email_service.py      SMTP sender
    oauth_send.py         Gmail API + Microsoft Graph send helpers
    sf_oauth.py           Salesforce OAuth + token refresh
    sf_live_account.py    Salesforce Account/Opportunity lookups
  utils/
    data_generator.py     Random opportunity/case/business email generator
    email_generator.py    Jinja2 email template renderer
    context_extract.py    Custom context + file/image text extraction
  templates/              HTML email templates (Jinja2)
```

## Local setup

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Copy and fill the environment file
cp .env.example .env       # Windows: copy .env.example .env
# Edit .env and fill the OAuth client IDs/secrets you plan to use.

# 3. Run the dev server
python app.py
# Open http://localhost:5000
```

## Environment variables

See `.env.example` for the full list. The minimum is `FLASK_SECRET_KEY`.
Add OAuth credentials only for the providers you actually want to use:

- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_OAUTH_REDIRECT`
- `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET` / `MICROSOFT_TENANT` /
  `MICROSOFT_OAUTH_REDIRECT`
- `SALESFORCE_CLIENT_ID` / `SALESFORCE_CLIENT_SECRET` /
  `SALESFORCE_OAUTH_REDIRECT`
- `SMTP_HOST` / `SMTP_PORT` (override the Gmail defaults if you use SMTP
  with another provider)
- `TESSERACT_CMD` (optional; path to the Tesseract OCR binary for image
  context extraction)

## Deployment

See `DEPLOYMENT_GUIDE.md` for step-by-step instructions on deploying to
Vercel (and notes for Railway / other hosts).

## Notes

- `.env` is git-ignored. Never commit real secrets — use `.env.example` as
  the public template.
- OAuth callback URLs configured in Google / Microsoft / Salesforce must
  match the values in your `.env` exactly (scheme, host, path).
