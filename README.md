# Salesforce Email Sender

A Python application for generating and sending professional emails related to Salesforce opportunities and cases. Supports both direct Salesforce API integration and manual data input via JSON/CSV files.

## ✨ NEW: Smart Agent with Random Data Generation!

**🎯 Specify how many emails to send - the agent generates random Salesforce data and sends them automatically!**

```python
# Generate and send 10 random opportunities + 5 random cases
python smart_agent.py
```

**No more manual data files!** Just tell the agent:
- How many opportunity emails to send (e.g., 10, 20, 50)
- How many case emails to send (e.g., 5, 15, 30)
- Agent generates realistic random data and sends all emails automatically!

👉 See [RANDOM_EMAIL_GUIDE.md](RANDOM_EMAIL_GUIDE.md) for the random generator guide
👉 See [AGENT_GUIDE.md](AGENT_GUIDE.md) for complete agent documentation

## Features

- **🎯 Random Data Generation** - Generate any number of realistic Salesforce emails
- **🤖 Autonomous Email Agent** - Automatically sends multiple emails
- **📊 Flexible Quantity** - Send 5, 10, 50, or any number of emails
- Send emails for Salesforce Opportunities and Cases
- Three data source options:
  - **Random generation** (unlimited data!)
  - Direct Salesforce API integration
  - Manual data input (JSON/CSV files)
- Professional HTML email templates
- SMTP email sending (Gmail, Outlook, etc.)
- Bulk email sending capability
- Send to multiple recipients
- Detailed reporting and statistics
- Configurable via environment variables
- Command-line interface
- Example scripts included

## Project Structure

```
Gptfy-send-email/
├── src/
│   ├── agent.py                     # 🤖 Autonomous Email Agent
│   ├── config.py                    # Configuration management
│   ├── main.py                      # Main application entry point
│   ├── services/
│   │   ├── email_service.py         # SMTP email sending
│   │   └── salesforce_service.py    # Salesforce API integration
│   ├── templates/
│   │   ├── opportunity_email.html   # Opportunity email template
│   │   └── case_email.html          # Case email template
│   └── utils/
│       ├── data_loader.py           # JSON/CSV data loading
│       └── email_generator.py       # Email content generation
├── data/
│   ├── sample_opportunities.json    # Sample opportunity data
│   └── sample_cases.json            # Sample case data
├── examples/
│   ├── simple_example.py            # Simple file-based example
│   ├── salesforce_example.py        # Salesforce API example
│   ├── agent_file_example.py        # Agent with file data
│   ├── agent_salesforce_example.py  # Agent with Salesforce
│   └── agent_multiple_recipients.py # Agent with multiple recipients
├── run_agent.py                     # 🚀 Interactive agent runner
├── quick_agent.py                   # ⚡ Quick agent (edit & run)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── README.md                        # This file
├── AGENT_GUIDE.md                   # Complete agent documentation
└── QUICKSTART.md                    # 5-minute quick start
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup Steps

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. Configure your `.env` file with your credentials (see Configuration section below)

## Configuration

Edit the `.env` file with your settings:

### Email Configuration (Required)

For Gmail, you need to use an "App Password" instead of your regular password:
1. Enable 2-factor authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an app password for "Mail"
4. Use this 16-character password in the `.env` file

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
SENDER_NAME=Your Name
DEFAULT_RECIPIENT_EMAIL=recipient@example.com
```

### Salesforce Configuration (Optional - for API integration)

Only required if you want to fetch data directly from Salesforce:

```env
SF_USERNAME=your-salesforce-username
SF_PASSWORD=your-salesforce-password
SF_SECURITY_TOKEN=your-security-token
SF_DOMAIN=login  # Use 'test' for sandbox, 'login' for production
```

To get your Salesforce Security Token:
1. Log in to Salesforce
2. Go to Settings > My Personal Information > Reset My Security Token
3. Check your email for the security token

## Usage

### 🤖 Method 1: Email Agent (Recommended - Automatic!)

The Email Agent is the easiest way to send multiple emails automatically.

#### Quick Agent (Edit & Run):

1. Open [quick_agent.py](quick_agent.py)
2. Edit configuration at the top with your credentials
3. Run:
```bash
python quick_agent.py
```

#### Interactive Agent:

```bash
python run_agent.py
```

The agent will prompt for your credentials and automatically send all emails!

#### Python Code:

```python
from agent import EmailAgent

# Initialize agent with your credentials
agent = EmailAgent(
    sender_email="your-email@gmail.com",
    sender_password="your-app-password"
)

# Send all opportunity emails to recipient
report = agent.send_opportunity_emails(
    recipient_email="recipient@example.com",
    data_source='file',
    file_path='data/sample_opportunities.json'
)

# View results
agent.print_report(report)
```

**Agent Features:**
- ✅ Sends multiple emails automatically
- ✅ Detailed progress logging
- ✅ Comprehensive error reporting
- ✅ Supports file or Salesforce data
- ✅ Can send to multiple recipients

👉 **Full documentation:** [AGENT_GUIDE.md](AGENT_GUIDE.md)

### Method 2: Command Line Interface

The application provides a command-line interface for easy usage.

#### Send emails from a JSON file:

```bash
# For opportunities
python src/main.py --source file --type opportunity --file data/sample_opportunities.json --recipient user@example.com

# For cases
python src/main.py --source file --type case --file data/sample_cases.json --recipient user@example.com

# With custom message
python src/main.py --source file --type opportunity --file data/sample_opportunities.json --recipient user@example.com --message "Please review urgently"
```

#### Send emails from Salesforce API:

```bash
# For opportunities
python src/main.py --source salesforce --type opportunity --recipient user@example.com --limit 10

# For cases
python src/main.py --source salesforce --type case --recipient user@example.com --limit 5
```

#### Command Line Options:

- `--source`: Data source (`salesforce` or `file`) - **Required**
- `--type`: Data type (`opportunity` or `case`) - **Required**
- `--file`: Path to data file (required if source is `file`)
- `--recipient`: Recipient email address (uses DEFAULT_RECIPIENT_EMAIL from .env if not specified)
- `--limit`: Maximum records to process from Salesforce (default: 10)
- `--message`: Custom message to include in emails
- `--config`: Path to custom .env file (optional)

### Method 2: Using Example Scripts

#### Simple Example (File-based):

```bash
python examples/simple_example.py
```

This will:
1. Load sample opportunities from `data/sample_opportunities.json`
2. Generate an email for the first opportunity
3. Prompt for recipient email
4. Send the email

#### Salesforce Example (API-based):

```bash
python examples/salesforce_example.py
```

This will:
1. Connect to Salesforce
2. Fetch opportunities (filtered by stage)
3. Generate emails for all opportunities
4. Prompt for recipient email
5. Send all emails

### Method 3: Python Code Integration

You can also use the modules directly in your Python code:

```python
from config import Config
from services.email_service import EmailService
from utils.email_generator import EmailGenerator
from utils.data_loader import DataLoader

# Initialize
config = Config()
email_service = EmailService(**config.get_email_config())
email_generator = EmailGenerator()

# Load data
data_loader = DataLoader()
opportunities = data_loader.load_from_json('data/sample_opportunities.json')

# Generate email
email_content = email_generator.generate_opportunity_email(
    opportunity_data=opportunities[0],
    custom_message="Please review this opportunity."
)

# Send email
email_service.send_email(
    to_email='recipient@example.com',
    subject=email_content['subject'],
    html_content=email_content['html_content']
)
```

## Data Formats

### Opportunity Data Format (JSON)

```json
{
  "opportunity_name": "Enterprise Cloud Migration",
  "account_name": "Acme Corporation",
  "stage": "Proposal/Price Quote",
  "amount": 125000,
  "close_date": "2025-03-15",
  "probability": 75,
  "owner_name": "John Smith",
  "description": "Large-scale cloud migration project",
  "next_steps": "Schedule technical review"
}
```

Required fields: `opportunity_name`, `stage`, `close_date`

### Case Data Format (JSON)

```json
{
  "case_number": "00001234",
  "subject": "Unable to access dashboard",
  "status": "New",
  "priority": "High",
  "type": "Technical Issue",
  "origin": "Web",
  "account_name": "Acme Corporation",
  "contact_name": "Jane Doe",
  "owner_name": "Support Team",
  "description": "Customer cannot access dashboard",
  "resolution": "",
  "created_date": "2025-01-15"
}
```

Required fields: `case_number`, `subject`, `status`

### CSV Format

You can also use CSV files with the same field names as headers.

## Email Templates

The application includes two professional HTML email templates:

- `src/templates/opportunity_email.html` - Blue-themed template for opportunities
- `src/templates/case_email.html` - Red-themed template for cases

You can customize these templates by editing the HTML files. They use Jinja2 template syntax for dynamic content.

## Troubleshooting

### Email Sending Issues

1. **Gmail "Less secure app access" error**: Use an App Password (see Configuration section)
2. **SMTP Authentication Failed**: Verify your username and password in `.env`
3. **Connection timeout**: Check your SMTP host and port settings
4. **Emails not received**: Check spam folder, verify recipient email address

### Salesforce Connection Issues

1. **Authentication Failed**: Verify username, password, and security token
2. **Invalid Domain**: Use `login` for production, `test` for sandbox
3. **API Permissions**: Ensure your Salesforce user has API access enabled

### General Issues

1. **Module not found**: Ensure all dependencies are installed: `pip install -r requirements.txt`
2. **File not found**: Use absolute paths or ensure you're in the correct directory
3. **Configuration errors**: Validate your `.env` file has all required fields

## Security Notes

- Never commit your `.env` file to version control (it's in `.gitignore`)
- Use environment-specific credentials
- For Gmail, always use App Passwords, never your main account password
- Rotate your Salesforce security token periodically

## Extending the Application

### Adding New Email Templates

1. Create a new HTML template in `src/templates/`
2. Add a generator method in `src/utils/email_generator.py`
3. Use Jinja2 syntax for dynamic content: `{{ variable_name }}`

### Adding Custom Fields

1. Update the Salesforce SOQL query in `src/services/salesforce_service.py`
2. Update the email template to display the new fields
3. Update sample data files in `data/` directory

### Supporting Other Email Providers

The application works with any SMTP provider. Just update the `.env` file:

- **Outlook**: smtp.office365.com, port 587
- **Yahoo**: smtp.mail.yahoo.com, port 465
- **Custom SMTP**: Use your provider's settings

## Dependencies

- `simple-salesforce`: Salesforce API integration
- `python-dotenv`: Environment variable management
- `jinja2`: Email template rendering
- `pandas`: CSV data handling
- `requests`: HTTP requests

See `requirements.txt` for version details.

## License

This project is provided as-is for educational and business purposes.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the example scripts in `examples/`
3. Verify your configuration in `.env`

## Next Steps

After setup:

1. Test with sample data: `python examples/simple_example.py`
2. Configure your real credentials in `.env`
3. Customize email templates in `src/templates/`
4. Create your own data files in `data/`
5. Integrate into your workflow using the CLI or Python code

Enjoy sending professional Salesforce emails!