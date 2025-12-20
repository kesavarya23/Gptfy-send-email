"""
Interactive Smart Agent
Asks you how many emails to send and generates random data automatically
"""

import sys
sys.path.append('src')

from agent import EmailAgent
from utils.data_generator import DataGenerator
from utils.email_generator import EmailGenerator


def main():
    print("="*70)
    print("INTERACTIVE SMART EMAIL AGENT")
    print("="*70)
    print("\nThis agent generates random Salesforce data and sends emails!")
    print()

    # Get email credentials
    print("EMAIL CREDENTIALS")
    print("-"*70)
    sender_email = input("Enter sender email [gptfy2025@gmail.com]: ").strip() or "gptfy2025@gmail.com"
    sender_password = input("Enter sender password [Kesav@12345]: ").strip() or "Kesav@12345"
    sender_name = input("Enter sender name [Gptfy Salesforce Team]: ").strip() or "Gptfy Salesforce Team"

    print()
    recipient_email = input("Enter recipient email [kalanithi@cloudcompliance.app]: ").strip() or "kalanithi@cloudcompliance.app"

    # Get email configuration
    print()
    print("EMAIL CONFIGURATION")
    print("-"*70)
    print("What type of emails do you want to send?")
    print("  1. Opportunities only")
    print("  2. Cases only")
    print("  3. Both opportunities and cases")

    choice = input("\nChoose option (1/2/3) [3]: ").strip() or "3"

    num_opportunities = 0
    num_cases = 0

    if choice in ["1", "3"]:
        num_opportunities = int(input("\nHow many opportunity emails? [5]: ").strip() or "5")

    if choice in ["2", "3"]:
        num_cases = int(input("How many case emails? [5]: ").strip() or "5")

    custom_message = input("\nCustom message (optional): ").strip() or "Please review this Salesforce data and take necessary action."

    # Confirmation
    total_emails = num_opportunities + num_cases
    print()
    print("="*70)
    print("CONFIRMATION")
    print("="*70)
    print(f"  Sender: {sender_email}")
    print(f"  Recipient: {recipient_email}")
    print(f"  Opportunity emails: {num_opportunities}")
    print(f"  Case emails: {num_cases}")
    print(f"  Total emails: {total_emails}")
    print()

    confirm = input("Send these emails? (yes/no) [yes]: ").strip().lower() or "yes"

    if confirm not in ["yes", "y"]:
        print("\nCancelled.")
        return

    # Initialize services
    print()
    print("="*70)
    print("INITIALIZING")
    print("="*70)

    print("✓ Initializing Data Generator...")
    data_generator = DataGenerator()

    print("✓ Initializing Email Agent...")
    agent = EmailAgent(
        sender_email=sender_email,
        sender_password=sender_password,
        sender_name=sender_name
    )

    print("✓ Initializing Email Generator...")
    email_generator = EmailGenerator()

    print()
    print("="*70)
    print("GENERATING AND SENDING EMAILS")
    print("="*70)
    print()

    all_reports = []

    try:
        # Send opportunity emails
        if num_opportunities > 0:
            print(f"📧 Generating {num_opportunities} random opportunities...")
            opportunities = data_generator.generate_opportunities(num_opportunities)
            print(f"✓ Generated {len(opportunities)} opportunities\n")

            print("Opportunities to be sent:")
            for i, opp in enumerate(opportunities, 1):
                print(f"  {i}. {opp['opportunity_name']} - ${opp['amount']:,} - {opp['stage']}")

            print(f"\n📤 Sending {num_opportunities} opportunity emails...\n")

            emails_sent = 0
            emails_failed = 0

            for i, opp in enumerate(opportunities, 1):
                try:
                    email_content = email_generator.generate_opportunity_email(
                        opportunity_data=opp,
                        custom_message=custom_message
                    )

                    success = agent.email_service.send_email(
                        to_email=recipient_email,
                        subject=email_content['subject'],
                        html_content=email_content['html_content']
                    )

                    if success:
                        emails_sent += 1
                        print(f"  ✓ [{i}/{num_opportunities}] Sent: {opp['opportunity_name']}")
                    else:
                        emails_failed += 1
                        print(f"  ✗ [{i}/{num_opportunities}] Failed: {opp['opportunity_name']}")

                except Exception as e:
                    emails_failed += 1
                    print(f"  ✗ [{i}/{num_opportunities}] Error: {str(e)}")

            print(f"\n  Result: {emails_sent} sent, {emails_failed} failed\n")
            all_reports.append({
                'type': 'Opportunity',
                'sent': emails_sent,
                'failed': emails_failed
            })

        # Send case emails
        if num_cases > 0:
            print(f"📧 Generating {num_cases} random cases...")
            cases = data_generator.generate_cases(num_cases)
            print(f"✓ Generated {len(cases)} cases\n")

            print("Cases to be sent:")
            for i, case in enumerate(cases, 1):
                print(f"  {i}. Case {case['case_number']}: {case['subject']} - {case['priority']} Priority")

            print(f"\n📤 Sending {num_cases} case emails...\n")

            emails_sent = 0
            emails_failed = 0

            for i, case in enumerate(cases, 1):
                try:
                    email_content = email_generator.generate_case_email(
                        case_data=case,
                        custom_message=custom_message
                    )

                    success = agent.email_service.send_email(
                        to_email=recipient_email,
                        subject=email_content['subject'],
                        html_content=email_content['html_content']
                    )

                    if success:
                        emails_sent += 1
                        print(f"  ✓ [{i}/{num_cases}] Sent: Case {case['case_number']}")
                    else:
                        emails_failed += 1
                        print(f"  ✗ [{i}/{num_cases}] Failed: Case {case['case_number']}")

                except Exception as e:
                    emails_failed += 1
                    print(f"  ✗ [{i}/{num_cases}] Error: {str(e)}")

            print(f"\n  Result: {emails_sent} sent, {emails_failed} failed\n")
            all_reports.append({
                'type': 'Case',
                'sent': emails_sent,
                'failed': emails_failed
            })

        # Final summary
        print("="*70)
        print("CAMPAIGN COMPLETE!")
        print("="*70)
        print()

        total_sent = sum(r['sent'] for r in all_reports)
        total_failed = sum(r['failed'] for r in all_reports)
        total_processed = total_sent + total_failed

        for report in all_reports:
            print(f"  {report['type']}s: {report['sent']} sent, {report['failed']} failed")

        print()
        print(f"  Total: {total_sent}/{total_processed} sent successfully")
        print(f"  Success Rate: {(total_sent/total_processed*100) if total_processed > 0 else 0:.1f}%")
        print()

        if total_failed == 0:
            print("✓ All emails sent successfully! 🎉")
        else:
            print(f"⚠ {total_failed} emails failed.")

        print()
        print(f"📬 Check inbox: {recipient_email}")
        print()

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
