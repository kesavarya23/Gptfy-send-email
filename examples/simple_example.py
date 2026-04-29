"""
Simple Example: Send emails from JSON file
This example demonstrates how to send emails using data from a JSON file
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from config import Config
from services.email_service import EmailService
from utils.email_generator import EmailGenerator
from utils.data_loader import DataLoader


def main():
    # Load configuration from .env file
    config = Config()

    # Validate email configuration
    if not config.validate_email_config():
        print("Error: Email configuration is invalid. Please check your .env file.")
        return

    # Initialize services
    email_service = EmailService(**config.get_email_config())
    email_generator = EmailGenerator()
    data_loader = DataLoader()

    # Load sample opportunity data
    opportunities = data_loader.load_from_json('data/sample_opportunities.json')

    if not opportunities:
        print("No opportunities found in file")
        return

    print(f"Loaded {len(opportunities)} opportunities")

    # Generate and send email for the first opportunity
    opportunity = opportunities[0]

    # Generate email content
    email_content = email_generator.generate_opportunity_email(
        opportunity_data=opportunity,
        custom_message="Please review this opportunity at your earliest convenience."
    )

    # Preview the email
    print("\n=== EMAIL PREVIEW ===")
    print(f"Subject: {email_content['subject']}")
    print(f"\nHTML Content Length: {len(email_content['html_content'])} characters")

    # Specify recipient email
    recipient_email = input("\nEnter recipient email address: ")

    # Send the email
    print(f"\nSending email to {recipient_email}...")
    success = email_service.send_email(
        to_email=recipient_email,
        subject=email_content['subject'],
        html_content=email_content['html_content']
    )

    if success:
        print("Email sent successfully!")
    else:
        print("Failed to send email. Check logs for details.")


if __name__ == '__main__':
    main()
