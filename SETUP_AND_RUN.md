# Setup and Run Guide - Your Configured Agent

## ✅ Your Agent is Already Configured!

Your email agent is ready with these credentials:
- **Sender:** gptfy2025@gmail.com
- **Recipient:** kalanithi@cloudcompliance.app
- **Data:** Sample opportunities (3 emails will be sent)

## Step 1: Install Python (If Not Already Installed)

### Check if Python is installed:
Open Command Prompt and type:
```bash
python --version
```

If you see a version number (like `Python 3.11.0`), you're good! Skip to Step 2.

### If Python is not installed:

1. Download Python from: https://www.python.org/downloads/
2. **Important:** During installation, check "Add Python to PATH"
3. Install and restart Command Prompt

## Step 2: Install Dependencies

Open Command Prompt in the project folder and run:

```bash
cd "c:\Projects\Gptfy send email\Gptfy-send-email"
pip install -r requirements.txt
```

This installs:
- `simple-salesforce` - Salesforce API
- `python-dotenv` - Configuration
- `jinja2` - Email templates
- `pandas` - Data handling
- `requests` - HTTP requests

## Step 3: Gmail App Password Setup

**⚠️ IMPORTANT:** Gmail requires an "App Password" for SMTP access.

### Current Status:
Your password `Kesav@12345` looks like a regular Gmail password. You need to:

1. **Enable 2-Factor Authentication:**
   - Go to: https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Generate App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Click "Generate"
   - Copy the 16-character password (like: `abcd efgh ijkl mnop`)

3. **Update the password in quick_agent.py:**
   - Open `quick_agent.py`
   - Replace line 18:
   ```python
   SENDER_PASSWORD = "your-16-char-app-password"  # No spaces
   ```

### Alternative: Use Regular Password (Less Secure)

If you don't want to use 2FA, you can try:
1. Go to: https://myaccount.google.com/lesssecureapps
2. Turn ON "Allow less secure apps"
3. Keep current password in `quick_agent.py`

**Note:** Google is phasing this out, so App Password is recommended.

## Step 4: Run the Agent

Once Python and dependencies are installed:

```bash
python quick_agent.py
```

### What will happen:
1. Agent loads 3 sample opportunities from `data/sample_opportunities.json`
2. Generates professional HTML emails for each
3. Sends all 3 emails to kalanithi@cloudcompliance.app
4. Shows you a detailed report

### Expected Output:

```
======================================================================
QUICK EMAIL AGENT
======================================================================

✓ Initializing Email Agent...

Configuration:
  Sender: gptfy2025@gmail.com
  Recipient: kalanithi@cloudcompliance.app
  Data Type: opportunity
  Data Source: file
  File: data/sample_opportunities.json

======================================================================
STARTING EMAIL CAMPAIGN
======================================================================

2025-01-20 10:30:15 - INFO - Loaded 3 opportunities
2025-01-20 10:30:15 - INFO - Processing opportunity 1/3: Enterprise Cloud Migration - Acme Corp
2025-01-20 10:30:16 - INFO - ✓ Sent: Salesforce Opportunity Update: Enterprise Cloud Migration - Acme Corp
2025-01-20 10:30:16 - INFO - Processing opportunity 2/3: CRM Implementation - TechStart Inc
2025-01-20 10:30:17 - INFO - ✓ Sent: Salesforce Opportunity Update: CRM Implementation - TechStart Inc
2025-01-20 10:30:17 - INFO - Processing opportunity 3/3: Security Audit - Global Finance
2025-01-20 10:30:18 - INFO - ✓ Sent: Salesforce Opportunity Update: Security Audit - Global Finance

======================================================================
EMAIL CAMPAIGN REPORT
======================================================================

Status: ✓ SUCCESS

Statistics:
  Total Processed: 3
  Successfully Sent: 3
  Failed: 0
  Success Rate: 100.0%
  Duration: 3.45 seconds

======================================================================

✓ Campaign completed successfully!
```

## Step 5: Verify Emails

Check the inbox: **kalanithi@cloudcompliance.app**

You should see 3 emails with subjects like:
- "Salesforce Opportunity Update: Enterprise Cloud Migration - Acme Corp"
- "Salesforce Opportunity Update: CRM Implementation - TechStart Inc"
- "Salesforce Opportunity Update: Security Audit - Global Finance"

Each email will have:
- Professional blue-themed HTML design
- Opportunity details (name, account, stage, amount, etc.)
- Custom message: "Please review these Salesforce opportunities and provide your feedback."

## Troubleshooting

### Error: "Authentication failed" or "Username and Password not accepted"

**Problem:** Gmail password issue

**Solutions:**
1. Use App Password (recommended - see Step 3)
2. Enable "Less secure apps" (not recommended)
3. Check 2FA is enabled and App Password is correct

### Error: "ModuleNotFoundError: No module named 'agent'"

**Problem:** Dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt
```

### Error: "FileNotFoundError: data/sample_opportunities.json"

**Problem:** Running from wrong directory

**Solution:**
```bash
cd "c:\Projects\Gptfy send email\Gptfy-send-email"
python quick_agent.py
```

### Error: "Connection timeout" or "SMTP error"

**Problem:** Network or firewall blocking SMTP

**Solutions:**
1. Check internet connection
2. Try different network (not corporate firewall)
3. Check antivirus isn't blocking port 587

### No emails received

**Check:**
1. Spam/Junk folder
2. Email address is correct: kalanithi@cloudcompliance.app
3. Check sender's "Sent" folder in Gmail

## Customizing the Agent

### Send Different Data:

Edit `quick_agent.py`:

```python
# For cases instead of opportunities
DATA_TYPE = "case"
FILE_PATH = "data/sample_cases.json"

# For your own data
FILE_PATH = "data/my_opportunities.json"
```

### Change Message:

```python
CUSTOM_MESSAGE = "Your custom message here"
```

### Send to Multiple Recipients:

Use the Python code method:

```python
import sys
sys.path.append('src')
from agent import EmailAgent

agent = EmailAgent(
    sender_email="gptfy2025@gmail.com",
    sender_password="your-app-password"
)

report = agent.send_bulk_to_multiple_recipients(
    recipient_emails=[
        'person1@company.com',
        'person2@company.com',
        'person3@company.com'
    ],
    data_type='opportunity',
    data_source='file',
    file_path='data/sample_opportunities.json'
)

agent.print_report(report)
```

## Other Ways to Run

### Interactive Mode:
```bash
python run_agent.py
```
Prompts you for all settings.

### Command Line:
```bash
python src/main.py --source file --type opportunity --file data/sample_opportunities.json --recipient kalanithi@cloudcompliance.app
```

### Python Script:
Create a file `my_agent.py`:
```python
import sys
sys.path.append('src')
from agent import EmailAgent

agent = EmailAgent(
    sender_email="gptfy2025@gmail.com",
    sender_password="your-password"
)

report = agent.send_opportunity_emails(
    recipient_email="kalanithi@cloudcompliance.app",
    data_source='file',
    file_path='data/sample_opportunities.json'
)

print(f"Sent {report['total_sent']} emails!")
```

Run: `python my_agent.py`

## Quick Summary

**Configured and ready to go:**
- ✅ Sender: gptfy2025@gmail.com
- ✅ Recipient: kalanithi@cloudcompliance.app
- ✅ Data: 3 sample opportunities
- ⚠️ Need: Gmail App Password

**To run:**
1. Install Python
2. Run: `pip install -r requirements.txt`
3. Get Gmail App Password
4. Update password in `quick_agent.py`
5. Run: `python quick_agent.py`

**Result:** 3 professional emails sent automatically! 🚀

## Need Help?

See these guides:
- [HOW_TO_USE_AGENT.md](HOW_TO_USE_AGENT.md) - Detailed usage guide
- [AGENT_GUIDE.md](AGENT_GUIDE.md) - Complete API reference
- [README.md](README.md) - Full project documentation

You're all set! Just get that App Password and run it! 🎉
