"""
Configuration Module
Handles loading configuration from environment variables
"""

import os
from dotenv import load_dotenv
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Config:
    """Application configuration"""

    def __init__(self, env_file: Optional[str] = None):
        """
        Load configuration from environment

        Args:
            env_file: Path to .env file (optional)
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Email configuration
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.sender_email = os.getenv('SENDER_EMAIL', '')
        self.sender_name = os.getenv('SENDER_NAME', '')
        self.default_recipient = os.getenv('DEFAULT_RECIPIENT_EMAIL', '')

        # Salesforce configuration
        self.sf_username = os.getenv('SF_USERNAME', '')
        self.sf_password = os.getenv('SF_PASSWORD', '')
        self.sf_security_token = os.getenv('SF_SECURITY_TOKEN', '')
        self.sf_domain = os.getenv('SF_DOMAIN', 'login')

        logger.info("Configuration loaded")

    def validate_email_config(self) -> bool:
        """
        Validate email configuration

        Returns:
            bool: True if valid, False otherwise
        """
        required = [
            self.smtp_host,
            self.smtp_username,
            self.smtp_password,
            self.sender_email
        ]

        if not all(required):
            logger.error("Email configuration is incomplete. Check .env file.")
            return False

        logger.info("Email configuration is valid")
        return True

    def validate_salesforce_config(self) -> bool:
        """
        Validate Salesforce configuration

        Returns:
            bool: True if valid, False otherwise
        """
        required = [
            self.sf_username,
            self.sf_password,
            self.sf_security_token
        ]

        if not all(required):
            logger.warning("Salesforce configuration is incomplete. API features will be disabled.")
            return False

        logger.info("Salesforce configuration is valid")
        return True

    def get_email_config(self) -> dict:
        """
        Get email configuration as dictionary

        Returns:
            Dictionary with email configuration
        """
        return {
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'username': self.smtp_username,
            'password': self.smtp_password,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name
        }

    def get_salesforce_config(self) -> dict:
        """
        Get Salesforce configuration as dictionary

        Returns:
            Dictionary with Salesforce configuration
        """
        return {
            'username': self.sf_username,
            'password': self.sf_password,
            'security_token': self.sf_security_token,
            'domain': self.sf_domain
        }
