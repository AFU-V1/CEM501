"""Memory package for CEM501 Agent."""

from memory.memory import (
    get_connection,
    add_contact,
    get_contact_by_email,
    get_contact_by_id,
    list_contacts,
    log_message,
    get_messages_for_contact,
    get_recent_messages,
    add_task,
    get_pending_tasks,
    get_overdue_tasks,
    complete_task,
    skip_task,
    seed_database,
)

__all__ = [
    "get_connection",
    "add_contact",
    "get_contact_by_email",
    "get_contact_by_id",
    "list_contacts",
    "log_message",
    "get_messages_for_contact",
    "get_recent_messages",
    "add_task",
    "get_pending_tasks",
    "get_overdue_tasks",
    "complete_task",
    "skip_task",
    "seed_database",
]
