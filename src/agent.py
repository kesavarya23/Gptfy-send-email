"""
Email Agent Module
Autonomous agent for generating and sending multiple emails
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import time

from config import Config
from services.email_service import EmailService
from services.salesforce_service import SalesforceService
from utils.email_generator import EmailGenerator
from utils.data_loader import DataLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailAgent:
    """
    Autonomous agent for generating and sending multiple emails

    This agent can:
    - Load data from Salesforce or files
    - Generate professional emails
    - Send emails to one or multiple recipients
    - Track success/failure
    - Provide detailed reports
    """

    def __init__(
        self,
        sender_email: str,
        sender_password: str,
        sender_name: Optional[str] = None,
        smtp_host: str = 'smtp.gmail.com',
        smtp_port: int = 587
    ):
        """
        Initialize the Email Agent

        Args:
            sender_email: Email address to send from
            sender_password: SMTP password (app password for Gmail)
            sender_name: Display name for sender
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.sender_name = sender_name or sender_email
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

        # Initialize services
        self.email_service = EmailService(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            username=sender_email,
            password=sender_password,
            sender_email=sender_email,
            sender_name=self.sender_name
        )
        self.email_generator = EmailGenerator()
        self.data_loader = DataLoader()
        self.sf_service = None

        # Statistics
        self.stats = {
            'total_processed': 0,
            'total_sent': 0,
            'total_failed': 0,
            'start_time': None,
            'end_time': None,
            'failed_items': []
        }

        logger.info(f"Email Agent initialized for sender: {sender_email}")

    def setup_salesforce(
        self,
        username: str,
        password: str,
        security_token: str,
        domain: str = 'login'
    ):
        """
        Setup Salesforce connection

        Args:
            username: Salesforce username
            password: Salesforce password
            security_token: Salesforce security token
            domain: 'login' for production, 'test' for sandbox
        """
        try:
            self.sf_service = SalesforceService(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain
            )
            logger.info("Salesforce connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {str(e)}")
            return False

    def send_opportunity_emails(
        self,
        recipient_email: str,
        data_source: str = 'salesforce',
        file_path: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: int = 100,
        custom_message: Optional[str] = None
    ) -> Dict:
        """
        Send opportunity emails to recipient

        Args:
            recipient_email: Email address to send to
            data_source: 'salesforce' or 'file'
            file_path: Path to data file (required if source is 'file')
            filters: Salesforce filters (optional)
            limit: Maximum records to process
            custom_message: Custom message for emails

        Returns:
            Dictionary with results and statistics
        """
        self.stats['start_time'] = datetime.now()
        logger.info(f"Starting opportunity email campaign to {recipient_email}")

        # Load data
        opportunities = self._load_data(
            data_type='opportunity',
            data_source=data_source,
            file_path=file_path,
            filters=filters,
            limit=limit
        )

        if not opportunities:
            logger.warning("No opportunities found")
            return self._generate_report()

        logger.info(f"Loaded {len(opportunities)} opportunities")

        # Generate and send emails
        for i, opp in enumerate(opportunities, 1):
            try:
                logger.info(f"Processing opportunity {i}/{len(opportunities)}: {opp.get('opportunity_name', 'Unknown')}")

                # Generate email
                email_content = self.email_generator.generate_opportunity_email(
                    opportunity_data=opp,
                    custom_message=custom_message
                )

                # Send email with both HTML and plain text
                success = self.email_service.send_email(
                    to_email=recipient_email,
                    subject=email_content['subject'],
                    html_content=email_content['html_content'],
                    plain_text=email_content.get('plain_text')
                )

                self.stats['total_processed'] += 1

                if success:
                    self.stats['total_sent'] += 1
                    logger.info(f"✓ Sent: {email_content['subject']}")
                else:
                    self.stats['total_failed'] += 1
                    self.stats['failed_items'].append({
                        'type': 'opportunity',
                        'name': opp.get('opportunity_name', 'Unknown'),
                        'reason': 'Failed to send'
                    })
                    logger.error(f"✗ Failed: {email_content['subject']}")

                # Delay between emails
                time.sleep(30)

            except Exception as e:
                self.stats['total_processed'] += 1
                self.stats['total_failed'] += 1
                self.stats['failed_items'].append({
                    'type': 'opportunity',
                    'name': opp.get('opportunity_name', 'Unknown'),
                    'reason': str(e)
                })
                logger.error(f"Error processing opportunity: {str(e)}")

        self.stats['end_time'] = datetime.now()
        return self._generate_report()

    def send_case_emails(
        self,
        recipient_email: str,
        data_source: str = 'salesforce',
        file_path: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: int = 100,
        custom_message: Optional[str] = None
    ) -> Dict:
        """
        Send case emails to recipient

        Args:
            recipient_email: Email address to send to
            data_source: 'salesforce' or 'file'
            file_path: Path to data file (required if source is 'file')
            filters: Salesforce filters (optional)
            limit: Maximum records to process
            custom_message: Custom message for emails

        Returns:
            Dictionary with results and statistics
        """
        self.stats['start_time'] = datetime.now()
        logger.info(f"Starting case email campaign to {recipient_email}")

        # Load data
        cases = self._load_data(
            data_type='case',
            data_source=data_source,
            file_path=file_path,
            filters=filters,
            limit=limit
        )

        if not cases:
            logger.warning("No cases found")
            return self._generate_report()

        logger.info(f"Loaded {len(cases)} cases")

        # Generate and send emails
        for i, case in enumerate(cases, 1):
            try:
                logger.info(f"Processing case {i}/{len(cases)}: {case.get('case_number', 'Unknown')}")

                # Generate email
                email_content = self.email_generator.generate_case_email(
                    case_data=case,
                    custom_message=custom_message
                )

                # Send email with both HTML and plain text
                success = self.email_service.send_email(
                    to_email=recipient_email,
                    subject=email_content['subject'],
                    html_content=email_content['html_content'],
                    plain_text=email_content.get('plain_text')
                )

                self.stats['total_processed'] += 1

                if success:
                    self.stats['total_sent'] += 1
                    logger.info(f"✓ Sent: {email_content['subject']}")
                else:
                    self.stats['total_failed'] += 1
                    self.stats['failed_items'].append({
                        'type': 'case',
                        'name': case.get('case_number', 'Unknown'),
                        'reason': 'Failed to send'
                    })
                    logger.error(f"✗ Failed: {email_content['subject']}")

                # Delay between emails
                time.sleep(30)

            except Exception as e:
                self.stats['total_processed'] += 1
                self.stats['total_failed'] += 1
                self.stats['failed_items'].append({
                    'type': 'case',
                    'name': case.get('case_number', 'Unknown'),
                    'reason': str(e)
                })
                logger.error(f"Error processing case: {str(e)}")

        self.stats['end_time'] = datetime.now()
        return self._generate_report()

    def send_bulk_to_multiple_recipients(
        self,
        recipient_emails: List[str],
        data_type: str,
        data_source: str = 'salesforce',
        file_path: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: int = 100,
        custom_message: Optional[str] = None
    ) -> Dict:
        """
        Send emails to multiple recipients

        Args:
            recipient_emails: List of email addresses
            data_type: 'opportunity' or 'case'
            data_source: 'salesforce' or 'file'
            file_path: Path to data file (required if source is 'file')
            filters: Salesforce filters (optional)
            limit: Maximum records to process
            custom_message: Custom message for emails

        Returns:
            Dictionary with results and statistics
        """
        self.stats['start_time'] = datetime.now()
        logger.info(f"Starting bulk email campaign to {len(recipient_emails)} recipients")

        # Load data once
        data = self._load_data(
            data_type=data_type,
            data_source=data_source,
            file_path=file_path,
            filters=filters,
            limit=limit
        )

        if not data:
            logger.warning(f"No {data_type} data found")
            return self._generate_report()

        logger.info(f"Loaded {len(data)} {data_type} records")

        # Send to each recipient
        for recipient in recipient_emails:
            logger.info(f"\n{'='*60}")
            logger.info(f"Sending to: {recipient}")
            logger.info(f"{'='*60}")

            for i, item in enumerate(data, 1):
                try:
                    # Generate email based on type
                    if data_type == 'opportunity':
                        email_content = self.email_generator.generate_opportunity_email(
                            opportunity_data=item,
                            custom_message=custom_message
                        )
                    else:
                        email_content = self.email_generator.generate_case_email(
                            case_data=item,
                            custom_message=custom_message
                        )

                    # Send email with both HTML and plain text
                    success = self.email_service.send_email(
                        to_email=recipient,
                        subject=email_content['subject'],
                        html_content=email_content['html_content'],
                        plain_text=email_content.get('plain_text')
                    )

                    self.stats['total_processed'] += 1

                    if success:
                        self.stats['total_sent'] += 1
                        logger.info(f"✓ [{i}/{len(data)}] Sent to {recipient}")
                    else:
                        self.stats['total_failed'] += 1
                        self.stats['failed_items'].append({
                            'recipient': recipient,
                            'type': data_type,
                            'item': item.get('opportunity_name' if data_type == 'opportunity' else 'case_number', 'Unknown'),
                            'reason': 'Failed to send'
                        })
                        logger.error(f"✗ [{i}/{len(data)}] Failed to send to {recipient}")

                    # Delay between emails
                    time.sleep(30)

                except Exception as e:
                    self.stats['total_processed'] += 1
                    self.stats['total_failed'] += 1
                    self.stats['failed_items'].append({
                        'recipient': recipient,
                        'type': data_type,
                        'reason': str(e)
                    })
                    logger.error(f"Error: {str(e)}")

        self.stats['end_time'] = datetime.now()
        return self._generate_report()

    def _load_data(
        self,
        data_type: str,
        data_source: str,
        file_path: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Load data from source

        Args:
            data_type: 'opportunity' or 'case'
            data_source: 'salesforce' or 'file'
            file_path: Path to data file
            filters: Salesforce filters
            limit: Maximum records

        Returns:
            List of data dictionaries
        """
        if data_source == 'salesforce':
            if not self.sf_service:
                logger.error("Salesforce not configured. Call setup_salesforce() first.")
                return []

            if data_type == 'opportunity':
                return self.sf_service.get_opportunities(filters=filters, limit=limit)
            else:
                return self.sf_service.get_cases(filters=filters, limit=limit)

        elif data_source == 'file':
            if not file_path:
                logger.error("File path is required for file source")
                return []

            if file_path.endswith('.json'):
                return self.data_loader.load_from_json(file_path)
            elif file_path.endswith('.csv'):
                return self.data_loader.load_from_csv(file_path)
            else:
                logger.error("Unsupported file format. Use .json or .csv")
                return []

        else:
            logger.error(f"Invalid data source: {data_source}")
            return []

    def _generate_report(self) -> Dict:
        """Generate execution report"""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        report = {
            'success': self.stats['total_failed'] == 0,
            'total_processed': self.stats['total_processed'],
            'total_sent': self.stats['total_sent'],
            'total_failed': self.stats['total_failed'],
            'success_rate': (
                (self.stats['total_sent'] / self.stats['total_processed'] * 100)
                if self.stats['total_processed'] > 0 else 0
            ),
            'duration_seconds': duration,
            'failed_items': self.stats['failed_items'],
            'start_time': self.stats['start_time'],
            'end_time': self.stats['end_time']
        }

        return report

    def print_report(self, report: Dict):
        """
        Print a formatted report

        Args:
            report: Report dictionary from send methods
        """
        print("\n" + "="*70)
        print("EMAIL CAMPAIGN REPORT")
        print("="*70)
        print(f"\nStatus: {'✓ SUCCESS' if report['success'] else '✗ COMPLETED WITH ERRORS'}")
        print(f"\nStatistics:")
        print(f"  Total Processed: {report['total_processed']}")
        print(f"  Successfully Sent: {report['total_sent']}")
        print(f"  Failed: {report['total_failed']}")
        print(f"  Success Rate: {report['success_rate']:.1f}%")

        if report['duration_seconds']:
            print(f"  Duration: {report['duration_seconds']:.2f} seconds")

        if report['failed_items']:
            print(f"\nFailed Items:")
            for item in report['failed_items']:
                print(f"  - {item}")

        print("\n" + "="*70 + "\n")

    def reset_stats(self):
        """Reset statistics for new campaign"""
        self.stats = {
            'total_processed': 0,
            'total_sent': 0,
            'total_failed': 0,
            'start_time': None,
            'end_time': None,
            'failed_items': []
        }
        logger.info("Statistics reset")
