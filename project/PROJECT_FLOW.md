# End-to-End Project Flow

This file shows the complete runtime flow of the CEM501 Construction Communication Agent. Use this as the demo/Q&A map: it explains what starts in the dashboard, what goes to OpenAI, what returns to the dashboard, what is stored in memory, and what can be sent by email.

---

## One-Screen System Flow

```text
USER / PM
   |
   v
+----------------------------+
| Web Dashboard              |
| Triage Inbox               |
| Approval Flow              |
| Message History            |
| Daily Reports              |
| Morning Digest             |
| Cron Job                   |
+-------------+--------------+
              |
              v
+----------------------------+
| Flask API                  |
| dashboard_app.py           |
| /api/bootstrap             |
| /api/inbox/refresh         |
| /api/queue/*               |
| /api/messages              |
| /api/reports/daily         |
| /api/digest/preview        |
| /api/tasks                 |
+-------------+--------------+
              |
              v
+----------------------------+
| Dashboard Orchestrator     |
| dashboard_store.py         |
| builds inbox, queue,       |
| reports, digests, tasks    |
+------+------+------+------+
       |      |      |
       |      |      +--------------------------+
       |      |                                 |
       v      v                                 v
+-------------+---------+          +------------------------+
| Runtime Dashboard     |          | SQLite Memory          |
| State JSON            |          | memory/memory.db       |
| dashboard_state.json  |          | contacts               |
| live inbox snapshot   |          | message_history        |
| approval queue        |          | scheduled_tasks        |
| saved reports/digests |          +-----------+------------+
+------------+----------+                      ^
             ^                                 |
             |                                 |
             |                                 |
+------------+-----------+         +-----------+------------+
| Email Pipeline         |         | Telegram Pipeline      |
| IMAP fetch             |         | text                   |
| parse/normalize TRT    |         | voice -> transcription |
| triage cache           |         | photo -> vision        |
| OpenAI semantic triage |         | semantic triage        |
| OpenAI draft cache     |         | silent memory logging  |
+------------+-----------+         +-----------+------------+
             |                                 |
             v                                 |
+------------+-----------+                     |
| Approval Flow          |<--------------------+
| edit To/Cc/Subject     |  photo messages can
| edit draft body        |  create email draft
| dry-run or real send   |  with attachment
+------------+-----------+
             |
             v
+------------------------+
| SMTP Sender            |
| validates recipients   |
| validates attachments  |
| sends real email or    |
| records dry-run        |
+------------+-----------+
             |
             v
+------------------------+
| Logs and Audit Trail   |
| logs/agent.log         |
| sent_log.txt           |
| SQLite message history |
+------------------------+
```

---

## Flow 1: Email Triage and Approval

1. User clicks **Refresh Live Inbox**.
2. Dashboard calls `POST /api/inbox/refresh`.
3. `dashboard_store.refresh_inbox_state("live")` calls the email pipeline.
4. `reader.py` fetches recent IMAP messages and normalizes dates to TRT.
5. `triage_email()` checks `logs/triage_cache.json`.
6. If the message is new or changed, sender, subject, and body are sent to OpenAI semantic triage.
7. OpenAI returns `category`, `reason`, and confidence metadata.
8. The classified email is stored in `logs/dashboard_state.json`.
9. Dashboard renders it in Triage Inbox under `URGENT`, `ACTION`, `FYI`, or `ARCHIVE`.
10. `URGENT` and `ACTION` messages enter Approval Flow.
11. OpenAI draft generation or draft cache prepares a reply.
12. User edits `To`, `Cc`, subject, and body.
13. User chooses dry-run or real send.
14. SMTP sender validates recipients, content, rate limits, and attachments.
15. Dry-run or sent result is logged to `sent_log.txt`, `logs/agent.log`, and SQLite memory.

Important detail: live inbox data is not primarily stored in SQLite. The current inbox snapshot and queue live in `logs/dashboard_state.json`; SQLite stores durable communication history, contacts, and tasks.

---

## Flow 2: Telegram Text, Voice, and Photo

```text
Telegram text
  -> triage_email()
  -> OpenAI semantic triage if not cached
  -> SQLite Message History
  -> Dashboard Message History

Telegram voice
  -> download voice file
  -> OpenAI transcription
  -> triage_email(transcript)
  -> SQLite Message History
  -> Dashboard Message History

Telegram photo
  -> download image to logs/telegram_media/
  -> OpenAI vision analysis
  -> triage_email(photo analysis)
  -> SQLite Message History
  -> Dashboard Message History
  -> Approval Queue email draft with original photo attached
```

Normal Telegram text, voice, and photo messages do not receive automatic bot replies. The bot silently processes the content, assigns an importance category, and records it for the dashboard.

---

## Flow 3: Daily Report

1. User selects rows in **Message History**.
2. Dashboard calls `POST /api/reports/daily`.
3. `generate_daily_report_from_messages()` reads selected messages from SQLite memory.
4. A daily construction report is generated.
5. The report is saved to `logs/dashboard_state.json`.
6. It appears in **Previous Reports**.
7. User can add the report back to Approval Flow.
8. If selected messages contain Telegram photo references, original image files from `logs/telegram_media/` are attached to the outgoing report email.

---

## Flow 4: Morning Digest

1. User generates Morning Digest from the dashboard.
2. Dashboard calls `POST /api/digest/preview`.
3. Digest source is the current Triage Inbox snapshot from `logs/dashboard_state.json`.
4. Summary text comes from the same preview shown in Triage Inbox.
5. Digest text/html is saved to `logs/dashboard_state.json`.
6. It appears in **Previous Digests**.

---

## Flow 5: Cron Job and Overdue Tasks

The demo Cron Job panel shows planned recurring communication automation plus local overdue checks.

Current rules:

- Send the Daily Digest email every morning at 08:00.
- If no field update is received before noon, remind site teams to send an update.
- If no field update is received from the site by 16:00, send a reminder.
- Generate an end-of-day daily report automatically from incoming and outgoing messages and emails.
- Generate a weekly report at the end of the week by combining daily reports.
- Generate a monthly report at the end of the month by combining weekly reports.
- Add overdue tasks for unanswered prior-day `URGENT` and `ACTION` emails.

Runtime flow:

```text
Dashboard Cron Job panel
  -> GET /api/tasks
  -> SQLite scheduled_tasks
  -> derived overdue email checks from dashboard inbox state
  -> pending/overdue cards in dashboard
```

---

## What Goes to OpenAI

| Source | OpenAI task | Returned result | Where result goes |
|--------|-------------|-----------------|-------------------|
| Incoming email | Semantic triage | Category, reason, confidence | `logs/dashboard_state.json`, Triage Inbox |
| Actionable email | Draft generation | Reply draft | Approval Flow queue |
| Triage inbox item | Summary | One-line preview | Triage Inbox and Morning Digest |
| Telegram text | Semantic triage | Category and reason | SQLite Message History |
| Telegram voice | Transcription, then triage | Transcript, category, reason | SQLite Message History |
| Telegram photo | Vision analysis, then triage | Site-photo description, category, reason | SQLite Message History and Approval Queue |
| Daily report / digest content | Report or summary assistance | Generated report/digest text | `logs/dashboard_state.json` |

---

## What Is Stored Where

| Location | Stored data |
|----------|-------------|
| `logs/dashboard_state.json` | Current live/demo inbox, approval queue, saved daily reports, saved morning digests |
| `memory/memory.db` | Contacts, Message History, scheduled tasks, durable communication memory |
| `logs/triage_cache.json` | Cached OpenAI semantic triage results |
| `logs/draft_cache.json` | Cached email draft replies |
| `logs/email_summary_cache.json` | Cached inbox/digest summaries |
| `logs/telegram_media/` | Downloaded Telegram photo files |
| `logs/agent.log` | End-to-end agent runtime proof |
| `sent_log.txt` | Dry-run and real send audit entries |

---

## Demo Reading Order

1. Start on dashboard health/status.
2. Click **Refresh Live Inbox** and show Triage Inbox categories.
3. Open one `URGENT` or `ACTION` item in Approval Flow.
4. Explain that OpenAI produces triage/draft, but human approval controls sending.
5. Use dry-run for safety.
6. Show Telegram Message History row for text, voice, or photo.
7. Show photo attachment behavior if a Telegram photo exists.
8. Generate Daily Report from Message History.
9. Generate Morning Digest from Triage Inbox.
10. Show Cron Job rules and overdue tasks.
11. Close with the PM safety message: the system does not replace the PM; it gives the PM a faster and safer first pass.
