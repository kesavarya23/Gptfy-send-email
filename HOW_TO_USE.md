# How to Use This App

A simple AI-powered email sender. You connect your inbox (Gmail / Outlook), optionally pull data from Salesforce, fill in who to email and how many — and the app writes and sends the emails for you.

---

## The screen at a glance

When you open the app, you'll see **two columns** side by side:

| Left side — **Setup & Connections** | Right side — **Compose & Send** |
| --- | --- |
| Connect your sending email account | Type recipients (To / CC / BCC) |
| (Optional) Connect Salesforce + load an account | Choose how many emails to send |
| (Optional) Connect "reply mailboxes" for testing | Pick topic style (Default / Custom) |
| | Set delay between emails and click **Send Emails** |

Below the form (right column) you'll see the **Results panel** after you send — it shows how many succeeded and lists each email with a **Get reply** button for testing.

---

## Step-by-step

### 1. Open the app
Open the app in your browser: [https://gptfy-send-email.vercel.app/](https://gptfy-send-email.vercel.app/)

### 2. Set up your sender (left column → "Sender Information")
Pick **one** sending method using the toggle at the top:
- **Gmail (OAuth)** → click **Connect Google** → sign in with the Google account you want to send from. A green ✓ appears once connected.
- **Outlook (OAuth)** → click **Connect Microsoft** → sign in with your Microsoft / work account.
- **SMTP (password)** → type your sender email, **app password**, and your name. Use this only if you can't use OAuth.

> Tip: OAuth (Gmail / Outlook) is easier and safer — you don't need to create app passwords.

### 3. (Optional) Connect Salesforce — left column → "Salesforce context"
Only needed if you want emails written from real CRM data:
1. Click **Connect Salesforce** and log into your org.
2. In the **Account name** box, type your account (e.g. *Acme Corp*) and click **Load from org**.
3. The app pulls that account's opportunities and stores them for the AI to use.

If you don't want to use Salesforce, skip this section — the app will generate sample emails on its own.

> **Want to give the AI extra context?** Use the **Opportunity details (text)** box to paste anything you want the AI to know about — stage, amount, contacts, next steps, or even a custom instruction like *"Mention that our pricing is locked for 30 days and ask them to confirm by Friday."* You can also **upload a file or screenshot** (PDF, image, .txt) in the same panel — the app reads it and feeds the content to the AI.

### 4. Add recipients (right column → "Recipients")
- **To** — at least one email is required. Separate multiple with commas, semicolons, or new lines.
- **CC / BCC** — optional, same format.

### 5. Choose how many emails (right column → "Email Configuration")
- **No. of emails to send** — type a number (e.g. `3`).
- **Topic selection**:
  - **Default** → the AI picks varied topics automatically (recommended for first-time users).
  - **Custom** → you tick the topics you want: *Meeting Invitation, Follow-up, Thank You, Project Update, Reminder, Product Queries, Demo Enquiry,* etc.
- **Email Delay** — seconds between each email (set `0` to send all at once, or `5–10` to space them out and avoid spam filters).

### 6. Click **Send Emails**
The button at the bottom of the right column runs everything:
1. The AI writes each email using your Salesforce + custom-message context.
2. Each email is sent through your connected Gmail / Outlook / SMTP account.
3. A **Results** panel appears below with **Total Sent**, **Failed**, and **Success Rate**, plus one row per email.

Open your **Sent** folder to verify the emails actually went out.

### 7. (Optional) Test replies — "Reply mailboxes"
This is for QA / demo purposes only:
1. Go to the **Reply mailboxes** panel on the left and connect a second test inbox (e.g. a Gmail account belonging to a fake "customer").
2. After sending, click **Get reply** next to any email in the Results panel.
3. The app simulates that contact replying to you (interested / asking / declining / custom), so you can see the full conversation thread without manually logging into the test inbox.

---

## Quick troubleshooting

| Problem | What to do |
| --- | --- |
| "Please connect Google / Microsoft first" | Go back to the **Sender** panel and click the connect button. |
| "Custom Salesforce context is on but no content was found" | Either type/upload some context, or untick the Salesforce **"Use this context"** option. |
| Email shows **Failed** in red | Hover the row to see the error. Most common: wrong app password, expired OAuth (reconnect), or invalid recipient address. |
| Want to start over | Click **Disconnect** next to any connection to remove it, or refresh the page. |

---

## That's it

Connect your inbox → (optionally) load a Salesforce account → enter recipients → pick how many emails → click **Send**. The app handles the writing and sending for you.
