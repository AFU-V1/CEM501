# System Architecture — CEM501 Communication Agent

**CEM501 Communication Skills for CEM -- Spring 2026**
**Milestone M5 Deliverable**

---

## System Overview

This system is a personal AI communication agent designed for construction project managers. It reads incoming emails via IMAP, classifies them by urgency using a keyword-based triage engine, drafts professional replies using OpenAI LLMs, and sends approved drafts via SMTP -- all with mandatory human-in-the-loop confirmation. The agent also integrates with Telegram for real-time messaging and uses SQLite for persistent memory across sessions. The design philosophy is **modular and incremental**: each component does one job, can be tested independently, and was built in the order prescribed by the course milestones (M0-M9).

### Architecture Diagram

```
                        +-----------+
                        | Scheduler |  (triggers pipeline on interval)
                        | scheduler |  scheduler.py
                        +-----+-----+
                              |
                              v
+-------+    +----------+         +-----------+
| IMAP  |--->|  Reader  |-------->| Classifier|
| Inbox |    | reader.py|  (raw   | (keyword  |
+-------+    +----------+  email) |  triage)  |
                                  +-----------+
                                       |
                            (category + email)
                                       |
                                       v
+----------+        +-----------+        +---------+
|  Memory  |<------>|  Drafter  |------->| Sender  |
| memory/  | context| (OpenAI    | (draft)| (SMTP)  |
| memory.db| + logs |  LLM)     |        +----+----+
+----------+        +-----------+             |
                                              v
+-------------------+                  +----------+
| Telegram Channel  |                  |   SMTP   |
| channels/         |                  |  Outbox  |
| telegram_channel  |                  +----------+
+-------------------+
```

**Data flow:** Scheduler wakes Reader on a timer. Reader connects to IMAP, fetches unread emails. Classifier (embedded in Reader via `triage_email()`) labels each email as URGENT, ACTION, FYI, or ARCHIVE. Drafter generates a reply using OpenAI, pulling context from Memory. Sender delivers the approved draft via SMTP. Memory logs every interaction for future reference.

---

## Components

### Reader
- **Responsibility:** Connects to the IMAP inbox, fetches recent emails, parses headers and body, and classifies each email by urgency.
- **Input:** IMAP credentials from `.env`; mailbox name (INBOX)
- **Output:** List of email dicts with fields: sender, subject, date, body, category, keyword
- **File:** `reader.py`
- **Key dependencies:** `imaplib`, `email` (standard library), `python-dotenv`

### Classifier (Triage Engine)
- **Responsibility:** Applies a multi-pass keyword matching algorithm to categorize emails into URGENT, ACTION, FYI, or ARCHIVE.
- **Input:** Email subject, sender, and body text
- **Output:** Tuple of (category, matched_keyword)
- **File:** `reader.py` (function: `triage_email()`)
- **Key dependencies:** None (pure Python logic)

### Drafter
- **Responsibility:** Takes a classified email and generates a professional reply using OpenAI (gpt-4o-mini). Falls back to template-based responses if the LLM is unavailable.
- **Input:** Email data dict with category, subject, sender, body
- **Output:** Draft reply text (string)
- **File:** `agent.py` (function: `draft_reply()`), also used in `channels/telegram_channel.py`
- **Key dependencies:** `openai` (OpenAI API)

### Sender
- **Responsibility:** Sends approved drafts via SMTP with TLS. Implements four safety guardrails: confirmation prompt, recipient validation, content check, and rate limiting.
- **Input:** Recipient address, subject, body, dry-run flag
- **Output:** Boolean (sent or skipped)
- **File:** `agent.py` (functions: `send_email()`, `_do_send()`)
- **Key dependencies:** `smtplib` (standard library)

### Memory
- **Responsibility:** Stores contacts, message history, and scheduled tasks in a SQLite database. Provides context for future interactions and an audit trail of all communications.
- **Input:** Contact data, message data, task data
- **Output:** Query results (contacts, messages, tasks)
- **File:** `memory/memory.py`
- **Key dependencies:** `sqlite3` (standard library)

### Scheduler
- **Responsibility:** Runs periodic checks for overdue follow-ups, generates morning summaries, and manages task reminders. Supports single-run and continuous loop modes.
- **Input:** Database queries (pending/overdue tasks)
- **Output:** Console output + log entries
- **File:** `scheduler.py`
- **Key dependencies:** `schedule` library

### Telegram Channel
- **Responsibility:** Receives messages via the Telegram Bot API, classifies them using the triage engine, drafts responses via OpenAI, and replies in real-time.
- **Input:** Telegram messages (Bot API polling)
- **Output:** Telegram replies with classification + drafted response
- **File:** `channels/telegram_channel.py`
- **Key dependencies:** `python-telegram-bot`

### Email Channel
- **Responsibility:** Wraps the IMAP/SMTP logic into a Channel abstraction for uniform multi-channel handling.
- **Input:** Same as Reader (IMAP credentials)
- **Output:** Standardized message dicts
- **File:** `channels/email_channel.py`

### Digest Generator
- **Responsibility:** Groups triaged emails by category and produces a formatted morning digest with LLM-generated summaries for URGENT and ACTION items.
- **Input:** List of email dicts (live or hardcoded samples)
- **Output:** Formatted text or HTML digest
- **File:** `digest.py`
- **Key dependencies:** `openai` (OpenAI API)

---

## Data Flow

1. **Scheduler** triggers the pipeline at a configured interval (or user runs `agent.py` manually).
2. **Reader** connects to the IMAP server, fetches the 20 most recent emails, and parses headers + body.
3. **Classifier** (`triage_email()`) runs a three-pass keyword analysis on each email to assign a category: URGENT, ACTION, FYI, or ARCHIVE.
4. **Agent** filters for actionable emails (URGENT + ACTION) and passes each to the Drafter.
5. **Drafter** calls OpenAI (gpt-4o-mini) with a structured prompt to generate a professional reply. On failure, it falls back to pre-written templates.
6. **Sender** displays the draft for human review with all warnings, then sends via SMTP after explicit `y` confirmation.
7. **Memory** logs the sent message for future reference.
8. **Telegram Channel** runs a parallel pipeline: incoming messages are classified and replied to in real-time.

---

## Design Decisions (ADR-style)

### ADR 1: Keyword-Based Triage Instead of LLM Classification

**Decision:** Use a multi-pass keyword matching algorithm for email classification instead of calling the LLM for every email.

**Context:** Calling the OpenAI API for each of the 20 fetched emails would be slow (3-5 seconds per call) and consume API quota. The keyword approach processes all 20 emails in under 1 second with zero API cost. Construction project emails follow predictable patterns: "stop work", "RFI", "submittal", "meeting minutes" are reliable signals. The three-pass design (junk words first, compound keywords second, single keywords third) handles edge cases like "meeting minutes" not falsely matching the single keyword "review".

**Consequences:** Classification is fast, free, and deterministic. However, it may miss novel email types that do not contain expected keywords. Future improvement: use LLM classification as a fallback for emails that fall to the default "ARCHIVE" category.

### ADR 2: Human-in-the-Loop Mandatory Confirmation

**Decision:** All draft replies must be explicitly approved by the user before sending. No automatic sends.

**Context:** In construction communication, a misdirected or incorrect email can have legal and financial consequences. LLMs can hallucinate project facts, use inappropriate tone, or address the wrong issue. Research shows misdirected email is the #1 reported data breach type in the UK (16% of all ICO-reported incidents). The confirmation gate (`y/n/e` prompt) is the agent's most critical safety feature.

**Consequences:** The agent cannot run fully autonomously -- it always requires a human at the keyboard for sends. This is slower but prevents costly mistakes. The `--dry-run` mode allows the full pipeline to run unattended for testing and digest generation.

### ADR 3: OpenAI (gpt-4o-mini) as the LLM Provider

**Decision:** Use OpenAI (gpt-4o-mini) for all LLM tasks (drafting, summarization) instead of Google Gemini or Anthropic Claude.

**Context:** The project originally planned to use Anthropic's Claude API. During development, the OpenAI API proved more accessible and offered high quality for email drafting tasks. The `gpt-4o-mini` model is optimized for speed and cost, which matters when generating many drafts.

**Consequences:** Single provider dependency. If OpenAI is unavailable, the agent falls back to pre-written templates. All LLM calls are wrapped in try/except with fallback behavior. Switching providers would require changing only the `draft_reply()` and `summarize_email()` functions.

### ADR 4: SQLite for Persistent Memory

**Decision:** Use SQLite as the persistence layer instead of JSON files or a client-server database.

**Context:** SQLite requires zero configuration, ships with Python's standard library, stores everything in a single portable file (`memory.db`), and handles concurrent reads safely. For a personal communication agent with one user, SQLite's limitations (single-writer) are irrelevant. The schema (contacts, message_history, scheduled_tasks) mirrors what a PM already tracks mentally.

**Consequences:** No server setup needed. Database file can be backed up by copying a single file. Limited to one concurrent writer, but this is acceptable for a single-user agent.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| **LLM API timeout / 403** | Logged as ERROR; fallback template used for drafts; agent continues processing remaining emails |
| **IMAP connection failure** | RuntimeError raised; logged; agent exits with error code 1 |
| **SMTP auth failure** | Logged as ERROR; user notified; draft is preserved (can retry) |
| **Rate limit exceeded** | Send blocked; WARNING logged; user notified |
| **Database locked** | Retry with exponential backoff (3 attempts, 1s/2s/4s delay + jitter) |
| **Unknown email format** | `extract_body_preview()` gracefully returns empty string; email classified as ARCHIVE |

---

## API Keys & Configuration

All secrets are stored in `.env` (never committed). See `.env.example` for required variables:

| Variable | Purpose |
|----------|---------|
| `EMAIL_ADDRESS` | IMAP/SMTP email account |
| `EMAIL_PASSWORD` | App-specific password (Gmail) |
| `IMAP_SERVER` | Incoming mail server (default: imap.gmail.com) |
| `SMTP_SERVER` | Outgoing mail server (default: smtp.gmail.com) |
| `SMTP_PORT` | SMTP port (default: 587 for TLS) |
| `OPENAI_API_KEY` | OpenAI API access |
| `TELEGRAM_BOT_TOKEN` | Telegram bot for messaging channel |

---

## Future Extensions

- [ ] **Attachment handling:** Parse PDF attachments (RFI responses, submittals) and include content in classification context
- [ ] **LLM classification fallback:** For emails that default to ARCHIVE, run a second pass with OpenAI to catch novel email types
- [ ] **Web dashboard:** Build a simple Flask/Streamlit UI for reviewing drafts, managing contacts, and viewing message history
- [ ] **Multi-language support:** Add Turkish language handling for cross-cultural project communication on Istanbul-based projects

---

*CEM501 - Spring 2026 - Dr. Eyuphan Koc - Bogazici University*
