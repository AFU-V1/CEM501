import email
import hashlib
import imaplib
import json
import os
import re
import sys
from email.header import decode_header

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IMAP_SERVER = "imap.gmail.com"
MAILBOX = "INBOX"
FETCH_COUNT = 20
LOG_DIR = os.path.join(BASE_DIR, "logs")
TRIAGE_CACHE_PATH = os.path.join(LOG_DIR, "triage_cache.json")
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
VALID_CATEGORIES = {"URGENT", "ACTION", "FYI", "ARCHIVE"}
VALID_CONFIDENCE = {"high", "medium", "low"}
TRIAGE_MODEL = "gpt-4o-mini"


def _normalize_cache_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _triage_cache_key(subject: str, sender: str, body: str) -> str:
    payload = {
        "subject": _normalize_cache_text(subject).lower(),
        "sender": _normalize_cache_text(sender).lower(),
        "body": _normalize_cache_text(body),
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def clean_triage_reason(reason: str | None) -> str:
    """Return a user-facing triage reason without legacy technical prefixes."""
    text = _normalize_cache_text(reason)
    if not text:
        return "review manually"

    if text.lower() in {"llm_error_review_manually", "review_manually"}:
        return "review manually"

    text = re.sub(r"^llm:(?:(?:high|medium|low):)?", "", text, flags=re.IGNORECASE).strip()
    if not text or text.lower() == "review":
        return "review manually"
    return text


def _load_triage_cache() -> dict:
    if not os.path.exists(TRIAGE_CACHE_PATH):
        return {}

    try:
        with open(TRIAGE_CACHE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_triage_cache(cache: dict) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    temp_path = f"{TRIAGE_CACHE_PATH}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(cache, handle, indent=2, ensure_ascii=False, sort_keys=True)
    os.replace(temp_path, TRIAGE_CACHE_PATH)


def _read_cached_triage(cache: dict, cache_key: str) -> tuple[str, str] | None:
    entry = cache.get(cache_key)
    if not isinstance(entry, dict):
        return None

    category = str(entry.get("category", "")).upper().strip()
    reason = clean_triage_reason(entry.get("triage_reason") or entry.get("raw_reason"))
    if category not in VALID_CATEGORIES or not reason:
        return None
    return category, reason


def _write_cached_triage(
    cache: dict,
    cache_key: str,
    category: str,
    triage_reason: str,
    raw_reason: str,
    confidence: str,
    source: str,
) -> None:
    triage_reason = clean_triage_reason(triage_reason)
    cache[cache_key] = {
        "category": category,
        "triage_reason": triage_reason,
        "raw_reason": raw_reason,
        "confidence": confidence,
        "source": source,
        "model": TRIAGE_MODEL,
    }
    _save_triage_cache(cache)


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
    """Classify email priority semantically with OpenAI.

    The return signature stays compatible with the old keyword classifier:
    (category, reason). The second value is stored in the existing `keyword`
    field, but now carries a cached LLM triage reason instead of a matched word.
    """
    load_dotenv()
    subject = subject or "(no subject)"
    sender = sender or "(unknown sender)"
    body = (body or "").strip()
    body_excerpt = body[:2400]
    cache_key = _triage_cache_key(subject, sender, body_excerpt)
    cache = _load_triage_cache()

    cached = _read_cached_triage(cache, cache_key)
    if cached:
        return cached

    system_prompt = (
        "You are a construction project manager triaging project communication. "
        "Classify one incoming message into exactly one category.\n\n"
        "Categories:\n"
        "- URGENT: safety risk, stop-work order, legal claim, delay risk, critical "
        "cost/schedule impact, immediate decision, or response needed today.\n"
        "- ACTION: RFI, submittal, approval, coordination, document request, "
        "or non-immediate deadline requiring PM follow-up.\n"
        "- FYI: progress update, report, meeting minutes, routine status, or "
        "information to record with no direct response required.\n"
        "- ARCHIVE: spam, marketing, unrelated, personal, or general admin/HR "
        "not requiring project-manager action.\n\n"
        "Return only JSON with keys: category, reason, confidence. "
        "category must be URGENT, ACTION, FYI, or ARCHIVE. "
        "confidence must be high, medium, or low. "
        "reason must be under 12 words and explain the priority."
    )

    user_prompt = (
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Body:\n{body_excerpt}"
    )

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=TRIAGE_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        category = str(payload.get("category", "")).upper().strip()
        reason = str(payload.get("reason", "")).strip()
        confidence = str(payload.get("confidence", "medium")).lower().strip()

        if category not in VALID_CATEGORIES:
            category = "ACTION"
            triage_reason = "review manually"
            _write_cached_triage(
                cache=cache,
                cache_key=cache_key,
                category=category,
                triage_reason=triage_reason,
                raw_reason="OpenAI returned an invalid category; review manually.",
                confidence="low",
                source="fallback",
            )
            return category, triage_reason
        if confidence not in VALID_CONFIDENCE:
            confidence = "medium"
        if not reason:
            reason = "semantic priority classification"

        reason = clean_triage_reason(re.sub(r"\s+", " ", reason)[:90])
        triage_reason = reason
        _write_cached_triage(
            cache=cache,
            cache_key=cache_key,
            category=category,
            triage_reason=triage_reason,
            raw_reason=reason,
            confidence=confidence,
            source="openai",
        )
        return category, triage_reason
    except Exception:
        category = "ACTION"
        triage_reason = "review manually"
        _write_cached_triage(
            cache=cache,
            cache_key=cache_key,
            category=category,
            triage_reason=triage_reason,
            raw_reason="OpenAI triage failed; review manually.",
            confidence="low",
            source="fallback",
        )
        return category, triage_reason


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
                "keyword": 26,
                "date": 31,
                "preview": 40,
            }
            header = (
                f"{'CATEGORY':<{widths['category']}}  "
                f"{'SENDER':<{widths['sender']}}  "
                f"{'SUBJECT':<{widths['subject']}}  "
                f"{'TRIAGE REASON':<{widths['keyword']}}  "
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
