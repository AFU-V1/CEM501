#!/usr/bin/env python3
"""
CEM501 — Send 20 scenario test emails to your own inbox.

Sends 20 realistic construction project emails (Istanbul Kadikoy Metro Station)
to test your reader.py triage logic. Uses your .env credentials to send via Gmail SMTP.

Usage:
  py send_scenario_test.py              # send all 20 emails
  py send_scenario_test.py --dry-run    # preview without sending
  py send_scenario_test.py --delay 5    # 5-second delay between emails (default: 10)
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
        "subject": "STOP WORK ORDER — Unsupported excavation face at Grid C-7",
        "body": (
            "Dear Project Manager,\n\n"
            "During today's site inspection at the Kadikoy Metro Station deep excavation, "
            "I observed an unsupported excavation face exceeding 3 meters at Grid C-7. "
            "This constitutes an immediate safety hazard under Regulation 29/2024.\n\n"
            "ALL WORK in the excavation zone must cease immediately until shoring is installed "
            "and verified by a qualified geotechnical engineer.\n\n"
            "A follow-up inspection will be conducted within 48 hours. Failure to comply will "
            "result in formal enforcement action.\n\n"
            "Murat Yilmaz\nSenior Inspector, OSHA Istanbul Division"
        ),
        "intended_category": "URGENT",
    },
    {
        "sender_name": "Dr. Elif Kara, Geotechnical Engineer",
        "subject": "Unexpected soil conditions at Abutment B — recommend stop work pending review",
        "body": (
            "Dear PM,\n\n"
            "Our field team has identified unexpected clay lens formations at Abutment B, "
            "elevation -18.5m. The encountered soil profile does not match the geotechnical "
            "investigation report (GIR Rev.3, dated 12 Jan 2026).\n\n"
            "I strongly recommend stopping excavation at this location until we can perform "
            "additional borings and reassess the retaining wall design. Continuing without "
            "review poses a risk of wall displacement.\n\n"
            "Please confirm receipt and schedule an urgent meeting with the design team.\n\n"
            "Dr. Elif Kara, PhD\nGeotechnical Lead, Zemin Engineering"
        ),
        "intended_category": "URGENT",
    },
    {
        "sender_name": "Ahmet Demir, IMM Inspector",
        "subject": "NOTICE: Vibration limits exceeded — adjacent historic building at risk",
        "body": (
            "Dear Project Manager,\n\n"
            "Vibration monitoring data from today's secant pile installation shows peak particle "
            "velocity of 12.4 mm/s at sensor VS-03, located on the facade of the historic "
            "Haydarpaşa Numune Hospital. The contractual limit is 5.0 mm/s per Section 8.2.\n\n"
            "You are hereby notified that immediate corrective measures are required. "
            "Continued operations at current intensity will result in a formal notice of "
            "non-compliance to Istanbul Metropolitan Municipality.\n\n"
            "Ahmet Demir\nStructural Monitoring Division, IMM"
        ),
        "intended_category": "URGENT",
    },
    {
        "sender_name": "Zeynep Arslan, Owner's Representative",
        "subject": "NOTICE: Liquidated damages clause activated — response required within 7 calendar days",
        "body": (
            "Dear Contractor,\n\n"
            "Per Section 12.4 of the General Conditions and the Project Agreement dated "
            "15 March 2025, I am formally notifying you that the Kadikoy Metro Station project "
            "has exceeded the contractual milestone for completion of secant pile wall installation "
            "by 14 calendar days.\n\n"
            "Liquidated damages of $8,500 per calendar day are now in effect. Per Section 12.4.3, "
            "you have 7 calendar days from receipt of this notice to submit a time extension "
            "request with supporting documentation, or damages will be assessed from the original "
            "milestone date.\n\n"
            "Failure to respond within the stated period will constitute acceptance of the "
            "damages assessment.\n\n"
            "Zeynep Arslan\nOwner's Representative, Kadikoy Metro Project"
        ),
        "intended_category": "URGENT",
    },
    {
        "sender_name": "Hasan Celik, Safety Officer",
        "subject": "Safety incident report — near-miss at Pier 4 crane operation",
        "body": (
            "INCIDENT REPORT — NEAR MISS\n\n"
            "Date: Today\nLocation: Pier 4 crane staging area\n"
            "Type: Near-miss (dropped load)\n\n"
            "A 2-ton steel beam slipped from the rigging during lifting at Pier 4 and fell "
            "approximately 3 meters to the ground. No personnel were in the drop zone at the "
            "time. The exclusion zone was properly maintained.\n\n"
            "Root cause: Worn sling identified during post-incident inspection. All similar "
            "slings have been taken out of service for inspection.\n\n"
            "Immediate actions taken:\n"
            "- Area cordoned off and secured\n"
            "- All lifting operations suspended pending rigging equipment audit\n"
            "- Toolbox talk scheduled for tomorrow morning\n\n"
            "Full investigation report to follow within 24 hours.\n\n"
            "Hasan Celik\nSite Safety Officer"
        ),
        "intended_category": "URGENT",
    },
    # --- ACTION (5 emails) ---
    {
        "sender_name": "Ayse Oztürk, Project Architect",
        "subject": "RFI-047 Response: Rebar spacing at Pier 3 footing — your review needed",
        "body": (
            "Dear PM,\n\n"
            "Please find attached the revised rebar spacing detail for the Pier 3 footing "
            "(Drawing S-301 Rev.C). The spacing has been changed from 150mm to 200mm c/c "
            "based on the updated structural analysis.\n\n"
            "Please review and confirm this is acceptable for construction. We need your "
            "sign-off by end of this week to maintain the pour schedule.\n\n"
            "Ayse Oztürk\nSenior Architect, Metro Design Group"
        ),
        "intended_category": "ACTION",
    },
    {
        "sender_name": "Kemal Baran, Steel Fabricator",
        "subject": "Shop drawing submittal SD-023 for review and approval",
        "body": (
            "Dear Project Manager,\n\n"
            "We are submitting shop drawings for the temporary decking steel framing "
            "(SD-023, 47 sheets) for your review and approval per the contract requirements.\n\n"
            "The submittal includes:\n"
            "- W-beam connection details\n"
            "- Bolted splice locations\n"
            "- Bearing plate details at secant pile cap interface\n\n"
            "Per the submittal schedule, your review is due within 10 business days. "
            "Please note that late approval will impact the decking installation schedule.\n\n"
            "Kemal Baran\nProject Manager, Baran Steel Fabrication"
        ),
        "intended_category": "ACTION",
    },
    {
        "sender_name": "Fatma Yildiz, Electrical Subcontractor",
        "subject": "Request for schedule coordination meeting — utility relocation Phase 2",
        "body": (
            "Dear PM,\n\n"
            "We need to coordinate the Phase 2 utility relocation with your excavation "
            "schedule. The existing 34.5kV TEDAS cable at -4m elevation needs to be "
            "relocated before you can proceed to -6m at Grids D-1 through D-5.\n\n"
            "Can we schedule a coordination meeting this week? We need at least 3 business "
            "days advance notice to mobilize the TEDAS crew.\n\n"
            "Please confirm available times.\n\n"
            "Fatma Yildiz\nElectrical Lead, Yildiz MEP"
        ),
        "intended_category": "ACTION",
    },
    {
        "sender_name": "Burak Sahin, Dewatering Contractor",
        "subject": "Change order proposal — additional wellpoints required at Grid B zone",
        "body": (
            "Dear Project Manager,\n\n"
            "Due to the higher-than-expected groundwater inflow at the Grid B excavation zone "
            "(measured at 45 L/min vs. design estimate of 20 L/min), we propose installing "
            "6 additional wellpoints to maintain the required drawdown.\n\n"
            "Change Order Proposal:\n"
            "- 6x additional wellpoints with submersible pumps\n"
            "- Additional header piping and discharge connections\n"
            "- Estimated cost: $42,000\n"
            "- Duration impact: None (can install concurrent with ongoing work)\n\n"
            "Please review and advise on approval process.\n\n"
            "Burak Sahin\nDewatering Manager, HydroControl Ltd."
        ),
        "intended_category": "ACTION",
    },
    {
        "sender_name": "Deniz Aksoy, Environmental Consultant",
        "subject": "Stormwater permit renewal — deadline April 15",
        "body": (
            "Dear PM,\n\n"
            "This is a reminder that the site stormwater discharge permit (Permit No. "
            "SW-2025-0847) expires on April 15, 2026. The renewal application must be "
            "submitted to the Istanbul Water and Sewerage Administration (ISKI) at least "
            "10 business days before expiry.\n\n"
            "I have prepared the draft renewal application. Please review the attached "
            "monitoring data summary and approve the submission.\n\n"
            "Note: Operating without a valid permit would require immediate site shutdown.\n\n"
            "Deniz Aksoy\nSenior Environmental Consultant, EcoTech"
        ),
        "intended_category": "ACTION",
    },
    # --- FYI (5 emails) ---
    {
        "sender_name": "Emre Koc, Project Scheduler",
        "subject": "Weekly schedule update — 2 days ahead of baseline",
        "body": (
            "Team,\n\n"
            "Attached is the weekly schedule update for the Kadikoy Metro Station project.\n\n"
            "Summary:\n"
            "- Overall project: 2 days ahead of baseline\n"
            "- Secant pile installation: 87% complete (on track)\n"
            "- Excavation to -12m: completed yesterday\n"
            "- Dewatering system: operating within design parameters\n"
            "- Next critical activity: Begin excavation to -16m (Monday)\n\n"
            "No schedule concerns at this time. Full Primavera P6 export attached.\n\n"
            "Emre Koc\nProject Scheduler"
        ),
        "intended_category": "FYI",
    },
    {
        "sender_name": "Selin Dogan, Field Engineer",
        "subject": "Daily work log — March 28 — no issues to report",
        "body": (
            "Daily Log — March 28, 2026\n\n"
            "Weather: Clear, 14°C\n"
            "Workforce: 34 laborers, 8 operators, 5 engineers\n"
            "Equipment: 2 excavators, 1 crane, 3 dump trucks, dewatering pumps\n\n"
            "Activities:\n"
            "- Continued excavation at Level -12m, Grids A-3 to A-7\n"
            "- Installed 4 secant piles (SP-145 through SP-148)\n"
            "- Dewatering monitoring: groundwater level at -14.2m (target: -14.0m)\n"
            "- Concrete delivery: 45 m³ for pile caps\n\n"
            "Issues: None\n"
            "Visitors: None\n\n"
            "Selin Dogan\nField Engineer"
        ),
        "intended_category": "FYI",
    },
    {
        "sender_name": "Canan Yilmaz, Document Controller",
        "subject": "Monthly progress photo update — March 2026",
        "body": (
            "Dear Team,\n\n"
            "The March 2026 progress photo album has been uploaded to the project document "
            "management system.\n\n"
            "Key photos include:\n"
            "- Aerial drone survey of excavation perimeter\n"
            "- Secant pile wall completion at Grid A\n"
            "- Temporary decking installation progress\n"
            "- Vibration monitoring equipment setup\n\n"
            "94 photos total. Access via ProjectDocs > Photos > 2026-03.\n\n"
            "Canan Yilmaz\nDocument Controller"
        ),
        "intended_category": "FYI",
    },
    {
        "sender_name": "Ozan Kaya, Quality Manager",
        "subject": "Concrete test results recap — all specimens passed 28-day strength",
        "body": (
            "Team,\n\n"
            "Summary of 28-day compressive strength test results for February pours:\n\n"
            "- Batch B-2026-021: 42.3 MPa (required: 35 MPa) ✅\n"
            "- Batch B-2026-022: 38.7 MPa (required: 35 MPa) ✅\n"
            "- Batch B-2026-023: 44.1 MPa (required: 35 MPa) ✅\n"
            "- Batch B-2026-024: 39.8 MPa (required: 35 MPa) ✅\n\n"
            "All specimens meet or exceed specified strength. Full lab reports attached.\n\n"
            "Ozan Kaya\nQuality Manager"
        ),
        "intended_category": "FYI",
    },
    {
        "sender_name": "Zeynep Arslan, Owner's Representative",
        "subject": "Meeting minutes — Monthly progress review March 22",
        "body": (
            "Dear All,\n\n"
            "Attached are the approved meeting minutes from the Monthly Progress Review "
            "held on March 22, 2026.\n\n"
            "Key decisions:\n"
            "- Excavation sequence for Level -16m approved\n"
            "- Additional vibration monitoring sensors approved for installation\n"
            "- Next monthly review scheduled for April 19, 2026\n\n"
            "Please review and notify me of any corrections within 5 business days.\n\n"
            "Zeynep Arslan\nOwner's Representative"
        ),
        "intended_category": "FYI",
    },
    # --- ARCHIVE (5 emails) ---
    {
        "sender_name": "ProBuild Software Sales",
        "subject": "Exclusive offer: 40% off ProBuild Project Management Suite",
        "body": (
            "Dear Construction Professional,\n\n"
            "Are you still managing your projects with spreadsheets? It's time to upgrade!\n\n"
            "ProBuild Project Management Suite offers:\n"
            "- Real-time schedule tracking\n"
            "- Automated daily reports\n"
            "- BIM integration\n"
            "- Mobile field reporting\n\n"
            "For a limited time, get 40% off your first year subscription. "
            "Use code BUILDNOW40 at checkout.\n\n"
            "Start your free trial today at www.probuild-fake.com\n\n"
            "The ProBuild Team"
        ),
        "intended_category": "ARCHIVE",
    },
    {
        "sender_name": "HR Department",
        "subject": "Annual benefits enrollment reminder — deadline April 10",
        "body": (
            "Dear Employee,\n\n"
            "This is a reminder that the annual benefits enrollment period is open until "
            "April 10, 2026. Please log in to the HR portal to review and update your "
            "selections.\n\n"
            "Changes available:\n"
            "- Health insurance plan selection\n"
            "- Dental and vision coverage\n"
            "- Life insurance beneficiary updates\n"
            "- Retirement contribution adjustments\n\n"
            "If you do not make changes, your current selections will carry forward.\n\n"
            "Human Resources Department"
        ),
        "intended_category": "ARCHIVE",
    },
    {
        "sender_name": "Mehmet Gunes, Colleague",
        "subject": "FW: Funny construction fails compilation 2026",
        "body": (
            "Haha you have to see this!\n\n"
            "Check out this hilarious compilation of construction fails: "
            "[link removed]\n\n"
            "The one at 2:35 with the excavator is gold 😂\n\n"
            "- Mehmet"
        ),
        "intended_category": "ARCHIVE",
    },
    {
        "sender_name": "Industry Newsletter",
        "subject": "Construction Weekly Digest — March 28, 2026",
        "body": (
            "CONSTRUCTION WEEKLY DIGEST\n"
            "March 28, 2026\n\n"
            "Top Stories:\n"
            "- Global cement prices rise 8% in Q1 2026\n"
            "- New OSHA regulations for high-rise construction take effect May 1\n"
            "- AI-powered project scheduling: promises and pitfalls\n"
            "- Turkey's mega-project pipeline: $45B in infrastructure planned for 2026-2030\n\n"
            "Read more at www.constructionweekly-fake.com\n\n"
            "You are receiving this because you subscribed to Construction Weekly."
        ),
        "intended_category": "ARCHIVE",
    },
    {
        "sender_name": "IT Support",
        "subject": "Scheduled server maintenance — Saturday March 29, 02:00-06:00",
        "body": (
            "Dear All,\n\n"
            "Please be advised that the company file server will undergo scheduled "
            "maintenance this Saturday, March 29, from 02:00 to 06:00 (Istanbul time).\n\n"
            "During this window:\n"
            "- Network shared drives will be unavailable\n"
            "- Email will continue to function normally\n"
            "- VPN access may be intermittent\n\n"
            "Please save any work from shared drives before the maintenance window.\n\n"
            "IT Support Team"
        ),
        "intended_category": "ARCHIVE",
    },
]


def main():
    parser = argparse.ArgumentParser(description="Send 20 CEM scenario test emails to yourself.")
    parser.add_argument("--dry-run", action="store_true", help="Preview emails without sending.")
    parser.add_argument("--delay", type=int, default=10, help="Seconds between emails (default: 10).")
    args = parser.parse_args()

    load_dotenv()

    email_address = os.getenv("EMAIL_ADDRESS", "").strip()
    email_password = os.getenv("EMAIL_PASSWORD", "").strip()

    if not email_address or not email_password:
        print("ERROR: EMAIL_ADDRESS and EMAIL_PASSWORD must be set in .env")
        sys.exit(1)

    print(f"Scenario: Istanbul Kadikoy Metro Station — Deep Excavation Support System")
    print(f"Emails to send: {len(SCENARIO_EMAILS)}")
    print(f"Target inbox: {email_address}")
    print()

    # Summary by category
    categories = {}
    for em in SCENARIO_EMAILS:
        cat = em["intended_category"]
        categories[cat] = categories.get(cat, 0) + 1
    for cat in ("URGENT", "ACTION", "FYI", "ARCHIVE"):
        print(f"  {cat}: {categories.get(cat, 0)} emails")
    print()

    if args.dry_run:
        print("=== DRY RUN — no emails will be sent ===\n")
        for i, em in enumerate(SCENARIO_EMAILS, 1):
            print(f"  [{i:>2}] Category: {em['intended_category']}")
            print(f"       From: {em['sender_name']}")
            print(f"       Subject: {em['subject']}")
            print(f"       Body: {em['body'][:80]}...")
            print()
        return

    confirm = input(f"Send {len(SCENARIO_EMAILS)} test emails to {email_address}? [y/N] ")
    if confirm.lower() != "y":
        print("Cancelled.")
        return

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
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
        print(f"\nDone! {len(SCENARIO_EMAILS)} scenario emails sent to {email_address}.")
        print("Wait a minute, then run: py reader.py")

    except smtplib.SMTPAuthenticationError:
        print("ERROR: SMTP authentication failed. Check your App Password in .env")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
