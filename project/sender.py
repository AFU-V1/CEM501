"""
sender.py -- Sender component
Handles sending emails with guardrails (rate limiting, validation).
"""

import logging
import os
import re
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from dotenv import load_dotenv

logger = logging.getLogger("agent")

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
SENT_LOG = os.path.join(LOG_DIR, "sent_log.txt")

RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 600

KNOWN_CONTACTS = [
    "furkan.cem501@gmail.com",
]

SUSPICIOUS_DOMAINS = [
    "gmial.com", "gmal.com", "gmali.com", "gamil.com",
    "yaho.com", "yahooo.com", "hotmal.com", "outllok.com",
]

_send_timestamps: list[float] = []

def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def _check_rate_limit() -> bool:
    now = time.time()
    while _send_timestamps and _send_timestamps[0] < now - RATE_LIMIT_WINDOW:
        _send_timestamps.pop(0)
    if len(_send_timestamps) >= RATE_LIMIT_MAX:
        logger.warning("Rate limit reached.")
        return False
    return True

def _validate_recipient(to_address: str) -> list[str]:
    warnings: list[str] = []
    if to_address.lower() not in [c.lower() for c in KNOWN_CONTACTS]:
        warnings.append(f"[!] Recipient '{to_address}' is NOT in your known contacts list.")
    domain = to_address.split("@")[-1].lower() if "@" in to_address else ""
    if domain in SUSPICIOUS_DOMAINS:
        warnings.append(f"[!] Suspicious domain detected: '{domain}' -- possible typo!")
    recipients = [r.strip() for r in to_address.split(",") if r.strip()]
    if len(recipients) > 5:
        warnings.append(f"[!] Sending to {len(recipients)} recipients! Review carefully.")
    return warnings

def _validate_content(subject: str, body: str) -> list[str]:
    warnings: list[str] = []
    if not subject or not subject.strip():
        warnings.append("[!] Subject line is EMPTY.")
    placeholder_patterns = [
        r"\[INSERT\]", r"\[TODO\]", r"\[PLACEHOLDER\]",
        r"\[TBD\]", r"\[FILL IN\]", r"\{\{.*?\}\}",
    ]
    for pattern in placeholder_patterns:
        if re.search(pattern, body, re.IGNORECASE):
            warnings.append(f"[!] Body contains placeholder text: {pattern}")
            break
    if len(body.strip()) < 20:
        warnings.append("[!] Body is very short (< 20 characters).")
    return warnings

def _log_sent(to_address: str, subject: str) -> None:
    os.makedirs(os.path.dirname(SENT_LOG), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} | To: {to_address} | Subject: {subject}\n"
    with open(SENT_LOG, "a", encoding="utf-8") as f:
        f.write(entry)

def _do_send(to_address: str, subject: str, body: str) -> bool:
    load_dotenv()
    email_address = require_env("EMAIL_ADDRESS")
    email_password = require_env("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip() or "smtp.gmail.com"
    smtp_port = int(os.getenv("SMTP_PORT", "587").strip() or "587")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = to_address

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg)

        _send_timestamps.append(time.time())
        _log_sent(to_address, subject)

        logger.info("[OK] Email sent to %s -- Subject: %s", to_address, subject)
        print("  [OK] Email sent successfully!")
        return True

    except smtplib.SMTPAuthenticationError as exc:
        logger.error("SMTP authentication failed: %s", exc)
        print("  [X] Authentication failed -- check your app password in .env")
        return False
    except smtplib.SMTPRecipientsRefused as exc:
        logger.error("Recipient refused: %s -- %s", to_address, exc)
        print(f"  [X] Recipient refused: {to_address}")
        return False
    except Exception as exc:
        logger.error("SMTP send failed: %s", exc)
        print(f"  [X] Send failed: {exc}")
        return False

def send_email(to_address: str, subject: str, body: str, dry_run: bool = False) -> bool:
    if not dry_run and not _check_rate_limit():
        print("\n[X] BLOCKED: Rate limit exceeded. Try again later.")
        return False

    recipient_warnings = _validate_recipient(to_address)
    content_warnings = _validate_content(subject, body)
    all_warnings = recipient_warnings + content_warnings

    print("\n" + "=" * 60)
    print(">>> DRAFT READY FOR REVIEW")
    print("=" * 60)
    print(f"  To:      {to_address}")
    print(f"  Subject: Re: {subject}")
    print("-" * 60)
    print(body)
    print("-" * 60)

    if all_warnings:
        print("\n  WARNINGS:")
        for w in all_warnings:
            print(f"  {w}")
        print()

    if dry_run:
        print("  [DRY RUN] -- no email will be sent.")
        logger.info("[DRY RUN] Draft displayed for: %s -> %s", subject[:40], to_address)
        return True

    print("\n  [y] Send   [n] Skip   [e] Edit (opens in editor)")
    choice = input("  Your choice: ").strip().lower()

    if choice == "y":
        return _do_send(to_address, f"Re: {subject}", body)
    elif choice == "e":
        print("  -> Open the draft above in your editor, then re-run the agent.")
        logger.info("User chose to edit draft for: %s", subject[:40])
        return False
    else:
        print("  -> Skipped.")
        logger.info("User skipped sending for: %s -> %s", subject[:40], to_address)
        return False
