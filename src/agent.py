"""
Email Agent
Thin wrapper around EmailService used by the Flask web UI for SMTP delivery.
"""

import logging
from typing import Optional

from services.email_service import EmailService

logger = logging.getLogger(__name__)


class EmailAgent:
    """Lightweight container that exposes a configured EmailService."""

    def __init__(
        self,
        sender_email: str,
        sender_password: str,
        sender_name: Optional[str] = None,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
    ):
        self.sender_email = sender_email
        self.sender_name = sender_name or sender_email
        self.email_service = EmailService(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            username=sender_email,
            password=sender_password,
            sender_email=sender_email,
            sender_name=self.sender_name,
        )
        logger.info("Email Agent initialized for sender: %s", sender_email)
