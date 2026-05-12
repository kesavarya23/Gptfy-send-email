# Salesforce Email Sender — Architecture

A Flask web app that generates and sends personalised B2B emails from Gmail or Outlook, grounded in real Salesforce account and opportunity data, with subject + body composed by an OpenAI model.

**Live URL:** https://gptfy-send-email.vercel.app

---

## At a glance

| | |
|---|---|
| OAuth providers | **3** — Google, Microsoft, Salesforce |
| HTTP routes | **11** |
| Service modules | **6** |
| Hosted on | Vercel (serverless `@vercel/python`) |
| Stateful storage | None — signed Flask cookies only |
| Frontend | Single page, vanilla JS, no build step |

---

## Tech stack

### Backend runtime
- `Python 3` + `Flask 3` single-file app (`app.py`)
- `flask-cors` for browser API calls
- `requests` for all outbound HTTP (Google, Microsoft, Salesforce, OpenAI)
- `jinja2` for legacy email templates

### Integrations
- `google-api-python-client` + `google-auth` — Gmail send
- `msal` — Microsoft refresh-token rotation; Graph called via `requests`
- `simple-salesforce` + raw OAuth — SOQL queries on Account / Opportunity / Contact
- `openai 2.x` — chat completions in JSON mode for email composition
- `pytesseract` + `Pillow` — local OCR with OpenAI vision fallback for screenshot uploads

### Frontend & infrastructure
- Single HTML page `templates/index.html`; vanilla JS — no React or build step
- `vercel.json` routes everything to `app.py` via `@vercel/python`
- Sessions are signed Flask cookies — no DB or Redis needed
- Configuration via Vercel environment variables (`FLASK_SECRET_KEY`, OAuth client IDs/secrets, OpenAI key)

---

## System architecture

Three logical layers: a static-feeling browser UI, a Flask API that mediates every external call, and per-user OAuth tokens kept inside a signed cookie so the app stays stateless and serverless-friendly.

### Component map

| Layer | Component | Responsibility | Key files |
|---|---|---|---|
| Browser | `index.html` UI | Sender method picker, recipients, Salesforce context, topic mix, send button | `templates/index.html` |
| Browser | `salesforce_setup.html` | Per-user form for the Connected App's Consumer Key / Secret / Login URL | `templates/salesforce_setup.html` |
| Web API | Flask routes | OAuth start/callback for Google, Microsoft, Salesforce; `/send_emails` orchestrator; `/api/auth/status` | `app.py` |
| Service | `oauth_send` | Send via Gmail API or Microsoft Graph using stored refresh tokens | `src/services/oauth_send.py` |
| Service | `email_service` | Legacy SMTP path (Gmail App Password / generic SMTP) | `src/services/email_service.py` |
| Service | `ai_writer` | Compose subject + paragraphs with OpenAI; render plain text + HTML | `src/services/ai_writer.py` |
| Service | `sf_oauth` | Salesforce OAuth flow, PKCE, refresh, identity enrichment | `src/services/sf_oauth.py` |
| Service | `sf_live_account` | SOQL on Account / open Opportunities / Contacts; flatten for the AI prompt | `src/services/sf_live_account.py` |
| Utils | `context_extract` | Read user-uploaded text/markdown; OCR images via Tesseract → OpenAI vision | `src/utils/context_extract.py` |
| External | Google / Microsoft / Salesforce / OpenAI | OAuth providers + send / SOQL / LLM APIs | — |

### Architecture diagram (text)

```
                        Browser (templates/index.html)
                                  |
                                  v
+-------------------------------------------------------------+
|                       Flask app (app.py)                    |
|                                                             |
|   /api/auth/google ----> Google OAuth     -----> Gmail API  |
|   /api/auth/outlook ---> Microsoft OAuth  -----> MS Graph   |
|   /api/auth/salesforce > Salesforce OAuth -----> SOQL       |
|                                                             |
|   /send_emails  --> ai_writer ---> OpenAI Chat Completions  |
|                  -> oauth_send/email_service ---> SMTP/API  |
+-------------------------------------------------------------+
                                  |
                signed Flask cookie holds:
        - google_refresh_token / microsoft_refresh_token
        - salesforce_refresh_token + instance_url
        - per-user Connected App credentials
```

---

## Three OAuth flows, one cookie session

Each provider has its own start + callback route. Tokens are stored in the Flask session (a signed cookie) so multiple users on the same Vercel deployment never see each other's data, and there is no DB to manage.

| Provider | Start route | Callback route | Auth pattern | Stored in session |
|---|---|---|---|---|
| Google (Gmail) | `/api/auth/google` | `/api/auth/google/callback` | OAuth2 code flow + offline access | `google_refresh_token` |
| Microsoft (Outlook) | `/api/auth/outlook` | `/api/auth/outlook/callback` | OAuth2 code flow + `offline_access` | `microsoft_refresh_token` |
| Salesforce (per-user Connected App) | `/api/auth/salesforce` | `/api/auth/salesforce/callback` | OAuth2 code flow + PKCE | `salesforce_refresh_token` + `instance_url` |

> **Why this is interesting in the demo:** every user authenticates with their own Google / Microsoft / Salesforce accounts — there is no shared mailbox or shared service account. The Salesforce Connected App is even configured per user via `/salesforce/setup`, so anyone in the org can plug in their own sandbox or production org without redeploying.

---

## End-to-end send flow

What actually happens between clicking **Send Emails** and the message arriving in the recipient's inbox.

### Step 1 — UI submit
Browser POSTs `/send_emails` with sender method, recipients, CC/BCC, count, topic mix, optional Salesforce account / opportunity text, and any uploaded screenshot.

### Step 2 — Build context
- If a Salesforce account is loaded, `resolve_account_bundle()` runs SOQL for **Account**, **open Opportunities**, and **Contacts**.
- Uploaded images are OCR'd via Tesseract or OpenAI vision.
- Output: a flat text blob the LLM can consume.

### Step 3 — Compose
For each email, `ai_writer.compose_email()` calls the LLM in JSON mode with:
- A **system prompt** with hard rules + the team's editable brand-voice file (`prompts/email_system_prompt.md`)
- A **user prompt** that includes the Salesforce facts and a per-email *variation hint* so a batch of N emails has N distinct openers

Output is normalised to `{ subject, paragraphs[] }` and rendered to plain text + minimal HTML.

### Step 4 — Send
Depending on the chosen sender method:
- **Gmail OAuth** → `send_gmail()` refreshes the access token and POSTs to the Gmail API
- **Outlook OAuth** → `get_microsoft_access_token()` via MSAL, then POST to `graph.microsoft.com/v1.0/me/sendMail`
- **SMTP** → `EmailService.send_email()` over `STARTTLS` with username + app password

> **Salesforce-anchored batches:** each email is bound to *one* open opportunity from the chosen account (cycled if the user asks for more emails than open opps). Closed-Won / Closed-Lost are intentionally excluded — outreach only goes against deals still in pipeline.

---

## HTTP routes

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Single-page UI |
| `POST` | `/send_emails` | Generate + send the batch |
| `GET` | `/api/auth/status` | Which providers are connected; which are configured |
| `GET` | `/api/auth/google` | Start Gmail OAuth |
| `GET` | `/api/auth/google/callback` | Exchange code → refresh token |
| `GET` | `/api/auth/outlook` | Start Microsoft OAuth |
| `GET` | `/api/auth/outlook/callback` | Exchange code → refresh token |
| `GET` / `POST` | `/salesforce/setup` | In-app form for the Connected App credentials |
| `GET` | `/api/auth/salesforce` | Start Salesforce OAuth (PKCE) |
| `GET` | `/api/auth/salesforce/callback` | Exchange code + verifier → refresh token |
| `POST` | `/api/salesforce/account` | Resolve an Account name/Id → opportunities + contacts |
| `POST` / `GET` | `/api/auth/disconnect` | Drop tokens from the session |

---

## How AI generation stays "demo-safe"

### Hard rules in the system prompt
- Use only the facts the prompt provides — never invent prices, dates, names, or partnerships
- Output strict JSON: `{ subject, paragraphs[] }`
- Subject ≤ 80 chars, no clickbait, no ALL CAPS
- Banned worn-out openers ("I hope this finds you well", "Just checking in", etc.)
- Vary opening structure, subject pattern, and sign-off across a batch

### Per-email variation
- A `variation_hint` argument is injected high in the user prompt for each email in a batch
- Temperature gets a small jitter (`+0.2 ± 0.1`) so 5 emails land on 5 different points of the sampling curve
- Output is parsed defensively: stripped code fences, salvage JSON between first `{` and last `}`, fall back to template-based generation on any failure

### Graceful degradation
Every external call has a fallback:
- No OpenAI key → Jinja templates
- OCR unavailable → vision API
- Salesforce not connected → random sample context
- Provider OAuth not configured → SMTP path remains

---

## Deployment + configuration

### Vercel deployment
- `vercel.json` uses `@vercel/python` and routes `/(.*)` to `app.py`
- Each request is a fresh serverless invocation. State lives in the signed cookie — no DB or Redis required
- `FLASK_SECRET_KEY` must be a stable env var; otherwise cookies break between cold starts and OAuth state checks fail

### Required Vercel environment variables

```
FLASK_SECRET_KEY
PUBLIC_BASE_URL
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_OAUTH_REDIRECT
MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET
MICROSOFT_TENANT
MICROSOFT_OAUTH_REDIRECT
OPENAI_API_KEY
OPENAI_MODEL
OPENAI_TEMPERATURE
OPENAI_TIMEOUT
```

> **Note:** Salesforce credentials are NOT env vars — each user enters them via the in-app `/salesforce/setup` page.

### Provider portals that also need configuration

| Portal | Setting | Value |
|---|---|---|
| Google Cloud Console | Authorized redirect URIs | `https://gptfy-send-email.vercel.app/api/auth/google/callback` |
| Azure Portal — Authentication | Web platform redirect URI | `https://gptfy-send-email.vercel.app/api/auth/outlook/callback` |
| Salesforce Connected App | Callback URL | `https://gptfy-send-email.vercel.app/api/auth/salesforce/callback` |

---

## Suggested demo script (5–7 minutes)

| # | Beat | What you click / say | What it proves |
|---|---|---|---|
| 1 | Open the app | Show the deployed URL; point to the three sender method pills | Stateless serverless deploy on Vercel |
| 2 | Connect Gmail | Click Connect Google → consent → land back with a green check | OAuth2 code flow + refresh token stored in cookie |
| 3 | Connect Outlook | Same flow with Microsoft | Multi-provider design; MSAL for token rotation |
| 4 | Connect Salesforce org | Open `/salesforce/setup`, paste Consumer Key + Secret of your Connected App | Per-user Connected App — anyone can plug in their own org |
| 5 | Load a real account | Tick *Use custom Account & Opportunity*, enter an Account name, click *Load from org* | Live SOQL: Account + open Opportunities + Contacts |
| 6 | Send a small batch | Set count = 3, pick a topic mix, hit Send Emails | Per-opportunity emails, AI-composed, anti-repetition variation hints |
| 7 | Show one inbox | Open Gmail and Outlook; show the sent message | Real send via Gmail API and Microsoft Graph |
| 8 | Show the prompt file | Open `prompts/email_system_prompt.md` | Brand voice is editable without code changes |

---

## 30-second verbal summary

> This is a stateless Flask app on Vercel. Users connect Gmail, Outlook, or their own Salesforce org via OAuth — all tokens live in a signed cookie, so there's no database. When you click Send, the app pulls real Account and open Opportunity data from Salesforce via SOQL, asks an OpenAI model to write each email anchored to one specific opportunity (with anti-repetition variation hints across the batch), and then sends through the Gmail API or Microsoft Graph. Every external call has a graceful fallback — no OpenAI key falls back to Jinja templates, no Salesforce falls back to random sample context, OCR falls back from Tesseract to OpenAI vision.

---

## Things to flag if asked

### Security follow-ups
- Rotate the secrets that have been in screenshots / chat history (Google, Microsoft, OpenAI, Flask)
- Confirm `.env` stays gitignored
- Consider replacing the cookie session with an encrypted server-side store if user volume grows past the 4 KB cookie limit

### Possible next features
- Send-later scheduling and per-recipient delay (UI already exposes a delay field)
- Reply-thread tracking via Gmail `threadId` / Graph `conversationId`
- Per-org system-prompt overrides (the file path is already env-configurable)
- Per-user audit log of sent emails (today only the in-page result tally exists)

---

## File map (for engineers joining the project)

```
gptfy-send-email/
├── app.py                              # Flask app + all routes
├── vercel.json                         # @vercel/python routing
├── requirements.txt                    # Python deps
├── runtime.txt / Procfile              # Heroku-style fallback
├── .env / .env.example                 # Local-only secrets (gitignored)
├── prompts/
│   └── email_system_prompt.md          # Editable brand voice
├── templates/
│   ├── index.html                      # Single-page UI
│   └── salesforce_setup.html           # Per-user Connected App form
└── src/
    ├── agent.py                        # SMTP wrapper
    ├── services/
    │   ├── ai_writer.py                # OpenAI email composer
    │   ├── email_service.py            # SMTP send
    │   ├── oauth_send.py               # Gmail API + Graph send
    │   ├── sf_live_account.py          # SOQL Account + Opps + Contacts
    │   └── sf_oauth.py                 # Salesforce OAuth + token refresh
    ├── templates/                      # Legacy Jinja email templates
    │   ├── meeting_invitation.html
    │   ├── followup.html
    │   ├── thank_you.html
    │   ├── project_update.html
    │   ├── reminder.html
    │   ├── case_email.html
    │   ├── opportunity_email.html
    │   ├── professional_context_email.html
    │   └── generic_business.html
    └── utils/
        ├── context_extract.py          # OCR + text extraction
        ├── data_generator.py           # Sample context fallback
        └── email_generator.py          # Jinja template renderer
```
