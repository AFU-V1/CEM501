# CEM501 Construction Communication Agent

**CEM501 Communication Skills for CEM -- Spring 2026**
**Bogazici University | Dr. Eyuphan Koc**

---

## Student Information

- **Name:** Furkan
- **Email:** furkan.cem501@gmail.com

---

## Description

This project is a personal AI communication agent for construction project managers. It reads project emails through IMAP, classifies each message semantically with OpenAI into `URGENT`, `ACTION`, `FYI`, or `ARCHIVE`, drafts professional responses, and keeps human approval mandatory before any outbound email is sent.

The final demo workflow is dashboard-first. The dashboard shows a triage inbox, approval queue, message history, contacts, daily report builder, saved morning digests, saved daily reports, Cron Job rules, health indicators, and logs. Telegram text, voice, and photo messages are also supported: text is triaged silently, voice is transcribed then triaged, and photos are analyzed with OpenAI vision, stored in Message History, and queued as email drafts with the image attached.

All user-facing generated timestamps are normalized to Turkey time (`Europe/Istanbul`, TRT).

---

## Architecture Overview

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system architecture, data flow diagram, components, and design decisions. See [PROJECT_FLOW.md](PROJECT_FLOW.md) for a presentation-friendly end-to-end runtime map of the whole project.

High-level flow:

```text
IMAP inbox -> reader.py -> semantic LLM triage -> dashboard review queue
            -> OpenAI drafter -> human approval -> SMTP send/dry-run
            -> SQLite memory + logs

Telegram text/voice/photo -> triage/transcription/vision -> SQLite memory
                           -> optional dashboard email draft with attachment

Message History -> Daily Report Generator -> Review Queue -> SMTP send/dry-run
```

LLM cache files live under `logs/` and are ignored by Git. Repeated `Refresh Live Inbox` calls reuse cached triage, preview, and draft results for unchanged emails, so only new or changed messages are sent to OpenAI.

---

## Key Features

- Semantic LLM triage with OpenAI `gpt-4o-mini`
- Four categories: `URGENT`, `ACTION`, `FYI`, `ARCHIVE`
- Cached triage, inbox previews, and draft replies
- Human-in-the-loop approval queue
- Demo-safe `Approve Dry Run` path
- Editable draft, `To`, and `Cc` fields before approval
- SMTP email sending with recipient/content/rate-limit guardrails
- Attachment support for Telegram photos and photo-based daily reports
- SQLite memory for contacts, messages, and tasks
- Dashboard Message History and Contacts Manager
- Telegram text triage
- Telegram voice transcription with `gpt-4o-mini-transcribe`
- Telegram photo analysis with OpenAI vision
- Daily Report Generator from selected Message History rows
- Saved Daily Reports and saved Morning Digests
- Morning Digest summaries reuse the Triage Inbox preview text
- Cron Job panel for planned automated construction communication workflows
- Overdue task projection for unanswered old `URGENT`/`ACTION` emails
- TRT-normalized timestamps across dashboard, memory, logs, scheduler, and generated reports

---

## Setup Instructions

### 1. Clone the repository

```powershell
git clone https://github.com/AFU-V1/CEM501.git
cd CEM501\project
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
Copy-Item .env.example .env
notepad .env
```

Required:

```env
OPENAI_API_KEY=your_openai_api_key
EMAIL_ADDRESS=your_email@example.com
EMAIL_PASSWORD=your_email_app_password
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

Optional Telegram/photo settings:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
OPENAI_VISION_MODEL=gpt-4o-mini
TELEGRAM_PHOTO_FORWARD_TO=recipient@example.com
```

If `TELEGRAM_PHOTO_FORWARD_TO` is not set, Telegram photo email drafts default to `EMAIL_ADDRESS`; the recipient can still be edited in the dashboard before sending.

### 5. Verify setup

```powershell
py -m compileall -q .
py -c "import openai; import flask; print('Setup OK')"
```

---

## How to Run

Run commands from the `project/` directory.

```powershell
# Dashboard for final demo
py -m flask --app dashboard_app run --host 127.0.0.1 --port 5001
```

Open:

```text
http://127.0.0.1:5001
```

Recommended demo buttons:

- `Load Demo Snapshot` for stable sample emails
- `Refresh Live Inbox` for live IMAP + refreshed Telegram Message History
- `Approve Dry Run` for safe approval without sending real email
- `Reset Demo State` to restore the demo inbox/review queue

Other useful commands:

```powershell
# Email agent summary only
py agent.py --summary

# Email agent dry-run
py agent.py --dry-run

# Full email agent with real send capability
py agent.py

# Telegram bot for text, voice, and photo messages
py run_telegram_bot.py

# Scheduler one-time check
py scheduler.py

# Scheduler loop mode
py scheduler.py --loop

# Morning digest CLI
py digest.py

# Memory database status
py -m memory.memory
```

---

## Dashboard Demo Path

1. Start the dashboard on `http://127.0.0.1:5001`.
2. Start the Telegram bot in a second terminal if using Telegram.
3. Use `Refresh Live Inbox` or `Load Demo Snapshot`.
4. Show Triage Inbox categories and semantic reasons.
5. Open Approval Flow and show the original email, editable draft, editable recipient, optional `Cc`, warnings, dry-run, and real send button.
6. Send Telegram text/voice/photo and refresh the dashboard to show Message History.
7. Select Message History rows and generate a Daily Report.
8. If selected rows include Telegram photos, the report email queued from the Daily Report includes the photo attachments.
9. Show Morning Digest history and Daily Report history.
10. Show Cron Job rules and Overdue Tasks.

---

## Telegram Behavior

Normal Telegram messages are processed silently. The bot does not send automatic replies for text, voice, or photo messages.

- Text messages become `Telegram Text (CATEGORY)` rows in Message History.
- Voice messages are transcribed and stored as `Telegram Voice (CATEGORY)`.
- Photo messages are downloaded to `logs/telegram_media/`, analyzed by OpenAI vision, stored as `Telegram Photo (CATEGORY)`, and added to the Review Queue as a draft email with the image attached.

Telegram photo prompt:

```text
Analyze this construction site photo for a construction project manager. Write 2-4 concise sentences. Mention visible safety issues, delays, work progress, materials, equipment, document/RFI relevance, and any immediate action needed. Do not invent facts that are not visible.
```

If a caption is provided, it is appended as Telegram context before the vision request.

---

## Cron Job Rules

The dashboard Cron Job panel documents the planned automation rules:

- `08:00 daily`: Send the Daily Digest email every morning.
- `Before noon`: If no field update has arrived, remind site teams to send their status update.
- `16:00 daily`: If no field information has arrived by 4 PM, send a follow-up reminder.
- `End of day`: Automatically generate the Daily Report from incoming and outgoing messages and emails.
- `End of week`: Create a Weekly Report by combining the daily reports from that week.
- `End of month`: Create a Monthly Report by combining the weekly reports from that month.

---

## Submission Files

Required M9 files:

- `README.md` -- clone-and-run instructions and feature summary
- `ARCHITECTURE.md` -- final architecture documentation
- `PROJECT_FLOW.md` -- end-to-end runtime flow for demo/Q&A
- `REFLECTION.md` -- 500-800 words, written by Furkan
- `logs/agent.log` -- at least 3 email scenarios end-to-end
- Code repository pushed to GitHub before demo

Note: runtime cache files are ignored by Git. If `logs/agent.log` is ignored or not staged, force-add it before final submission:

```powershell
git add -f logs/agent.log
```

---

## Milestones Completed

- [x] **M0:** Environment setup and API key configuration
- [x] **M1:** Prompt template library
- [x] **M2:** Email reader and semantic LLM triage
- [x] **M3:** Daily digest generator
- [x] **M4:** Email agent with drafting, sending, and guardrails
- [x] **M5:** Architecture documentation
- [x] **M6:** Multi-channel integration with Email and Telegram
- [x] **M7:** SQLite memory, scheduler, and logging
- [x] **M8:** Progress presentation completed
- [x] **M9:** Final dashboard, docs, demo flow, and submission package prepared

---

## AI Tools Used

| Tool / Model | How It Was Used |
| --- | --- |
| OpenAI `gpt-4o-mini` | Semantic email/Telegram triage, email drafts, digest/report support, Telegram photo analysis |
| OpenAI `gpt-4o-mini-transcribe` | Telegram voice-message transcription |
| OpenAI Codex / ChatGPT | Development assistance, debugging, documentation support |
| Cursor | Code editing and review workflow |
| Gemini CLI / Antigravity | Earlier development and debugging support |

---

## Project Structure

```text
project/
  agent.py                    # Email agent pipeline and SMTP sender
  reader.py                   # IMAP reader and semantic triage
  digest.py                   # Morning digest generator
  scheduler.py                # Scheduler and Cron Job checks
  dashboard_app.py            # Flask dashboard API
  dashboard_store.py          # Dashboard state, reports, queue helpers
  time_utils.py               # Europe/Istanbul time normalization
  run_telegram_bot.py         # Telegram bot entry point
  ARCHITECTURE.md             # Final architecture document
  PROJECT_FLOW.md             # End-to-end runtime flow
  REFLECTION.md               # Student reflection
  README.md                   # This file
  requirements.txt            # Python dependencies
  channels/
    base.py
    email_channel.py
    telegram_channel.py       # Text, voice, and photo handling
  memory/
    memory.py                 # SQLite contacts/messages/tasks
    memory.db                 # Local generated DB
  templates/
    rfi_drafter.md
    daily_report.md
    delaynotice_report.md
  logs/
    agent.log                 # Submission log
    sent_log.txt              # Sent email audit trail
    dashboard_state.json      # Runtime dashboard state, ignored
    triage_cache.json         # Runtime triage cache, ignored
    email_summary_cache.json  # Runtime summary cache, ignored
    draft_cache.json          # Runtime draft cache, ignored
    telegram_media/           # Runtime Telegram photo attachments, ignored
  web/
    templates/
    static/
  tests/
```

---

## Reflection

See [REFLECTION.md](REFLECTION.md). The submitted reflection must remain in Furkan's own voice.

---

*CEM501 - Spring 2026 - Dr. Eyuphan Koc - Bogazici University*
