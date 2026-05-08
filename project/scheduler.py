"""
scheduler.py -- Agent Scheduler (Milestone M7)
CEM501: Communication Skills for CEM
Bogazici University -- Spring 2026

Runs scheduled tasks for the communication agent:
  - Checks for overdue follow-ups and sends reminders
  - Generates morning digest on schedule
  - Logs all operations

Usage:
    py scheduler.py              # Run once and check pending tasks
    py scheduler.py --loop       # Run continuously (check every 60s)
    py scheduler.py --seed       # Seed database with sample data first
"""

import argparse
import logging
import os
import random
import sys
import time
from datetime import datetime

import schedule as schedule_lib

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory.memory import (
    seed_database,
    get_pending_tasks,
    get_overdue_tasks,
    complete_task,
    get_recent_messages,
    list_contacts,
    DB_PATH,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
AGENT_LOG = os.path.join(LOG_DIR, "agent.log")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(AGENT_LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("scheduler")


# ---------------------------------------------------------------------------
# Retry with exponential backoff (M7 requirement)
# ---------------------------------------------------------------------------

def retry_with_backoff(func, max_retries: int = 3, *args, **kwargs):
    """
    Execute a function with exponential backoff on failure.

    Implements the AWS/Microsoft recommended pattern:
      - Exponential delay: 2^attempt seconds
      - Jitter: random 0-1 second addition
      - Logs each attempt
    """
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            if attempt > 0:
                logger.info(
                    "Function %s succeeded on attempt %d", func.__name__, attempt + 1
                )
            return result
        except Exception as exc:
            wait = (2 ** attempt) + random.uniform(0, 1)
            logger.warning(
                "Attempt %d/%d for %s failed: %s -- retrying in %.1fs",
                attempt + 1, max_retries, func.__name__, exc, wait,
            )
            if attempt < max_retries - 1:
                time.sleep(wait)
            else:
                logger.error(
                    "All %d attempts failed for %s: %s",
                    max_retries, func.__name__, exc,
                )
                raise


# ---------------------------------------------------------------------------
# Scheduled task handlers
# ---------------------------------------------------------------------------

def check_overdue_tasks() -> None:
    """
    Check for overdue tasks and print reminders.
    This is the primary scheduled job for the agent.
    """
    logger.info("Checking for overdue tasks...")

    try:
        overdue = retry_with_backoff(get_overdue_tasks)
    except Exception as exc:
        logger.error("Failed to query overdue tasks: %s", exc)
        return

    if not overdue:
        logger.info("No overdue tasks found.")
        print("  [OK] No overdue tasks.")
        return

    print(f"\n  [!] {len(overdue)} OVERDUE TASK(S) FOUND:")
    print("-" * 50)

    for task in overdue:
        contact = task.get("contact_name", "N/A")
        print(f"  OVERDUE: {task['description']}")
        print(f"           Due: {task['due_at']} | Contact: {contact}")
        print(f"           Task ID: {task['id']}")
        logger.warning(
            "OVERDUE task #%d: %s (due: %s)",
            task["id"], task["description"], task["due_at"],
        )

    print("-" * 50)
    print(f"  Total overdue: {len(overdue)}")


def check_pending_tasks() -> None:
    """Show all pending (not yet overdue) tasks."""
    logger.info("Checking pending tasks...")

    try:
        pending = retry_with_backoff(get_pending_tasks)
    except Exception as exc:
        logger.error("Failed to query pending tasks: %s", exc)
        return

    if not pending:
        logger.info("No pending tasks.")
        print("  [OK] No pending tasks.")
        return

    print(f"\n  Pending Tasks ({len(pending)}):")
    print("-" * 50)
    for task in pending:
        contact = task.get("contact_name", "N/A")
        status_marker = "[!]" if task["due_at"] <= datetime.now().strftime("%Y-%m-%d %H:%M:%S") else "[ ]"
        print(f"  {status_marker} {task['description']}")
        print(f"      Due: {task['due_at']} | Contact: {contact}")
    print("-" * 50)


def generate_morning_summary() -> None:
    """Generate a quick morning summary of contacts and recent activity."""
    logger.info("Generating morning summary...")

    contacts = list_contacts()
    messages = get_recent_messages(limit=5)

    print("\n" + "=" * 50)
    print("  MORNING SUMMARY")
    print("=" * 50)
    print(f"  Date: {datetime.now().strftime('%B %d, %Y at %H:%M')}")
    print(f"  Active contacts: {len(contacts)}")

    if messages:
        print(f"\n  Last {len(messages)} messages:")
        for m in messages:
            direction = ">>" if m["direction"] == "sent" else "<<"
            contact = m.get("contact_name", "Unknown")
            print(f"    {direction} {contact}: {m['subject']}")

    # Check overdue
    overdue = get_overdue_tasks()
    if overdue:
        print(f"\n  [!] {len(overdue)} OVERDUE TASKS need attention!")
    else:
        print("\n  [OK] No overdue tasks.")

    print("=" * 50)
    logger.info("Morning summary complete.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="CEM501 Agent Scheduler -- manages follow-ups, reminders, and periodic tasks.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously, checking every 60 seconds.",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed the memory database with sample data before running.",
    )
    args = parser.parse_args()

    print()
    print("=" * 50)
    print("  CEM501 AGENT SCHEDULER")
    print("=" * 50)

    # Seed database if requested
    if args.seed:
        logger.info("Seeding database with sample data...")
        seed_database()

    if args.loop:
        print("  Mode: CONTINUOUS (checking every 60s)")
        print("  Press Ctrl+C to stop.")
        print("=" * 50)

        # Set up scheduled jobs
        schedule_lib.every(60).seconds.do(check_overdue_tasks)
        schedule_lib.every().day.at("08:00").do(generate_morning_summary)

        logger.info("Scheduler started in loop mode.")

        # Run immediately once, then loop
        check_overdue_tasks()

        try:
            while True:
                schedule_lib.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n  Scheduler stopped.")
            logger.info("Scheduler stopped by user (Ctrl+C).")

    else:
        print("  Mode: SINGLE RUN")
        print("=" * 50)

        # Run all checks once
        generate_morning_summary()
        print()
        check_overdue_tasks()
        print()
        check_pending_tasks()

        logger.info("Single-run scheduler complete.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
