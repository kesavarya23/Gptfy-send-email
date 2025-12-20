"""
Email Generator Module
Generates email content from templates and data
"""

from jinja2 import Environment, FileSystemLoader, Template
from datetime import datetime
from typing import Dict, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailGenerator:
    """Generate emails from templates"""

    def __init__(self, templates_dir: str = None):
        """
        Initialize email generator

        Args:
            templates_dir: Path to templates directory
        """
        if templates_dir is None:
            # Default to templates directory relative to this file
            templates_dir = Path(__file__).parent.parent / 'templates'

        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))
        logger.info(f"Email generator initialized with templates from: {templates_dir}")

    def generate_opportunity_email(
        self,
        opportunity_data: Dict,
        custom_message: Optional[str] = None,
        subject_prefix: str = "Salesforce Opportunity Update"
    ) -> Dict[str, str]:
        """
        Generate email for an opportunity

        Args:
            opportunity_data: Dictionary with opportunity fields
            custom_message: Optional custom message to include
            subject_prefix: Prefix for email subject

        Returns:
            Dictionary with 'subject' and 'html_content'
        """
        try:
            template = self.env.get_template('opportunity_email.html')

            # Add custom message and generated date
            template_data = opportunity_data.copy()
            if custom_message:
                template_data['custom_message'] = custom_message
            template_data['generated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Ensure amount is formatted
            if 'amount' in template_data and template_data['amount']:
                try:
                    template_data['amount'] = f"{float(template_data['amount']):,.2f}"
                except (ValueError, TypeError):
                    template_data['amount'] = '0.00'

            html_content = template.render(**template_data)

            # Generate subject
            opp_name = opportunity_data.get('opportunity_name', 'Unknown')
            subject = f"{subject_prefix}: {opp_name}"

            logger.info(f"Generated opportunity email for: {opp_name}")

            return {
                'subject': subject,
                'html_content': html_content
            }

        except Exception as e:
            logger.error(f"Error generating opportunity email: {str(e)}")
            raise

    def generate_case_email(
        self,
        case_data: Dict,
        custom_message: Optional[str] = None,
        subject_prefix: str = "Salesforce Case Update"
    ) -> Dict[str, str]:
        """
        Generate email for a case

        Args:
            case_data: Dictionary with case fields
            custom_message: Optional custom message to include
            subject_prefix: Prefix for email subject

        Returns:
            Dictionary with 'subject' and 'html_content'
        """
        try:
            template = self.env.get_template('case_email.html')

            # Add custom message and generated date
            template_data = case_data.copy()
            if custom_message:
                template_data['custom_message'] = custom_message
            template_data['generated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            html_content = template.render(**template_data)

            # Generate subject
            case_number = case_data.get('case_number', 'Unknown')
            case_subject = case_data.get('subject', 'No Subject')
            subject = f"{subject_prefix}: {case_number} - {case_subject}"

            logger.info(f"Generated case email for: {case_number}")

            return {
                'subject': subject,
                'html_content': html_content
            }

        except Exception as e:
            logger.error(f"Error generating case email: {str(e)}")
            raise

    def generate_custom_email(
        self,
        template_string: str,
        data: Dict,
        subject: str
    ) -> Dict[str, str]:
        """
        Generate email from a custom template string

        Args:
            template_string: Jinja2 template string
            data: Dictionary with template variables
            subject: Email subject

        Returns:
            Dictionary with 'subject' and 'html_content'
        """
        try:
            template = Template(template_string)
            template_data = data.copy()
            template_data['generated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            html_content = template.render(**template_data)

            logger.info("Generated custom email")

            return {
                'subject': subject,
                'html_content': html_content
            }

        except Exception as e:
            logger.error(f"Error generating custom email: {str(e)}")
            raise

    def preview_email(self, email_data: Dict[str, str]) -> None:
        """
        Print email preview to console

        Args:
            email_data: Dictionary with 'subject' and 'html_content'
        """
        print("\n" + "="*80)
        print("EMAIL PREVIEW")
        print("="*80)
        print(f"\nSubject: {email_data['subject']}")
        print("\nHTML Content:")
        print("-"*80)
        print(email_data['html_content'][:500] + "..." if len(email_data['html_content']) > 500 else email_data['html_content'])
        print("="*80 + "\n")
