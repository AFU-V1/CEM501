"""
memory.py -- Agent Memory Module (Milestone M7)
CEM501: Communication Skills for CEM
Bogazici University -- Spring 2026

Provides persistent storage for:
  - Contacts (project stakeholders)
  - Message history (sent/received log)
  - Scheduled tasks (follow-ups, reminders)

Uses SQLite for zero-configuration, file-based persistence.
"""

import os
import sqlite3
from datetime import datetime

# ---------------------------------------------------------------------------
# Database path
# ---------------------------------------------------------------------------

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "memory.db")


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
-- Contacts you communicate with on the project
CREATE TABLE IF NOT EXISTS contacts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    email       TEXT,
    phone       TEXT,
    role        TEXT,
    company     TEXT,
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Every message your agent sends or receives
CREATE TABLE IF NOT EXISTS message_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id  INTEGER REFERENCES contacts(id),
    direction   TEXT CHECK(direction IN ('sent', 'received')),
    subject     TEXT,
    body        TEXT,
    channel     TEXT,
    sent_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled follow-ups and reminders
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    due_at      TIMESTAMP NOT NULL,
    contact_id  INTEGER REFERENCES contacts(id),
    status      TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'done', 'skipped')),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_connection() -> sqlite3.Connection:
    """Get a connection to the memory database, creating tables if needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)
    return conn


# ---------------------------------------------------------------------------
# Contact operations
# ---------------------------------------------------------------------------

def add_contact(
    name: str,
    email: str = "",
    phone: str = "",
    role: str = "",
    company: str = "",
    notes: str = "",
) -> int:
    """Insert a new contact and return the new contact ID."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO contacts (name, email, phone, role, company, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, phone, role, company, notes),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_contact_by_email(email: str) -> dict | None:
    """Look up a contact by email address. Returns dict or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM contacts WHERE LOWER(email) = LOWER(?)", (email,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_contact_by_id(contact_id: int) -> dict | None:
    """Look up a contact by ID. Returns dict or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_contacts() -> list[dict]:
    """Return all contacts as a list of dicts."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM contacts ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Message history operations
# ---------------------------------------------------------------------------

def log_message(
    contact_id: int | None,
    direction: str,
    subject: str,
    body: str,
    channel: str = "email",
) -> int:
    """
    Log a sent or received message.

    Args:
        contact_id: FK to contacts table (can be None for unknown senders)
        direction: 'sent' or 'received'
        subject: Email subject line
        body: Message body (or preview)
        channel: 'email', 'telegram', etc.

    Returns:
        The new message_history row ID.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO message_history (contact_id, direction, subject, body, channel) "
            "VALUES (?, ?, ?, ?, ?)",
            (contact_id, direction, subject, body, channel),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_messages_for_contact(contact_id: int, limit: int = 20) -> list[dict]:
    """Retrieve message history for a specific contact, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM message_history WHERE contact_id = ? "
            "ORDER BY sent_at DESC LIMIT ?",
            (contact_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_recent_messages(limit: int = 20) -> list[dict]:
    """Retrieve the most recent messages across all contacts."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT mh.*, c.name AS contact_name, c.company AS contact_company "
            "FROM message_history mh "
            "LEFT JOIN contacts c ON mh.contact_id = c.id "
            "ORDER BY mh.sent_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Scheduled tasks operations
# ---------------------------------------------------------------------------

def add_task(
    description: str,
    due_at: str,
    contact_id: int | None = None,
) -> int:
    """
    Schedule a new follow-up task.

    Args:
        description: What needs to be done.
        due_at: Due date/time as ISO string (e.g. '2026-04-10 09:00:00').
        contact_id: Optional FK to contacts table.

    Returns:
        The new task row ID.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO scheduled_tasks (description, due_at, contact_id) "
            "VALUES (?, ?, ?)",
            (description, due_at, contact_id),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_pending_tasks() -> list[dict]:
    """Return all pending tasks, ordered by due date."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT st.*, c.name AS contact_name "
            "FROM scheduled_tasks st "
            "LEFT JOIN contacts c ON st.contact_id = c.id "
            "WHERE st.status = 'pending' "
            "ORDER BY st.due_at ASC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_overdue_tasks() -> list[dict]:
    """Return all pending tasks that are past due."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT st.*, c.name AS contact_name "
            "FROM scheduled_tasks st "
            "LEFT JOIN contacts c ON st.contact_id = c.id "
            "WHERE st.status = 'pending' AND st.due_at <= ? "
            "ORDER BY st.due_at ASC",
            (now,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def complete_task(task_id: int) -> None:
    """Mark a scheduled task as done."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE scheduled_tasks SET status = 'done' WHERE id = ?",
            (task_id,),
        )
        conn.commit()
    finally:
        conn.close()


def skip_task(task_id: int) -> None:
    """Mark a scheduled task as skipped."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE scheduled_tasks SET status = 'skipped' WHERE id = ?",
            (task_id,),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Seed data -- populate with realistic CEM contacts and messages
# ---------------------------------------------------------------------------

def seed_database() -> None:
    """
    Populate the database with sample construction project contacts,
    messages, and scheduled tasks for demonstration and grading.
    """
    conn = get_connection()
    try:
        # Check if already seeded
        count = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        if count > 0:
            print(f"  Database already has {count} contacts -- skipping seed.")
            return

        # --- 7 sample contacts ---
        contacts = [
            ("Eyuphan Koc", "eyuphan.koc@gmail.com", "+90-532-100-0001",
             "Project Owner Representative", "Bogazici University", "Course instructor and project owner rep"),
            ("Mehmet Arslan", "mehmet@archdesign.com", "+90-532-200-0002",
             "Project Architect", "ArchDesign Ltd.", "Lead architect for Kadikoy Metro Station"),
            ("Burak Demir", "burak@kayasteel.com", "+90-532-300-0003",
             "Structural Subcontractor PM", "Kaya Steel Construction", "Manages steel and piling work"),
            ("Hasan Yilmaz", "hasan@betonplus.com.tr", "+90-532-400-0004",
             "Concrete Supplier Contact", "Beton Plus Ready-Mix", "Ready-mix concrete supply for all pours"),
            ("Ayse Ozkan", "ayse@riverfront.com", "+90-532-500-0005",
             "Owner's Representative", "Riverfront Development Group", "Represents the owner on-site"),
            ("Fatih Celik", "fatih@igdas.istanbul", "+90-532-600-0006",
             "Utility Coordinator", "IGDAS Istanbul Gas Distribution", "Gas main coordination contact"),
            ("Zeynep Kara", "zeynep@meridianbuilders.com", "+90-532-700-0007",
             "Safety Manager", "Meridian Builders", "Site safety and compliance officer"),
        ]

        contact_ids = []
        for name, email_addr, phone, role, company, notes in contacts:
            cursor = conn.execute(
                "INSERT INTO contacts (name, email, phone, role, company, notes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, email_addr, phone, role, company, notes),
            )
            contact_ids.append(cursor.lastrowid)

        # --- 12 sample messages ---
        messages = [
            (contact_ids[0], "received", "URGENT: Stop work order", "Unauthorized utility crossing found at Grid C-7.", "email"),
            (contact_ids[0], "sent", "Re: URGENT: Stop work order", "Acknowledged. Work stopped within 5m radius of C-7. Investigation underway.", "email"),
            (contact_ids[1], "received", "RFI-031: Waler beam connection", "Discrepancy between Drawing S-204 Detail 7 and Spec 05 12 00.", "email"),
            (contact_ids[1], "sent", "Re: RFI-031: Waler beam connection", "Thank you. Under review with structural engineer. Response within 24h.", "email"),
            (contact_ids[2], "received", "Pile installation schedule Week 14", "Crew mobilized, 8 piles completed yesterday. On track.", "email"),
            (contact_ids[2], "sent", "Re: Pile installation schedule Week 14", "Good progress noted. Updated project tracker.", "email"),
            (contact_ids[3], "received", "Price adjustment notice April 2026", "C25/30 up 8%, C35/45 up 6%. New prices effective April 1.", "email"),
            (contact_ids[4], "received", "Meeting minutes February 28", "OAC meeting notes attached. Action items listed.", "email"),
            (contact_ids[4], "sent", "Re: Meeting minutes February 28", "Reviewed and acknowledged. Will address action items.", "email"),
            (contact_ids[5], "received", "Gas main maintenance April 2-3", "Scheduled maintenance on Bahariye Caddesi gas main.", "telegram"),
            (contact_ids[6], "received", "Weekly safety report Week 13", "No incidents. 98% PPE compliance. 6 toolbox talks.", "email"),
            (contact_ids[6], "sent", "Re: Weekly safety report Week 13", "Excellent safety record. Continue the same standard.", "email"),
        ]

        for contact_id, direction, subject, body, channel in messages:
            conn.execute(
                "INSERT INTO message_history (contact_id, direction, subject, body, channel) "
                "VALUES (?, ?, ?, ?, ?)",
                (contact_id, direction, subject, body, channel),
            )

        # --- 5 sample scheduled tasks ---
        tasks = [
            ("Follow up on RFI-031 response from architect", "2026-04-05 09:00:00", contact_ids[1]),
            ("Remind Kaya Steel about updated pile schedule", "2026-04-07 08:00:00", contact_ids[2]),
            ("Review concrete price impact on project budget", "2026-04-10 14:00:00", contact_ids[3]),
            ("Submit road closure permit renewal to IMM", "2026-03-29 10:00:00", None),
            ("Prepare weekly status digest for owner", "2026-04-08 07:00:00", contact_ids[4]),
        ]

        for description, due_at, contact_id in tasks:
            conn.execute(
                "INSERT INTO scheduled_tasks (description, due_at, contact_id) "
                "VALUES (?, ?, ?)",
                (description, due_at, contact_id),
            )

        conn.commit()
        print(f"  Database seeded: {len(contacts)} contacts, {len(messages)} messages, {len(tasks)} tasks.")

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI entry point for testing
# ---------------------------------------------------------------------------

def main() -> None:
    """Quick CLI to verify database contents."""
    print("=" * 60)
    print("  CEM501 Agent Memory -- Database Status")
    print("=" * 60)

    # Seed if empty
    seed_database()

    # Show contacts
    contacts = list_contacts()
    print(f"\n  Contacts ({len(contacts)}):")
    for c in contacts:
        print(f"    {c['id']}. {c['name']} ({c['role']}) -- {c['company']}")

    # Show recent messages
    messages = get_recent_messages(limit=10)
    print(f"\n  Recent Messages ({len(messages)}):")
    for m in messages:
        direction_arrow = ">>" if m["direction"] == "sent" else "<<"
        contact_name = m.get("contact_name", "Unknown")
        print(f"    {direction_arrow} {contact_name}: {m['subject']}")

    # Show pending tasks
    tasks = get_pending_tasks()
    print(f"\n  Pending Tasks ({len(tasks)}):")
    for t in tasks:
        contact_name = t.get("contact_name", "N/A")
        print(f"    [{t['status'].upper()}] {t['description']} (due: {t['due_at']}, contact: {contact_name})")

    # Show overdue tasks
    overdue = get_overdue_tasks()
    if overdue:
        print(f"\n  OVERDUE Tasks ({len(overdue)}):")
        for t in overdue:
            print(f"    [!] {t['description']} (was due: {t['due_at']})")

    print("\n" + "=" * 60)
    print(f"  Database file: {DB_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
