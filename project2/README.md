# CEM501 Construction Communication Agent

**CEM501 Communication Skills for CEM -- Spring 2026**
**Bogazici University | Dr. Eyuphan Koc**

---

## Student Information

- **Name:** Furkan
- **Email:** furkan.cem501@gmail.com

---

## Description

An AI-powered communication agent for construction project managers that automates email triage, drafts professional replies, and sends them with human-in-the-loop safety guardrails. The agent reads incoming project emails via IMAP, classifies them by urgency (URGENT/ACTION/FYI/ARCHIVE) using a multi-pass keyword engine, generates context-aware draft responses using Google Gemini 2.5 Flash, and supports multi-channel communication through both Email and Telegram. Built with a modular architecture that enables independent testing and incremental improvement.

---

## Architecture Overview

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system architecture, component descriptions, data flow diagram, and design decisions.

**High-level summary:** A modular pipeline that reads incoming emails via IMAP, classifies them by urgency using keyword-based triage, drafts context-aware responses via Gemini LLM, and sends them after explicit user approval -- with persistent SQLite memory for contacts and message history.

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/CEM501.git
cd CEM501
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your actual API keys and credentials
```

### 5. Verify setup

```bash
python -c "from google import genai; print('Setup OK')"
```

---

## How to Run

```bash
# Run the email agent (full pipeline with send capability)
python agent.py

# Run in dry-run mode (show drafts without sending)
python agent.py --dry-run

# Show triage summary only (no drafting)
python agent.py --summary

# Run the daily digest generator (hardcoded samples)
python digest.py

# Run the daily digest with live inbox data
python digest.py --live

# Run the Telegram bot
python run_telegram_bot.py

# Run the scheduler (single check)
python scheduler.py

# Run the scheduler in continuous mode
python scheduler.py --loop

# View memory database status
python -m memory.memory
```

---

## Milestones Completed

- [x] **M0:** Environment setup and API key configuration
- [x] **M1:** Prompt template library (`templates/` -- RFI, daily report, delay notice)
- [x] **M2:** Email reader and triage module (`reader.py` -- IMAP + keyword classification)
- [x] **M3:** Daily digest generator (`digest.py` -- Gemini summarization + HTML output)
- [x] **M4:** Email agent v1 (`agent.py` -- read + triage + draft + send with 4 guardrails)
- [x] **M5:** Architecture documentation (`ARCHITECTURE.md` -- components, data flow, 4 ADRs)
- [x] **M6:** Multi-channel integration (`channels/` -- Email + Telegram with shared triage)
- [x] **M7:** Persistent memory + scheduling (`memory/` + `scheduler.py` + `agent.log`)
- [ ] **M8:** Progress presentation
- [ ] **M9:** Final demo + reflection document

---

## AI Tools Used

| Tool / Model | How It Was Used |
|--------------|-----------------|
| Google Gemini 2.5 Flash | Email draft generation, daily digest summarization, Telegram response drafting |
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
    sent_log.txt        # M4: Sent email audit trail
  tests/
    (test scripts and results)
```

---

## Reflection

See [REFLECTION.md](REFLECTION.md) for the full project reflection, including lessons learned, challenges encountered, and thoughts on AI-assisted development.

---

*CEM501 - Spring 2026 - Dr. Eyuphan Koc - Bogazici University*
