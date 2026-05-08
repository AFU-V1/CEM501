"""
digest.py — Daily Digest Generator (Milestone M3)
CEM501: Communication Skills for CEM
Bogazici University — Spring 2026

Reads emails (from hardcoded samples or live inbox via reader.py),
groups them by triage category, generates LLM summaries for
URGENT and ACTION items, and prints a formatted morning digest.

Usage:
    python digest.py              # Run with hardcoded test emails
    python digest.py --live       # Run with live inbox data via reader.py
    python digest.py --format html  # Output as HTML (stretch goal)
"""

import os
import sys
import email
import imaplib
from datetime import datetime
from email.header import decode_header

import os
from openai import OpenAI


# ---------------------------------------------------------------------------
# Hardcoded test emails (Requirement #6: at least 3 for grader verification)
# ---------------------------------------------------------------------------

SAMPLE_EMAILS = [
    {
        "subject": "URGENT: Fall protection deficiency — immediate correction required",
        "sender": "OSHA Inspector <inspector@osha.gov>",
        "body": (
            "During today's site walk at the Kadikoy Bridge project, missing guardrails "
            "were observed on Level 4 east side scaffolding. All work above Level 3 must "
            "cease until guardrails are installed and inspected. Failure to comply may "
            "result in a stop-work order and penalties. Respond within 24 hours with a "
            "corrective action plan."
        ),
        "triage_category": "URGENT",
    },
    {
        "subject": "Notice of Delay — Pier 5 foundation work",
        "sender": "Kaya Steel <mehmet@kayasteel.com>",
        "body": (
            "Due to the unresolved RFI-018 regarding anchor bolt specifications, we are "
            "formally notifying the GC that Pier 5 bearing installation cannot proceed. "
            "This is a critical path activity. Each day of delay beyond March 21 will "
            "result in a one-day extension to the project schedule. We request immediate "
            "escalation to the Architect."
        ),
        "triage_category": "URGENT",
    },
    {
        "subject": "RFI-047 Response: Rebar spacing at Pier 3",
        "sender": "Project Architect <arslan@archdesign.com>",
        "body": (
            "In response to RFI-047 regarding rebar spacing at Pier 3, the design team "
            "has reviewed the structural calculations and approves Option B (150mm spacing). "
            "Please proceed with installation per the attached revised detail SK-047-R1. "
            "No cost impact anticipated."
        ),
        "triage_category": "ACTION",
    },
    {
        "subject": "Updated delivery schedule for Week 12",
        "sender": "Beton Plus <hasan@betonplus.com.tr>",
        "body": (
            "Please note that the Thursday concrete pour has been moved to Friday due to "
            "plant maintenance at the batching facility. Adjust formwork crew scheduling "
            "accordingly. Volume remains 12 m3 of C35/45 mix. Pump truck will arrive at "
            "07:00 instead of the usual 08:00."
        ),
        "triage_category": "ACTION",
    },
    {
        "subject": "Schedule review meeting — agenda items needed",
        "sender": "Owner's Rep <ozkan@riverfront.com>",
        "body": (
            "Weekly OAC meeting is confirmed for Friday at 10:00. Please submit agenda "
            "items by EOD Wednesday. Topics already on the list: RFI status update, "
            "Pier 4-5 schedule recovery plan, and concrete testing results review."
        ),
        "triage_category": "ACTION",
    },
    {
        "subject": "Weekly safety stats — February summary",
        "sender": "Safety Dept <safety@meridianbuilders.com>",
        "body": (
            "February safety summary: 0 lost-time incidents, 2 near-misses (both resolved), "
            "14 toolbox talks conducted, 98% PPE compliance. Full report attached."
        ),
        "triage_category": "FYI",
    },
    {
        "subject": "Subcontractor insurance cert renewal (Demir AS)",
        "sender": "Procurement <procurement@meridianbuilders.com>",
        "body": (
            "Demir AS has submitted their renewed certificate of insurance, valid through "
            "December 2026. All coverage limits meet contract requirements. Filed in the "
            "project document control system."
        ),
        "triage_category": "FYI",
    },
    {
        "subject": "Project photo album updated",
        "sender": "Documentation <docs@meridianbuilders.com>",
        "body": "March site photos have been uploaded to the shared drive. 47 new photos added.",
        "triage_category": "FYI",
    },
    {
        "subject": "Industry newsletter: New OSHA silica dust rules",
        "sender": "Construction Weekly <newsletter@constructionweekly.com>",
        "body": (
            "New OSHA regulations on silica dust exposure limits take effect July 2026. "
            "Summary of changes and compliance checklist enclosed."
        ),
        "triage_category": "FYI",
    },
    {
        "subject": "RE: Team lunch next Friday",
        "sender": "Admin <admin@meridianbuilders.com>",
        "body": "Reminder: Team lunch next Friday. Please RSVP by Wednesday.",
        "triage_category": "ARCHIVE",
    },
    {
        "subject": "Your benefits enrollment confirmation",
        "sender": "HR <hr@meridianbuilders.com>",
        "body": "Your 2026 benefits enrollment has been confirmed. No action needed.",
        "triage_category": "ARCHIVE",
    },
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def group_by_category(emails: list[dict]) -> dict[str, list[dict]]:
    """
    Groups a list of email dictionaries by their 'triage_category' field.
    Returns a dict with keys: URGENT, ACTION, FYI, ARCHIVE.
    Each value is a list of email dicts belonging to that category.
    """
    groups = {"URGENT": [], "ACTION": [], "FYI": [], "ARCHIVE": []}
    for msg in emails:
        category = msg.get("triage_category", "ARCHIVE")
        if category in groups:
            groups[category].append(msg)
        else:
            groups["ARCHIVE"].append(msg)
    return groups


def summarize_email(body: str) -> str:
    """
    Uses the OpenAI API to generate a one-sentence summary of an email body.
    Only called for URGENT and ACTION emails to keep API usage minimal.
    Falls back to a truncated body if the API call fails.
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": (
                "Summarize the following construction project email in exactly "
                "one concise sentence. Focus on the key action item or issue. "
                "Do not add any information not present in the email.\n\n"
                f"{body}"
            )}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Graceful fallback: return truncated body if LLM is unavailable
        print(f"    [!] LLM summary failed ({e}), using truncated body.", file=sys.stderr)
        return body[:120] + "..." if len(body) > 120 else body


def format_text_digest(groups: dict[str, list[dict]], use_llm: bool = True) -> str:
    """
    Formats grouped emails into a readable text digest.
    URGENT and ACTION items get one-sentence LLM summaries.
    FYI items show subject lines only.
    ARCHIVE items are counted but not shown.
    """
    now = datetime.now()
    total = sum(len(v) for v in groups.values())

    lines = []
    lines.append("=" * 50)
    lines.append("=== PROJECT MORNING DIGEST ===")
    lines.append(f"Generated: {now.strftime('%B %d, %Y at %H:%M')}")
    lines.append(f"Covering: {total} emails")
    lines.append("=" * 50)

    # --- URGENT ---
    urgent = groups["URGENT"]
    lines.append(f"\n--- URGENT ({len(urgent)}) ---")
    if urgent:
        for i, msg in enumerate(urgent, 1):
            lines.append(f"[{i}] From: {msg['sender']}")
            lines.append(f"    Subject: {msg['subject']}")
            if use_llm:
                summary = summarize_email(msg["body"])
            else:
                summary = msg["body"][:120] + ("..." if len(msg["body"]) > 120 else "")
            lines.append(f"    Summary: {summary}")
            lines.append("")
    else:
        lines.append("  (none)")

    # --- ACTION ---
    action = groups["ACTION"]
    lines.append(f"--- ACTION ({len(action)}) ---")
    if action:
        counter = len(urgent)
        for i, msg in enumerate(action, counter + 1):
            lines.append(f"[{i}] From: {msg['sender']}")
            lines.append(f"    Subject: {msg['subject']}")
            if use_llm:
                summary = summarize_email(msg["body"])
            else:
                summary = msg["body"][:120] + ("..." if len(msg["body"]) > 120 else "")
            lines.append(f"    Summary: {summary}")
            lines.append("")
    else:
        lines.append("  (none)")

    # --- FYI (subject lines only) ---
    fyi = groups["FYI"]
    lines.append(f"--- FYI ({len(fyi)}) ---")
    if fyi:
        for msg in fyi:
            lines.append(f"  - {msg['subject']}")
    else:
        lines.append("  (none)")

    # --- ARCHIVE (count only) ---
    archive_count = len(groups["ARCHIVE"])
    lines.append(f"\n--- ARCHIVE ({archive_count} emails skipped) ---")

    lines.append("=" * 50)
    lines.append("=== END DIGEST ===")
    lines.append("")
    lines.append(
        "REMINDER: URGENT and ACTION summaries are AI-generated drafts. "
        "Always verify against the original email before taking action."
    )

    return "\n".join(lines)


def format_html_digest(groups: dict[str, list[dict]], use_llm: bool = True) -> str:
    """
    Formats grouped emails into an HTML digest suitable for email distribution.
    Stretch goal: --format html flag.
    """
    now = datetime.now()
    total = sum(len(v) for v in groups.values())

    html = []
    html.append("<!DOCTYPE html>")
    html.append('<html lang="en"><head><meta charset="utf-8">')
    html.append("<title>Project Morning Digest</title>")
    html.append("<style>")
    html.append("  body { font-family: Arial, sans-serif; max-width: 700px; margin: 20px auto; color: #333; }")
    html.append("  h1 { color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 10px; }")
    html.append("  h2 { margin-top: 25px; }")
    html.append("  .urgent { color: #dc3545; } .action { color: #fd7e14; }")
    html.append("  .fyi { color: #0d6efd; } .archive { color: #6c757d; }")
    html.append("  .email-item { background: #f8f9fa; padding: 12px; margin: 8px 0; border-radius: 6px; border-left: 4px solid; }")
    html.append("  .email-item.urgent { border-color: #dc3545; } .email-item.action { border-color: #fd7e14; }")
    html.append("  .meta { font-size: 0.85em; color: #666; } .summary { margin-top: 6px; }")
    html.append("  .disclaimer { font-size: 0.8em; color: #999; margin-top: 30px; padding: 10px; background: #fff3cd; border-radius: 4px; }")
    html.append("</style></head><body>")
    html.append(f"<h1>Project Morning Digest</h1>")
    html.append(f"<p class='meta'>Generated: {now.strftime('%B %d, %Y at %H:%M')} | {total} emails</p>")

    # URGENT
    urgent = groups["URGENT"]
    html.append(f"<h2 class='urgent'>URGENT ({len(urgent)})</h2>")
    for msg in urgent:
        summary = summarize_email(msg["body"]) if use_llm else msg["body"][:120]
        html.append(f"<div class='email-item urgent'>")
        html.append(f"  <strong>{msg['subject']}</strong><br>")
        html.append(f"  <span class='meta'>From: {msg['sender']}</span>")
        html.append(f"  <div class='summary'>{summary}</div></div>")

    # ACTION
    action = groups["ACTION"]
    html.append(f"<h2 class='action'>ACTION ({len(action)})</h2>")
    for msg in action:
        summary = summarize_email(msg["body"]) if use_llm else msg["body"][:120]
        html.append(f"<div class='email-item action'>")
        html.append(f"  <strong>{msg['subject']}</strong><br>")
        html.append(f"  <span class='meta'>From: {msg['sender']}</span>")
        html.append(f"  <div class='summary'>{summary}</div></div>")

    # FYI
    fyi = groups["FYI"]
    html.append(f"<h2 class='fyi'>FYI ({len(fyi)})</h2><ul>")
    for msg in fyi:
        html.append(f"  <li>{msg['subject']}</li>")
    html.append("</ul>")

    # ARCHIVE
    html.append(f"<h2 class='archive'>ARCHIVE ({len(groups['ARCHIVE'])} emails skipped)</h2>")

    html.append("<div class='disclaimer'>REMINDER: URGENT and ACTION summaries are AI-generated drafts. "
                "Always verify against the original email before taking action.</div>")
    html.append("</body></html>")

    return "\n".join(html)


# ---------------------------------------------------------------------------
# Live inbox integration (connects to reader.py)
# ---------------------------------------------------------------------------

def fetch_live_emails() -> list[dict]:
    """
    Connects to the user's inbox via IMAP (reusing reader.py's logic)
    and returns a list of email dicts with triage categories assigned.
    """
    # Import logic from components
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from reader import fetch_emails
    from classifier import triage_email

    emails = []
    raw_emails = fetch_emails()

    for em in raw_emails:
        category, _ = triage_email(em["subject"], em["sender"], em["body"])
        emails.append({
            "subject": em["subject"],
            "sender": em["sender"],
            "body": em["body"],
            "triage_category": category,
        })

    return emails


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    use_live = "--live" in sys.argv
    output_html = "--format" in sys.argv and "html" in sys.argv

    # Step 1: Get emails (live inbox or hardcoded samples)
    if use_live:
        print("Fetching emails from inbox...")
        try:
            emails = fetch_live_emails()
            print(f"Fetched {len(emails)} emails from inbox.\n")
        except Exception as e:
            print(f"Error fetching live emails: {e}", file=sys.stderr)
            print("Falling back to hardcoded sample emails.\n")
            emails = SAMPLE_EMAILS
    else:
        print("Running with hardcoded sample emails (use --live for inbox data).\n")
        emails = SAMPLE_EMAILS

    # Step 2: Group emails by triage category
    groups = group_by_category(emails)

    # Step 3: Format and output the digest
    if output_html:
        digest = format_html_digest(groups, use_llm=True)
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "digest.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(digest)
        print(f"HTML digest saved to: {output_file}")
    else:
        digest = format_text_digest(groups, use_llm=True)
        print(digest)


if __name__ == "__main__":
    main()
