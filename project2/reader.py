import email
import imaplib
import os
import re
import sys
from email.header import decode_header

from dotenv import load_dotenv


DEFAULT_IMAP_SERVER = "imap.gmail.com"
MAILBOX = "INBOX"
FETCH_COUNT = 20
CATEGORY_PRIORITY = {
    "URGENT": 0,
    "ACTION": 1,
    "FYI": 2,
    "ARCHIVE": 3,
}
ANSI_COLORS = {
    "URGENT": "\033[31m",
    "ACTION": "\033[33m",
    "FYI": "\033[34m",
    "ARCHIVE": "\033[90m",
}
ANSI_RESET = "\033[0m"


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


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def triage_email(subject: str, sender: str, body: str = "") -> tuple[str, str]:
    del sender

    search_text = f"{subject} {body}".lower()

    # Pass 0: check obvious junk/non-project words immediately
    junk_keywords = [
        "benefits", "offer", "digest", "fw:",
        "server maintenance", "system maintenance",
        "occupational health", "health checkup", "job application",
    ]
    for keyword in junk_keywords:
        if keyword in search_text:
            return "ARCHIVE", keyword

    # Pass 1: compound (multi-word) keywords checked first for specificity.
    # This prevents false positives like "meeting minutes" matching "review".
    compound_groups = (
        ("URGENT", (
            "stop work", "notice of delay", "time extension",
            "liquidated damages", "vibration damage",
        )),
        ("ACTION", (
            "change order", "response required", "action required",
            "meeting request", "shop drawing", "permit renewal",
            "price adjustment", "renewal required",
            "certificate of insurance", "installation schedule",
            "gas main",
        )),
        ("FYI", (
            "meeting minutes", "daily log", "work log", "daily report",
            "progress photo", "test results", "weekly schedule",
            "weekly report", "schedule update",
            "safety inspection", "safety report", "inspection report",
            "monitoring report", "noise monitoring",
            "survey completed", "as-built",
            "no incidents", "no issues",
        )),
    )

    for category, keywords in compound_groups:
        for keyword in keywords:
            if keyword in search_text:
                return category, keyword

    # Pass 2: single-word keywords for broader matching.
    single_groups = (
        ("URGENT", (
            "urgent", "safety", "incident", "notice", "claim", "immediate",
            "complaint", "damage",
        )),
        ("ACTION", (
            "rfi", "submittal", "review", "approval", "deadline",
            "coordination", "permit", "insurance", "renewal",
        )),
        ("FYI", (
            "update", "recap", "photos", "minutes", "progress", "log", "fyi",
            "monitoring", "completed",
        )),
    )

    for category, keywords in single_groups:
        for keyword in keywords:
            if keyword in search_text:
                return category, keyword

    return "ARCHIVE", "default"


def supports_color() -> bool:
    if not sys.stdout.isatty():
        return False

    term = os.getenv("TERM", "").lower()
    return term != "dumb"


def format_cell(value: str, width: int) -> str:
    text = value.replace("\r", " ").replace("\n", " ").strip()
    if len(text) > width:
        return text[: max(0, width - 3)] + "..."
    return text.ljust(width)


def colorize_category(category: str, use_color: bool) -> str:
    label = format_cell(category, 8)
    if not use_color:
        return label
    return f"{ANSI_COLORS[category]}{label}{ANSI_RESET}"


def html_to_text(value: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def decode_part_payload(part: email.message.Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        raw_payload = part.get_payload()
        return raw_payload if isinstance(raw_payload, str) else ""

    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def extract_body_preview(message: email.message.Message, limit: int = 200) -> str:
    plain_text_parts = []
    html_parts = []

    if message.is_multipart():
        for part in message.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_filename():
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

    normalized = re.sub(r"\s+", " ", body_text).strip()
    return normalized[:limit]


def main() -> int:
    load_dotenv()

    email_address = require_env("EMAIL_ADDRESS")
    email_password = require_env("EMAIL_PASSWORD")
    imap_server = os.getenv("IMAP_SERVER", DEFAULT_IMAP_SERVER).strip() or DEFAULT_IMAP_SERVER

    try:
        with imaplib.IMAP4_SSL(imap_server) as mail:
            mail.login(email_address, email_password)

            status, _ = mail.select(MAILBOX)
            if status != "OK":
                raise RuntimeError(f"Could not open mailbox: {MAILBOX}")

            status, data = mail.search(None, "ALL")
            if status != "OK":
                raise RuntimeError("Could not fetch message ids")

            message_ids = data[0].split()
            recent_ids = message_ids[-FETCH_COUNT:][::-1]

            if not recent_ids:
                print("No emails found.")
                return 0

            rows = []

            for index, msg_id in enumerate(recent_ids, start=1):
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    print(f"{index}. Failed to fetch message {msg_id.decode()}", file=sys.stderr)
                    continue

                raw_message = None
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        raw_message = response_part[1]
                        break

                if not raw_message:
                    print(f"{index}. Empty response for message {msg_id.decode()}", file=sys.stderr)
                    continue

                message = email.message_from_bytes(raw_message)
                sender = decode_mime_header(message.get("From"))
                subject = decode_mime_header(message.get("Subject"))
                date = decode_mime_header(message.get("Date"))
                preview = extract_body_preview(message)
                category, keyword = triage_email(subject, sender, preview)

                rows.append(
                    {
                        "category": category,
                        "sender": sender,
                        "subject": subject,
                        "date": date,
                        "preview": preview,
                        "keyword": keyword,
                    }
                )

            rows.sort(
                key=lambda row: (
                    CATEGORY_PRIORITY[row["category"]],
                    row["date"].lower(),
                    row["sender"].lower(),
                    row["subject"].lower(),
                )
            )

            use_color = supports_color()
            widths = {
                "category": 8,
                "sender": 30,
                "subject": 40,
                "keyword": 15,
                "date": 31,
                "preview": 40,
            }
            header = (
                f"{'CATEGORY':<{widths['category']}}  "
                f"{'SENDER':<{widths['sender']}}  "
                f"{'SUBJECT':<{widths['subject']}}  "
                f"{'MATCHED WORD':<{widths['keyword']}}  "
                f"{'DATE':<{widths['date']}}  "
                f"{'PREVIEW':<{widths['preview']}}"
            )

            print(header)
            print("-" * len(header))
            for row in rows:
                print(
                    f"{colorize_category(row['category'], use_color)}  "
                    f"{format_cell(row['sender'], widths['sender'])}  "
                    f"{format_cell(row['subject'], widths['subject'])}  "
                    f"{format_cell(row['keyword'], widths['keyword'])}  "
                    f"{format_cell(row['date'], widths['date'])}  "
                    f"{format_cell(row['preview'], widths['preview'])}"
                )

        return 0
    except imaplib.IMAP4.error as exc:
        print(f"IMAP error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
