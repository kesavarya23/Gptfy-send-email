"""
Email Agent Runner
Simple script to run the email agent with your credentials
"""

import sys
sys.path.append('src')

from agent import EmailAgent


def main():
    print("="*70)
    print("SALESFORCE EMAIL AGENT")
    print("="*70)
    print("\nThis agent will automatically generate and send multiple emails.")
    print()

    # Get sender credentials
    print("SENDER CREDENTIALS")
    print("-" * 70)
    sender_email = input("Enter sender email address: ").strip()
    sender_password = input("Enter sender password (app password for Gmail): ").strip()
    sender_name = input("Enter sender name (optional): ").strip() or None

    print()

    # Get recipient
    print("RECIPIENT")
    print("-" * 70)
    recipient_email = input("Enter recipient email address: ").strip()

    print()

    # Get data source
    print("DATA SOURCE")
    print("-" * 70)
    print("1. Load from file (JSON/CSV)")
    print("2. Load from Salesforce API")
    data_source_choice = input("Choose option (1 or 2): ").strip()

    # Get data type
    print()
    print("DATA TYPE")
    print("-" * 70)
    print("1. Opportunities")
    print("2. Cases")
    data_type_choice = input("Choose option (1 or 2): ").strip()

    data_type = 'opportunity' if data_type_choice == '1' else 'case'

    print()

    # Initialize agent
    print("Initializing Email Agent...")
    agent = EmailAgent(
        sender_email=sender_email,
        sender_password=sender_password,
        sender_name=sender_name
    )

    # Configure based on data source
    if data_source_choice == '1':
        # File source
        print()
        print("FILE SOURCE")
        print("-" * 70)
        default_file = f"data/sample_{data_type if data_type == 'opportunity' else 'case'}es.json"
        file_path = input(f"Enter file path (or press Enter for {default_file}): ").strip()
        file_path = file_path or default_file

        custom_message = input("\nEnter custom message (optional): ").strip() or None

        print("\n" + "="*70)
        print(f"STARTING EMAIL CAMPAIGN")
        print("="*70)
        print(f"Source: File ({file_path})")
        print(f"Type: {data_type.title()}")
        print(f"Recipient: {recipient_email}")
        print("="*70 + "\n")

        # Run agent
        if data_type == 'opportunity':
            report = agent.send_opportunity_emails(
                recipient_email=recipient_email,
                data_source='file',
                file_path=file_path,
                custom_message=custom_message
            )
        else:
            report = agent.send_case_emails(
                recipient_email=recipient_email,
                data_source='file',
                file_path=file_path,
                custom_message=custom_message
            )

    else:
        # Salesforce source
        print()
        print("SALESFORCE CREDENTIALS")
        print("-" * 70)
        sf_username = input("Enter Salesforce username: ").strip()
        sf_password = input("Enter Salesforce password: ").strip()
        sf_token = input("Enter Salesforce security token: ").strip()
        sf_domain = input("Enter Salesforce domain (login/test) [login]: ").strip() or 'login'

        print("\nConnecting to Salesforce...")
        if not agent.setup_salesforce(sf_username, sf_password, sf_token, sf_domain):
            print("Failed to connect to Salesforce. Exiting.")
            return

        limit = input("\nEnter maximum number of records to process [10]: ").strip()
        limit = int(limit) if limit else 10

        custom_message = input("Enter custom message (optional): ").strip() or None

        print("\n" + "="*70)
        print(f"STARTING EMAIL CAMPAIGN")
        print("="*70)
        print(f"Source: Salesforce")
        print(f"Type: {data_type.title()}")
        print(f"Recipient: {recipient_email}")
        print(f"Limit: {limit}")
        print("="*70 + "\n")

        # Run agent
        if data_type == 'opportunity':
            report = agent.send_opportunity_emails(
                recipient_email=recipient_email,
                data_source='salesforce',
                limit=limit,
                custom_message=custom_message
            )
        else:
            report = agent.send_case_emails(
                recipient_email=recipient_email,
                data_source='salesforce',
                limit=limit,
                custom_message=custom_message
            )

    # Print report
    agent.print_report(report)

    print("Email campaign complete!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
