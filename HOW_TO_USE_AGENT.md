# How to Use the Email Agent - Step by Step

## What is the Email Agent?

The Email Agent is an **autonomous system** that automatically generates and sends multiple emails for you. Just give it your sender email, recipient email, and it handles everything else!

## 3 Ways to Use the Agent

### ⚡ Option 1: Quick Agent (EASIEST - 2 Minutes)

**Best for:** Quick testing or one-time sends

1. Open `quick_agent.py` in any text editor
2. Find the configuration section at the top
3. Replace these values with yours:

```python
SENDER_EMAIL = "your-email@gmail.com"          # Your email
SENDER_PASSWORD = "your-app-password"          # Your Gmail app password
RECIPIENT_EMAIL = "recipient@example.com"      # Who to send to
```

4. Save the file
5. Run it:
```bash
python quick_agent.py
```

That's it! The agent will automatically:
- Load the data
- Generate professional emails
- Send them all
- Show you a detailed report

**Example output:**
```
======================================================================
QUICK EMAIL AGENT
======================================================================

✓ Initializing Email Agent...

Configuration:
  Sender: your-email@gmail.com
  Recipient: recipient@example.com
  Data Type: opportunity
  Data Source: file
  File: data/sample_opportunities.json

======================================================================
STARTING EMAIL CAMPAIGN
======================================================================

✓ [1/3] Sent to recipient@example.com
✓ [2/3] Sent to recipient@example.com
✓ [3/3] Sent to recipient@example.com

======================================================================
EMAIL CAMPAIGN REPORT
======================================================================

Status: ✓ SUCCESS

Statistics:
  Total Processed: 3
  Successfully Sent: 3
  Failed: 0
  Success Rate: 100.0%
  Duration: 5.23 seconds

======================================================================
```

---

### 🚀 Option 2: Interactive Agent

**Best for:** Flexible use when you want to choose options each time

Simply run:
```bash
python run_agent.py
```

The agent will ask you step-by-step:
1. Your sender email and password
2. Recipient email
3. Data source (file or Salesforce)
4. Data type (opportunity or case)

Then it runs automatically!

---

### 💻 Option 3: Python Code (Most Flexible)

**Best for:** Integration into your own scripts or automation

```python
import sys
sys.path.append('src')

from agent import EmailAgent

# 1. Create the agent with your credentials
agent = EmailAgent(
    sender_email="your-email@gmail.com",
    sender_password="your-app-password",
    sender_name="Your Name"  # Optional
)

# 2. Send emails (choose ONE of these)

# Option A: Send from file
report = agent.send_opportunity_emails(
    recipient_email="recipient@example.com",
    data_source='file',
    file_path='data/sample_opportunities.json',
    custom_message="Please review these opportunities."
)

# Option B: Send from Salesforce
agent.setup_salesforce(
    username="sf-username",
    password="sf-password",
    security_token="sf-token"
)
report = agent.send_opportunity_emails(
    recipient_email="recipient@example.com",
    data_source='salesforce',
    limit=10
)

# 3. View the report
agent.print_report(report)

# Check if successful
if report['success']:
    print("All emails sent successfully!")
else:
    print(f"{report['total_failed']} emails failed")
```

---

## Getting Your Credentials

### Gmail App Password

The agent needs an **App Password** (not your regular password):

1. Go to Google Account: https://myaccount.google.com
2. Enable **2-Factor Authentication** (Security > 2-Step Verification)
3. Go to: https://myaccount.google.com/apppasswords
4. Select "Mail" and your device
5. Click "Generate"
6. Copy the 16-character password (looks like: `abcd efgh ijkl mnop`)
7. Use this password in the agent (remove spaces)

### Salesforce Token (Optional)

Only needed if you want to fetch data from Salesforce:

1. Log in to Salesforce
2. Click your profile picture > Settings
3. Go to: My Personal Information > Reset My Security Token
4. Check your email for the token
5. Your full password is: `your-password` + `security-token` (combined)

---

## Common Use Cases

### Use Case 1: Send Daily Reports

Edit `quick_agent.py`:
```python
SENDER_EMAIL = "reports@company.com"
RECIPIENT_EMAIL = "manager@company.com"
DATA_SOURCE = "salesforce"
SF_LIMIT = 20
```

Run daily:
```bash
python quick_agent.py
```

### Use Case 2: Send to Multiple People

```python
from agent import EmailAgent

agent = EmailAgent(
    sender_email="your-email@gmail.com",
    sender_password="password"
)

# Send same emails to 3 people
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

### Use Case 3: Different Email Types

```python
agent = EmailAgent(
    sender_email="your-email@gmail.com",
    sender_password="password"
)

# Send opportunities
report1 = agent.send_opportunity_emails(
    recipient_email="sales@company.com",
    data_source='file',
    file_path='data/opportunities.json'
)

# Reset stats for new campaign
agent.reset_stats()

# Send cases
report2 = agent.send_case_emails(
    recipient_email="support@company.com",
    data_source='file',
    file_path='data/cases.json'
)
```

---

## Understanding the Report

After sending, the agent gives you a detailed report:

```python
{
    'success': True,              # Overall success
    'total_processed': 10,        # How many emails tried to send
    'total_sent': 9,              # Successfully sent
    'total_failed': 1,            # Failed to send
    'success_rate': 90.0,         # Percentage
    'duration_seconds': 15.3,     # How long it took
    'failed_items': [             # What failed and why
        {
            'type': 'opportunity',
            'name': 'Failed Opportunity',
            'reason': 'Connection timeout'
        }
    ]
}
```

---

## Troubleshooting

### "Authentication failed"
❌ **Problem:** Wrong email or password
✅ **Solution:**
- For Gmail, use App Password (not regular password)
- Check you copied it correctly (no spaces)

### "No data found"
❌ **Problem:** Can't find data file
✅ **Solution:**
- Check file path is correct
- Make sure file exists
- Try absolute path: `C:\path\to\file.json`

### "Connection timeout"
❌ **Problem:** Network or SMTP issue
✅ **Solution:**
- Check internet connection
- Verify SMTP settings (Gmail: smtp.gmail.com, port 587)
- Check firewall isn't blocking

### "Some emails failed"
❌ **Problem:** Some recipients invalid or connection issues
✅ **Solution:**
- Check `failed_items` in report for details
- Verify recipient email addresses
- Try resending failed ones

---

## Examples Included

The project includes working examples:

```bash
# Simple file-based example
python examples/agent_file_example.py

# Salesforce example
python examples/agent_salesforce_example.py

# Multiple recipients example
python examples/agent_multiple_recipients.py
```

---

## Quick Reference

| Task | Command |
|------|---------|
| **Quick send** | Edit `quick_agent.py` and run `python quick_agent.py` |
| **Interactive** | `python run_agent.py` |
| **File to one person** | `agent.send_opportunity_emails(recipient, data_source='file', file_path='...')` |
| **Salesforce to one** | `agent.send_opportunity_emails(recipient, data_source='salesforce')` |
| **Send to many** | `agent.send_bulk_to_multiple_recipients(recipients, ...)` |
| **Reset stats** | `agent.reset_stats()` |
| **View report** | `agent.print_report(report)` |

---

## Next Steps

1. **Start simple:** Try `quick_agent.py` with sample data
2. **Add your credentials:** Update with your real email
3. **Test with yourself:** Send emails to your own email first
4. **Go live:** Send to real recipients
5. **Automate:** Set up scheduled sending (daily/weekly)

Need more details? See:
- [AGENT_GUIDE.md](AGENT_GUIDE.md) - Complete agent documentation
- [README.md](README.md) - Full project documentation
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide

---

## Summary

✅ **Quick Agent** - Edit config and run (2 minutes)
✅ **Interactive Agent** - Answer prompts (5 minutes)
✅ **Python Code** - Full control (10 minutes)

The agent handles:
- Loading data (file or Salesforce)
- Generating professional emails
- Sending to one or many recipients
- Tracking success/failure
- Detailed reporting

**Just provide credentials and let it run!** 🚀
