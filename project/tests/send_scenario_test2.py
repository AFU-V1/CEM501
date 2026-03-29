#!/usr/bin/env python3
"""
CEM501 — Send 20 NEW scenario test emails to your own inbox.

Usage:
  py send_scenario_test2.py              # send all 20 emails
  py send_scenario_test2.py --dry-run    # preview without sending
  py send_scenario_test2.py --delay 5    # 5-second delay between emails
"""

import argparse
import os
import smtplib
import sys
import time
from email.mime.text import MIMEText
from email.utils import formataddr

from dotenv import load_dotenv

SCENARIO_EMAILS = [
    # --- URGENT (5 emails) ---
    {
        "sender_name": "Murat Yilmaz, OSHA Inspector",
        "subject": "STOP WORK ORDER — Trench collapse hazard at Sector 4",
        "body": "Immediate halting of all activities in Sector 4 until proper shoring is verified.",
        "intended_category": "URGENT",
    },
    {
        "sender_name": "Metin Yildirim, Steel Contractor",
        "subject": "Notice of Delay — Late structural steel delivery impacts critical path",
        "body": "Due to supply chain issues, delivery is delayed by 3 weeks.",
        "intended_category": "URGENT",
    },
    {
        "sender_name": "Hasan Celik, Safety Officer",
        "subject": "Safety Incident — Worker fall from scaffolding",
        "body": "A worker fell 2 meters. Minor injuries. An incident report is being filed.",
        "intended_category": "URGENT",
    },
    {
        "sender_name": "Zeynep Arslan, Owner's Rep",
        "subject": "Urgent review required: Claim of Differing Site Conditions",
        "body": "The excavation contractor filed a massive claim. Review attached documents.",
        "intended_category": "URGENT",
    },
    {
        "sender_name": "Ahmet Demir, IMM Inspector",
        "subject": "Immediate Action: Crane permit rescinded by City",
        "body": "Your tower crane permit #88229 is suspended due to wind safety violations.",
        "intended_category": "URGENT",
    },
    # --- ACTION (5 emails) ---
    {
        "sender_name": "Ayse Oztürk, Architect",
        "subject": "RFI-088: Clarification on HVAC duct routing in basement",
        "body": "Please confirm the clash resolution between plumbing and HVAC on level B1.",
        "intended_category": "ACTION",
    },
    {
        "sender_name": "Kemal Baran, Facade Sub",
        "subject": "Submittal 044: Curtain wall glazing specifications",
        "body": "Attached is the submittal for the low-E coating glazing. Awaiting your review.",
        "intended_category": "ACTION",
    },
    {
        "sender_name": "Burak Sahin, Earthworks",
        "subject": "Change Order 012 for approval - additional excavation volume",
        "body": "Proposal attached for the extra rock removal encountered last week.",
        "intended_category": "ACTION",
    },
    {
        "sender_name": "Ali Veli, Finance",
        "subject": "Response Required: Subcontractor payment application #4",
        "body": "Please review and approve the attached pay app so we can process it.",
        "intended_category": "ACTION",
    },
    {
        "sender_name": "Fatma Yildiz, Utilities",
        "subject": "Coordination Meeting Request — Utilities tie-in next Tuesday",
        "body": "We need all hands on deck to coordinate the main power swap.",
        "intended_category": "ACTION",
    },
    # --- FYI (5 emails) ---
    {
        "sender_name": "Selin Dogan, Field Eng",
        "subject": "Daily work log — April 2 — weather delay morning",
        "body": "Heavy rain stopped work till 10am. Resumed normally afterwards.",
        "intended_category": "FYI",
    },
    {
        "sender_name": "Canan Yilmaz, Doc Control",
        "subject": "Progress photo album — Week 14",
        "body": "Latest site drone overview pictures are uploaded to the shared folder.",
        "intended_category": "FYI",
    },
    {
        "sender_name": "Ozan Kaya, QA/QC",
        "subject": "Test results — Soil compaction density meets specs",
        "body": "All 12 locations passed the 95% threshold requirement.",
        "intended_category": "FYI",
    },
    {
        "sender_name": "Emre Koc, Scheduler",
        "subject": "Weekly schedule update — 1 week behind baseline",
        "body": "We lost some time to rain. Updated P6 schedule attached.",
        "intended_category": "FYI",
    },
    {
        "sender_name": "Zeynep Arslan, Owner's Rep",
        "subject": "Meeting minutes — Safety standalone review",
        "body": "Distributing the notes from yesterday's all-hands safety briefing.",
        "intended_category": "FYI",
    },
    # --- ARCHIVE (5 emails) ---
    {
        "sender_name": "Con-Tech Magazine",
        "subject": "Newsletter: Top 10 trends in Construction Tech 2026",
        "body": "Read our monthly digest on new robotics entering the site.",
        "intended_category": "ARCHIVE",
    },
    {
        "sender_name": "HR Department",
        "subject": "Benefits open enrollment ends Friday",
        "body": "Don't forget to submit your choices for health insurance by EOW.",
        "intended_category": "ARCHIVE",
    },
    {
        "sender_name": "Cat Rentals",
        "subject": "Exclusive offer on heavy equipment rentals from Cat",
        "body": "Discounted rates for spring mobilization. Check it out!",
        "intended_category": "ARCHIVE",
    },
    {
        "sender_name": "Mehmet Gunes, Colleague",
        "subject": "FW: You won't believe this concrete pour disaster",
        "body": "Look at what happened in this video I found.",
        "intended_category": "ARCHIVE",
    },
    {
        "sender_name": "IT Support",
        "subject": "Maintenance: Network downtime on Sunday night",
        "body": "Office network will be offline from 1am to 3am for upgrades.",
        "intended_category": "ARCHIVE",
    },
]

def main():
    parser = argparse.ArgumentParser(description="Send 20 NEW CEM scenario test emails to yourself.")
    parser.add_argument("--dry-run", action="store_true", help="Preview emails without sending.")
    parser.add_argument("--delay", type=int, default=5, help="Seconds between emails (default: 5).")
    args = parser.parse_args()

    # Automatically navigate up to project root to find .env if run from tests/
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()

    email_address = os.getenv("EMAIL_ADDRESS", "").strip()
    email_password = os.getenv("EMAIL_PASSWORD", "").strip()

    if not email_address or not email_password:
        print("ERROR: EMAIL_ADDRESS and EMAIL_PASSWORD must be set in .env")
        sys.exit(1)

    print(f"Emails to send: {len(SCENARIO_EMAILS)}")
    print(f"Target inbox: {email_address}\n")

    if args.dry_run:
        print("=== DRY RUN ===\n")
        return

    confirm = input(f"Send {len(SCENARIO_EMAILS)} test emails to {email_address}? [y/N] ")
    if confirm.lower() != "y":
        print("Cancelled.")
        return

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_address, email_password)

        for i, em in enumerate(SCENARIO_EMAILS, 1):
            msg = MIMEText(em["body"], "plain", "utf-8")
            msg["Subject"] = em["subject"]
            msg["From"] = formataddr((em["sender_name"], email_address))
            msg["To"] = email_address

            server.send_message(msg)
            print(f"  [{i:>2}/{len(SCENARIO_EMAILS)}] ✓ Sent: {em['subject'][:60]}...")

            if i < len(SCENARIO_EMAILS):
                time.sleep(args.delay)

        server.quit()
        print("\nDone! Wait a minute, then run: py reader.py")

    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
