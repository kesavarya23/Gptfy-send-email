"""
Email Service Module
Handles SMTP email sending functionality
"""

import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Union

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _normalize_to_addresses(
    to_email: Union[str, List[str], None]
) -> List[str]:
    """Coerce a single string or list of strings to a non-empty list of addresses."""
    if to_email is None:
        return []
    if isinstance(to_email, list):
        return [str(x).strip() for x in to_email if str(x).strip()]
    s = str(to_email).strip()
    if not s:
        return []
    parts = re.split(r"[\s,;]+", s.replace("\n", " "))
    return [p.strip() for p in parts if p.strip()]


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
        to_email: Union[str, List[str]],
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email

        Args:
            to_email: One or more To addresses (string, comma/semicolon-separated, or list)
            subject: Email subject
            html_content: HTML content of email
            plain_text: Plain text version (optional)
            cc: List of CC recipients (optional)
            bcc: List of BCC recipients (optional, envelope only — not in MIME headers)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            to_list = _normalize_to_addresses(to_email)
            if not to_list:
                return False
            cc = [x.strip() for x in (cc or []) if x and str(x).strip()]
            bcc = [x.strip() for x in (bcc or []) if x and str(x).strip()]

            # Create message
            # If plain_text is provided, send a simple plain text email only.
            if plain_text:
                msg = MIMEText(plain_text, 'plain')
            else:
                msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = ", ".join(to_list)
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = ", ".join(cc)
            # Do not set Bcc in headers so hidden recipients are not visible to other parties.

            # For pure plain text emails, we've already built the body above.
            # Only attach HTML if no plain text is provided.
            if not plain_text:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)

            # Envelope: all To + CC + BCC
            recipients: List[str] = list(to_list)
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Connect to SMTP server and send
            logger.info(f"Connecting to SMTP server: {self.smtp_host}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                # to_addrs must include BCC; they are omitted from MIME headers.
                server.send_message(msg, to_addrs=recipients)

            logger.info("Email sent successfully to %s", to_list)
            return True

        except Exception as e:
            logger.error("Failed to send email: %s", str(e))
            return False
