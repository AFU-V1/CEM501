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
from reader import (
    triage_email,
    require_env,
    decode_mime_header,
    extract_body_preview,
    DEFAULT_IMAP_SERVER,
    MAILBOX,
    FETCH_COUNT,
)


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
            with imaplib.IMAP4_SSL(self._imap_server) as mail:
                mail.login(self._address, self._password)
                status, _ = mail.select(MAILBOX)
                if status != "OK":
                    print(f"[email] Could not open mailbox: {MAILBOX}", file=sys.stderr)
                    return messages

                status, data = mail.search(None, "ALL")
                if status != "OK":
                    print("[email] Could not fetch message IDs.", file=sys.stderr)
                    return messages

                message_ids = data[0].split()
                recent_ids = message_ids[-FETCH_COUNT:][::-1]

                for msg_id in recent_ids:
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue

                    raw_message = None
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            raw_message = response_part[1]
                            break
                    if not raw_message:
                        continue

                    message = email.message_from_bytes(raw_message)
                    sender = decode_mime_header(message.get("From"))
                    subject = decode_mime_header(message.get("Subject"))
                    body = extract_body_preview(message, limit=500)
                    category, _ = triage_email(subject, sender, body)

                    messages.append({
                        "sender": sender,
                        "subject": subject,
                        "text": body,
                        "channel": self.channel_name,
                        "triage_category": category,
                    })

        except imaplib.IMAP4.error as exc:
            print(f"[email] IMAP error: {exc}", file=sys.stderr)
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
