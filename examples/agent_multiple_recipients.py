"""
Agent Example: Send emails to multiple recipients
This example shows how to send the same emails to multiple recipients
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from agent import EmailAgent


def main():
    print("="*70)
    print("EMAIL AGENT - MULTIPLE RECIPIENTS EXAMPLE")
    print("="*70)
    print()

    # Get credentials
    sender_email = input("Enter your email address: ")
    sender_password = input("Enter your password (app password for Gmail): ")

    # Get multiple recipients
    print("\nEnter recipient email addresses (comma-separated):")
    recipients_input = input("Recipients: ")
    recipient_emails = [email.strip() for email in recipients_input.split(',')]

    print(f"\nWill send to {len(recipient_emails)} recipients:")
    for i, email in enumerate(recipient_emails, 1):
        print(f"  {i}. {email}")

    confirm = input("\nContinue? (y/n): ").lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    print("\nInitializing agent...")

    # Create agent
    agent = EmailAgent(
        sender_email=sender_email,
        sender_password=sender_password,
        sender_name="Salesforce Team"
    )

    print("\n" + "="*70)
    print("SENDING BULK EMAILS TO MULTIPLE RECIPIENTS")
    print("="*70 + "\n")

    # Send to multiple recipients
    report = agent.send_bulk_to_multiple_recipients(
        recipient_emails=recipient_emails,
        data_type='opportunity',
        data_source='file',
        file_path='data/sample_opportunities.json',
        custom_message="This is an important update regarding Salesforce opportunities."
    )

    # Print report
    agent.print_report(report)

    print(f"\nSent emails to {len(recipient_emails)} recipients!")


if __name__ == '__main__':
    main()
