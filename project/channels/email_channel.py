"""
email_channel.py — Email channel implementation.

Wraps the existing reader.py IMAP logic into the Channel abstraction,
so email can be used alongside Telegram (or any future channel)
through the same interface.

CEM501 — Milestone M6: Multi-Channel Integration
"""

import email
import imaplib
import os
import smtplib
import sys
from email.mime.text import MIMEText

from dotenv import load_dotenv

from channels.base import Channel

# Import helpers from reader.py (same project directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from reader import require_env, fetch_emails
from classifier import triage_email


class EmailChannel(Channel):
    """
    Email channel using IMAP for receiving and SMTP for sending.

    Credentials are loaded from environment variables:
        - EMAIL_ADDRESS
        - EMAIL_PASSWORD
        - IMAP_SERVER (optional, defaults to imap.gmail.com)
    """

    channel_name = "email"

    def __init__(self):
        """Initialize the email channel with credentials from .env."""
        load_dotenv()
        self._address = require_env("EMAIL_ADDRESS")
        self._password = require_env("EMAIL_PASSWORD")
        self._imap_server = (
            os.getenv("IMAP_SERVER", DEFAULT_IMAP_SERVER).strip()
            or DEFAULT_IMAP_SERVER
        )

    def fetch_messages(self) -> list[dict]:
        """
        Connect to the inbox via IMAP and fetch recent emails.

        Returns a list of dicts with keys:
            sender, text, subject, channel, triage_category
        """
        messages = []

        try:
            raw_emails = fetch_emails()
            for em in raw_emails:
                category, _ = triage_email(em["subject"], em["sender"], em["body"])
                messages.append({
                    "sender": em["sender"],
                    "subject": em["subject"],
                    "text": em["body"],
                    "channel": self.channel_name,
                    "triage_category": category,
                })
        except Exception as exc:
            print(f"[email] Error fetching emails: {exc}", file=sys.stderr)

        return messages

    def send_message(self, recipient: str, text: str) -> bool:
        """
        Send an email reply via SMTP (Gmail).

        Args:
            recipient: The email address to send to.
            text: The message body.

        Returns:
            True if sent successfully, False otherwise.
        """
        try:
            msg = MIMEText(text)
            msg["Subject"] = "Agent Response"
            msg["From"] = self._address
            msg["To"] = recipient

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self._address, self._password)
                server.send_message(msg)

            print(f"[email] Sent reply to {recipient}")
            return True

        except Exception as exc:
            print(f"[email] Failed to send: {exc}", file=sys.stderr)
            return False
