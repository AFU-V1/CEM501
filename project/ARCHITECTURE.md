# System Architecture — CEM501 Communication Agent

**CEM501 Communication Skills for CEM -- Spring 2026**
**Final M9 Architecture Deliverable**

---

## System Overview

This system is a personal AI communication agent designed for construction project managers. It reads incoming emails via IMAP, classifies them by urgency using OpenAI semantic triage, drafts professional replies using OpenAI LLMs, and sends approved drafts via SMTP -- all with mandatory human-in-the-loop confirmation. The agent also integrates with Telegram for real-time messaging and uses SQLite for persistent memory across sessions. The design philosophy is **modular and incremental**: each component does one job, can be tested independently, and was built in the order prescribed by the course milestones (M0-M9).

### Architecture Diagram

```
+------------+      +-----------+      +------------+      +--------------+
| IMAP Inbox |----->| Reader    |----->| Semantic   |----->| OpenAI       |
| Gmail      |      | reader.py |      | LLM Triage |      | Drafter      |
+------------+      +-----------+      +------------+      +------+-------+
                                                                  |
                                                                  v
                                                        +------------------+
                                                        | Web Dashboard    |
                                                        | Review Queue     |
                                                        | dashboard_app.py |
                                                        +----+--------+----+
                                                             |        |
                                            demo dry-run/send |        | daily reports
                                                             v        v
                                                      +----------+  +----------+
                                                      | SMTP     |  | Digest   |
                                                      | Sender   |  | Builder  |
                                                      +----+-----+  +----+-----+
                                                           |             |
                                                           v             v
                                                      +----------------------+
                                                      | SQLite Memory        |
                                                      | contacts/messages/   |
                                                      | tasks + audit trail  |
                                                      +----+-------------+---+
                                                           ^             ^
                                                           |             |
                                                  +--------+---+   +-----+------+
                                                  | Scheduler  |   | Telegram   |
                                                  | scheduler  |   | Channel    |
                                                  +------------+   +------------+
```

**Data flow:** The Reader connects to IMAP and fetches recent project emails. The Classifier (embedded in Reader via `triage_email()`) first checks the local semantic triage cache; if the same sender, subject, and body were already classified, it reuses that result. Only new or changed messages are sent to OpenAI for semantic classification as URGENT, ACTION, FYI, or ARCHIVE. Inbox preview summaries and generated review drafts are cached the same way, so repeated dashboard refreshes do not resend unchanged emails to the LLM. Actionable messages are placed into the Web Dashboard review queue. A user can edit, reject, approve as a demo dry run, or approve for SMTP sending. Approved activity is logged to SQLite memory. Scheduler, digest generation, and Telegram use the same memory and triage foundations.

---

## Components

### Reader
- **Responsibility:** Connects to the IMAP inbox, fetches recent emails, parses headers and body, and classifies each email by urgency.
- **Input:** IMAP credentials from `.env`; mailbox name (INBOX)
- **Output:** List of email dicts with fields: sender, subject, date, body, category, keyword/reason
- **File:** `reader.py`
- **Key dependencies:** `imaplib`, `email` (standard library), `python-dotenv`

### Classifier (Semantic Triage Engine)
- **Responsibility:** Uses OpenAI (gpt-4o-mini) to classify emails into URGENT, ACTION, FYI, or ARCHIVE based on construction-management meaning, not just surface words.
- **Input:** Email subject, sender, and body text
- **Output:** Tuple of (category, semantic_reason). The existing `keyword` field stores the LLM reason for backward compatibility.
- **File:** `reader.py` (function: `triage_email()`)
- **Key dependencies:** `openai`, `python-dotenv`
- **Cache:** `logs/triage_cache.json` stores category, reason, confidence, source, and model for each sender/subject/body hash. The file is ignored by Git because it contains runtime inbox-derived data.

### Drafter
- **Responsibility:** Takes a classified email and generates a professional reply using OpenAI (gpt-4o-mini). Falls back to template-based responses if the LLM is unavailable.
- **Input:** Email data dict with category, subject, sender, body
- **Output:** Draft reply text (string)
- **File:** `agent.py` (function: `draft_reply()`), also used in `channels/telegram_channel.py`
- **Key dependencies:** `openai` (OpenAI API)
- **Cache:** `logs/draft_cache.json` stores generated drafts by category/sender/subject/body hash to avoid repeated draft-generation calls for unchanged emails.

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

### Web Dashboard
- **Responsibility:** Provides a modern GUI (Flask + Vanilla HTML/JS/CSS) to monitor agent health, triage emails, review/approve/delete drafts in the queue, view memory (contacts and message history), and generate daily reports based on selected messages.
- **Input:** Agent memory (`memory.db`), live IMAP inbox
- **Output:** JSON API, rendered HTML
- **File:** `dashboard_app.py`, `dashboard_store.py`, `web/`
- **Key dependencies:** `Flask`, `sqlite3`

### Digest Generator
- **Responsibility:** Groups triaged emails by category and produces a formatted morning digest with LLM-generated summaries for URGENT and ACTION items.
- **Input:** List of email dicts (live or hardcoded samples)
- **Output:** Formatted text or HTML digest
- **File:** `digest.py`
- **Key dependencies:** `openai` (OpenAI API)
- **Cache:** `logs/email_summary_cache.json` stores one-sentence summaries by email body hash.

---

## Data Flow

1. **Scheduler** triggers the pipeline at a configured interval (or user runs `agent.py` manually).
2. **Reader** connects to the IMAP server, fetches the 20 most recent emails, and parses headers + body.
3. **Classifier** (`triage_email()`) checks `logs/triage_cache.json`; cache hits return immediately, and cache misses send subject, sender, and body excerpt to OpenAI to receive JSON with category, reason, and confidence.
4. **Agent** filters for actionable emails (URGENT + ACTION) and passes each to the Drafter.
5. **Drafter** checks `logs/draft_cache.json`; cache misses call OpenAI (gpt-4o-mini) with a structured prompt to generate a professional reply. On failure, it falls back to pre-written templates.
6. **Sender** displays the draft for human review with all warnings, then sends via SMTP after explicit `y` confirmation.
7. **Memory** logs the sent message for future reference.
8. **Web Dashboard** exposes the review queue, health status, memory, daily report builder, and demo-safe dry-run approval path.
9. **Telegram Channel** runs a parallel pipeline: incoming messages are classified, drafted with OpenAI, replied to in real-time, and logged to memory.

---

## Design Decisions (ADR-style)

### ADR 1: Semantic LLM Triage Instead of Keyword Matching

**Decision:** Use OpenAI (gpt-4o-mini) for email classification instead of relying on keyword matching.

**Context:** Construction emails often hide urgency in the body rather than the subject line. A routine-looking report may include failed concrete test results, legal exposure, critical path risk, or a hidden deadline. Keyword matching is fast, but it can miss semantic priority and overreact to isolated words like "safety" in a routine report.

**Consequences:** Classification is more context-aware and easier to explain in the final demo. It is slower on first pass and depends on API availability, so triage, summaries, and drafts are cached locally and reused on later refreshes. If the LLM call fails or returns invalid JSON, the agent labels the message as ACTION with `review manually` so a potentially important message is reviewed instead of silently archived.

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
| **LLM triage timeout / invalid JSON** | Email classified as ACTION with `review manually` so it enters manual review |
| **LLM draft timeout / 403** | Logged as ERROR; fallback template used for drafts; agent continues processing remaining emails |
| **IMAP connection failure** | RuntimeError raised; logged; agent exits with error code 1 |
| **SMTP auth failure** | Logged as ERROR; user notified; draft is preserved (can retry) |
| **Rate limit exceeded** | Send blocked; WARNING logged; user notified |
| **Database locked** | Retry with exponential backoff (3 attempts, 1s/2s/4s delay + jitter) |
| **Unknown email format** | `extract_body_preview()` gracefully returns empty string; LLM triage still uses sender and subject |

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
- [ ] **Confidence-aware routing:** Highlight low-confidence LLM classifications for manual review
- [x] **Web dashboard:** Build a simple Flask/Streamlit UI for reviewing drafts, managing contacts, and viewing message history
- [x] **Daily Report Generator:** Allow selecting messages from memory to compile a daily construction report draft.
- [ ] **Multi-language support:** Add Turkish language handling for cross-cultural project communication on Istanbul-based projects

---

*CEM501 - Spring 2026 - Dr. Eyuphan Koc - Bogazici University*
