"""
Smart Email Agent - Generate and Send Random Emails
Specify how many emails you want and what type - agent generates random data and sends!
"""

import sys
sys.path.append('src')

from agent import EmailAgent
from utils.data_generator import DataGenerator


# ============================================================================
# CONFIGURATION - ENTER YOUR SETTINGS HERE
# ============================================================================

# Email Credentials
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"  # Use Gmail App Password
SENDER_NAME = "Your Name"
RECIPIENT_EMAIL = "recipient@example.com"

# Email Configuration
# Options: "opportunity", "case", or "both"
EMAIL_TYPE = "both"

# How many emails to send?
NUM_OPPORTUNITIES = 5   # Number of opportunity emails
NUM_CASES = 5           # Number of case emails

# Custom message in emails (optional)
CUSTOM_MESSAGE = "This is an automated email with Salesforce data. Please review and take necessary action."

# ============================================================================
# DO NOT EDIT BELOW THIS LINE
# ============================================================================


def main():
    print("="*70)
    print("SMART EMAIL AGENT - RANDOM DATA GENERATOR")
    print("="*70)
    print()

    # Validate configuration
    if SENDER_EMAIL == "your-email@gmail.com":
        print("❌ Error: Please configure SENDER_EMAIL in smart_agent.py")
        return

    if RECIPIENT_EMAIL == "recipient@example.com":
        print("❌ Error: Please configure RECIPIENT_EMAIL in smart_agent.py")
        return

    # Display configuration
    print("Configuration:")
    print(f"  Sender: {SENDER_EMAIL}")
    print(f"  Recipient: {RECIPIENT_EMAIL}")
    print(f"  Email Type: {EMAIL_TYPE}")

    if EMAIL_TYPE in ["opportunity", "both"]:
        print(f"  Opportunities to send: {NUM_OPPORTUNITIES}")
    if EMAIL_TYPE in ["case", "both"]:
        print(f"  Cases to send: {NUM_CASES}")

    total_emails = 0
    if EMAIL_TYPE in ["opportunity", "both"]:
        total_emails += NUM_OPPORTUNITIES
    if EMAIL_TYPE in ["case", "both"]:
        total_emails += NUM_CASES

    print(f"  Total emails: {total_emails}")
    print()

    # Initialize data generator
    print("✓ Initializing Random Data Generator...")
    data_generator = DataGenerator()

    # Initialize email agent
    print("✓ Initializing Email Agent...")
    agent = EmailAgent(
        sender_email=SENDER_EMAIL,
        sender_password=SENDER_PASSWORD,
        sender_name=SENDER_NAME
    )

    print()
    print("="*70)
    print("GENERATING RANDOM DATA AND SENDING EMAILS")
    print("="*70)
    print()

    all_reports = []

    try:
        # Send opportunity emails
        if EMAIL_TYPE in ["opportunity", "both"]:
            print(f"📧 Generating {NUM_OPPORTUNITIES} random opportunities...")
            opportunities = data_generator.generate_opportunities(NUM_OPPORTUNITIES)

            print(f"✓ Generated {len(opportunities)} opportunities")
            print(f"📤 Sending opportunity emails...\n")

            for i, opp in enumerate(opportunities, 1):
                print(f"  [{i}/{NUM_OPPORTUNITIES}] {opp['opportunity_name']} - ${opp['amount']:,}")

            print()

            # Send emails
            report = agent.send_opportunity_emails(
                recipient_email=RECIPIENT_EMAIL,
                data_source='file',  # Using generated data, not actual file
                file_path=None,
                custom_message=CUSTOM_MESSAGE
            )

            # Actually we need to send manually with generated data
            # Let me use the agent differently
            emails_sent = 0
            emails_failed = 0

            for opp in opportunities:
                try:
                    from utils.email_generator import EmailGenerator
                    email_gen = EmailGenerator()

                    email_content = email_gen.generate_opportunity_email(
                        opportunity_data=opp,
                        custom_message=CUSTOM_MESSAGE
                    )

                    success = agent.email_service.send_email(
                        to_email=RECIPIENT_EMAIL,
                        subject=email_content['subject'],
                        html_content=email_content['html_content']
                    )

                    if success:
                        emails_sent += 1
                        print(f"    ✓ Sent: {email_content['subject']}")
                    else:
                        emails_failed += 1
                        print(f"    ✗ Failed: {email_content['subject']}")

                except Exception as e:
                    emails_failed += 1
                    print(f"    ✗ Error: {str(e)}")

            print(f"\n  Opportunity Emails: {emails_sent} sent, {emails_failed} failed\n")
            all_reports.append({
                'type': 'opportunity',
                'sent': emails_sent,
                'failed': emails_failed
            })

        # Send case emails
        if EMAIL_TYPE in ["case", "both"]:
            if EMAIL_TYPE == "both":
                agent.reset_stats()

            print(f"📧 Generating {NUM_CASES} random cases...")
            cases = data_generator.generate_cases(NUM_CASES)

            print(f"✓ Generated {len(cases)} cases")
            print(f"📤 Sending case emails...\n")

            for i, case in enumerate(cases, 1):
                print(f"  [{i}/{NUM_CASES}] Case {case['case_number']}: {case['subject']}")

            print()

            # Send emails
            emails_sent = 0
            emails_failed = 0

            for case in cases:
                try:
                    from utils.email_generator import EmailGenerator
                    email_gen = EmailGenerator()

                    email_content = email_gen.generate_case_email(
                        case_data=case,
                        custom_message=CUSTOM_MESSAGE
                    )

                    success = agent.email_service.send_email(
                        to_email=RECIPIENT_EMAIL,
                        subject=email_content['subject'],
                        html_content=email_content['html_content']
                    )

                    if success:
                        emails_sent += 1
                        print(f"    ✓ Sent: {email_content['subject']}")
                    else:
                        emails_failed += 1
                        print(f"    ✗ Failed: {email_content['subject']}")

                except Exception as e:
                    emails_failed += 1
                    print(f"    ✗ Error: {str(e)}")

            print(f"\n  Case Emails: {emails_sent} sent, {emails_failed} failed\n")
            all_reports.append({
                'type': 'case',
                'sent': emails_sent,
                'failed': emails_failed
            })

        # Final summary
        print("="*70)
        print("FINAL SUMMARY")
        print("="*70)
        print()

        total_sent = sum(r['sent'] for r in all_reports)
        total_failed = sum(r['failed'] for r in all_reports)
        total_processed = total_sent + total_failed

        for report in all_reports:
            print(f"  {report['type'].title()}s: {report['sent']} sent, {report['failed']} failed")

        print()
        print(f"  Total Processed: {total_processed}")
        print(f"  Total Sent: {total_sent}")
        print(f"  Total Failed: {total_failed}")
        print(f"  Success Rate: {(total_sent/total_processed*100) if total_processed > 0 else 0:.1f}%")
        print()

        if total_failed == 0:
            print("✓ All emails sent successfully!")
        else:
            print(f"⚠ {total_failed} emails failed. Check error messages above.")

        print()
        print(f"📬 Check inbox: {RECIPIENT_EMAIL}")
        print()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
