# Random Email Generator Guide

## ✨ NEW Feature: Generate Random Salesforce Data!

The agent can now **generate random Salesforce data** automatically! No need for pre-made files - just tell the agent how many emails you want, and it creates realistic data and sends them!

## 🎯 What You Can Do

1. **Specify the number** - Send 5, 10, 50, or any number of emails
2. **Choose the type** - Opportunities, Cases, or Both
3. **Automatic generation** - Agent creates realistic random data
4. **Instant sending** - All emails sent automatically

## 🚀 Three Ways to Use

### Option 1: Smart Agent (Edit & Run) ⚡ EASIEST

**Best for:** When you know exactly what you want

1. Open [smart_agent.py](smart_agent.py)
2. Edit the configuration:

```python
# How many emails?
EMAIL_TYPE = "both"        # "opportunity", "case", or "both"
NUM_OPPORTUNITIES = 5      # Number of opportunity emails
NUM_CASES = 5              # Number of case emails
```

3. Run:
```bash
python smart_agent.py
```

**Example configurations:**

```python
# Send 10 opportunity emails only
EMAIL_TYPE = "opportunity"
NUM_OPPORTUNITIES = 10

# Send 20 case emails only
EMAIL_TYPE = "case"
NUM_CASES = 20

# Send 15 opportunities + 10 cases = 25 total
EMAIL_TYPE = "both"
NUM_OPPORTUNITIES = 15
NUM_CASES = 10
```

### Option 2: Interactive Smart Agent 🎮 FLEXIBLE

**Best for:** When you want to be asked each time

Simply run:
```bash
python interactive_smart_agent.py
```

The agent will ask you:
- How many opportunity emails?
- How many case emails?
- Custom message?
- Confirm before sending?

### Option 3: Python Code 💻 MOST POWERFUL

**Best for:** Custom scripts and automation

```python
import sys
sys.path.append('src')

from agent import EmailAgent
from utils.data_generator import DataGenerator
from utils.email_generator import EmailGenerator

# 1. Generate random data
data_gen = DataGenerator()
opportunities = data_gen.generate_opportunities(10)  # 10 random opportunities
cases = data_gen.generate_cases(5)                   # 5 random cases

# 2. Initialize agent
agent = EmailAgent(
    sender_email="gptfy2025@gmail.com",
    sender_password="your-password"
)
email_gen = EmailGenerator()

# 3. Send opportunity emails
for opp in opportunities:
    email = email_gen.generate_opportunity_email(opp)
    agent.email_service.send_email(
        to_email="recipient@example.com",
        subject=email['subject'],
        html_content=email['html_content']
    )

# 4. Send case emails
for case in cases:
    email = email_gen.generate_case_email(case)
    agent.email_service.send_email(
        to_email="recipient@example.com",
        subject=email['subject'],
        html_content=email['html_content']
    )
```

## 📊 What Random Data Looks Like

### Random Opportunities Include:

- **Realistic company names:** "TechStart Inc", "Global Finance Ltd", "Cloud Nine Services"
- **Opportunity types:** "Cloud Migration", "CRM Implementation", "Security Audit"
- **Stages:** "Prospecting", "Proposal/Price Quote", "Negotiation/Review"
- **Amounts:** $10,000 to $500,000
- **Close dates:** Next 1-90 days
- **Descriptions:** Realistic business scenarios
- **Next steps:** Actual action items

**Example:**
```json
{
  "opportunity_name": "Cloud Migration - TechStart Inc",
  "account_name": "TechStart Inc",
  "stage": "Proposal/Price Quote",
  "amount": 125000,
  "close_date": "2025-03-15",
  "probability": 75,
  "owner_name": "Sarah Johnson",
  "description": "Strategic initiative to improve operational efficiency",
  "next_steps": "Schedule follow-up call with decision maker"
}
```

### Random Cases Include:

- **Case numbers:** 5-digit numbers (e.g., 45231)
- **Subjects:** "Unable to access dashboard", "System performance is slow"
- **Statuses:** "New", "In Progress", "Escalated"
- **Priorities:** "Low", "Medium", "High", "Critical"
- **Types:** "Technical Issue", "Bug Report", "Feature Request"
- **Origins:** "Web", "Email", "Phone", "Chat"
- **Descriptions:** Realistic technical issues
- **Resolutions:** Actual resolution text

**Example:**
```json
{
  "case_number": "45231",
  "subject": "Unable to access dashboard",
  "status": "New",
  "priority": "High",
  "type": "Technical Issue",
  "origin": "Web",
  "account_name": "Acme Corporation",
  "contact_name": "John Smith",
  "description": "Customer reports issue with system functionality",
  "resolution": ""
}
```

## 🎮 Usage Examples

### Example 1: Send 20 Mixed Emails

Edit [smart_agent.py](smart_agent.py):
```python
EMAIL_TYPE = "both"
NUM_OPPORTUNITIES = 12
NUM_CASES = 8
```

Run: `python smart_agent.py`

Result: **20 emails sent** (12 opportunities + 8 cases)

### Example 2: Send 50 Opportunity Emails

Edit [smart_agent.py](smart_agent.py):
```python
EMAIL_TYPE = "opportunity"
NUM_OPPORTUNITIES = 50
```

Run: `python smart_agent.py`

Result: **50 opportunity emails sent**

### Example 3: Interactive - Choose Each Time

Run: `python interactive_smart_agent.py`

```
How many opportunity emails? 10
How many case emails? 15
Custom message: Please review urgently
```

Result: **25 emails sent** (10 opportunities + 15 cases)

## 📧 What Gets Sent

### Opportunity Email Example:

**Subject:** Salesforce Opportunity Update: Cloud Migration - TechStart Inc

**Content:**
- Beautiful blue-themed HTML design
- Opportunity name: Cloud Migration - TechStart Inc
- Account: TechStart Inc
- Stage: Proposal/Price Quote
- Amount: $125,000
- Close Date: 2025-03-15
- Probability: 75%
- Owner: Sarah Johnson
- Description: Full business context
- Next Steps: Action items
- Custom message (if provided)

### Case Email Example:

**Subject:** Salesforce Case Update: 45231 - Unable to access dashboard

**Content:**
- Beautiful red-themed HTML design
- Case Number: 45231
- Subject: Unable to access dashboard
- Status: New
- Priority: High (color-coded)
- Type: Technical Issue
- Account: Acme Corporation
- Contact: John Smith
- Description: Full issue details
- Custom message (if provided)

## 🎯 Quick Reference

| Want to... | Use | Configuration |
|-----------|-----|---------------|
| **Send 10 opportunities** | smart_agent.py | `EMAIL_TYPE="opportunity"`, `NUM_OPPORTUNITIES=10` |
| **Send 20 cases** | smart_agent.py | `EMAIL_TYPE="case"`, `NUM_CASES=20` |
| **Send 15 opp + 10 cases** | smart_agent.py | `EMAIL_TYPE="both"`, `NUM_OPPORTUNITIES=15`, `NUM_CASES=10` |
| **Choose interactively** | interactive_smart_agent.py | Run and answer prompts |
| **Custom script** | Python code | Use DataGenerator class |

## 🔧 Configuration Files

### [smart_agent.py](smart_agent.py) - Already Configured!

```python
# Your credentials
SENDER_EMAIL = "gptfy2025@gmail.com"
SENDER_PASSWORD = "Kesav@12345"
RECIPIENT_EMAIL = "kalanithi@cloudcompliance.app"

# Email settings
EMAIL_TYPE = "both"           # Change to "opportunity", "case", or "both"
NUM_OPPORTUNITIES = 5         # Change to any number
NUM_CASES = 5                 # Change to any number
CUSTOM_MESSAGE = "Your custom message here"
```

**Just change the numbers and run!**

## 💡 Pro Tips

1. **Test First:** Start with small numbers (5-10 emails) to test
2. **Check Spam:** Some email providers may filter bulk emails
3. **Rate Limiting:** Gmail has sending limits (check your account)
4. **Use App Password:** Required for Gmail SMTP
5. **Mix Types:** Send both opportunities and cases for variety
6. **Custom Messages:** Personalize emails for context

## 📈 Realistic Data Quality

The random data generator creates **highly realistic** Salesforce data:

✅ **Real company names** (28 different companies)
✅ **Actual opportunity types** (16 different types)
✅ **Proper Salesforce stages** (8 standard stages)
✅ **Realistic amounts** ($10k-$500k range)
✅ **Future close dates** (1-90 days out)
✅ **Business descriptions** (8 realistic scenarios)
✅ **Action-oriented next steps**
✅ **Professional case subjects** (14 common issues)
✅ **Proper priority levels** (Low to Critical)
✅ **Multiple contact names** (256 combinations)

**The emails look completely real!**

## 🚀 Ready to Use

Your agent is **already configured** with:
- ✅ Sender: gptfy2025@gmail.com
- ✅ Recipient: kalanithi@cloudcompliance.app
- ✅ Default: 5 opportunities + 5 cases = 10 emails

**To send 10 random emails right now:**

```bash
python smart_agent.py
```

**To choose how many:**

```bash
python interactive_smart_agent.py
```

## 🎉 Summary

| Feature | Description |
|---------|-------------|
| **Random Generation** | ✅ Generates realistic Salesforce data automatically |
| **Flexible Count** | ✅ Send any number of emails (1 to 1000+) |
| **Mixed Types** | ✅ Opportunities, Cases, or Both |
| **Realistic Data** | ✅ Company names, amounts, dates, descriptions |
| **Easy to Use** | ✅ Edit numbers and run, or use interactive mode |
| **Already Configured** | ✅ Your credentials are set up |

**No more manual data files - just specify numbers and send!** 🚀

---

## Comparison

### Old Way (Using Files):
```bash
# Limited to sample data in files
python quick_agent.py  # Sends 3 pre-made opportunities
```

### New Way (Random Generation):
```bash
# Unlimited data, any quantity
python smart_agent.py  # Sends 5 opportunities + 5 cases (configurable)
python interactive_smart_agent.py  # Choose any number on the fly
```

**The new way gives you unlimited flexibility!** 🎯
