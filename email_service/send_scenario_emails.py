#!/usr/bin/env python3
"""
CEM501 — Send scenario emails for the Week 5 Triage Live Test.

Loads 12 fictional project emails from scenario_emails.json and sends them
to student inboxes listed in triage_recipients.json.

Usage:
  python send_scenario_emails.py              # send all 12 emails
  python send_scenario_emails.py --dry-run    # preview without sending
  python send_scenario_emails.py --delay 30   # 30-second delay between emails (default: 45)
"""

import argparse
import json
import sys
import time
from pathlib import Path
from send_email import load_env, send_email

SCRIPT_DIR = Path(__file__).parent
SCENARIO_FILE = SCRIPT_DIR / "scenario_emails.json"
RECIPIENTS_FILE = SCRIPT_DIR / "triage_recipients.json"


def load_scenario():
    """Load scenario emails from JSON."""
    with open(SCENARIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_recipients():
    """Load triage recipient addresses from JSON."""
    with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    recipients = []
    for r in data["recipients"]:
        addr = r.get("triage_email", "").strip()
        if addr:
            recipients.append({"name": r["name"], "email": addr})

    return recipients


def main():
    parser = argparse.ArgumentParser(description="Send Week 5 scenario emails to students.")
    parser.add_argument("--dry-run", action="store_true", help="Preview emails without sending.")
    parser.add_argument("--delay", type=int, default=45, help="Seconds between emails (default: 45).")
    args = parser.parse_args()

    scenario = load_scenario()
    recipients = load_recipients()

    if not recipients:
        print("ERROR: No recipients found in triage_recipients.json.")
        print("Fill in the 'triage_email' field for each student first.")
        sys.exit(1)

    emails = scenario["emails"]
    recipient_addrs = [r["email"] for r in recipients]

    print(f"Scenario: {scenario['scenario']}")
    print(f"Emails to send: {len(emails)}")
    print(f"Recipients ({len(recipients)}):")
    for r in recipients:
        print(f"  - {r['name']}: {r['email']}")
    print()

    if args.dry_run:
        print("=== DRY RUN — no emails will be sent ===\n")
        for em in emails:
            print(f"  [{em['id']:>2}] From: {em['sender_name']}")
            print(f"       Subject: {em['subject']}")
            print(f"       Body: {em['body'][:80]}...")
            print(f"       Category: {em['intended_category']}")
            print()
        print(f"Total: {len(emails)} emails x {len(recipients)} recipients = {len(emails) * len(recipients)} deliveries")
        print(f"Estimated time: {len(emails) * args.delay // 60} min {len(emails) * args.delay % 60} sec")
        return

    confirm = input(f"Send {len(emails)} emails to {len(recipients)} recipients? [y/N] ")
    if confirm.lower() != "y":
        print("Cancelled.")
        return

    for i, em in enumerate(emails):
        print(f"[{i+1}/{len(emails)}] Sending: {em['subject'][:60]}...")

        send_email(
            subject=em["subject"],
            body=em["body"],
            recipients=recipient_addrs,
            sender_name=em["sender_name"],
        )

        if i < len(emails) - 1:
            print(f"         Waiting {args.delay}s before next email...")
            time.sleep(args.delay)

    print(f"\nDone. {len(emails)} scenario emails sent to {len(recipients)} recipients.")


if __name__ == "__main__":
    main()
