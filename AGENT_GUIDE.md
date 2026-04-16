# Email Agent Guide

The Email Agent is an autonomous system that automatically generates and sends multiple Salesforce-related emails. Just provide your credentials, and it handles everything!

## Features

- **Autonomous Operation**: Set it up once and let it run
- **Bulk Email Sending**: Send multiple emails automatically
- **Multiple Recipients**: Send to one or many recipients
- **Data Source Flexibility**: Load from files or Salesforce API
- **Smart Reporting**: Get detailed statistics and error reports
- **Error Handling**: Continues even if some emails fail
- **Progress Tracking**: Real-time logging of email sending

## Quick Start

### Option 1: Quick Agent (Easiest)

1. Open [quick_agent.py](quick_agent.py)
2. Edit the configuration section at the top:

```python
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"
SENDER_NAME = "Your Name"
RECIPIENT_EMAIL = "recipient@example.com"
DATA_TYPE = "opportunity"
DATA_SOURCE = "file"
FILE_PATH = "data/sample_opportunities.json"
```

3. Run it:
```bash
python quick_agent.py
```

That's it! The agent will automatically send all emails.

### Option 2: Interactive Agent

Run the interactive script that asks for your credentials:

```bash
python run_agent.py
```

Follow the prompts to enter:
- Sender email and password
- Recipient email
- Data source (file or Salesforce)
- Data type (opportunity or case)

### Option 3: Use in Python Code

```python
from agent import EmailAgent

# Initialize agent
agent = EmailAgent(
    sender_email="your-email@gmail.com",
    sender_password="your-app-password",
    sender_name="Your Name"
)

# Send opportunity emails
report = agent.send_opportunity_emails(
    recipient_email="recipient@example.com",
    data_source='file',
    file_path='data/sample_opportunities.json',
    custom_message="Please review these opportunities."
)

# Print results
agent.print_report(report)
```

## Agent Capabilities

### 1. Send Opportunity Emails

Send multiple opportunity-related emails:

```python
report = agent.send_opportunity_emails(
    recipient_email="user@example.com",
    data_source='file',
    file_path='data/sample_opportunities.json',
    custom_message="Please review urgently."
)
```

**From Salesforce:**
```python
agent.setup_salesforce(
    username="sf-user",
    password="sf-pass",
    security_token="token"
)

report = agent.send_opportunity_emails(
    recipient_email="user@example.com",
    data_source='salesforce',
    filters={'StageName': 'Prospecting'},
    limit=20
)
```

### 2. Send Case Emails

Send multiple case-related emails:

```python
report = agent.send_case_emails(
    recipient_email="support@example.com",
    data_source='file',
    file_path='data/sample_cases.json'
)
```

### 3. Send to Multiple Recipients

Send the same emails to multiple people:

```python
report = agent.send_bulk_to_multiple_recipients(
    recipient_emails=['user1@example.com', 'user2@example.com', 'user3@example.com'],
    data_type='opportunity',
    data_source='file',
    file_path='data/sample_opportunities.json'
)
```

## Agent Methods

### `__init__`

Initialize the agent:

```python
agent = EmailAgent(
    sender_email="your@email.com",
    sender_password="password",
    sender_name="Your Name",      # Optional
    smtp_host="smtp.gmail.com",   # Optional
    smtp_port=587                  # Optional
)
```

### `setup_salesforce`

Configure Salesforce connection:

```python
agent.setup_salesforce(
    username="salesforce-username",
    password="salesforce-password",
    security_token="security-token",
    domain="login"  # or "test" for sandbox
)
```

### `send_opportunity_emails`

Send opportunity emails:

```python
report = agent.send_opportunity_emails(
    recipient_email="user@example.com",
    data_source='file',              # 'file' or 'salesforce'
    file_path='path/to/data.json',   # Required if source is 'file'
    filters={'Stage': 'Open'},       # Optional Salesforce filters
    limit=50,                        # Max records to process
    custom_message="Your message"    # Optional custom message
)
```

### `send_case_emails`

Send case emails (same parameters as `send_opportunity_emails`):

```python
report = agent.send_case_emails(
    recipient_email="user@example.com",
    data_source='salesforce',
    filters={'Status': 'New'},
    limit=20
)
```

### `send_bulk_to_multiple_recipients`

Send to multiple recipients:

```python
report = agent.send_bulk_to_multiple_recipients(
    recipient_emails=['user1@example.com', 'user2@example.com'],
    data_type='opportunity',         # 'opportunity' or 'case'
    data_source='file',
    file_path='data.json',
    limit=10,
    custom_message="Update"
)
```

### `print_report`

Display formatted report:

```python
agent.print_report(report)
```

### `reset_stats`

Reset statistics for new campaign:

```python
agent.reset_stats()
```

## Report Format

All sending methods return a report dictionary:

```python
{
    'success': True,                 # Overall success status
    'total_processed': 10,           # Total emails processed
    'total_sent': 9,                 # Successfully sent
    'total_failed': 1,               # Failed to send
    'success_rate': 90.0,            # Success percentage
    'duration_seconds': 15.3,        # Time taken
    'failed_items': [                # Details of failures
        {
            'type': 'opportunity',
            'name': 'Failed Item',
            'reason': 'Connection timeout'
        }
    ],
    'start_time': datetime(...),
    'end_time': datetime(...)
}
```

## Example Use Cases

### Use Case 1: Daily Opportunity Report

Send daily opportunity updates:

```python
from agent import EmailAgent

agent = EmailAgent(
    sender_email="reports@company.com",
    sender_password="password"
)

agent.setup_salesforce(
    username="sf-user",
    password="sf-pass",
    security_token="token"
)

# Send to sales team
report = agent.send_opportunity_emails(
    recipient_email="sales-team@company.com",
    data_source='salesforce',
    filters={'LastModifiedDate': 'TODAY'},
    limit=50,
    custom_message="Here are today's updated opportunities."
)

if report['success']:
    print(f"✓ Sent {report['total_sent']} opportunity updates")
else:
    print(f"⚠ {report['total_failed']} emails failed")
```

### Use Case 2: Weekly Case Summary

Send weekly case summaries to support managers:

```python
agent = EmailAgent(
    sender_email="support@company.com",
    sender_password="password"
)

agent.setup_salesforce(
    username="sf-user",
    password="sf-pass",
    security_token="token"
)

managers = [
    "manager1@company.com",
    "manager2@company.com",
    "manager3@company.com"
]

report = agent.send_bulk_to_multiple_recipients(
    recipient_emails=managers,
    data_type='case',
    data_source='salesforce',
    filters={'Status': 'Open'},
    limit=100,
    custom_message="Weekly case summary for your review."
)

agent.print_report(report)
```

### Use Case 3: File-Based Notifications

Send notifications from prepared data files:

```python
agent = EmailAgent(
    sender_email="notify@company.com",
    sender_password="password"
)

# Process opportunity notifications
report1 = agent.send_opportunity_emails(
    recipient_email="exec@company.com",
    data_source='file',
    file_path='data/priority_opportunities.json',
    custom_message="Priority opportunities requiring your attention."
)

# Reset stats for new campaign
agent.reset_stats()

# Process case notifications
report2 = agent.send_case_emails(
    recipient_email="support@company.com",
    data_source='file',
    file_path='data/escalated_cases.json',
    custom_message="Escalated cases requiring immediate action."
)
```

## Configuration

### Gmail Setup

1. Enable 2-factor authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the app password, not your regular password

### Other Email Providers

**Outlook:**
```python
agent = EmailAgent(
    sender_email="your@outlook.com",
    sender_password="password",
    smtp_host="smtp.office365.com",
    smtp_port=587
)
```

**Yahoo:**
```python
agent = EmailAgent(
    sender_email="your@yahoo.com",
    sender_password="password",
    smtp_host="smtp.mail.yahoo.com",
    smtp_port=587
)
```

## Best Practices

1. **Test First**: Use sample data files to test before sending to real recipients
2. **Check Reports**: Always review the report to ensure emails were sent
3. **Handle Failures**: Check `failed_items` in the report to diagnose issues
4. **Use Custom Messages**: Personalize emails with custom messages
5. **Set Appropriate Limits**: Don't fetch too many records at once from Salesforce
6. **Monitor Rate Limits**: Some email providers limit sending rate
7. **Reset Stats**: Call `reset_stats()` between campaigns for accurate reporting

## Error Handling

The agent continues even if individual emails fail:

```python
report = agent.send_opportunity_emails(...)

if not report['success']:
    print(f"Some emails failed!")
    for failed in report['failed_items']:
        print(f"Failed: {failed['name']} - {failed['reason']}")
```

## Running Examples

The project includes several example scripts:

```bash
# File-based example
python examples/agent_file_example.py

# Salesforce example
python examples/agent_salesforce_example.py

# Multiple recipients example
python examples/agent_multiple_recipients.py
```

## Troubleshooting

**"Authentication failed"**
- Check your email password
- For Gmail, ensure you're using an App Password

**"No data found"**
- Verify file path is correct
- Check Salesforce connection and filters

**"Some emails failed to send"**
- Check the `failed_items` in the report
- Verify recipient email addresses are valid
- Check your internet connection

**"Connection timeout"**
- Check SMTP host and port settings
- Verify firewall isn't blocking SMTP

## Advanced Usage

### Custom Filters

Filter Salesforce data:

```python
# Only opportunities in specific stage
report = agent.send_opportunity_emails(
    recipient_email="user@example.com",
    data_source='salesforce',
    filters={
        'StageName': 'Proposal',
        'Amount': '> 50000'
    }
)

# Only high priority cases
report = agent.send_case_emails(
    recipient_email="support@example.com",
    data_source='salesforce',
    filters={
        'Priority': 'High',
        'Status': 'New'
    }
)
```

### Scheduled Sending

Use with task scheduler:

**Windows Task Scheduler:**
- Create a task to run `python quick_agent.py` daily

**Linux Cron:**
```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/project && python quick_agent.py
```

**Python Scheduler:**
```python
import schedule
import time

def send_daily_report():
    agent = EmailAgent(...)
    report = agent.send_opportunity_emails(...)
    agent.print_report(report)

schedule.every().day.at("09:00").do(send_daily_report)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Summary

The Email Agent provides a powerful, autonomous way to send multiple Salesforce-related emails:

✅ **Easy to use** - Configure once and run
✅ **Flexible** - File or Salesforce data sources
✅ **Robust** - Handles errors gracefully
✅ **Detailed reporting** - Know exactly what happened
✅ **Multiple recipients** - Send to one or many
✅ **Production-ready** - Built for real-world use

Get started now with [quick_agent.py](quick_agent.py)!
