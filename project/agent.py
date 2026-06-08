"""
agent.py -- Email Agent v1 (Milestone M4)
CEM501: Communication Skills for CEM
Bogazici University -- Spring 2026

A complete email-agent pipeline that:
  1. Reads the inbox via IMAP (reuses reader.py)
  2. Triages each email into URGENT / ACTION / FYI / ARCHIVE
  3. Drafts professional replies for URGENT and ACTION emails (OpenAI)
  4. Sends approved drafts via SMTP -- with human-in-the-loop confirmation

Usage:
    py agent.py              # Full pipeline with send capability
    py agent.py --dry-run    # Show drafts without sending
    py agent.py --summary    # Triage only, no drafting or sending
"""

import argparse
import email
import hashlib
import imaplib
import json
import logging
import mimetypes
import os
import re
import smtplib
import sys
import time
from email.message import EmailMessage
from email.header import decode_header

from dotenv import load_dotenv
from openai import OpenAI
from time_utils import tr_now_string

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
DRAFT_CACHE_PATH = os.path.join(LOG_DIR, "draft_cache.json")
DRAFT_MODEL = "gpt-4o-mini"

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


def _split_recipients(*address_groups: str) -> list[str]:
    recipients: list[str] = []
    for group in address_groups:
        recipients.extend(address.strip() for address in (group or "").split(",") if address.strip())
    return recipients


def _validate_recipient(to_address: str, cc_address: str = "") -> list[str]:
    """Guardrail 2: Recipient validation -- returns a list of warnings."""
    warnings: list[str] = []
    recipients = _split_recipients(to_address, cc_address)

    if not recipients:
        warnings.append("[!] No recipient email address provided.")
        return warnings

    known_contacts = [c.lower() for c in KNOWN_CONTACTS]
    for recipient in recipients:
        if "@" not in recipient:
            warnings.append(f"[!] Recipient '{recipient}' is not a valid email address.")
            continue

        if recipient.lower() not in known_contacts:
            warnings.append(f"[!] Recipient '{recipient}' is NOT in your known contacts list.")

        domain = recipient.split("@")[-1].lower()
        if domain in SUSPICIOUS_DOMAINS:
            warnings.append(f"[!] Suspicious domain detected: '{domain}' -- possible typo!")

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


def get_send_warnings(to_address: str, subject: str, body: str, cc_address: str = "") -> list[str]:
    """Return all non-blocking warnings for a proposed outbound email."""
    return _validate_recipient(to_address, cc_address) + _validate_content(subject, body)


def _normalize_attachments(attachments: list[dict] | None) -> list[dict]:
    normalized: list[dict] = []
    for attachment in attachments or []:
        if not isinstance(attachment, dict):
            continue
        path = str(attachment.get("path", "")).strip()
        if not path:
            continue
        filename = str(attachment.get("filename") or os.path.basename(path)).strip()
        content_type = str(attachment.get("content_type") or mimetypes.guess_type(path)[0] or "application/octet-stream")
        normalized.append(
            {
                "path": path,
                "filename": filename or os.path.basename(path),
                "content_type": content_type,
            }
        )
    return normalized


def _validate_attachments(attachments: list[dict] | None) -> tuple[list[str], bool]:
    """Return attachment warnings and whether missing files should block sending."""
    warnings: list[str] = []
    block_send = False

    for attachment in _normalize_attachments(attachments):
        path = attachment["path"]
        filename = attachment["filename"]
        if not os.path.exists(path):
            warnings.append(f"[!] Attachment '{filename}' is missing and will not be sent.")
            block_send = True
            continue

        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > 20:
            warnings.append(f"[!] Attachment '{filename}' is {size_mb:.1f} MB; email delivery may fail.")

    return warnings, block_send


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
            display_body = extract_body_preview(
                message,
                limit=None,
                preserve_line_breaks=True,
            )
            triage_body = extract_body_preview(message, limit=500)
            category, keyword = triage_email(subject, sender, triage_body)

            emails.append({
                "sender": sender,
                "sender_email": _extract_sender_email(sender),
                "subject": subject,
                "date": date_str,
                "body": display_body,
                "triage_body": triage_body,
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


def _draft_cache_key(email_data: dict) -> str:
    payload = {
        "category": email_data.get("category", ""),
        "sender": " ".join((email_data.get("sender") or "").split()).lower(),
        "subject": " ".join((email_data.get("subject") or "").split()).lower(),
        "body": " ".join((email_data.get("body") or "").split()),
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _load_draft_cache() -> dict:
    if not os.path.exists(DRAFT_CACHE_PATH):
        return {}
    try:
        with open(DRAFT_CACHE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_draft_cache(cache: dict) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    temp_path = f"{DRAFT_CACHE_PATH}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(cache, handle, indent=2, ensure_ascii=False, sort_keys=True)
    os.replace(temp_path, DRAFT_CACHE_PATH)


def _read_cached_draft(cache: dict, cache_key: str) -> str | None:
    entry = cache.get(cache_key)
    if not isinstance(entry, dict):
        return None
    draft = str(entry.get("draft", "")).strip()
    return draft or None


def _write_cached_draft(cache: dict, cache_key: str, draft: str, source: str) -> None:
    cache[cache_key] = {
        "draft": draft,
        "source": source,
        "model": DRAFT_MODEL,
    }
    _save_draft_cache(cache)


def draft_reply(email_data: dict) -> str:
    """
    DECIDE phase -- use OpenAI to generate a professional draft reply.
    """
    category = email_data["category"]
    subject = email_data["subject"]
    sender = email_data["sender"]
    body = email_data["body"]
    cache_key = _draft_cache_key(email_data)
    cache = _load_draft_cache()

    cached_draft = _read_cached_draft(cache, cache_key)
    if cached_draft:
        logger.info("Draft cache hit for: %s", subject[:60])
        return cached_draft

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
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=DRAFT_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        draft = response.choices[0].message.content.strip()
        _write_cached_draft(cache, cache_key, draft, source="openai")
        logger.info("Draft generated for: %s", subject[:60])
        return draft
    except Exception as exc:
        logger.error("LLM draft generation failed: %s", exc)
        # Fallback templates based on category
        if category == "URGENT":
            draft = (
                "Thank you for flagging this urgent matter. I have received your message "
                "and am reviewing it immediately. I will respond with a detailed action "
                "plan within the next two hours. Please do not hesitate to call if the "
                "situation requires immediate attention."
            )
        else:
            draft = (
                "Thank you for your email. I have received your message and will review "
                "the details. I will follow up with a response by end of business today."
            )
        _write_cached_draft(cache, cache_key, draft, source="fallback")
        return draft


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


def send_approved_email(
    to_address: str,
    subject: str,
    body: str,
    dry_run: bool = False,
    cc_address: str = "",
    attachments: list[dict] | None = None,
) -> tuple[bool, list[str], str]:
    """
    Send an already-reviewed draft without CLI prompts.

    This is intended for the web dashboard, where the dashboard itself is the
    human confirmation surface required by ADR 2.
    """
    attachment_warnings, block_send = _validate_attachments(attachments)
    warnings = get_send_warnings(to_address, subject, body, cc_address) + attachment_warnings

    if dry_run:
        attachment_names = [item["filename"] for item in _normalize_attachments(attachments)]
        logger.info(
            "[DRY RUN] Approved dashboard draft for: %s -> %s cc=%s attachments=%s",
            subject[:40],
            to_address,
            cc_address,
            ", ".join(attachment_names) if attachment_names else "none",
        )
        return True, warnings, "dry_run"

    if block_send:
        logger.warning("Blocked approved send for %s: attachment missing.", to_address)
        return False, warnings, "blocked"

    if not _check_rate_limit():
        warning = "Rate limit exceeded. Try again later."
        logger.warning("Blocked approved send for %s: %s", to_address, warning)
        return False, warnings + [warning], "blocked"

    success = _do_send(to_address, subject, body, cc_address=cc_address, attachments=attachments)
    return success, warnings, "sent" if success else "error"


def _do_send(
    to_address: str,
    subject: str,
    body: str,
    cc_address: str = "",
    attachments: list[dict] | None = None,
) -> bool:
    """Actually send the email via SMTP and log the result."""
    load_dotenv()
    email_address = require_env("EMAIL_ADDRESS")
    email_password = require_env("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip() or "smtp.gmail.com"
    smtp_port = int(os.getenv("SMTP_PORT", "587").strip() or "587")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = to_address
    if cc_address.strip():
        msg["Cc"] = cc_address.strip()
    msg.set_content(body)

    for attachment in _normalize_attachments(attachments):
        path = attachment["path"]
        filename = attachment["filename"]
        content_type = attachment["content_type"]
        if not os.path.exists(path):
            logger.error("Attachment missing: %s", path)
            print(f"  [X] Attachment missing: {filename}")
            return False

        maintype, subtype = content_type.split("/", 1) if "/" in content_type else ("application", "octet-stream")
        with open(path, "rb") as handle:
            msg.add_attachment(
                handle.read(),
                maintype=maintype,
                subtype=subtype,
                filename=filename,
            )

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg)

        # Record the send timestamp for rate limiting
        _send_timestamps.append(time.time())

        # Log to sent_log.txt
        logged_recipient = to_address if not cc_address.strip() else f"{to_address} | Cc: {cc_address.strip()}"
        _log_sent(logged_recipient, subject)

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
    timestamp = tr_now_string()
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
