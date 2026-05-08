"""
agent.py -- Email Agent v1 (Milestone M4)
CEM501: Communication Skills for CEM
Bogazici University -- Spring 2026

A complete email-agent pipeline that:
  1. Reads the inbox via IMAP (reuses reader.py)
  2. Triages each email into URGENT / ACTION / FYI / ARCHIVE
  3. Drafts professional replies for URGENT and ACTION emails (Gemini)
  4. Sends approved drafts via SMTP -- with human-in-the-loop confirmation

Usage:
    python agent.py              # Full pipeline with send capability
    python agent.py --dry-run    # Show drafts without sending
    python agent.py --summary    # Triage only, no drafting or sending
"""

import argparse
import email
import imaplib
import logging
import os
import re
import smtplib
import sys
import time
from datetime import datetime
from email.header import decode_header
from email.mime.text import MIMEText

from dotenv import load_dotenv
from google import genai

# ---------------------------------------------------------------------------
# Import triage helpers from reader.py (same project directory)
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reader import (
    triage_email,
    require_env,
    decode_mime_header,
    extract_body_preview,
    html_to_text,
    DEFAULT_IMAP_SERVER,
    MAILBOX,
    FETCH_COUNT,
    CATEGORY_PRIORITY,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
SENT_LOG = os.path.join(LOG_DIR, "sent_log.txt")
AGENT_LOG = os.path.join(LOG_DIR, "agent.log")

# Rate-limit: max sends per window
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 600  # seconds (10 minutes)

# Known contacts -- extend this list with your project contacts
KNOWN_CONTACTS = [
    "furkan.cem501@gmail.com",
    # Add your real project contacts here
]

# Suspicious domain typos to flag
SUSPICIOUS_DOMAINS = [
    "gmial.com", "gmal.com", "gmali.com", "gamil.com",
    "yaho.com", "yahooo.com", "hotmal.com", "outllok.com",
]

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(AGENT_LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("agent")


# ---------------------------------------------------------------------------
# Guardrail helpers
# ---------------------------------------------------------------------------

_send_timestamps: list[float] = []


def _check_rate_limit() -> bool:
    """Guardrail 4: Rate limiting -- max RATE_LIMIT_MAX sends per window."""
    now = time.time()
    # Prune old timestamps outside the window
    while _send_timestamps and _send_timestamps[0] < now - RATE_LIMIT_WINDOW:
        _send_timestamps.pop(0)
    if len(_send_timestamps) >= RATE_LIMIT_MAX:
        logger.warning(
            "Rate limit reached: %d sends in the last %d seconds. Blocking send.",
            RATE_LIMIT_MAX,
            RATE_LIMIT_WINDOW,
        )
        return False
    return True


def _validate_recipient(to_address: str) -> list[str]:
    """Guardrail 2: Recipient validation -- returns a list of warnings."""
    warnings: list[str] = []

    # Check if recipient is known
    if to_address.lower() not in [c.lower() for c in KNOWN_CONTACTS]:
        warnings.append(f"[!] Recipient '{to_address}' is NOT in your known contacts list.")

    # Check for suspicious domain typos
    domain = to_address.split("@")[-1].lower() if "@" in to_address else ""
    if domain in SUSPICIOUS_DOMAINS:
        warnings.append(f"[!] Suspicious domain detected: '{domain}' -- possible typo!")

    # Check for multiple recipients (if comma-separated)
    recipients = [r.strip() for r in to_address.split(",") if r.strip()]
    if len(recipients) > 5:
        warnings.append(
            f"[!] Sending to {len(recipients)} recipients! Review carefully."
        )

    return warnings


def _validate_content(subject: str, body: str) -> list[str]:
    """Guardrail 3: Content check -- returns a list of warnings."""
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


def _extract_sender_email(sender_field: str) -> str:
    """Extract a bare email address from a 'Name <email>' formatted sender."""
    match = re.search(r"<([^>]+)>", sender_field)
    if match:
        return match.group(1).strip()
    # Might already be a bare email
    if "@" in sender_field:
        return sender_field.strip()
    return sender_field


# ---------------------------------------------------------------------------
# Core pipeline functions
# ---------------------------------------------------------------------------

def fetch_emails() -> list[dict]:
    """
    SENSE phase -- connect to the inbox, fetch recent emails, and triage each one.
    Returns a list of email dicts sorted by priority.
    """
    load_dotenv()
    email_address = require_env("EMAIL_ADDRESS")
    email_password = require_env("EMAIL_PASSWORD")
    imap_server = (
        os.getenv("IMAP_SERVER", DEFAULT_IMAP_SERVER).strip() or DEFAULT_IMAP_SERVER
    )

    emails: list[dict] = []

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
            category, keyword = triage_email(subject, sender, body)

            emails.append({
                "sender": sender,
                "sender_email": _extract_sender_email(sender),
                "subject": subject,
                "date": date_str,
                "body": body,
                "category": category,
                "keyword": keyword,
            })

    # Sort by priority
    emails.sort(key=lambda e: CATEGORY_PRIORITY.get(e["category"], 99))

    logger.info(
        "Triage complete: %d URGENT, %d ACTION, %d FYI, %d ARCHIVE",
        sum(1 for e in emails if e["category"] == "URGENT"),
        sum(1 for e in emails if e["category"] == "ACTION"),
        sum(1 for e in emails if e["category"] == "FYI"),
        sum(1 for e in emails if e["category"] == "ARCHIVE"),
    )

    return emails


def draft_reply(email_data: dict) -> str:
    """
    DECIDE phase -- use Gemini to generate a professional draft reply.
    """
    category = email_data["category"]
    subject = email_data["subject"]
    sender = email_data["sender"]
    body = email_data["body"]

    prompt = (
        f"You are a construction project manager's AI communication assistant.\n\n"
        f"An email was received and classified as **{category}**.\n\n"
        f"--- ORIGINAL EMAIL ---\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Body:\n{body}\n"
        f"--- END ---\n\n"
        f"Draft a professional reply appropriate for a construction project context.\n"
        f"Guidelines:\n"
        f"- Be direct, concise, and action-oriented.\n"
        f"- For URGENT emails: acknowledge the urgency, state immediate next steps.\n"
        f"- For ACTION emails: confirm receipt, state your intended action and timeline.\n"
        f"- Use a formal but approachable tone.\n"
        f"- Keep the reply under 150 words.\n"
        f"- Do NOT include a subject line -- only the body of the reply.\n"
        f"- Do NOT add any placeholders like [Your Name].\n"
    )

    try:
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        draft = response.text.strip()
        logger.info("Draft generated for: %s", subject[:60])
        return draft
    except Exception as exc:
        logger.error("LLM draft generation failed: %s", exc)
        # Fallback templates based on category
        if category == "URGENT":
            return (
                "Thank you for flagging this urgent matter. I have received your message "
                "and am reviewing it immediately. I will respond with a detailed action "
                "plan within the next two hours. Please do not hesitate to call if the "
                "situation requires immediate attention."
            )
        return (
            "Thank you for your email. I have received your message and will review "
            "the details. I will follow up with a response by end of business today."
        )


def send_email(
    to_address: str,
    subject: str,
    body: str,
    dry_run: bool = False,
) -> bool:
    """
    ACT phase -- send the approved draft via SMTP with all four guardrails.

    Returns True if the email was sent (or would be sent in dry-run),
    False if skipped or blocked.
    """

    # --- Guardrail 4: Rate limiting ---
    if not dry_run and not _check_rate_limit():
        print("\n[X] BLOCKED: Rate limit exceeded. Try again later.")
        return False

    # --- Guardrail 2: Recipient validation ---
    recipient_warnings = _validate_recipient(to_address)

    # --- Guardrail 3: Content check ---
    content_warnings = _validate_content(subject, body)

    all_warnings = recipient_warnings + content_warnings

    # --- Guardrail 1: Human confirmation prompt ---
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

    # Ask for confirmation
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


def _do_send(to_address: str, subject: str, body: str) -> bool:
    """Actually send the email via SMTP and log the result."""
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

        # Record the send timestamp for rate limiting
        _send_timestamps.append(time.time())

        # Log to sent_log.txt
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


def _log_sent(to_address: str, subject: str) -> None:
    """Append an entry to sent_log.txt with timestamp, recipient, and subject."""
    os.makedirs(os.path.dirname(SENT_LOG), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} | To: {to_address} | Subject: {subject}\n"
    with open(SENT_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

CATEGORY_LABELS = {
    "URGENT": "[!!!]",
    "ACTION": "[>>]",
    "FYI": "[i]",
    "ARCHIVE": "[--]",
}


def print_triage_table(emails: list[dict]) -> None:
    """Print a summary table of all triaged emails."""
    print("\n" + "=" * 70)
    print("  INBOX TRIAGE SUMMARY")
    print("=" * 70)

    for i, e in enumerate(emails, 1):
        icon = CATEGORY_LABELS.get(e["category"], "[?]")
        sender_short = e["sender"][:30] + "..." if len(e["sender"]) > 30 else e["sender"]
        subject_short = e["subject"][:45] + "..." if len(e["subject"]) > 45 else e["subject"]
        print(f"  {i:2d}. {icon:5s} {e['category']:8s} | {sender_short:33s} | {subject_short}")

    urgent = sum(1 for e in emails if e["category"] == "URGENT")
    action = sum(1 for e in emails if e["category"] == "ACTION")
    fyi = sum(1 for e in emails if e["category"] == "FYI")
    archive = sum(1 for e in emails if e["category"] == "ARCHIVE")

    print("-" * 70)
    print(f"  Total: {len(emails)} emails -- {urgent} URGENT, {action} ACTION, {fyi} FYI, {archive} ARCHIVE")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="CEM501 Email Agent -- read, triage, draft, and send.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the full pipeline without actually sending emails.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show triage summary only -- no drafting or sending.",
    )
    args = parser.parse_args()

    print()
    print("=" * 70)
    print("  CEM501 EMAIL AGENT v1")
    print("  Construction Communication Assistant")
    print("=" * 70)
    if args.dry_run:
        print("  Mode: DRY RUN (no emails will be sent)")
    elif args.summary:
        print("  Mode: SUMMARY ONLY (triage only, no drafts)")
    else:
        print("  Mode: LIVE (drafts will require your approval to send)")
    print("=" * 70)

    # ----- SENSE: Fetch and triage -----
    try:
        emails = fetch_emails()
    except Exception as exc:
        logger.error("Failed to fetch emails: %s", exc)
        print(f"\n[X] Error: {exc}")
        return 1

    if not emails:
        print("\n  No emails found in inbox.")
        return 0

    # ----- Display triage summary -----
    print_triage_table(emails)

    if args.summary:
        logger.info("Summary-only mode -- exiting after triage display.")
        return 0

    # ----- DECIDE + ACT: Draft and (optionally) send for URGENT & ACTION -----
    actionable = [e for e in emails if e["category"] in ("URGENT", "ACTION")]

    if not actionable:
        print("\n  [OK] No URGENT or ACTION emails -- nothing to draft.")
        return 0

    print(f"\n  Generating drafts for {len(actionable)} actionable email(s)...\n")

    sent_count = 0
    skipped_count = 0

    for i, email_data in enumerate(actionable, 1):
        print(f"\n{'=' * 60}")
        print(f"  [{i}/{len(actionable)}] {email_data['category']}: {email_data['subject'][:50]}")
        print(f"  From: {email_data['sender']}")
        print(f"{'=' * 60}")

        # Generate draft
        draft = draft_reply(email_data)

        # Attempt to send (with guardrails)
        result = send_email(
            to_address=email_data["sender_email"],
            subject=email_data["subject"],
            body=draft,
            dry_run=args.dry_run,
        )

        if result:
            sent_count += 1
        else:
            skipped_count += 1

    # ----- Summary -----
    print("\n" + "=" * 70)
    print("  SESSION SUMMARY")
    print("=" * 70)
    print(f"  Emails scanned:   {len(emails)}")
    print(f"  Drafts generated: {len(actionable)}")
    if args.dry_run:
        print(f"  Drafts displayed: {sent_count} (dry run -- nothing sent)")
    else:
        print(f"  Emails sent:      {sent_count}")
    print(f"  Skipped:          {skipped_count}")
    print("=" * 70)

    logger.info(
        "Session complete: %d scanned, %d drafted, %d sent, %d skipped",
        len(emails), len(actionable), sent_count, skipped_count,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
