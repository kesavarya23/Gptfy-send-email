"""
Salesforce Example: Fetch data from Salesforce and send emails
This example demonstrates how to fetch opportunities from Salesforce and send emails
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from config import Config
from services.email_service import EmailService
from services.salesforce_service import SalesforceService
from utils.email_generator import EmailGenerator


def main():
    # Load configuration from .env file
    config = Config()

    # Validate configurations
    if not config.validate_email_config():
        print("Error: Email configuration is invalid. Please check your .env file.")
        return

    if not config.validate_salesforce_config():
        print("Error: Salesforce configuration is invalid. Please check your .env file.")
        return

    # Initialize services
    try:
        email_service = EmailService(**config.get_email_config())
        sf_service = SalesforceService(**config.get_salesforce_config())
        email_generator = EmailGenerator()
    except Exception as e:
        print(f"Error initializing services: {str(e)}")
        return

    # Fetch opportunities from Salesforce
    print("Fetching opportunities from Salesforce...")
    opportunities = sf_service.get_opportunities(
        filters={'StageName': 'Prospecting'},  # Optional: filter by stage
        limit=5
    )

    if not opportunities:
        print("No opportunities found")
        return

    print(f"Found {len(opportunities)} opportunities")

    # Display opportunities
    for i, opp in enumerate(opportunities, 1):
        print(f"\n{i}. {opp['opportunity_name']} - {opp['stage']} - ${opp['amount']}")

    # Specify recipient email
    recipient_email = input("\nEnter recipient email address: ")

    # Generate and send emails for all opportunities
    print(f"\nGenerating and sending emails...")

    emails_data = []
    for opp in opportunities:
        email_content = email_generator.generate_opportunity_email(
            opportunity_data=opp,
            custom_message="Please review this opportunity from Salesforce."
        )
        emails_data.append({
            'to_email': recipient_email,
            'subject': email_content['subject'],
            'html_content': email_content['html_content']
        })

    # Send all emails
    result = email_service.send_bulk_emails(emails_data)

    print(f"\n=== RESULTS ===")
    print(f"Successfully sent: {result['success_count']}")
    print(f"Failed: {result['failed_count']}")

    if result['failed_emails']:
        print(f"Failed emails: {', '.join(result['failed_emails'])}")


if __name__ == '__main__':
    main()
