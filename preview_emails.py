"""
Preview Emails Without Sending
Shows you exactly what emails will be generated without actually sending them
"""

import sys
sys.path.append('src')

from utils.email_generator import EmailGenerator
from utils.data_loader import DataLoader


def main():
    print("="*70)
    print("EMAIL PREVIEW (No emails will be sent)")
    print("="*70)
    print()

    # Load data
    data_loader = DataLoader()
    email_generator = EmailGenerator()

    # Load opportunities
    opportunities = data_loader.load_from_json('data/sample_opportunities.json')

    print(f"Found {len(opportunities)} opportunities:\n")

    # Preview each email
    for i, opp in enumerate(opportunities, 1):
        print(f"\n{'='*70}")
        print(f"EMAIL {i} OF {len(opportunities)}")
        print(f"{'='*70}\n")

        # Generate email
        email = email_generator.generate_opportunity_email(
            opportunity_data=opp,
            custom_message="Please review these Salesforce opportunities and provide your feedback."
        )

        print(f"To: kalanithi@cloudcompliance.app")
        print(f"From: gptfy2025@gmail.com (Gptfy Salesforce Team)")
        print(f"Subject: {email['subject']}")
        print()
        print("Content Preview:")
        print("-" * 70)
        print(f"Opportunity: {opp['opportunity_name']}")
        print(f"Account: {opp['account_name']}")
        print(f"Stage: {opp['stage']}")
        print(f"Amount: ${opp['amount']:,.2f}")
        print(f"Close Date: {opp['close_date']}")
        print(f"Probability: {opp['probability']}%")
        if opp.get('description'):
            print(f"Description: {opp['description']}")
        if opp.get('next_steps'):
            print(f"Next Steps: {opp['next_steps']}")
        print("-" * 70)

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}\n")
    print(f"Total emails to be sent: {len(opportunities)}")
    print(f"Sender: gptfy2025@gmail.com")
    print(f"Recipient: kalanithi@cloudcompliance.app")
    print(f"\nTo actually send these emails, run: python quick_agent.py")
    print()


if __name__ == '__main__':
    main()
