"""
Easy Email Agent - Interactive Version
Just run and answer simple questions!
"""

import sys
sys.path.append('src')

from agent import EmailAgent
from utils.data_generator import DataGenerator
from utils.email_generator import EmailGenerator


# Your credentials (already set up)
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"
SENDER_NAME = "Your Name"
RECIPIENT_EMAIL = "recipient@example.com"


def main():
    print("="*70)
    print("EASY EMAIL AGENT")
    print("="*70)
    print()
    print("Your credentials are already set up!")
    print(f"  Sender: {SENDER_EMAIL}")
    print(f"  Sender Name: {SENDER_NAME}")
    print(f"  Recipient: {RECIPIENT_EMAIL}")
    print()

    # Ask user how many emails
    print("HOW MANY EMAILS DO YOU WANT TO SEND?")
    print("-"*70)

    # Ask about opportunities
    opp_input = input("How many OPPORTUNITY emails? (or 0 for none) [5]: ").strip()
    num_opportunities = int(opp_input) if opp_input else 5

    # Ask about cases
    case_input = input("How many CASE emails? (or 0 for none) [5]: ").strip()
    num_cases = int(case_input) if case_input else 5

    total_emails = num_opportunities + num_cases

    if total_emails == 0:
        print("\nNo emails to send! Exiting.")
        return

    # Ask for custom message
    print()
    custom_message = input("Enter custom message (or press Enter to skip): ").strip()
    if not custom_message:
        custom_message = "This is an automated email with Salesforce data. Please review and take necessary action."

    # Confirmation
    print()
    print("="*70)
    print("CONFIRMATION")
    print("="*70)
    print(f"  Opportunity emails: {num_opportunities}")
    print(f"  Case emails: {num_cases}")
    print(f"  Total emails: {total_emails}")
    print(f"  Recipient: {RECIPIENT_EMAIL}")
    print()

    confirm = input("Ready to send? (yes/no) [yes]: ").strip().lower()
    if confirm and confirm not in ['yes', 'y']:
        print("\nCancelled.")
        return

    # Initialize services
    print()
    print("="*70)
    print("STARTING EMAIL CAMPAIGN")
    print("="*70)
    print()

    print("✓ Initializing services...")
    data_generator = DataGenerator()
    agent = EmailAgent(
        sender_email=SENDER_EMAIL,
        sender_password=SENDER_PASSWORD,
        sender_name=SENDER_NAME
    )
    email_generator = EmailGenerator()

    all_results = []

    try:
        # Send opportunity emails
        if num_opportunities > 0:
            print(f"\n📧 Generating {num_opportunities} random opportunities...")
            opportunities = data_generator.generate_opportunities(num_opportunities)
            print(f"✓ Generated {len(opportunities)} opportunities\n")

            print("Opportunities:")
            for i, opp in enumerate(opportunities, 1):
                print(f"  {i}. {opp['opportunity_name']} - ${opp['amount']:,}")

            print(f"\n📤 Sending {num_opportunities} opportunity emails...\n")

            sent = 0
            failed = 0

            for i, opp in enumerate(opportunities, 1):
                try:
                    email_content = email_generator.generate_opportunity_email(
                        opportunity_data=opp,
                        custom_message=custom_message
                    )

                    success = agent.email_service.send_email(
                        to_email=RECIPIENT_EMAIL,
                        subject=email_content['subject'],
                        html_content=email_content['html_content']
                    )

                    if success:
                        sent += 1
                        print(f"  ✓ [{i}/{num_opportunities}] Sent: {opp['opportunity_name']}")
                    else:
                        failed += 1
                        print(f"  ✗ [{i}/{num_opportunities}] Failed: {opp['opportunity_name']}")

                except Exception as e:
                    failed += 1
                    print(f"  ✗ [{i}/{num_opportunities}] Error: {str(e)}")

            print(f"\n  Result: {sent} sent, {failed} failed\n")
            all_results.append({'type': 'Opportunity', 'sent': sent, 'failed': failed})

        # Send case emails
        if num_cases > 0:
            print(f"\n📧 Generating {num_cases} random cases...")
            cases = data_generator.generate_cases(num_cases)
            print(f"✓ Generated {len(cases)} cases\n")

            print("Cases:")
            for i, case in enumerate(cases, 1):
                print(f"  {i}. Case {case['case_number']}: {case['subject']}")

            print(f"\n📤 Sending {num_cases} case emails...\n")

            sent = 0
            failed = 0

            for i, case in enumerate(cases, 1):
                try:
                    email_content = email_generator.generate_case_email(
                        case_data=case,
                        custom_message=custom_message
                    )

                    success = agent.email_service.send_email(
                        to_email=RECIPIENT_EMAIL,
                        subject=email_content['subject'],
                        html_content=email_content['html_content']
                    )

                    if success:
                        sent += 1
                        print(f"  ✓ [{i}/{num_cases}] Sent: Case {case['case_number']}")
                    else:
                        failed += 1
                        print(f"  ✗ [{i}/{num_cases}] Failed: Case {case['case_number']}")

                except Exception as e:
                    failed += 1
                    print(f"  ✗ [{i}/{num_cases}] Error: {str(e)}")

            print(f"\n  Result: {sent} sent, {failed} failed\n")
            all_results.append({'type': 'Case', 'sent': sent, 'failed': failed})

        # Final summary
        print("="*70)
        print("CAMPAIGN COMPLETE!")
        print("="*70)
        print()

        total_sent = sum(r['sent'] for r in all_results)
        total_failed = sum(r['failed'] for r in all_results)
        total_processed = total_sent + total_failed

        for result in all_results:
            print(f"  {result['type']}s: {result['sent']} sent, {result['failed']} failed")

        print()
        print(f"  Total: {total_sent}/{total_processed} sent successfully")
        if total_processed > 0:
            print(f"  Success Rate: {(total_sent/total_processed*100):.1f}%")
        print()

        if total_failed == 0:
            print("✓ All emails sent successfully! 🎉")
        else:
            print(f"⚠ {total_failed} emails failed.")

        print()
        print(f"📬 Check inbox: {RECIPIENT_EMAIL}")
        print()

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
