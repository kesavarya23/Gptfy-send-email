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

            # Build plain-text version using key fields
            lines = [
                f"{subject}",
                "",
                f"Opportunity Name: {template_data.get('opportunity_name', 'N/A')}",
                f"Account Name: {template_data.get('account_name', 'N/A')}",
                f"Stage: {template_data.get('stage_name', 'N/A')}",
                f"Amount: {template_data.get('amount', 'N/A')}",
                f"Close Date: {template_data.get('close_date', 'N/A')}",
                f"Owner: {template_data.get('owner_name', 'N/A')}",
            ]
            if custom_message:
                lines.extend(["", f"Message: {custom_message}"])
            lines.extend([
                "",
                f"Generated at: {template_data.get('generated_date')}"
            ])

            plain_text = "\n".join(lines)

            return {
                'subject': subject,
                'html_content': html_content,
                'plain_text': plain_text
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

            # Build plain-text version using key fields
            lines = [
                f"{subject}",
                "",
                f"Case Number: {template_data.get('case_number', 'N/A')}",
                f"Subject: {template_data.get('subject', 'N/A')}",
                f"Status: {template_data.get('status', 'N/A')}",
                f"Priority: {template_data.get('priority', 'N/A')}",
                f"Contact: {template_data.get('contact_name', 'N/A')}",
                f"Owner: {template_data.get('owner_name', 'N/A')}",
            ]
            if custom_message:
                lines.extend(["", f"Message: {custom_message}"])
            lines.extend([
                "",
                f"Generated at: {template_data.get('generated_date')}"
            ])

            plain_text = "\n".join(lines)

            return {
                'subject': subject,
                'html_content': html_content,
                'plain_text': plain_text
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

    def generate_business_email(self, business_data: Dict) -> Dict[str, str]:
        """
        Generate business email based on type

        Args:
            business_data: Dictionary with business email data including 'type' field

        Returns:
            Dictionary with 'subject' and 'html_content'
        """
        try:
            email_type = business_data.get('type')

            # Map type to template
            template_map = {
                'meeting_invitation': 'meeting_invitation.html',
                'followup': 'followup.html',
                'thank_you': 'thank_you.html',
                'project_update': 'project_update.html',
                'reminder': 'reminder.html',
                'trial_feedback': 'generic_business.html',
                'product_queries': 'generic_business.html',
                'product_issues': 'generic_business.html',
                'demo_enquiry': 'generic_business.html',
            }

            template_name = template_map.get(email_type)
            if not template_name:
                raise ValueError(f"Unknown business email type: {email_type}")

            template = self.env.get_template(template_name)

            # Add generated date
            template_data = business_data.copy()
            template_data['generated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            html_content = template.render(**template_data)

            # Get subject from business_data
            subject = business_data.get('subject', 'Business Email')

            logger.info(f"Generated {email_type} email")

            # Build richer plain-text version (aim for 10–15 lines)
            recipient_name = template_data.get('recipient_name', 'there')
            sender_name = template_data.get('sender_name', 'Your team')
            custom_message = template_data.get('custom_message', '')

            lines = [
                f"Hi {recipient_name},",
                "",
            ]

            # Type-specific context lines
            if email_type == 'meeting_invitation':
                lines.extend([
                    "I wanted to send over the details for our upcoming meeting so you have everything in one place.",
                    f"Date: {template_data.get('date', 'TBD')}",
                    f"Time: {template_data.get('time', 'TBD')}",
                    f"Location: {template_data.get('location', 'TBD')}",
                ])
            elif email_type == 'followup':
                lines.append(f"I'm following up on {template_data.get('context', 'our recent conversation')} and next steps we discussed.")
            elif email_type == 'thank_you':
                lines.append(f"Thank you again for {template_data.get('reason', 'your support and collaboration')} with us.")
            elif email_type == 'project_update':
                lines.extend([
                    f"This is a quick update on the \"{template_data.get('project_name', 'project')}\" work.",
                    f"Current milestone: {template_data.get('milestone', 'N/A')}",
                    f"Overall completion: {template_data.get('completion', 'N/A')}%",
                    f"Status: {template_data.get('status', 'N/A')}",
                ])
            elif email_type == 'reminder':
                lines.append(f"This is a friendly reminder about the {template_data.get('reminder_about', 'upcoming item')} due on {template_data.get('due_date', 'TBD')}.")
            elif email_type == 'trial_feedback':
                lines.append("Thank you for trying the product. We'd like to hear how it's going and have shared an update below.")
            elif email_type == 'product_queries':
                lines.append("Here are some answers to the questions you raised about the product.")
            elif email_type == 'product_issues':
                lines.append("We wanted to give you an update on the product issues you reported.")
            elif email_type == 'demo_enquiry':
                lines.append("Thank you for your interest in a product demo. We would be glad to arrange one.")

            # Add custom message split into multiple lines for more natural flow
            if custom_message:
                lines.append("")
                # Naive sentence splitting to create more lines
                for sentence in custom_message.split(". "):
                    sentence = sentence.strip()
                    if sentence:
                        if not sentence.endswith("."):
                            sentence += "."
                        lines.append(sentence)

            # Closing and sign-off
            lines.extend([
                "",
                "If anything here doesn't quite match your expectations, please let me know so we can adjust.",
                "Thanks again for your time and support.",
                "",
                "Best regards,",
                sender_name,
            ])

            plain_text = "\n".join(lines)

            return {
                'subject': subject,
                'html_content': html_content,
                'plain_text': plain_text
            }

        except Exception as e:
            logger.error(f"Error generating business email: {str(e)}")
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
