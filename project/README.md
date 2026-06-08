# CEM501 Construction Communication Agent

**CEM501 Communication Skills for CEM -- Spring 2026**
**Bogazici University | Dr. Eyuphan Koc**

---

## Student Information

- **Name:** Furkan
- **Email:** furkan.cem501@gmail.com

---

## Description

An AI-powered communication agent for construction project managers that automates email triage, drafts professional replies, and sends them with human-in-the-loop safety guardrails. The agent reads incoming project emails via IMAP, classifies them semantically by urgency (URGENT/ACTION/FYI/ARCHIVE) using OpenAI (gpt-4o-mini), generates context-aware draft responses, and supports silent Telegram text/voice triage into message history. Built with a modular architecture that enables independent testing and incremental improvement.

---

## Architecture Overview

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system architecture, component descriptions, data flow diagram, and design decisions.

**High-level summary:** A modular pipeline that reads incoming emails via IMAP, classifies them by urgency using semantic LLM triage, drafts context-aware responses via OpenAI, and sends them after explicit user approval -- with persistent SQLite memory for contacts and message history.

**LLM cache:** Semantic classification, email previews, and draft replies are cached locally under `logs/`. Refreshing the live inbox reuses cached LLM results for emails with the same sender, subject, and body, so only new or changed emails require new OpenAI calls.

---

## Setup Instructions

### 1. Clone the repository

```powershell
git clone https://github.com/AFU-V1/CEM501.git
cd CEM501
```

### 2. Create a virtual environment

```powershell
py -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
Copy-Item project\.env.example project\.env
# Edit project\.env with your actual API keys and credentials
```

### 5. Verify setup

```powershell
py -c "import openai; print('Setup OK')"
```

---

## How to Run

```powershell
cd project

# Run the email agent (full pipeline with send capability)
py agent.py

# Run in dry-run mode (show drafts without sending)
py agent.py --dry-run

# Show triage summary only (no drafting)
py agent.py --summary

# Run the daily digest generator (hardcoded samples)
py digest.py

# Run the daily digest with live inbox data
py digest.py --live

# Run the Telegram bot (silent text/voice triage into Message History)
py run_telegram_bot.py

# Run the scheduler (single check)
py scheduler.py

# Run the scheduler in continuous mode
py scheduler.py --loop

# View memory database status
py -m memory.memory

# Run the web dashboard for the final demo
py dashboard_app.py
# Open http://127.0.0.1:5000
# Use "Load Demo Snapshot" and "Approve Dry Run" for a safe live demo.
```

---

## Milestones Completed

- [x] **M0:** Environment setup and API key configuration
- [x] **M1:** Prompt template library (`templates/` -- RFI, daily report, delay notice)
- [x] **M2:** Email reader and triage module (`reader.py` -- IMAP + semantic LLM classification)
- [x] **M3:** Daily digest generator (`digest.py` -- OpenAI summarization + HTML output)
- [x] **M4:** Email agent v1 (`agent.py` -- read + triage + draft + send with 4 guardrails)
- [x] **M5:** Architecture documentation (`ARCHITECTURE.md` -- components, data flow, 4 ADRs)
- [x] **M6:** Multi-channel integration (`channels/` -- Email + Telegram with shared triage)
- [x] **M7:** Persistent memory + scheduling (`memory/` + `scheduler.py` + `agent.log`)
- [x] **M8:** Progress presentation completed
- [ ] **M9:** Final demo package prepared; student-written `REFLECTION.md` must be finalized before submission

---

## AI Tools Used

| Tool / Model | How It Was Used |
|--------------|-----------------|
| OpenAI (gpt-4o-mini) | Semantic email/Telegram triage, email draft generation, daily digest summarization |
| OpenAI (gpt-4o-mini-transcribe) | Telegram voice-message transcription |
| Gemini CLI / Antigravity | Building and debugging the agent pipeline, generating architecture documentation |
| Cursor | Primary IDE for development and code review |

---

## Project Structure

```
project/
  agent.py              # M4: Email agent v1 (main pipeline)
  reader.py             # M2: IMAP email reader + triage engine
  digest.py             # M3: Daily digest generator
  scheduler.py          # M7: Task scheduler with retry logic
  dashboard_app.py      # Web dashboard entry point
  dashboard_store.py    # Dashboard state and API helpers
  run_telegram_bot.py   # M6: Telegram bot entry point
  test_bot.py           # Telegram bot echo test
  ARCHITECTURE.md       # M5: System architecture document
  README.md             # This file
  .env                  # API keys and credentials (not committed)
  .env.example          # Template for .env
  requirements.txt      # Python dependencies
  channels/
    base.py             # M6: Channel base class (interface)
    email_channel.py    # M6: Email channel implementation
    telegram_channel.py # M6: Telegram channel implementation
  memory/
    memory.py           # M7: SQLite persistence module
    memory.db           # M7: Agent database (auto-generated)
  templates/
    rfi_drafter.md      # M1: RFI prompt template
    daily_report.md     # M1: Daily report prompt template
    delaynotice_report.md # M1: Delay notice prompt template
  logs/
    agent.log           # M7: Agent operation log
    triage_cache.json   # Runtime cache for semantic LLM triage (not committed)
    email_summary_cache.json # Runtime cache for inbox preview summaries (not committed)
    draft_cache.json     # Runtime cache for generated email drafts (not committed)
    sent_log.txt        # M4: Sent email audit trail
  web/
    templates/          # Dashboard HTML shell
    static/             # Dashboard CSS and JS
  tests/
    (test scripts and results)
```

---

## Reflection

See [REFLECTION.md](REFLECTION.md) for the required reflection structure. The final 500-800 word reflection must be written in Furkan's own words before submission.

---

*CEM501 - Spring 2026 - Dr. Eyuphan Koc - Bogazici University*
