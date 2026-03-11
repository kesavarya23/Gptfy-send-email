"""
Email Service Module
Handles SMTP email sending functionality
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        sender_email: str,
        sender_name: Optional[str] = None
    ):
        """
        Initialize email service

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            sender_email: Email address to send from
            sender_name: Display name for sender
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender_email = sender_email
        self.sender_name = sender_name or sender_email

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of email
            plain_text: Plain text version (optional)
            cc: List of CC recipients (optional)
            bcc: List of BCC recipients (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            # If plain_text is provided, send a simple plain text email only.
            if plain_text:
                msg = MIMEText(plain_text, 'plain')
            else:
                msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)

            # For pure plain text emails, we've already built the body above.
            # Only attach HTML if no plain text is provided.
            if not plain_text:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)

            # Create recipient list
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Connect to SMTP server and send
            logger.info(f"Connecting to SMTP server: {self.smtp_host}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_bulk_emails(
        self,
        emails_data: List[dict]
    ) -> dict:
        """
        Send multiple emails

        Args:
            emails_data: List of dicts with keys: to_email, subject, html_content, plain_text (optional)

        Returns:
            dict: Summary with 'success_count', 'failed_count', and 'failed_emails'
        """
        success_count = 0
        failed_count = 0
        failed_emails = []

        for email_data in emails_data:
            success = self.send_email(
                to_email=email_data['to_email'],
                subject=email_data['subject'],
                html_content=email_data['html_content'],
                plain_text=email_data.get('plain_text'),
                cc=email_data.get('cc'),
                bcc=email_data.get('bcc')
            )

            if success:
                success_count += 1
            else:
                failed_count += 1
                failed_emails.append(email_data['to_email'])

        logger.info(f"Bulk email complete: {success_count} sent, {failed_count} failed")

        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_emails': failed_emails
        }
