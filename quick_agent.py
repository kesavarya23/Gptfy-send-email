"""
Quick Email Agent
Configure your credentials once and run immediately
"""

import sys
sys.path.append('src')

from agent import EmailAgent


# ============================================================================
# CONFIGURATION - ENTER YOUR CREDENTIALS HERE
# ============================================================================

# Sender Configuration
SENDER_EMAIL = "your-email@gmail.com"          # Your Gmail address
SENDER_PASSWORD = "your-app-password"          # Your Gmail app password
SENDER_NAME = "Your Name"                      # Display name

# Recipient Configuration
RECIPIENT_EMAIL = "recipient@example.com"      # Email to send to

# Email Settings
DATA_TYPE = "opportunity"                      # "opportunity" or "case"
DATA_SOURCE = "file"                           # "file" or "salesforce"
FILE_PATH = "data/sample_opportunities.json"   # Path to data file (if using file source)
CUSTOM_MESSAGE = "Please review these Salesforce opportunities and provide your feedback."  # Optional custom message

# Salesforce Configuration (only needed if DATA_SOURCE = "salesforce")
SF_USERNAME = "your-salesforce-username"
SF_PASSWORD = "your-salesforce-password"
SF_SECURITY_TOKEN = "your-security-token"
SF_DOMAIN = "login"                            # "login" for production, "test" for sandbox
SF_LIMIT = 10                                  # Maximum records to fetch

# ============================================================================
# DO NOT EDIT BELOW THIS LINE
# ============================================================================


def main():
    print("="*70)
    print("QUICK EMAIL AGENT")
    print("="*70)
    print()

    # Validate configuration
    if SENDER_EMAIL == "your-email@gmail.com":
        print("❌ Error: Please configure SENDER_EMAIL in quick_agent.py")
        return

    if RECIPIENT_EMAIL == "recipient@example.com":
        print("❌ Error: Please configure RECIPIENT_EMAIL in quick_agent.py")
        return

    # Initialize agent
    print("✓ Initializing Email Agent...")
    agent = EmailAgent(
        sender_email=SENDER_EMAIL,
        sender_password=SENDER_PASSWORD,
        sender_name=SENDER_NAME
    )

    # Setup Salesforce if needed
    if DATA_SOURCE == "salesforce":
        print("✓ Connecting to Salesforce...")
        if not agent.setup_salesforce(SF_USERNAME, SF_PASSWORD, SF_SECURITY_TOKEN, SF_DOMAIN):
            print("❌ Failed to connect to Salesforce. Check your credentials.")
            return

    # Display configuration
    print()
    print("Configuration:")
    print(f"  Sender: {SENDER_EMAIL}")
    print(f"  Recipient: {RECIPIENT_EMAIL}")
    print(f"  Data Type: {DATA_TYPE}")
    print(f"  Data Source: {DATA_SOURCE}")
    if DATA_SOURCE == "file":
        print(f"  File: {FILE_PATH}")
    else:
        print(f"  Salesforce Limit: {SF_LIMIT}")
    print()

    print("="*70)
    print("STARTING EMAIL CAMPAIGN")
    print("="*70)
    print()

    # Run agent
    try:
        if DATA_TYPE == "opportunity":
            report = agent.send_opportunity_emails(
                recipient_email=RECIPIENT_EMAIL,
                data_source=DATA_SOURCE,
                file_path=FILE_PATH if DATA_SOURCE == "file" else None,
                limit=SF_LIMIT if DATA_SOURCE == "salesforce" else 100,
                custom_message=CUSTOM_MESSAGE if CUSTOM_MESSAGE else None
            )
        else:
            report = agent.send_case_emails(
                recipient_email=RECIPIENT_EMAIL,
                data_source=DATA_SOURCE,
                file_path=FILE_PATH if DATA_SOURCE == "file" else None,
                limit=SF_LIMIT if DATA_SOURCE == "salesforce" else 100,
                custom_message=CUSTOM_MESSAGE if CUSTOM_MESSAGE else None
            )

        # Print report
        agent.print_report(report)

        if report['success']:
            print("✓ Campaign completed successfully!")
        else:
            print("⚠ Campaign completed with some errors. See report above.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
