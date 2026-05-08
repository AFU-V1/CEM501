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
from email.utils import parseaddr

from agent import draft_reply, fetch_emails, get_send_warnings, send_approved_email
from digest import SAMPLE_EMAILS, format_html_digest, format_text_digest, group_by_category
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
from reader import triage_email


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
STATE_PATH = os.path.join(LOG_DIR, "dashboard_state.json")
AGENT_LOG_PATH = os.path.join(LOG_DIR, "agent.log")


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
    }


def load_dashboard_state() -> dict:
    """Load the cached dashboard state from disk."""
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(STATE_PATH):
        state = default_state()
        save_dashboard_state(state)
        return state

    with open(STATE_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


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
            email_item.get("body", ""),
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


def _normalize_email(email_item: dict, fallback_date: str) -> dict:
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
        "category": email_item.get("category", "ARCHIVE"),
        "keyword": email_item.get("keyword", "default"),
    }
    normalized["id"] = _queue_key(normalized)
    normalized["preview"] = normalized["body"][:180]
    return normalized


def sample_inbox_snapshot() -> list[dict]:
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
    warnings = get_send_warnings(email_item["sender_email"], reply_subject, draft)
    updated_at = now_iso()

    return {
        "id": email_item["id"],
        "status": existing_item.get("status", "pending") if existing_item else "pending",
        "category": email_item["category"],
        "keyword": email_item["keyword"],
        "sender": email_item["sender"],
        "sender_name": email_item["sender_name"],
        "sender_email": email_item["sender_email"],
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
    resolved_source = source

    try:
        emails = fetch_emails() if source == "live" else sample_inbox_snapshot()
        status_message = "Live inbox snapshot loaded." if source == "live" else "Sample inbox snapshot loaded."
    except Exception as exc:
        emails = sample_inbox_snapshot()
        resolved_source = "sample"
        status_message = f"Live inbox unavailable. Showing sample inbox instead: {exc}"

    normalized_emails = [_normalize_email(item, fallback_date=now_iso()) for item in emails]
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


def dashboard_overview(state: dict) -> dict:
    """Top-level counts for the hero metrics."""
    emails = state.get("emails", [])
    queue_items = state.get("queue", [])
    tasks = get_pending_tasks()
    overdue = get_overdue_tasks()
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


def update_queue_draft(queue_id: str, draft: str) -> dict:
    """Update a draft body and recompute dashboard warnings."""
    state, item, index = find_queue_item(queue_id)
    item["draft"] = draft.strip()
    item["edited"] = True
    item["updated_at"] = now_iso()
    item["warnings"] = get_send_warnings(item["sender_email"], item["reply_subject"], item["draft"])
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
    success, warnings, mode = send_approved_email(
        to_address=item["sender_email"],
        subject=item["reply_subject"],
        body=item["draft"],
        dry_run=dry_run,
    )

    item["warnings"] = warnings
    item["updated_at"] = now_iso()
    item["send_mode"] = mode

    if success:
        contact_id = _ensure_contact(item["sender_name"], item["sender_email"])
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
    return {
        "pending": get_pending_tasks(),
        "overdue": get_overdue_tasks(),
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
            "triage_category": item["category"],
        }
        for item in emails
    ]
    groups = group_by_category(digest_emails)

    return {
        "text": format_text_digest(groups, use_llm=use_llm),
        "html": format_html_digest(groups, use_llm=use_llm),
    }


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
