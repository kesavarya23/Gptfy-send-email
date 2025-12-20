"""
Main Application Module
Entry point for the Salesforce Email Sender application
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from config import Config
from services.email_service import EmailService
from services.salesforce_service import SalesforceService
from utils.email_generator import EmailGenerator
from utils.data_loader import DataLoader
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SalesforceEmailApp:
    """Main application class"""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize application

        Args:
            config_file: Path to .env file (optional)
        """
        self.config = Config(config_file)
        self.email_service = None
        self.sf_service = None
        self.email_generator = EmailGenerator()
        self.data_loader = DataLoader()

    def setup_email_service(self):
        """Initialize email service"""
        if not self.config.validate_email_config():
            raise ValueError("Email configuration is invalid. Please check your .env file.")

        self.email_service = EmailService(**self.config.get_email_config())
        logger.info("Email service initialized")

    def setup_salesforce_service(self):
        """Initialize Salesforce service"""
        if not self.config.validate_salesforce_config():
            logger.warning("Salesforce configuration is invalid. API features disabled.")
            return False

        try:
            self.sf_service = SalesforceService(**self.config.get_salesforce_config())
            logger.info("Salesforce service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Salesforce service: {str(e)}")
            return False

    def send_opportunity_emails_from_salesforce(
        self,
        recipient_email: Optional[str] = None,
        filters: Optional[dict] = None,
        limit: int = 10,
        custom_message: Optional[str] = None
    ):
        """
        Fetch opportunities from Salesforce and send emails

        Args:
            recipient_email: Email address to send to
            filters: Salesforce query filters
            limit: Maximum number of opportunities
            custom_message: Custom message for emails
        """
        if not self.sf_service:
            logger.error("Salesforce service not initialized")
            return

        recipient = recipient_email or self.config.default_recipient
        if not recipient:
            logger.error("No recipient email specified")
            return

        logger.info(f"Fetching opportunities from Salesforce...")
        opportunities = self.sf_service.get_opportunities(filters=filters, limit=limit)

        if not opportunities:
            logger.warning("No opportunities found")
            return

        logger.info(f"Found {len(opportunities)} opportunities. Generating emails...")

        emails_data = []
        for opp in opportunities:
            email_content = self.email_generator.generate_opportunity_email(
                opp, custom_message=custom_message
            )
            emails_data.append({
                'to_email': recipient,
                'subject': email_content['subject'],
                'html_content': email_content['html_content']
            })

        logger.info(f"Sending {len(emails_data)} emails...")
        result = self.email_service.send_bulk_emails(emails_data)

        logger.info(f"Email sending complete: {result['success_count']} sent, {result['failed_count']} failed")

    def send_case_emails_from_salesforce(
        self,
        recipient_email: Optional[str] = None,
        filters: Optional[dict] = None,
        limit: int = 10,
        custom_message: Optional[str] = None
    ):
        """
        Fetch cases from Salesforce and send emails

        Args:
            recipient_email: Email address to send to
            filters: Salesforce query filters
            limit: Maximum number of cases
            custom_message: Custom message for emails
        """
        if not self.sf_service:
            logger.error("Salesforce service not initialized")
            return

        recipient = recipient_email or self.config.default_recipient
        if not recipient:
            logger.error("No recipient email specified")
            return

        logger.info(f"Fetching cases from Salesforce...")
        cases = self.sf_service.get_cases(filters=filters, limit=limit)

        if not cases:
            logger.warning("No cases found")
            return

        logger.info(f"Found {len(cases)} cases. Generating emails...")

        emails_data = []
        for case in cases:
            email_content = self.email_generator.generate_case_email(
                case, custom_message=custom_message
            )
            emails_data.append({
                'to_email': recipient,
                'subject': email_content['subject'],
                'html_content': email_content['html_content']
            })

        logger.info(f"Sending {len(emails_data)} emails...")
        result = self.email_service.send_bulk_emails(emails_data)

        logger.info(f"Email sending complete: {result['success_count']} sent, {result['failed_count']} failed")

    def send_emails_from_file(
        self,
        file_path: str,
        data_type: str,
        recipient_email: Optional[str] = None,
        custom_message: Optional[str] = None
    ):
        """
        Load data from file and send emails

        Args:
            file_path: Path to JSON or CSV file
            data_type: 'opportunity' or 'case'
            recipient_email: Email address to send to
            custom_message: Custom message for emails
        """
        recipient = recipient_email or self.config.default_recipient
        if not recipient:
            logger.error("No recipient email specified")
            return

        # Load data from file
        if file_path.endswith('.json'):
            data = self.data_loader.load_from_json(file_path)
        elif file_path.endswith('.csv'):
            data = self.data_loader.load_from_csv(file_path)
        else:
            logger.error("Unsupported file format. Use .json or .csv")
            return

        if not data:
            logger.error("No data loaded from file")
            return

        logger.info(f"Loaded {len(data)} records. Generating emails...")

        emails_data = []
        for item in data:
            try:
                if data_type == 'opportunity':
                    email_content = self.email_generator.generate_opportunity_email(
                        item, custom_message=custom_message
                    )
                elif data_type == 'case':
                    email_content = self.email_generator.generate_case_email(
                        item, custom_message=custom_message
                    )
                else:
                    logger.error(f"Invalid data type: {data_type}")
                    return

                emails_data.append({
                    'to_email': recipient,
                    'subject': email_content['subject'],
                    'html_content': email_content['html_content']
                })
            except Exception as e:
                logger.error(f"Error generating email: {str(e)}")
                continue

        if not emails_data:
            logger.error("No emails generated")
            return

        logger.info(f"Sending {len(emails_data)} emails...")
        result = self.email_service.send_bulk_emails(emails_data)

        logger.info(f"Email sending complete: {result['success_count']} sent, {result['failed_count']} failed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Send Salesforce-related emails'
    )
    parser.add_argument(
        '--config',
        help='Path to .env configuration file',
        default=None
    )
    parser.add_argument(
        '--source',
        choices=['salesforce', 'file'],
        required=True,
        help='Data source: salesforce or file'
    )
    parser.add_argument(
        '--type',
        choices=['opportunity', 'case'],
        required=True,
        help='Data type: opportunity or case'
    )
    parser.add_argument(
        '--file',
        help='Path to data file (required if source is file)',
        default=None
    )
    parser.add_argument(
        '--recipient',
        help='Recipient email address',
        default=None
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of records to process (for Salesforce source)'
    )
    parser.add_argument(
        '--message',
        help='Custom message to include in emails',
        default=None
    )

    args = parser.parse_args()

    try:
        # Initialize app
        app = SalesforceEmailApp(config_file=args.config)
        app.setup_email_service()

        # Process based on source
        if args.source == 'salesforce':
            if not app.setup_salesforce_service():
                logger.error("Cannot proceed without Salesforce connection")
                sys.exit(1)

            if args.type == 'opportunity':
                app.send_opportunity_emails_from_salesforce(
                    recipient_email=args.recipient,
                    limit=args.limit,
                    custom_message=args.message
                )
            else:
                app.send_case_emails_from_salesforce(
                    recipient_email=args.recipient,
                    limit=args.limit,
                    custom_message=args.message
                )

        elif args.source == 'file':
            if not args.file:
                logger.error("--file is required when source is 'file'")
                sys.exit(1)

            app.send_emails_from_file(
                file_path=args.file,
                data_type=args.type,
                recipient_email=args.recipient,
                custom_message=args.message
            )

        logger.info("Application completed successfully")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
