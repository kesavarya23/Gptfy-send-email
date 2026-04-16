# Quick Start Guide

Get up and running in 5 minutes!

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure Email Settings

Copy the example configuration:
```bash
cp .env.example .env
```

Edit `.env` and add your email settings:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
SENDER_NAME=Your Name
DEFAULT_RECIPIENT_EMAIL=recipient@example.com
```

### Getting Gmail App Password

1. Enable 2-factor authentication on your Google account
2. Visit: https://myaccount.google.com/apppasswords
3. Generate an app password for "Mail"
4. Use the 16-character password in `.env`

## 3. Test with Sample Data

Run the simple example:

```bash
python examples/simple_example.py
```

When prompted, enter the recipient email address.

## 4. Send Your First Email

### Using the CLI:

```bash
python src/main.py --source file --type opportunity --file data/sample_opportunities.json --recipient your-email@example.com
```

### Using Python Code:

```python
import sys
sys.path.append('src')

from config import Config
from services.email_service import EmailService
from utils.email_generator import EmailGenerator

# Initialize
config = Config()
email_service = EmailService(**config.get_email_config())
email_generator = EmailGenerator()

# Create opportunity data
opportunity = {
    "opportunity_name": "Test Opportunity",
    "account_name": "Test Account",
    "stage": "Prospecting",
    "amount": 50000,
    "close_date": "2025-03-31",
    "probability": 50
}

# Generate and send
email = email_generator.generate_opportunity_email(opportunity)
email_service.send_email(
    to_email='recipient@example.com',
    subject=email['subject'],
    html_content=email['html_content']
)
```

## 5. Optional: Configure Salesforce

If you want to fetch data from Salesforce, add these to `.env`:

```env
SF_USERNAME=your-salesforce-username
SF_PASSWORD=your-salesforce-password
SF_SECURITY_TOKEN=your-security-token
SF_DOMAIN=login
```

Then run:

```bash
python src/main.py --source salesforce --type opportunity --recipient your-email@example.com --limit 5
```

## Common Issues

**"Authentication failed"**: Check your email password in `.env`

**"Module not found"**: Run `pip install -r requirements.txt`

**"File not found"**: Make sure you're in the project root directory

## Next Steps

- Customize email templates in `src/templates/`
- Add your own data files in `data/`
- Read the full [README.md](README.md) for advanced features

Need help? Check the [README.md](README.md) troubleshooting section!
