"""
reader.py -- Reader component
Connects to IMAP server, fetches unread emails, parses headers and body.
"""
import email
import imaplib
import logging
import os
import re
from email.header import decode_header
from dotenv import load_dotenv

logger = logging.getLogger("agent")

DEFAULT_IMAP_SERVER = "imap.gmail.com"
MAILBOX = "INBOX"
FETCH_COUNT = 20

def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def decode_mime_header(value: str | None) -> str:
    if not value:
        return ""
    parts = []
    for chunk, encoding in decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(encoding or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts).strip()

def html_to_text(value: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()

def decode_part_payload(part: email.message.Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        raw_payload = part.get_payload()
        return raw_payload if isinstance(raw_payload, str) else ""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")

def extract_body_preview(message: email.message.Message, limit: int = 500) -> str:
    plain_text_parts = []
    html_parts = []
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_maintype() == "multipart" or part.get_filename():
                continue
            content_type = part.get_content_type()
            content = decode_part_payload(part).strip()
            if not content:
                continue
            if content_type == "text/plain":
                plain_text_parts.append(content)
            elif content_type == "text/html":
                html_parts.append(content)
    else:
        content = decode_part_payload(message).strip()
        if message.get_content_type() == "text/html":
            html_parts.append(content)
        else:
            plain_text_parts.append(content)
            
    body_text = " ".join(plain_text_parts).strip()
    if not body_text and html_parts:
        body_text = html_to_text(" ".join(html_parts))
    return re.sub(r"\s+", " ", body_text).strip()[:limit]

def extract_sender_email(sender_field: str) -> str:
    match = re.search(r"<([^>]+)>", sender_field)
    if match:
        return match.group(1).strip()
    if "@" in sender_field:
        return sender_field.strip()
    return sender_field

def fetch_emails() -> list[dict]:
    load_dotenv()
    email_address = require_env("EMAIL_ADDRESS")
    email_password = require_env("EMAIL_PASSWORD")
    imap_server = os.getenv("IMAP_SERVER", DEFAULT_IMAP_SERVER).strip() or DEFAULT_IMAP_SERVER

    emails = []
    logger.info("Connecting to IMAP server: %s", imap_server)
    
    with imaplib.IMAP4_SSL(imap_server) as mail:
        mail.login(email_address, email_password)
        status, _ = mail.select(MAILBOX)
        if status != "OK":
            raise RuntimeError(f"Could not open mailbox: {MAILBOX}")
            
        status, data = mail.search(None, "ALL")
        if status != "OK":
            raise RuntimeError("Could not fetch message IDs")
            
        message_ids = data[0].split()
        recent_ids = message_ids[-FETCH_COUNT:][::-1]
        logger.info("Found %d messages, processing last %d.", len(message_ids), len(recent_ids))
        
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
            date_str = decode_mime_header(message.get("Date"))
            body = extract_body_preview(message, limit=500)
            
            emails.append({
                "sender": sender,
                "sender_email": extract_sender_email(sender),
                "subject": subject,
                "date": date_str,
                "body": body,
            })
            
    return emails
