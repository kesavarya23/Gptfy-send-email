"""
Agent Example: Send emails from file
This example shows how to use the agent to send multiple emails from a JSON file
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from agent import EmailAgent


def main():
    print("="*70)
    print("EMAIL AGENT - FILE EXAMPLE")
    print("="*70)
    print()

    # Get credentials
    sender_email = input("Enter your email address: ")
    sender_password = input("Enter your password (app password for Gmail): ")
    recipient_email = input("Enter recipient email address: ")

    print("\nInitializing agent...")

    # Create agent
    agent = EmailAgent(
        sender_email=sender_email,
        sender_password=sender_password,
        sender_name="Salesforce Email System"
    )

    print("\n" + "="*70)
    print("SENDING OPPORTUNITY EMAILS")
    print("="*70 + "\n")

    # Send opportunity emails
    report = agent.send_opportunity_emails(
        recipient_email=recipient_email,
        data_source='file',
        file_path='data/sample_opportunities.json',
        custom_message="Please review these opportunities and provide feedback."
    )

    # Print report
    agent.print_report(report)

    # Reset stats for next campaign
    agent.reset_stats()

    print("\n" + "="*70)
    print("SENDING CASE EMAILS")
    print("="*70 + "\n")

    # Send case emails
    report = agent.send_case_emails(
        recipient_email=recipient_email,
        data_source='file',
        file_path='data/sample_cases.json',
        custom_message="Please review these cases and take necessary action."
    )

    # Print report
    agent.print_report(report)

    print("\nAll campaigns complete!")


if __name__ == '__main__':
    main()
