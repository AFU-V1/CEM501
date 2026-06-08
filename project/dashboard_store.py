"""
dashboard_store.py -- State and data helpers for the web dashboard.

Bridges the existing CLI agent modules to a GUI-friendly state model:
  - Cached inbox snapshots
  - Human-in-the-loop draft review queue
  - Memory/contact lookup helpers
  - Task and log projections for the frontend
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from email.utils import parsedate_to_datetime, parseaddr

from agent import draft_reply, fetch_emails, get_send_warnings, send_approved_email
from digest import SAMPLE_EMAILS, format_html_digest, format_text_digest, group_by_category, summarize_email
from memory.memory import (
    add_contact,
    complete_task,
    get_contact_by_email,
    get_messages_for_contact,
    get_overdue_tasks,
    get_pending_tasks,
    get_recent_messages,
    list_contacts,
    log_message,
    skip_task,
)
from reader import clean_triage_reason, triage_email


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
STATE_PATH = os.path.join(LOG_DIR, "dashboard_state.json")
AGENT_LOG_PATH = os.path.join(LOG_DIR, "agent.log")
MAX_ARTIFACT_HISTORY = 20


def now_iso() -> str:
    """Return a consistent local timestamp for dashboard state."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def default_state() -> dict:
    """Initial empty dashboard state."""
    return {
        "last_refresh": None,
        "source": "sample",
        "status_message": "No inbox snapshot loaded yet.",
        "emails": [],
        "queue": [],
        "daily_reports": [],
        "morning_digests": [],
    }


def _ensure_state_defaults(state: dict) -> bool:
    changed = False
    for key, default_value in default_state().items():
        if key not in state:
            state[key] = default_value
            changed = True
    return changed


def _sanitize_state_reasons(state: dict) -> bool:
    changed = False
    for collection_name in ("emails", "queue"):
        for item in state.get(collection_name, []):
            if not isinstance(item, dict) or "keyword" not in item:
                continue
            cleaned = clean_triage_reason(item.get("keyword"))
            if item.get("keyword") != cleaned:
                item["keyword"] = cleaned
                changed = True
    return changed


def load_dashboard_state() -> dict:
    """Load the cached dashboard state from disk."""
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(STATE_PATH):
        state = default_state()
        save_dashboard_state(state)
        return state

    with open(STATE_PATH, "r", encoding="utf-8") as handle:
        state = json.load(handle)

    changed = _ensure_state_defaults(state)
    changed = _sanitize_state_reasons(state) or changed
    if changed:
        save_dashboard_state(state)
    return state


def save_dashboard_state(state: dict) -> None:
    """Persist the dashboard state to disk."""
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def _queue_key(email_item: dict) -> str:
    source = "|".join(
        [
            email_item.get("sender_email", ""),
            email_item.get("subject", ""),
            email_item.get("triage_body") or email_item.get("body", ""),
        ]
    )
    return hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]


def _display_name(sender: str, sender_email: str) -> str:
    name, parsed_email = parseaddr(sender)
    if name:
        return name
    if parsed_email:
        return parsed_email.split("@")[0].replace(".", " ").title()
    if sender_email:
        return sender_email.split("@")[0].replace(".", " ").title()
    return sender


def _normalize_email(email_item: dict, fallback_date: str, previous_emails: dict | None = None) -> dict:
    sender = email_item.get("sender", "")
    sender_name, sender_email = parseaddr(sender)
    if not sender_email:
        sender_email = email_item.get("sender_email", "")

    normalized = {
        "sender": sender,
        "sender_name": _display_name(sender, sender_email),
        "sender_email": sender_email,
        "subject": email_item.get("subject", "(no subject)"),
        "date": email_item.get("date", fallback_date),
        "body": email_item.get("body") or email_item.get("preview") or "",
        "triage_body": email_item.get("triage_body") or email_item.get("body") or email_item.get("preview") or "",
        "category": email_item.get("category", "ARCHIVE"),
        "keyword": clean_triage_reason(email_item.get("keyword", "review manually")),
    }
    normalized["id"] = _queue_key(normalized)
    
    # Triage inbox için mail body'sini digest.py'daki summarize_email ile özetle
    # Eğer önceden özetlenmişse önbellekten oku, LLM'i tekrar yorma
    if previous_emails and normalized["id"] in previous_emails and previous_emails[normalized["id"]].get("preview"):
        normalized["preview"] = previous_emails[normalized["id"]]["preview"]
    elif normalized["body"]:
        normalized["preview"] = summarize_email(normalized["body"])
    else:
        normalized["preview"] = ""
        
    return normalized


def sample_inbox_snapshot(previous_emails: dict | None = None) -> list[dict]:
    """Build a demo inbox snapshot from the digest samples."""
    stamp = now_iso()
    snapshot = []

    for item in SAMPLE_EMAILS:
        category, keyword = triage_email(item["subject"], item["sender"], item["body"])
        snapshot.append(
            _normalize_email(
                {
                    "sender": item["sender"],
                    "subject": item["subject"],
                    "date": stamp,
                    "body": item["body"],
                    "category": category or item.get("triage_category", "ARCHIVE"),
                    "keyword": keyword,
                },
                fallback_date=stamp,
                previous_emails=previous_emails
            )
        )

    return snapshot


def _build_queue_item(email_item: dict, existing_item: dict | None = None) -> dict:
    if existing_item and existing_item.get("edited"):
        draft = existing_item["draft"]
    elif existing_item and existing_item.get("status") == "pending":
        draft = existing_item["draft"]
    else:
        draft = draft_reply(email_item)

    reply_subject = f"Re: {email_item['subject']}"
    to_address = existing_item.get("to_address") if existing_item else None
    cc_address = existing_item.get("cc_address") if existing_item else None
    to_address = to_address or email_item["sender_email"]
    cc_address = cc_address or ""
    warnings = get_send_warnings(to_address, reply_subject, draft, cc_address)
    updated_at = now_iso()

    return {
        "id": email_item["id"],
        "status": existing_item.get("status", "pending") if existing_item else "pending",
        "category": email_item["category"],
        "keyword": clean_triage_reason(email_item["keyword"]),
        "sender": email_item["sender"],
        "sender_name": email_item["sender_name"],
        "sender_email": email_item["sender_email"],
        "to_address": to_address,
        "cc_address": cc_address,
        "subject": email_item["subject"],
        "reply_subject": reply_subject,
        "date": email_item["date"],
        "body": email_item["body"],
        "draft": draft,
        "warnings": warnings,
        "edited": existing_item.get("edited", False) if existing_item else False,
        "created_at": existing_item.get("created_at", updated_at) if existing_item else updated_at,
        "updated_at": updated_at,
        "last_action": existing_item.get("last_action") if existing_item else None,
        "send_mode": existing_item.get("send_mode") if existing_item else None,
        "error": existing_item.get("error") if existing_item else None,
    }


def refresh_inbox_state(source: str = "live") -> dict:
    """
    Refresh cached inbox and review queue using the real agent when possible.

    Falls back to the bundled sample inbox if live access fails.
    """
    state = load_dashboard_state()
    previous_queue = {item["id"]: item for item in state.get("queue", [])}
    previous_emails = {item["id"]: item for item in state.get("emails", [])}
    resolved_source = source

    try:
        emails = fetch_emails() if source == "live" else sample_inbox_snapshot(previous_emails)
        status_message = "Live inbox snapshot loaded." if source == "live" else "Sample inbox snapshot loaded."
    except Exception as exc:
        emails = sample_inbox_snapshot(previous_emails)
        resolved_source = "sample"
        status_message = f"Live inbox unavailable. Showing sample inbox instead: {exc}"

    normalized_emails = [_normalize_email(item, fallback_date=now_iso(), previous_emails=previous_emails) for item in emails]
    actionable = [item for item in normalized_emails if item["category"] in ("URGENT", "ACTION")]

    pending_queue = []
    for item in actionable:
        pending_queue.append(_build_queue_item(item, previous_queue.get(item["id"])))

    closed_items = [
        previous_queue[item_id]
        for item_id in previous_queue
        if item_id not in {email["id"] for email in actionable}
        and previous_queue[item_id].get("status") != "pending"
    ]

    state.update(
        {
            "last_refresh": now_iso(),
            "source": resolved_source,
            "status_message": status_message,
            "emails": normalized_emails,
            "queue": pending_queue + closed_items[:8],
        }
    )
    save_dashboard_state(state)
    return state


def reset_demo_state() -> dict:
    """
    Rebuild the demo inbox and review queue from bundled sample messages.

    This clears demo queue edits/statuses for a fresh rehearsal while keeping
    unrelated dashboard artifacts such as saved reports and digest history.
    """
    state = load_dashboard_state()
    normalized_emails = sample_inbox_snapshot(previous_emails=None)
    actionable = [item for item in normalized_emails if item["category"] in ("URGENT", "ACTION")]
    fresh_queue = [_build_queue_item(item, existing_item=None) for item in actionable]

    state.update(
        {
            "last_refresh": now_iso(),
            "source": "sample",
            "status_message": "Demo snapshot reset to its original sample state.",
            "emails": normalized_emails,
            "queue": fresh_queue,
        }
    )
    save_dashboard_state(state)
    return state


def grouped_inbox(emails: list[dict]) -> dict[str, list[dict]]:
    """Group inbox items by triage category for the UI."""
    grouped = {"URGENT": [], "ACTION": [], "FYI": [], "ARCHIVE": []}
    for email_item in emails:
        grouped.setdefault(email_item["category"], []).append(email_item)
    return grouped


def queue_metrics(queue_items: list[dict]) -> dict:
    """Summaries for the review queue header cards."""
    pending = [item for item in queue_items if item["status"] == "pending"]
    approved = [item for item in queue_items if item["status"] == "approved"]
    rejected = [item for item in queue_items if item["status"] == "rejected"]
    return {
        "pending": len(pending),
        "approved": len(approved),
        "rejected": len(rejected),
    }


def _parse_email_date(value: str | None) -> datetime | None:
    """Parse dashboard/IMAP date strings without failing the task view."""
    if not value:
        return None

    text = str(value).strip()
    parsers = [
        lambda candidate: parsedate_to_datetime(candidate),
        lambda candidate: datetime.fromisoformat(candidate),
        lambda candidate: datetime.strptime(candidate, "%Y-%m-%d %H:%M:%S"),
        lambda candidate: datetime.strptime(candidate, "%Y-%m-%d"),
    ]
    for parser in parsers:
        try:
            return parser(text)
        except (TypeError, ValueError, IndexError, OverflowError):
            continue
    return None


def _unanswered_overdue_email_tasks(state: dict) -> list[dict]:
    """
    Project overdue email follow-ups into the scheduler view.

    URGENT/ACTION emails from before today become overdue tasks until the
    matching review queue item is approved.
    """
    today = datetime.now().date()
    queue_by_id = {item.get("id"): item for item in state.get("queue", [])}
    tasks = []

    for email_item in state.get("emails", []):
        if email_item.get("category") not in {"URGENT", "ACTION"}:
            continue

        email_id = email_item.get("id")
        queue_item = queue_by_id.get(email_id, {})
        if queue_item.get("status") == "approved":
            continue

        received_at = _parse_email_date(email_item.get("date"))
        if not received_at or received_at.date() >= today:
            continue

        sender = (
            email_item.get("sender_name")
            or email_item.get("sender_email")
            or email_item.get("sender")
            or "Unknown sender"
        )
        tasks.append(
            {
                "id": f"email-overdue-{email_id}",
                "description": email_item.get("subject") or "(no subject)",
                "due_at": email_item.get("date") or "",
                "contact_name": sender,
                "source": "email_overdue",
                "category": email_item.get("category"),
                "status": "pending",
                "actionable": False,
            }
        )

    return tasks


def dashboard_overview(state: dict) -> dict:
    """Top-level counts for the hero metrics."""
    emails = state.get("emails", [])
    queue_items = state.get("queue", [])
    tasks = get_pending_tasks()
    overdue = get_overdue_tasks() + _unanswered_overdue_email_tasks(state)
    contacts = list_contacts()
    messages = get_recent_messages(limit=50)

    counts = {
        "emails": len(emails),
        "urgent": sum(1 for item in emails if item["category"] == "URGENT"),
        "action": sum(1 for item in emails if item["category"] == "ACTION"),
        "fyi": sum(1 for item in emails if item["category"] == "FYI"),
        "archive": sum(1 for item in emails if item["category"] == "ARCHIVE"),
        "queue_pending": sum(1 for item in queue_items if item["status"] == "pending"),
        "contacts": len(contacts),
        "messages": len(messages),
        "tasks": len(tasks),
        "overdue": len(overdue),
    }

    return {
        "counts": counts,
        "last_refresh": state.get("last_refresh"),
        "source": state.get("source", "sample"),
        "status_message": state.get("status_message", ""),
    }


def find_queue_item(queue_id: str) -> tuple[dict, dict, int]:
    """Locate a queue item inside the persisted state."""
    state = load_dashboard_state()
    for index, item in enumerate(state.get("queue", [])):
        if item["id"] == queue_id:
            return state, item, index
    raise KeyError(queue_id)


def update_queue_draft(
    queue_id: str,
    draft: str,
    to_address: str | None = None,
    cc_address: str | None = None,
) -> dict:
    """Update a draft body/recipients and recompute dashboard warnings."""
    state, item, index = find_queue_item(queue_id)
    item["draft"] = draft.strip()
    if to_address is not None:
        item["to_address"] = to_address.strip()
    if cc_address is not None:
        item["cc_address"] = cc_address.strip()
    item["edited"] = True
    item["updated_at"] = now_iso()
    item["warnings"] = get_send_warnings(
        item.get("to_address") or item["sender_email"],
        item["reply_subject"],
        item["draft"],
        item.get("cc_address", ""),
    )
    item["error"] = None
    state["queue"][index] = item
    save_dashboard_state(state)
    return item


def reject_queue_item(queue_id: str) -> dict:
    """Reject a queued draft without sending it."""
    state, item, index = find_queue_item(queue_id)
    item["status"] = "rejected"
    item["last_action"] = f"Rejected at {now_iso()}"
    item["updated_at"] = now_iso()
    item["error"] = None
    state["queue"][index] = item
    save_dashboard_state(state)
    return item


def delete_queue_item(queue_id: str) -> bool:
    """Completely remove a queued draft from the state."""
    state = load_dashboard_state()
    queue = state.get("queue", [])
    for index, item in enumerate(queue):
        if item["id"] == queue_id:
            del queue[index]
            save_dashboard_state(state)
            return True
    raise KeyError(queue_id)


def _ensure_contact(sender_name: str, sender_email: str) -> int | None:
    if not sender_email:
        return None

    existing = get_contact_by_email(sender_email)
    if existing:
        return existing["id"]

    return add_contact(name=sender_name or sender_email, email=sender_email)


def approve_queue_item(queue_id: str, dry_run: bool = False) -> dict:
    """Approve a draft and send it through the agent SMTP path."""
    state, item, index = find_queue_item(queue_id)
    to_address = item.get("to_address") or item["sender_email"]
    cc_address = item.get("cc_address", "")
    success, warnings, mode = send_approved_email(
        to_address=to_address,
        subject=item["reply_subject"],
        body=item["draft"],
        dry_run=dry_run,
        cc_address=cc_address,
    )

    item["warnings"] = warnings
    item["updated_at"] = now_iso()
    item["send_mode"] = mode

    if success:
        contact_id = _ensure_contact(item["sender_name"], to_address.split(",")[0].strip())
        log_message(
            contact_id=contact_id,
            direction="sent",
            subject=item["reply_subject"],
            body=item["draft"],
            channel="email",
        )
        item["status"] = "approved"
        item["last_action"] = f"Approved at {now_iso()}"
        item["error"] = None
    else:
        item["status"] = "pending"
        item["error"] = "Delivery failed or was blocked. Review warnings and retry."
        item["last_action"] = f"Send attempt failed at {now_iso()}"

    state["queue"][index] = item
    save_dashboard_state(state)
    return item


def search_contacts(query: str = "") -> list[dict]:
    """Search contacts in memory with a lightweight in-Python filter."""
    query_text = query.strip().lower()
    contacts = list_contacts()
    if not query_text:
        return contacts

    return [
        contact
        for contact in contacts
        if query_text in (contact.get("name") or "").lower()
        or query_text in (contact.get("email") or "").lower()
        or query_text in (contact.get("company") or "").lower()
        or query_text in (contact.get("role") or "").lower()
    ]


def search_messages(query: str = "", limit: int = 40) -> list[dict]:
    """Search the recent audit trail across subject, body, and contact name."""
    query_text = query.strip().lower()
    messages = get_recent_messages(limit=max(limit, 40))

    if not query_text:
        return messages[:limit]

    filtered = [
        message
        for message in messages
        if query_text in (message.get("subject") or "").lower()
        or query_text in (message.get("body") or "").lower()
        or query_text in (message.get("contact_name") or "").lower()
    ]
    return filtered[:limit]


def memory_snapshot(query: str = "") -> dict:
    """Bundle contacts and messages for the frontend memory panel."""
    contacts = search_contacts(query)
    messages = search_messages(query)
    for contact in contacts[:12]:
        contact["message_count"] = len(get_messages_for_contact(contact["id"], limit=100))

    return {
        "contacts": contacts[:12],
        "messages": messages,
    }


def tasks_snapshot() -> dict:
    """Return pending and overdue tasks for the scheduler panel."""
    state = load_dashboard_state()
    return {
        "pending": get_pending_tasks(),
        "overdue": get_overdue_tasks() + _unanswered_overdue_email_tasks(state),
    }


def mark_task_done(task_id: int) -> dict:
    """Mark a task as complete and return the latest task snapshot."""
    complete_task(task_id)
    return tasks_snapshot()


def mark_task_skipped(task_id: int) -> dict:
    """Mark a task as skipped and return the latest task snapshot."""
    skip_task(task_id)
    return tasks_snapshot()


def digest_snapshot(source: str | None = None, use_llm: bool = False) -> dict:
    """Generate text and HTML digest previews from cached inbox state."""
    state = load_dashboard_state()
    emails = state.get("emails", [])

    if not emails or source in {"sample", "live"} and state.get("source") != source:
        state = refresh_inbox_state(source or "sample")
        emails = state.get("emails", [])

    digest_emails = [
        {
            "subject": item["subject"],
            "sender": item["sender"],
            "body": item["body"],
            "summary": item.get("preview") or item.get("body", ""),
            "triage_category": item["category"],
        }
        for item in emails
    ]
    groups = group_by_category(digest_emails)

    return {
        "text": format_text_digest(groups, use_llm=use_llm),
        "html": format_html_digest(groups, use_llm=use_llm),
    }


def _artifact_id(kind: str, content: str, created_at: str) -> str:
    payload = f"{kind}|{created_at}|{content}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _save_artifact(collection_name: str, item: dict) -> dict:
    state = load_dashboard_state()
    collection = state.setdefault(collection_name, [])
    collection.insert(0, item)
    state[collection_name] = collection[:MAX_ARTIFACT_HISTORY]
    save_dashboard_state(state)
    return item


def daily_report_history() -> list[dict]:
    state = load_dashboard_state()
    return state.get("daily_reports", [])[:MAX_ARTIFACT_HISTORY]


def digest_history() -> list[dict]:
    state = load_dashboard_state()
    return state.get("morning_digests", [])[:MAX_ARTIFACT_HISTORY]


def save_daily_report(content: str, selected_message_count: int) -> dict:
    created_at = now_iso()
    item = {
        "id": _artifact_id("daily_report", content, created_at),
        "title": f"Daily Report - {created_at}",
        "created_at": created_at,
        "selected_message_count": selected_message_count,
        "content": content,
    }
    return _save_artifact("daily_reports", item)


def save_morning_digest(text: str, html: str, source: str | None, use_llm: bool) -> dict:
    created_at = now_iso()
    source_label = source or "current"
    item = {
        "id": _artifact_id("morning_digest", text, created_at),
        "title": f"Morning Digest - {source_label} - {created_at}",
        "created_at": created_at,
        "source": source_label,
        "use_llm": use_llm,
        "text": text,
        "html": html,
    }
    return _save_artifact("morning_digests", item)


def parse_log_lines(limit: int = 20) -> list[dict]:
    """Read the tail of agent.log and parse level/timestamp/message fields."""
    if not os.path.exists(AGENT_LOG_PATH):
        return []

    with open(AGENT_LOG_PATH, "r", encoding="utf-8", errors="replace") as handle:
        lines = handle.readlines()[-limit:]

    entries = []
    for line in lines:
        parts = [part.strip() for part in line.split("|", 2)]
        if len(parts) == 3:
            entries.append(
                {
                    "timestamp": parts[0],
                    "level": parts[1],
                    "message": parts[2],
                }
            )
        else:
            entries.append({"timestamp": "", "level": "INFO", "message": line.strip()})
    return entries


def generate_daily_report_from_messages(message_ids: list[int]) -> str:
    from memory.memory import get_connection
    import os
    conn = get_connection()
    messages = []
    try:
        placeholders = ",".join("?" for _ in message_ids)
        rows = conn.execute(
            f"SELECT mh.*, c.name AS contact_name FROM message_history mh "
            f"LEFT JOIN contacts c ON mh.contact_id = c.id "
            f"WHERE mh.id IN ({placeholders})",
            message_ids
        ).fetchall()
        messages = [dict(r) for r in rows]
    finally:
        conn.close()
    
    if not messages:
        return "No messages selected."
        
    messages_text = ""
    for m in messages:
        direction = "sent to" if m["direction"] == "sent" else "received from"
        messages_text += f"- Message {direction} {m.get('contact_name', 'Unknown')} (Subject: {m.get('subject', '')}):\n  {m.get('body', '')}\n\n"
        
    from dotenv import load_dotenv
    from datetime import datetime
    import re
    load_dotenv()
    template_path = os.path.join(BASE_DIR, "templates", "daily_report.md")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    else:
        template_content = "DAILY CONSTRUCTION REPORT TEMPLATE"

    current_date = datetime.now().strftime("%B %d, %Y")
    current_day = datetime.now().strftime("%A")

    state = load_dashboard_state()
    reports = state.get("daily_reports", [])
    next_report_no = "DR-001"
    if reports:
        last_report_content = reports[0].get("content", "")
        match = re.search(r"Report Number:\s*DR-(\d+)", last_report_content)
        if not match:
            match = re.search(r"Report No\.?\s*\|\s*DR-(\d+)", last_report_content)
        if match:
            last_num = int(match.group(1))
            next_report_no = f"DR-{last_num + 1:03d}"

    prompt = (
        "You are an AI assistant generating a Daily Construction Report.\n"
        "Use the following template rules and structure.\n"
        "Extract information ONLY from the provided messages below.\n"
        "IMPORTANT: You MUST use the following specific values for this report (replace placeholders):\n"
        f"- Report Number: {next_report_no}\n"
        f"- Date: {current_date}\n"
        f"- Day: {current_day}\n"
        "If other information required by the template is missing, write '[Not Provided]'.\n\n"
        "--- TEMPLATE START ---\n"
        f"{template_content}\n"
        "--- TEMPLATE END ---\n\n"
        "--- MESSAGES START ---\n"
        f"{messages_text}\n"
        "--- MESSAGES END ---\n\n"
        "Generate the completed report now. Do not include any other conversational text."
    )
    
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def queue_synthetic_draft(subject: str, body: str, draft: str, sender_email: str = "project@example.com") -> dict:
    state = load_dashboard_state()
    import hashlib
    
    item_id = hashlib.sha1(now_iso().encode()).hexdigest()[:12]
    
    new_item = {
        "id": item_id,
        "status": "pending",
        "category": "ACTION",
        "keyword": "report",
        "sender": "System <system@local>",
        "sender_name": "System",
        "sender_email": sender_email,
        "to_address": sender_email,
        "cc_address": "",
        "subject": subject,
        "reply_subject": subject,
        "date": now_iso(),
        "body": body,
        "draft": draft,
        "warnings": get_send_warnings(sender_email, subject, draft),
        "edited": False,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "last_action": None,
        "send_mode": None,
        "error": None
    }
    
    state.setdefault("queue", []).insert(0, new_item)
    save_dashboard_state(state)
    return new_item
