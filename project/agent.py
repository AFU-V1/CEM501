"""
agent.py -- Email Agent Pipeline Orchestrator
CEM501: Communication Skills for CEM
Bogazici University -- Spring 2026

Coordinates the pipeline:
  1. Reader (IMAP)
  2. Classifier (Keyword/LLM)
  3. Drafter (OpenAI)
  4. Sender (SMTP)
"""

import argparse
import logging
import os
import sys

from reader import fetch_emails
from classifier import triage_email, CATEGORY_PRIORITY
from drafter import draft_reply
from sender import send_email

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
logger = logging.getLogger("agent")

CATEGORY_LABELS = {
    "URGENT": "[!!!]",
    "ACTION": "[>>]",
    "FYI": "[i]",
    "ARCHIVE": "[--]",
}

def print_triage_table(emails: list[dict]) -> None:
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

def main() -> int:
    parser = argparse.ArgumentParser(description="CEM501 Email Agent Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending.")
    parser.add_argument("--summary", action="store_true", help="Show triage summary only.")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  CEM501 EMAIL AGENT")
    print("=" * 70)

    # 1. READ
    try:
        raw_emails = fetch_emails()
    except Exception as exc:
        logger.error("Failed to fetch emails: %s", exc)
        print(f"\n[X] Error: {exc}")
        return 1

    if not raw_emails:
        print("\n  No emails found in inbox.")
        return 0

    # 2. CLASSIFY
    emails = []
    for em in raw_emails:
        cat, kw = triage_email(em["subject"], em["sender"], em["body"])
        em["category"] = cat
        em["keyword"] = kw
        emails.append(em)

    emails.sort(key=lambda e: CATEGORY_PRIORITY.get(e["category"], 99))
    print_triage_table(emails)

    if args.summary:
        return 0

    # Filter actionable
    actionable = [e for e in emails if e["category"] in ("URGENT", "ACTION")]
    if not actionable:
        print("\n  [OK] No actionable emails.")
        return 0

    print(f"\n  Generating drafts for {len(actionable)} actionable email(s)...\n")

    sent_count = 0
    skipped_count = 0

    # 3. DRAFT & 4. SEND
    for i, em in enumerate(actionable, 1):
        print(f"\n{'=' * 60}")
        print(f"  [{i}/{len(actionable)}] {em['category']}: {em['subject'][:50]}")
        print(f"  From: {em['sender']}")
        print(f"{'=' * 60}")

        draft = draft_reply(em)
        result = send_email(em["sender_email"], em["subject"], draft, dry_run=args.dry_run)

        if result:
            sent_count += 1
        else:
            skipped_count += 1

    print("\n" + "=" * 70)
    print("  SESSION SUMMARY")
    print("=" * 70)
    print(f"  Emails scanned:   {len(emails)}")
    print(f"  Drafts generated: {len(actionable)}")
    print(f"  Emails sent:      {sent_count}")
    print(f"  Skipped:          {skipped_count}")
    print("=" * 70)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
