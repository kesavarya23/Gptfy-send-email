"""
Agent Example: Send emails from Salesforce
This example shows how to use the agent to fetch data from Salesforce and send emails
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from agent import EmailAgent


def main():
    print("="*70)
    print("EMAIL AGENT - SALESFORCE EXAMPLE")
    print("="*70)
    print()

    # Get email credentials
    print("EMAIL CREDENTIALS")
    print("-"*70)
    sender_email = input("Enter your email address: ")
    sender_password = input("Enter your password (app password for Gmail): ")
    recipient_email = input("Enter recipient email address: ")

    # Get Salesforce credentials
    print("\nSALESFORCE CREDENTIALS")
    print("-"*70)
    sf_username = input("Enter Salesforce username: ")
    sf_password = input("Enter Salesforce password: ")
    sf_token = input("Enter Salesforce security token: ")
    sf_domain = input("Enter domain (login/test) [login]: ") or "login"

    print("\nInitializing agent...")

    # Create agent
    agent = EmailAgent(
        sender_email=sender_email,
        sender_password=sender_password,
        sender_name="Salesforce Notification System"
    )

    # Setup Salesforce
    print("Connecting to Salesforce...")
    if not agent.setup_salesforce(sf_username, sf_password, sf_token, sf_domain):
        print("Failed to connect to Salesforce!")
        return

    print("✓ Connected to Salesforce")

    print("\n" + "="*70)
    print("FETCHING AND SENDING OPPORTUNITY EMAILS")
    print("="*70 + "\n")

    # Send opportunity emails from Salesforce
    report = agent.send_opportunity_emails(
        recipient_email=recipient_email,
        data_source='salesforce',
        filters={'StageName': 'Prospecting'},  # Optional: filter by stage
        limit=5,
        custom_message="Please review these opportunities from Salesforce."
    )

    # Print report
    agent.print_report(report)

    # Ask if user wants to send case emails too
    send_cases = input("\nDo you want to send case emails too? (y/n): ").lower()

    if send_cases == 'y':
        agent.reset_stats()

        print("\n" + "="*70)
        print("FETCHING AND SENDING CASE EMAILS")
        print("="*70 + "\n")

        # Send case emails from Salesforce
        report = agent.send_case_emails(
            recipient_email=recipient_email,
            data_source='salesforce',
            filters={'Status': 'New'},  # Optional: filter by status
            limit=5,
            custom_message="Please review these cases from Salesforce."
        )

        # Print report
        agent.print_report(report)

    print("\nAll campaigns complete!")


if __name__ == '__main__':
    main()
