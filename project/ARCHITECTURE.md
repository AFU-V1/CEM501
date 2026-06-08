# System Architecture -- CEM501 Communication Agent

**CEM501 Communication Skills for CEM -- Spring 2026**
**Final M9 Architecture Deliverable**

---

## System Overview

This system is a personal AI communication agent for construction project managers. It reads incoming email through IMAP, receives Telegram text, voice, and photo messages, sends new or changed content to OpenAI for semantic triage, drafts email replies only when human approval is required, and stores all communication history locally. The dashboard is the main demo surface: it shows the triage inbox, approval flow, memory, daily reports, morning digests, Telegram-derived messages, and Cron Job planning.

The main design principle is controlled automation. The agent can classify, summarize, draft, transcribe, and analyze images, but outgoing email still requires explicit human approval or demo dry-run. All runtime-generated timestamps are normalized to **Europe/Istanbul (TRT)** so inbox dates, Telegram entries, reports, digests, and overdue task checks use the same time basis.

### Architecture Diagram

```
+-------------+      +--------------+      +------------------+
| IMAP Inbox  |----->| Email Reader |----->| Shared Triage    |
| Gmail       |      | reader.py    |      | Gate + Cache     |
+-------------+      +--------------+      +----+--------+----+
                                             |        |
                                  cache hit  |        | cache miss
                                             |        v
                                             |  +------------------+
                                             |  | OpenAI APIs      |
                                             |  | triage/drafting  |
                                             |  | transcription    |
                                             |  | photo vision     |
                                             |  +--------+---------+
                                             |           |
+------------------+      text/voice/photo   |           | category/reason
| Telegram Bot API |----------------->       v           v
| Telegram Adapter |                 +-------------------------+
+------------------+                 | Classified Message      |
                                     | sender/subject/body     |
                                     | category/reason/summary |
                                     +-----------+-------------+
                                                 |
                                                 v
                                     +-------------------------+
                                     | Dashboard Store         |
                                     | logs/dashboard_state.json |
                                     | live inbox + queue      |
                                     | saved reports/digests   |
                                     +-----------+-------------+
                                                 |
                                                 v
                                     +-------------------------+
                                     | Web Dashboard           |
                                     | Triage Inbox            |
                                     | Approval Flow           |
                                     | Message History         |
                                     | Cron Job panel          |
                                     +-----+-------------+-----+
                                           |             |
                                           | approve     | selected rows
                                           v             v
                                     +-----------+   +------------------+
                                     | SMTP      |   | Daily Report /   |
                                     | Sender    |   | Morning Digest   |
                                     +-----+-----+   +--------+---------+
                                           |                  |
                                           v                  v
                                     +-------------------------------+
                                     | SQLite Memory                 |
                                     | sent/dry-run history          |
                                     | Telegram history              |
                                     | contacts/tasks                |
                                     +---------------+---------------+
                                                     ^
                                                     |
                                     +---------------+---------------+
                                     | Cron Job / Scheduler Layer    |
                                     | reminders, reports, overdue   |
                                     +-------------------------------+
```

**Email path:** IMAP email is read by `reader.py`, then the triage gate checks the local cache. If the same sender, subject, and body were already classified, the cached result is reused. If it is new or changed, the email content goes to OpenAI and returns as a classified message with category and reason. That classified message is stored in `logs/dashboard_state.json` for the dashboard Triage Inbox and Approval Flow. SQLite memory records durable communication events such as approved/dry-run sends, Telegram history, contacts, and tasks; the live inbox snapshot itself is kept in dashboard state.

**Telegram path:** Telegram messages are not stored as plain side-channel data. Text messages go directly to semantic LLM triage. Voice messages first go to OpenAI transcription, then the transcript goes to semantic LLM triage. Photo messages go to OpenAI vision analysis, then the generated construction-site description goes to semantic LLM triage. Telegram photo messages also create a review-queue email draft with the original photo attached, so the user can forward the image after approval.

**Cron Job path:** Cron Job rules are shown in the dashboard task area and are supported by the scheduler/task layer. The current demo version exposes planned automation and overdue checks locally; it is designed so the same rules can later be attached to a production cron service or hosted scheduler.

---

## Full Project Flow

The dashboard is the control center. Every demo action starts in the browser, passes through Flask APIs in `dashboard_app.py`, uses orchestration helpers in `dashboard_store.py`, and then reads or writes one of the runtime stores.

For a shorter presentation/Q&A version of this operational flow, see [PROJECT_FLOW.md](PROJECT_FLOW.md).

```
USER / BROWSER
     |
     v
+-----------------------------+
| Flask Dashboard             |
| dashboard_app.py            |
| /api/bootstrap              |
| /api/inbox/refresh          |
| /api/queue/*                |
| /api/messages               |
| /api/reports/daily          |
| /api/digest/preview         |
| /api/tasks                  |
+-------------+---------------+
              |
              v
+-----------------------------+
| Dashboard Orchestrator      |
| dashboard_store.py          |
| state, queue, reports,      |
| digests, overdue checks     |
+------+------+------+-------+
       |      |      |
       |      |      +-----------------------------+
       |      |                                    |
       |      v                                    v
       |  +-----------------------+        +-----------------------+
       |  | Dashboard State JSON  |        | SQLite Memory         |
       |  | live inbox snapshot   |        | contacts              |
       |  | approval queue        |        | message_history       |
       |  | saved reports/digests |        | scheduled_tasks       |
       |  +-----------+-----------+        +-----------+-----------+
       |              ^                                ^
       |              |                                |
       v              |                                |
+----------------+    |                                |
| Email Pipeline |----+                                |
| IMAP reader    |                                     |
| triage cache   |                                     |
| OpenAI triage  |                                     |
| draft cache    |                                     |
+-------+--------+                                     |
        |                                              |
        v                                              |
+----------------+                                     |
| Approval Flow  |-------------------------------------+
| edit recipient |
| cc/subject/body|
| dry-run/send   |
+-------+--------+
        |
        v
+----------------+       +-----------------------+
| SMTP Sender    |------>| sent_log + agent.log  |
| real email     |       | runtime audit files   |
| attachments    |       +-----------------------+
+----------------+

+-------------------+       +------------------------+
| Telegram Pipeline |------>| OpenAI triage/audio/   |
| text              |       | vision services        |
| voice             |       +-----------+------------+
| photo             |                   |
+---------+---------+                   v
          |                  +------------------------+
          +----------------->| SQLite Message History |
          |                  | Telegram Text/Voice/   |
          |                  | Photo with category    |
          |                  +------------------------+
          |
          +-----------------> Dashboard approval queue
                              for photo email drafts

+-------------------+       +------------------------+
| Cron Job Panel    |------>| Scheduler / Task Layer |
| planned rules     |       | overdue email checks   |
| pending/overdue   |       | reminders/reports      |
+-------------------+       +------------------------+
```

### Main Runtime Flows

1. **Initial dashboard load:** The browser calls `/api/bootstrap`. Flask loads dashboard state, SQLite contacts/messages/tasks, health status, saved reports, saved digests, and logs.
2. **Refresh Live Inbox:** The browser calls `/api/inbox/refresh`. `dashboard_store.refresh_inbox_state("live")` fetches IMAP mail through `agent.fetch_emails()` and `reader.py`, normalizes each email, checks the triage cache, calls OpenAI only for new or changed messages, builds the approval queue for `URGENT` and `ACTION`, and saves the result in `logs/dashboard_state.json`.
3. **Load Demo Snapshot / Reset:** The same refresh path can use sample emails instead of IMAP. Reset rebuilds the sample inbox and queue while keeping unrelated saved reports and digests.
4. **Approval Flow:** The user edits recipient, cc, subject, and body in the dashboard. Approve dry-run records the action without sending. Real approve calls `send_approved_email()`, validates recipients/attachments, sends via SMTP, writes runtime logs, and records the event in SQLite memory.
5. **Telegram text:** Telegram bot receives text, sends it through `triage_email()`, and writes one categorized Message History row. No Telegram reply is sent.
6. **Telegram voice:** Telegram bot downloads the voice file, sends it to OpenAI transcription, triages the transcript, and writes one categorized Message History row. No draft is created.
7. **Telegram photo:** Telegram bot downloads the image, sends it to OpenAI vision analysis, triages the generated site-photo description, writes Message History, and creates a dashboard approval-queue email draft with the original image attached.
8. **Message History:** The dashboard reads `/api/messages` from SQLite. Telegram entries, approved/dry-run email actions, and stored communication history appear here.
9. **Daily Report:** The user selects Message History rows and calls `/api/reports/daily`. The report is generated from selected messages, saved to dashboard state, and can be added back to the approval queue. If selected rows contain Telegram photo references, those photos are carried as email attachments.
10. **Morning Digest:** The user calls `/api/digest/preview`. The digest is generated directly from the current Triage Inbox snapshot, saved to dashboard state, and can be reviewed later from Previous Digests.
11. **Cron Job:** The dashboard calls `/api/tasks`. The task layer returns SQLite scheduled tasks plus derived overdue email follow-ups for prior-day unanswered `URGENT` and `ACTION` emails.
12. **Logs and proof:** `agent.log`, `sent_log.txt`, triage/draft/summary caches, Telegram media files, SQLite memory, and dashboard state provide the demo audit trail.

### Runtime Storage Map

| Store | What it holds | Why it exists |
|-------|---------------|---------------|
| `logs/dashboard_state.json` | Live/demo inbox snapshot, approval queue, saved daily reports, saved morning digests | Fast dashboard state and demo reset/load behavior |
| `memory/memory.db` | Contacts, message history, scheduled tasks | Durable project memory and audit history |
| `logs/triage_cache.json` | LLM category/reason/confidence for each message hash | Prevents resending unchanged emails to OpenAI |
| `logs/draft_cache.json` | Draft replies for unchanged actionable emails | Prevents repeated draft-generation calls |
| `logs/email_summary_cache.json` | One-line email summaries | Keeps digest/preview refreshes fast |
| `logs/telegram_media/` | Downloaded Telegram photos | Allows photo messages and daily reports to attach original images |
| `logs/agent.log` | End-to-end agent activity | Submission proof for scenarios |
| `sent_log.txt` | Sent or dry-run approval actions | Lightweight audit of outbound flow |

---

## Components

### Email Reader

- **Responsibility:** Connect to IMAP, fetch recent project emails, parse headers/body, normalize dates to TRT, and prepare messages for triage.
- **Input:** IMAP credentials from `.env`; mailbox name.
- **Output:** Email dictionaries with sender, subject, date, raw date, body, category, and semantic reason.
- **File:** `reader.py`
- **Key dependencies:** `imaplib`, `email`, `python-dotenv`

### Semantic Triage Engine

- **Responsibility:** Classify email and Telegram-derived text into `URGENT`, `ACTION`, `FYI`, or `ARCHIVE` using OpenAI semantic reasoning instead of keyword matching.
- **Input:** Sender, subject, and body text. For Telegram voice/photo, the input body is a transcript or photo analysis.
- **Output:** Category and clean semantic reason text.
- **File:** `reader.py` (`triage_email()`)
- **Cache:** `logs/triage_cache.json` stores category, reason, confidence, source, and model per content hash. Refreshing the live inbox reuses cached classifications for unchanged messages and only sends new or changed messages to OpenAI.

### OpenAI Services

- **Responsibility:** Provide five AI operations: semantic triage, email drafting, inbox/digest summaries, voice transcription, and photo vision analysis.
- **Models:** `gpt-4o-mini` for triage/drafting/summaries by default, `gpt-4o-mini-transcribe` for Telegram voice, and `OPENAI_VISION_MODEL` for photo analysis.
- **Files:** `reader.py`, `agent.py`, `digest.py`, `channels/telegram_channel.py`
- **Fallbacks:** Failed triage becomes `ACTION` with `review manually`; failed draft generation uses templates; failed voice/photo analysis creates manual-review content instead of silently dropping the message.

### Web Dashboard

- **Responsibility:** Provide the main demo UI for triage inbox, approval flow, message history, contacts, daily reports, morning digests, Cron Job tasks, overdue follow-ups, Telegram status, and demo snapshot/reset controls.
- **Input:** Live IMAP inbox, SQLite memory, dashboard state JSON, Telegram-generated history rows.
- **Output:** JSON API responses and browser UI.
- **Files:** `dashboard_app.py`, `dashboard_store.py`, `web/static/app.js`, `web/static/styles.css`

### Approval Flow and SMTP Sender

- **Responsibility:** Hold drafted outgoing emails until the user approves, rejects, edits, or runs demo dry-run. SMTP sends only after explicit approval.
- **Input:** Queue item with recipient, optional cc, subject, draft body, category, source message, and optional attachments.
- **Output:** Sent email or dry-run audit entry.
- **Files:** `agent.py`, `dashboard_store.py`, `dashboard_app.py`
- **Safety:** Recipient validation, content checks, rate limiting, dry-run mode, and attachment validation.

### Telegram Channel

- **Responsibility:** Receive Telegram text, voice, and photo messages without automatic replies for normal messages.
- **Text flow:** Message text -> semantic triage -> Message History.
- **Voice flow:** Voice file -> OpenAI transcription -> semantic triage -> Message History.
- **Photo flow:** Photo file -> OpenAI vision analysis -> semantic triage -> Message History + approval-queue email draft with image attachment.
- **Output examples:** `Telegram Text (ACTION)`, `Telegram Voice (URGENT)`, `Telegram Photo (FYI)`.
- **File:** `channels/telegram_channel.py`
- **Key dependencies:** `python-telegram-bot`, `openai`

### Memory

- **Responsibility:** Store contacts, message history, and scheduled tasks in SQLite.
- **Input:** Incoming/outgoing messages, Telegram entries, approved email actions, task records.
- **Output:** Dashboard memory tables, daily report inputs, overdue follow-up checks.
- **File:** `memory/memory.py`
- **Database:** `memory/memory.db`

### Daily Report and Morning Digest

- **Daily Report:** Builds a construction daily report from selected Message History rows. If selected rows reference Telegram photos, those image files are carried into the review queue as email attachments.
- **Morning Digest:** Builds a digest directly from the current Triage Inbox preview, so the digest summary matches what the dashboard shows.
- **Persistence:** Saved report and digest previews are stored in `logs/dashboard_state.json`, newest first, capped at the latest 20 records.
- **Files:** `dashboard_store.py`, `dashboard_app.py`, `digest.py`

### Cron Job / Scheduler Layer

- **Responsibility:** Represent planned recurring communication automation and run local overdue/pending task checks.
- **Dashboard name:** `Cron Job`
- **Files:** `scheduler.py`, `dashboard_store.py`, `memory/memory.py`

Current Cron Job rules shown in the demo:

- Send the Daily Digest email every morning at 08:00.
- If no field update is received before noon, remind site teams to send an update.
- If no field update is received from the site by 16:00, send a reminder.
- Generate an end-of-day daily report automatically from incoming and outgoing messages and emails.
- Generate a weekly report at the end of the week by combining daily reports.
- Generate a monthly report at the end of the month by combining weekly reports.
- Add overdue tasks for unanswered `URGENT` and `ACTION` emails received before today.

---

## Data Flow

1. The user clicks **Refresh Live Inbox** in the dashboard or runs the agent manually.
2. The Email Reader fetches recent IMAP messages and normalizes dates to TRT.
3. The Semantic Triage Engine checks `logs/triage_cache.json`.
4. If the email is unchanged, cached category and reason are reused. If it is new or changed, the subject, sender, and body are sent to OpenAI for semantic classification.
5. The dashboard groups messages into `URGENT`, `ACTION`, `FYI`, and `ARCHIVE` sections.
6. `URGENT` and `ACTION` emails enter the approval flow with a draft reply generated by OpenAI or a fallback template.
7. The user can edit recipient, cc, subject, and body, then dry-run or send through SMTP.
8. Approved or dry-run actions are recorded in SQLite memory.
9. Telegram text, voice transcripts, and photo analyses enter the same semantic triage path and appear in Message History.
10. Telegram photo messages also create a draft email with the original image attached.
11. Daily reports and morning digests use dashboard/memory data, are saved to dashboard state, and can be reloaded later.
12. Cron Job rules and overdue checks appear in the Cron Job section, including unanswered prior-day `URGENT`/`ACTION` emails.

---

## Design Decisions

### ADR 1: Semantic LLM Triage Instead of Keyword Matching

**Decision:** Use OpenAI semantic classification instead of keyword lists.

**Context:** Construction communication often hides urgency in context. A message can mention a schedule slip, failed inspection, safety exposure, or claim risk without using obvious trigger words. Keyword matching was fast but too shallow for realistic CEM scenarios.

**Consequences:** Classification is more context-aware and easier to justify during Q&A. First-pass triage is slower and depends on API availability, so results are cached. If the LLM fails or returns invalid JSON, the message becomes `ACTION` with `review manually` to keep it visible.

### ADR 2: Human Approval Before Sending

**Decision:** Generated replies are never sent automatically.

**Context:** In construction management, a wrong email can create contractual, safety, cost, or relationship risk. The agent may draft quickly, but the PM must remain accountable for outgoing communication.

**Consequences:** The system is safer and demo-friendly. Dry-run gives proof without sending real mail, while real SMTP sending remains available after review.

### ADR 3: One OpenAI Provider for AI Tasks

**Decision:** Use OpenAI for triage, drafting, summaries, voice transcription, and photo analysis.

**Context:** Using one provider reduced integration complexity before the M9 deadline. It also made caching, error handling, and `.env` configuration simpler.

**Consequences:** There is a single external AI dependency. Fallbacks are implemented for triage, drafting, transcription, and image analysis so the dashboard still exposes manual review items when OpenAI is unavailable.

### ADR 4: SQLite Plus Dashboard State JSON

**Decision:** Store communication memory in SQLite and UI artifacts in dashboard state JSON.

**Context:** SQLite is appropriate for contacts, message history, and tasks. Saved report/digest previews are dashboard runtime artifacts, so JSON state is lighter than a schema migration for the final demo.

**Consequences:** The repo remains clone-and-run friendly. The database holds audit/history data, while `logs/dashboard_state.json` can be reset or regenerated for demo cleanup.

### ADR 5: TRT Time Normalization

**Decision:** Normalize generated dates and task comparisons to Europe/Istanbul.

**Context:** The demo deadline and project context use Turkish local time. Mixed UTC/local timestamps caused confusing dashboard behavior and overdue task checks.

**Consequences:** Email display, Telegram entries, reports, digests, and overdue checks now speak the same time language: TRT.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| LLM triage timeout or invalid JSON | Message classified as `ACTION` with `review manually` |
| Draft generation failure | Fallback template is used |
| Voice transcription failure | Telegram voice is logged for manual review |
| Photo vision analysis failure | Telegram photo is logged with manual-review text and image remains attached |
| Missing attachment at send time | Send is blocked and user is notified |
| IMAP connection failure | Error is surfaced to the dashboard/console |
| SMTP authentication failure | Send fails safely; draft remains in the queue |
| Rate limit exceeded | Send is blocked |
| SQLite lock | Retried with backoff in memory operations |

---

## API Keys and Configuration

All secrets are stored in `.env` and are not committed. See `.env.example` for required variables.

| Variable | Purpose |
|----------|---------|
| `EMAIL_ADDRESS` | IMAP/SMTP email account |
| `EMAIL_PASSWORD` | App-specific password |
| `IMAP_SERVER` | Incoming mail server |
| `SMTP_SERVER` | Outgoing mail server |
| `SMTP_PORT` | SMTP TLS port |
| `OPENAI_API_KEY` | OpenAI API access |
| `OPENAI_TRIAGE_MODEL` | Optional triage model override |
| `OPENAI_DRAFT_MODEL` | Optional drafting model override |
| `OPENAI_TRANSCRIPTION_MODEL` | Optional Telegram voice transcription model |
| `OPENAI_VISION_MODEL` | Optional Telegram photo vision model |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_PHOTO_FORWARD_TO` | Optional default recipient for Telegram photo email drafts |

---

## Future Extensions

- [ ] Parse PDF/DOCX attachments such as RFIs, submittals, inspection reports, and change orders.
- [ ] Add confidence-aware routing for low-confidence LLM classifications.
- [ ] Add Turkish/English bilingual drafting and triage controls.
- [ ] Connect Cron Job rules to a production scheduler or hosted worker.
- [x] Semantic LLM triage for emails and Telegram-derived messages.
- [x] Silent Telegram text and voice triage.
- [x] Telegram photo vision analysis and email-forward approval flow.
- [x] Dashboard daily reports, morning digests, memory, and approval review.

---

*CEM501 - Spring 2026 - Dr. Eyuphan Koc - Bogazici University*
