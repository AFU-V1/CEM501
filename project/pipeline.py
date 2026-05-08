"""Shared message-processing pipeline used by email and messaging channels."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from classifier import classify_message
from drafter import draft_reply
from memory import (
    add_task,
    get_messages_for_contact,
    get_or_create_contact,
    has_logged_message,
    has_pending_task,
    log_message,
)

logger = logging.getLogger("agent")

FOLLOW_UP_TYPES = {"RFI", "APPROVAL", "PROCUREMENT", "DELAY", "SITE_ISSUE"}


def build_history_context(contact_id: int | None, limit: int = 5) -> str:
    """Format recent history so the drafter can stay context-aware."""
    if not contact_id:
        return "No prior history available."

    history = get_messages_for_contact(contact_id, limit=limit)
    if not history:
        return "No prior history available."

    lines = []
    for item in reversed(history):
        subject = item.get("subject") or "(no subject)"
        body = (item.get("body") or "").strip().replace("\n", " ")
        preview = body[:120]
        lines.append(f"{item['direction'].upper()} | {item['channel']} | {subject} | {preview}")
    return "\n".join(lines)


def maybe_schedule_follow_up(contact_id: int | None, subject: str, message_type: str) -> None:
    """Create one reminder task for message types that usually need follow-up."""
    if not contact_id or message_type not in FOLLOW_UP_TYPES:
        return

    due_at = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    description = f"Follow up on {message_type}: {subject[:80]}"
    if has_pending_task(description, contact_id):
        return
    add_task(description=description, due_at=due_at, contact_id=contact_id)
    logger.info("Scheduled follow-up task for contact_id=%s subject=%s", contact_id, subject[:60])


def process_incoming_message(message: dict, send_reply: bool = False, dry_run: bool = False) -> dict:
    """
    Run the shared workflow:
    receive -> classify -> save incoming -> draft -> optionally send -> save outgoing.
    """
    classification = classify_message(
        subject=message.get("subject", ""),
        sender=message.get("sender", ""),
        body=message.get("text", ""),
    )

    sender_email = message.get("sender_email", "")
    sender_phone = message.get("sender_phone", "")
    contact_id = get_or_create_contact(
        name=message.get("sender") or sender_email or sender_phone or "Unknown Contact",
        email=sender_email,
        phone=sender_phone,
        notes=f"Auto-created from {message.get('channel', 'unknown')} channel",
    )

    subject = message.get("subject") or f"{message.get('channel', 'message').title()} message"
    if not has_logged_message(
        contact_id=contact_id,
        direction="received",
        subject=subject,
        body=message.get("text", ""),
        channel=message.get("channel", "unknown"),
    ):
        log_message(
            contact_id=contact_id,
            direction="received",
            subject=subject,
            body=message.get("text", ""),
            channel=message.get("channel", "unknown"),
        )

    history_context = build_history_context(contact_id)
    enriched = {
        "sender": message.get("sender", ""),
        "subject": subject,
        "body": message.get("text", ""),
        "category": classification["category"],
        "message_type": classification["message_type"],
        "matched_keyword": classification["matched_keyword"],
        "history_context": history_context,
        "channel": message.get("channel", "unknown"),
    }
    draft = draft_reply(enriched)

    if classification["needs_reply"]:
        maybe_schedule_follow_up(contact_id, subject, classification["message_type"])

    send_result = None
    if send_reply and message.get("channel_adapter") is not None:
        adapter = message["channel_adapter"]
        send_result = adapter.send_message(
            recipient=message.get("reply_to") or sender_email or message.get("chat_id", ""),
            text=draft,
            subject=subject,
            dry_run=dry_run,
        )
        if send_result and not dry_run:
            log_message(
                contact_id=contact_id,
                direction="sent",
                subject=f"Re: {subject}",
                body=draft,
                channel=message.get("channel", "unknown"),
            )

    return {
        "classification": classification,
        "draft": draft,
        "contact_id": contact_id,
        "history_context": history_context,
        "send_result": send_result,
    }
