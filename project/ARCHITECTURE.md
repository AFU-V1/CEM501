# System Architecture

**CEM501 Communication Skills for CEM -- Spring 2026**  
**Project: Construction Communication Agent**

---

## System Overview

The system is a construction communication agent for project managers. It is designed around a shared processing pipeline and channel adapters so the core logic stays independent from Email and Telegram while still supporting persistent memory, draft generation, reminders, and message logging.

### Architecture Diagram

```text
+-------------------+
|     Scheduler     |
| reminders/summary |
+---------+---------+
          |
          v
+-------------------+   +-------------------+   +----------------------+
|  Email Adapter    |   |   Demo Adapter    |   |  Telegram Adapter    |
| email_channel.py  |   | demo_channel.py   |   | telegram_channel.py  |
+---------+---------+   +---------+---------+   +----------+-----------+
          \                   |                         /
           \                  |                        /
            v                 v                       v
          +-------------------------+
          | Shared Pipeline         |
          | pipeline.py             |
          | receive -> classify ->  |
          | load history -> draft   |
          | -> send/save            |
          +-----------+-------------+
                      |
        +-------------+-------------+
        |                           |
        v                           v
+---------------+          +----------------+
| classifier.py |          | drafter.py     |
| bucket + type |          | reply drafts   |
+---------------+          +----------------+
                      |
                      v
              +----------------+
              | memory.py      |
              | SQLite memory  |
              | contacts       |
              | messages       |
              | tasks          |
              +----------------+
```

---

## Components

### Reader / Email Adapter
**Files:** `reader.py`, `channels/email_channel.py`  
**Responsibility:** Read incoming emails from IMAP, normalize them into a shared message structure, and send reviewed replies through SMTP.

### Demo Adapter
**Files:** `channels/demo_channel.py`, `scenarios/demo_scenarios.json`  
**Responsibility:** Provide a reliable live-demo path using realistic construction scenarios. This is the safest presentation channel because it removes inbox and network dependency while still exercising the same shared pipeline.

### Telegram Adapter
**Files:** `channels/telegram_channel.py`, `run_telegram_bot.py`  
**Responsibility:** Receive Telegram messages through polling, pass them into the shared pipeline, and reply with the classification and drafted response.

### Shared Pipeline
**File:** `pipeline.py`  
**Responsibility:** Central workflow independent from channel implementation. It classifies messages, stores incoming history, loads prior context, drafts the reply, logs the result, and creates follow-up tasks when needed.

### Classifier
**File:** `classifier.py`  
**Responsibility:** Assign both a workflow bucket (`URGENT`, `ACTION`, `FYI`, `ARCHIVE`) and a construction message type (`RFI`, `DELAY`, `APPROVAL`, `SITE_ISSUE`, `SAFETY`, `PROCUREMENT`, `REPORT`).

### Drafter
**File:** `drafter.py`  
**Responsibility:** Generate a construction-appropriate reply using OpenAI with recent communication history as context. Fallback responses are used if the API is unavailable.

### Memory
**File:** `memory.py`  
**Responsibility:** Persist contacts, message history, and scheduled tasks in SQLite for auditability and follow-up tracking.

### Scheduler
**File:** `scheduler.py`  
**Responsibility:** Check overdue tasks, print a morning summary, and print a weekly communication summary.

---

## Data Flow

1. A channel adapter receives a message.
2. The adapter normalizes the message into a shared dict format.
3. `pipeline.py` classifies the message.
4. `memory.py` stores the incoming message and loads recent history for that contact.
5. `drafter.py` generates a reply draft.
6. The channel sends or displays the reply.
7. `memory.py` stores the outgoing message.
8. `pipeline.py` creates a follow-up task for categories like RFI, approval, procurement, delay, or site issue.
9. `scheduler.py` reports pending and overdue tasks for reminders and demo summaries.

---

## API Keys and Configuration

Secrets are expected in `.env` and should never be committed.

- `OPENAI_API_KEY`
- `EMAIL_ADDRESS`
- `EMAIL_PASSWORD`
- `IMAP_SERVER`
- `SMTP_SERVER`
- `SMTP_PORT`
- `TELEGRAM_BOT_TOKEN`

---

## Current Limitations

- Email is the main fully reviewed send path.
- The default presentation path is now the demo channel because it is more reliable for the Week 14 rubric.
- Telegram uses the same shared logic for classification, drafting, and memory, but it is event-driven rather than run from `agent.py`.
- Classification is rule-based rather than LLM-based, which is acceptable for a class demo but less flexible than a production classifier.
