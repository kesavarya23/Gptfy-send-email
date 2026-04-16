"""
Salesforce Email Sender - Fully Interactive
No hardcoded values - enter everything when you run it!
"""

import sys
sys.path.append('src')

from agent import EmailAgent
from utils.data_generator import DataGenerator
from utils.email_generator import EmailGenerator


def main():
    print("="*70)
    print("SALESFORCE EMAIL SENDER")
    print("="*70)
    print()

    # Step 1: Get sender credentials
    print("STEP 1: SENDER INFORMATION")
    print("-"*70)
    sender_email = input("Enter sender email address: ").strip()
    sender_password = input("Enter sender password (Gmail App Password): ").strip()
    sender_name = input("Enter sender name (optional, press Enter to use email): ").strip()

    if not sender_name:
        sender_name = sender_email

    # Step 2: Get recipient
    print()
    print("STEP 2: RECIPIENT INFORMATION")
    print("-"*70)
    recipient_email = input("Enter recipient email address: ").strip()

    # Step 3: Get number of emails
    print()
    print("STEP 3: EMAIL CONFIGURATION")
    print("-"*70)

    opp_input = input("How many OPPORTUNITY emails to send? (0 to skip) [0]: ").strip()
    num_opportunities = int(opp_input) if opp_input else 0

    case_input = input("How many CASE emails to send? (0 to skip) [0]: ").strip()
    num_cases = int(case_input) if case_input else 0

    total_emails = num_opportunities + num_cases

    if total_emails == 0:
        print("\n❌ No emails to send! Please enter at least 1 opportunity or case email.")
        return

    # Step 4: Custom message (optional)
    print()
    custom_message = input("Enter custom message (optional, press Enter to skip): ").strip()
    if not custom_message:
        custom_message = "Please review this Salesforce data and take necessary action."

    # Step 5: Confirmation
    print()
    print("="*70)
    print("CONFIRMATION - PLEASE REVIEW")
    print("="*70)
    print(f"  From: {sender_name} <{sender_email}>")
    print(f"  To: {recipient_email}")
    print(f"  Opportunity emails: {num_opportunities}")
    print(f"  Case emails: {num_cases}")
    print(f"  Total emails: {total_emails}")
    print(f"  Message: {custom_message[:50]}..." if len(custom_message) > 50 else f"  Message: {custom_message}")
    print()

    confirm = input("Send these emails? (yes/no) [yes]: ").strip().lower()
    if confirm and confirm not in ['yes', 'y']:
        print("\n❌ Cancelled by user.")
        return

    # Step 6: Initialize and send
    print()
    print("="*70)
    print("INITIALIZING EMAIL SYSTEM")
    print("="*70)
    print()

    try:
        print("⚙️  Initializing data generator...")
        data_generator = DataGenerator()

        print("⚙️  Connecting to email server...")
        agent = EmailAgent(
            sender_email=sender_email,
            sender_password=sender_password,
            sender_name=sender_name
        )

        print("⚙️  Loading email templates...")
        email_generator = EmailGenerator()

        print("✓ All systems ready!")

    except Exception as e:
        print(f"\n❌ Initialization failed: {str(e)}")
        return

    # Step 7: Send emails
    print()
    print("="*70)
    print("SENDING EMAILS")
    print("="*70)
    print()

    all_results = []

    # Send opportunity emails
    if num_opportunities > 0:
        print(f"📧 Generating {num_opportunities} random opportunities...")
        opportunities = data_generator.generate_opportunities(num_opportunities)
        print(f"✓ Generated {len(opportunities)} opportunities\n")

        print("Opportunities to be sent:")
        for i, opp in enumerate(opportunities, 1):
            print(f"  {i}. {opp['opportunity_name']} - ${opp['amount']:,}")

        print(f"\n📤 Sending {num_opportunities} opportunity emails to {recipient_email}...\n")

        sent = 0
        failed = 0

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
                    sent += 1
                    print(f"  ✓ [{i}/{num_opportunities}] Sent: {opp['opportunity_name']}")
                else:
                    failed += 1
                    print(f"  ✗ [{i}/{num_opportunities}] Failed: {opp['opportunity_name']}")

            except Exception as e:
                failed += 1
                print(f"  ✗ [{i}/{num_opportunities}] Error: {str(e)}")

        print(f"\n  Opportunities: {sent} sent, {failed} failed\n")
        all_results.append({'type': 'Opportunity', 'sent': sent, 'failed': failed})

    # Send case emails
    if num_cases > 0:
        print(f"📧 Generating {num_cases} random cases...")
        cases = data_generator.generate_cases(num_cases)
        print(f"✓ Generated {len(cases)} cases\n")

        print("Cases to be sent:")
        for i, case in enumerate(cases, 1):
            print(f"  {i}. Case {case['case_number']}: {case['subject']}")

        print(f"\n📤 Sending {num_cases} case emails to {recipient_email}...\n")

        sent = 0
        failed = 0

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
                    sent += 1
                    print(f"  ✓ [{i}/{num_cases}] Sent: Case {case['case_number']}")
                else:
                    failed += 1
                    print(f"  ✗ [{i}/{num_cases}] Failed: Case {case['case_number']}")

            except Exception as e:
                failed += 1
                print(f"  ✗ [{i}/{num_cases}] Error: {str(e)}")

        print(f"\n  Cases: {sent} sent, {failed} failed\n")
        all_results.append({'type': 'Case', 'sent': sent, 'failed': failed})

    # Step 8: Final summary
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
    print(f"  Total Processed: {total_processed}")
    print(f"  Successfully Sent: {total_sent}")
    print(f"  Failed: {total_failed}")

    if total_processed > 0:
        print(f"  Success Rate: {(total_sent/total_processed*100):.1f}%")

    print()

    if total_failed == 0:
        print("✓✓✓ ALL EMAILS SENT SUCCESSFULLY! ✓✓✓")
    else:
        print(f"⚠ {total_failed} email(s) failed to send.")

    print()
    print(f"📬 Check inbox: {recipient_email}")
    print()
    print("="*70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
