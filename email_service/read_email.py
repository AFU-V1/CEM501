#!/usr/bin/env python3
"""
CEM501 Email Reader — Fetch recent emails via Gmail IMAP.

Usage:
  python read_email.py        # fetch 20 most recent
  python read_email.py 10     # fetch 10 most recent
"""

import email
import imaplib
import re
import sys
from email.header import decode_header
from html.parser import HTMLParser
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / ".env"


def load_env():
    """Load credentials from .env file."""
    if not ENV_FILE.exists():
        print("ERROR: .env file not found.")
        sys.exit(1)
    env = {}
    for line in ENV_FILE.read_text().strip().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            env[key.strip()] = val.strip()
    return env


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


def strip_html(html_text):
    stripper = HTMLStripper()
    stripper.feed(html_text)
    return re.sub(r"\s+", " ", stripper.get_text()).strip()


def decode_mime_header(header_value):
    if header_value is None:
        return ""
    parts = decode_header(header_value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def get_body_preview(msg, max_chars=200):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    break
            elif ct == "text/html" and not body:
                payload = part.get_payload(decode=True)
                if payload:
                    body = strip_html(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            raw = payload.decode(charset, errors="replace")
            body = strip_html(raw) if msg.get_content_type() == "text/html" else raw

    body = re.sub(r"\s+", " ", body).strip()
    return body[:max_chars] + "..." if len(body) > max_chars else body


def fetch_emails(count=20):
    env = load_env()
    imap_server = env.get("IMAP_SERVER", "imap.gmail.com")
    email_addr = env["GMAIL_ADDRESS"]
    email_pass = env["GMAIL_APP_PASSWORD"]

    mail = imaplib.IMAP4_SSL(imap_server)
    try:
        mail.login(email_addr, email_pass)
        mail.select("INBOX")

        _, data = mail.search(None, "ALL")
        msg_ids = data[0].split()

        recent_ids = msg_ids[-count:] if len(msg_ids) >= count else msg_ids
        recent_ids = list(reversed(recent_ids))

        results = []
        for msg_id in recent_ids:
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            results.append({
                "subject": decode_mime_header(msg["Subject"]),
                "from": decode_mime_header(msg["From"]),
                "date": decode_mime_header(msg["Date"]),
                "preview": get_body_preview(msg),
            })

        return results
    finally:
        mail.logout()


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(f"Fetching {count} most recent emails...\n")

    try:
        emails = fetch_emails(count)
        print(f"Found {len(emails)} email(s).\n")
        for i, e in enumerate(emails, 1):
            print(f"{i:>2}.  {e['subject'][:70]}")
            print(f"     From: {e['from'][:60]}")
            print(f"     Date: {e['date']}")
            print(f"     {e['preview'][:100]}")
            print()
    except imaplib.IMAP4.error as err:
        print(f"IMAP error: {err}")
        print("Check your credentials in .env and ensure the App Password is correct.")
        sys.exit(1)
