"""Email channel adapter used by the shared agent pipeline."""

import os
import sys

from dotenv import load_dotenv

from channels.base import Channel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from reader import fetch_emails, require_env
from sender import send_email

DEFAULT_IMAP_SERVER = "imap.gmail.com"


class EmailChannel(Channel):
    """Wrap the existing IMAP/SMTP logic in the shared channel interface."""

    channel_name = "email"

    def __init__(self):
        load_dotenv()
        self._address = require_env("EMAIL_ADDRESS")
        self._password = require_env("EMAIL_PASSWORD")
        self._imap_server = (
            os.getenv("IMAP_SERVER", DEFAULT_IMAP_SERVER).strip()
            or DEFAULT_IMAP_SERVER
        )

    def fetch_messages(self) -> list[dict]:
        messages = []
        try:
            for email_message in fetch_emails():
                messages.append({
                    "sender": email_message["sender"],
                    "sender_email": email_message["sender_email"],
                    "reply_to": email_message["sender_email"],
                    "subject": email_message["subject"] or "No subject",
                    "text": email_message["body"],
                    "channel": self.channel_name,
                })
        except Exception as exc:
            print(f"[email] Error fetching emails: {exc}", file=sys.stderr)
        return messages

    def send_message(
        self,
        recipient: str,
        text: str,
        subject: str = "",
        dry_run: bool = False,
    ) -> bool:
        return send_email(
            to_address=recipient,
            subject=subject or "Agent Response",
            body=text,
            dry_run=dry_run,
        )
