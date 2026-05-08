"""Channel-agnostic orchestrator for the construction communication agent."""

import argparse
import logging
import os
import sys

from channels.demo_channel import DemoChannel
from channels.email_channel import EmailChannel
from memory import has_logged_message, log_message
from pipeline import process_incoming_message

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


def print_triage_table(messages: list[dict]) -> None:
    print("\n" + "=" * 90)
    print("  MESSAGE TRIAGE SUMMARY")
    print("=" * 90)

    for i, item in enumerate(messages, 1):
        icon = CATEGORY_LABELS.get(item["category"], "[?]")
        sender_short = item["sender"][:28] + "..." if len(item["sender"]) > 28 else item["sender"]
        subject_short = item["subject"][:34] + "..." if len(item["subject"]) > 34 else item["subject"]
        print(
            f"  {i:2d}. {icon:5s} {item['category']:8s} | "
            f"{item['message_type']:11s} | {sender_short:31s} | {subject_short}"
        )

    urgent = sum(1 for item in messages if item["category"] == "URGENT")
    action = sum(1 for item in messages if item["category"] == "ACTION")
    fyi = sum(1 for item in messages if item["category"] == "FYI")
    archive = sum(1 for item in messages if item["category"] == "ARCHIVE")

    print("-" * 90)
    print(
        f"  Total: {len(messages)} messages -- "
        f"{urgent} URGENT, {action} ACTION, {fyi} FYI, {archive} ARCHIVE"
    )
    print("=" * 90)


def main() -> int:
    parser = argparse.ArgumentParser(description="CEM501 Construction Communication Agent")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending.")
    parser.add_argument("--summary", action="store_true", help="Show triage summary only.")
    parser.add_argument(
        "--channel",
        default="demo",
        choices=["demo", "email"],
        help="Channel adapter to run through the shared pipeline.",
    )
    parser.add_argument(
        "--scenario-file",
        default="",
        help="Optional JSON scenario file for the demo channel.",
    )
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  CEM501 CONSTRUCTION COMMUNICATION AGENT")
    print("=" * 70)

    try:
        if args.channel == "email":
            channel = EmailChannel()
        elif args.channel == "demo":
            channel = DemoChannel(scenario_file=args.scenario_file or None)
        else:
            raise RuntimeError(f"Unsupported channel: {args.channel}")
        incoming_messages = channel.fetch_messages()
    except Exception as exc:
        logger.error("Failed to fetch messages: %s", exc)
        print(f"\n[X] Error: {exc}")
        return 1

    if not incoming_messages:
        print("\n  No messages found.")
        return 0

    processed = []
    for message in incoming_messages:
        result = process_incoming_message(
            {**message, "channel_adapter": channel},
            send_reply=False,
            dry_run=args.dry_run,
        )
        classification = result["classification"]
        processed.append({
            "sender": message["sender"],
            "subject": message["subject"],
            "category": classification["category"],
            "message_type": classification["message_type"],
            "keyword": classification["matched_keyword"],
            "priority": classification["priority"],
            "draft": result["draft"],
            "reply_to": message.get("reply_to", ""),
            "channel": message["channel"],
            "contact_id": result["contact_id"],
            "scenario_name": message.get("scenario_name", ""),
            "scenario_notes": message.get("scenario_notes", ""),
        })

    processed.sort(key=lambda item: item["priority"])
    print_triage_table(processed)

    if args.summary:
        return 0

    actionable = [item for item in processed if item["category"] in ("URGENT", "ACTION")]
    if not actionable:
        print("\n  [OK] No actionable messages.")
        return 0

    print(f"\n  Generating drafts for {len(actionable)} actionable message(s)...\n")

    sent_count = 0
    skipped_count = 0

    for i, item in enumerate(actionable, 1):
        print(f"\n{'=' * 60}")
        print(
            f"  [{i}/{len(actionable)}] {item['category']} / "
            f"{item['message_type']}: {item['subject'][:50]}"
        )
        print(f"  From: {item['sender']}")
        if item["scenario_name"]:
            print(f"  Scenario: {item['scenario_name']}")
        if item["scenario_notes"]:
            print(f"  Demo note: {item['scenario_notes']}")
        print(f"{'=' * 60}")

        result = channel.send_message(
            recipient=item["reply_to"],
            text=item["draft"],
            subject=item["subject"],
            dry_run=args.dry_run,
        )

        if result:
            sent_count += 1
            if not args.dry_run:
                sent_subject = f"Re: {item['subject']}"
                if not has_logged_message(
                    contact_id=item["contact_id"],
                    direction="sent",
                    subject=sent_subject,
                    body=item["draft"],
                    channel=item["channel"],
                ):
                    log_message(
                        contact_id=item["contact_id"],
                        direction="sent",
                        subject=sent_subject,
                        body=item["draft"],
                        channel=item["channel"],
                    )
        else:
            skipped_count += 1

    print("\n" + "=" * 70)
    print("  SESSION SUMMARY")
    print("=" * 70)
    print(f"  Messages scanned: {len(processed)}")
    print(f"  Drafts generated: {len(actionable)}")
    summary_label = "Drafts shown" if args.dry_run else "Messages sent"
    print(f"  {summary_label}:    {sent_count}")
    print(f"  Skipped:          {skipped_count}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
