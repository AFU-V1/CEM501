# CEM501 Construction Communication Agent

This project is a course-appropriate communication agent for construction project management. It is not only a generic chatbot: it reads project communications, classifies them into construction-relevant categories, drafts professional responses, logs the communication history, stores contacts and follow-up tasks in SQLite, and supports both Email and Telegram as channels.

## What the app does

- Reads incoming email messages from IMAP.
- Classifies messages into workflow buckets: `URGENT`, `ACTION`, `FYI`, `ARCHIVE`.
- Adds construction-specific types: `RFI`, `DELAY`, `APPROVAL`, `SITE_ISSUE`, `SAFETY`, `PROCUREMENT`, `REPORT`.
- Drafts a response with OpenAI and uses simple fallbacks if the API is unavailable.
- Logs incoming and outgoing messages to SQLite.
- Stores contacts and message history in `memory.db`.
- Creates follow-up tasks for items that usually require tracking.
- Supports a Telegram bot for live message classification and drafting.
- Provides daily and weekly summary output through the scheduler.
- Includes a demo channel with realistic Week 14 scenarios so the final presentation can run reliably.

## Architecture summary

Main modules:

- `agent.py`: main orchestrator for the email pipeline.
- `pipeline.py`: shared receive -> classify -> draft -> save workflow.
- `channels/base.py`: adapter interface.
- `channels/email_channel.py`: email adapter.
- `channels/demo_channel.py`: reliable demo adapter with realistic scenarios.
- `channels/telegram_channel.py`: Telegram adapter.
- `classifier.py`: workflow and construction-type classification.
- `drafter.py`: response drafting.
- `memory.py`: SQLite contacts, messages, and tasks.
- `scheduler.py`: reminders and summaries.

This is the intended architecture for the presentation:

1. Channel receives message.
2. Shared pipeline classifies it.
3. Memory stores the incoming message and loads recent history.
4. Drafter produces a reply draft.
5. Channel sends or displays the draft.
6. Memory stores the outgoing message and any reminder task.

## Setup

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the environment template and fill it in:

```bash
copy .env.example .env
```

Required variables:

- `OPENAI_API_KEY`
- `EMAIL_ADDRESS`
- `EMAIL_PASSWORD`
- `IMAP_SERVER`
- `SMTP_SERVER`
- `SMTP_PORT`
- `TELEGRAM_BOT_TOKEN` for Telegram demo

## Run

Recommended Week 14 demo pipeline:

```bash
python agent.py
python scheduler.py
```

Email pipeline:

```bash
python agent.py --summary
python agent.py --channel email --dry-run
python agent.py
```

Telegram bot:

```bash
python run_telegram_bot.py
```

Scheduler:

```bash
python scheduler.py
python scheduler.py --loop
```

## Recommended demo

Use `--dry-run` for the presentation unless you want to send real mail.

Suggested flow:

1. Run `python agent.py` to show 3 realistic construction scenarios from the demo channel.
2. Show one RFI, one delay notice, and one safety escalation.
3. Point out the workflow class and construction-specific type.
4. Show the drafted reply.
5. Explain that the message and contact are stored in SQLite and that a follow-up task is added automatically.
6. Run `python scheduler.py` to show the reminder and weekly summary output.
7. Optionally switch to `python agent.py --channel email --dry-run` or `python run_telegram_bot.py` as the extra-channel proof.

Alternative live-email flow:

1. Show an incoming RFI or delay email in the inbox.
2. Run `python agent.py --channel email --dry-run`.
3. Show the classification table with the construction type.
4. Show the drafted reply.
5. Run `python scheduler.py`.

## Notes

- The default Week 14 demo path is the built-in demo channel.
- The email channel is the main real-world operational path.
- Telegram is implemented as an event-driven adapter that reuses the same classification, drafting, and memory pipeline.
- `.env` is ignored by Git. Do not commit real credentials.
