# Repository Guidelines

## Project Context

This is a **CEM501 Communication Skills for CEM** course project (Spring 2026, Boğaziçi University, Dr. Eyuphan Koç). The system is a personal AI communication agent for construction project managers. It reads incoming emails via IMAP, classifies them by urgency using a keyword-based triage engine, drafts professional replies using OpenAI (gpt-4o-mini), and sends approved drafts via SMTP — all with mandatory human-in-the-loop confirmation. It also integrates with Telegram for real-time messaging, uses SQLite for persistent memory, and includes a Flask web dashboard.

## Project Structure & Module Organization

**Working directory for all commands:** `project/`

Core application logic lives in the `project/` directory. Key modules:

| File | Purpose |
|------|---------|
| `agent.py` | Main pipeline: read → triage → draft → send (with 4 safety guardrails) |
| `reader.py` | IMAP email reader + multi-pass keyword triage engine |
| `digest.py` | Daily digest generator with LLM summarization |
| `scheduler.py` | Periodic task runner (follow-ups, reminders, morning summaries) |
| `dashboard_app.py` | Flask web dashboard entry point |
| `dashboard_store.py` | Dashboard state management + API helpers |
| `run_telegram_bot.py` | Telegram bot entry point |

Sub-packages and directories:

| Directory | Purpose |
|-----------|---------|
| `channels/` | Multi-channel abstraction — `base.py` (ABC), `email_channel.py`, `telegram_channel.py` |
| `memory/` | SQLite persistence — `memory.py` (CRUD for contacts, messages, tasks), `memory.db` (auto-generated) |
| `templates/` | LLM prompt templates — `rfi_drafter.md`, `daily_report.md`, `delaynotice_report.md` |
| `web/templates/` | Dashboard HTML (`dashboard.html`) |
| `web/static/` | Dashboard frontend — `app.js`, `index.css` |
| `tests/` | Scenario-based integration test scripts and fixtures |
| `logs/` | Runtime logs — `agent.log`, `sent_log.txt` (gitignored) |

## Build, Test, and Development Commands

Create a virtual environment, then install dependencies with `pip install -r requirements.txt`.

All commands run from the `project/` directory:

- `py agent.py --dry-run`: run the full email pipeline without sending mail.
- `py agent.py --summary`: inspect triage results only.
- `py agent.py`: full pipeline with live send (requires human confirmation).
- `py digest.py --live`: generate a digest from live inbox data.
- `py digest.py`: generate a digest with sample data.
- `py dashboard_app.py`: start the web dashboard (Flask dev server).
- `py -m flask --app dashboard_app run --debug`: alternative dashboard start with debug mode.
- `py scheduler.py`: single scheduler check.
- `py scheduler.py --loop`: run scheduled checks continuously.
- `py run_telegram_bot.py`: start the Telegram bot.
- `py tests/send_scenario_test.py --dry-run`: preview the scripted test inbox scenarios.
- `py test_bot.py`: verify Telegram bot wiring with the echo bot.

## Critical Design Decisions

These decisions are intentional and must be preserved:

1. **Keyword triage over LLM classification** — The triage engine in `reader.py` uses a three-pass keyword matching algorithm (junk words → compound keywords → single keywords) instead of calling the LLM for every email. This is fast (~1 second for 20 emails), free, and deterministic. Do not replace this with LLM-based classification.

2. **Human-in-the-loop is mandatory** — All draft replies require explicit user confirmation (`y/n/e` prompt) before sending. No automatic sends, ever. Construction emails can have legal and financial consequences. The `--dry-run` flag exists for unattended testing.

3. **OpenAI gpt-4o-mini as primary LLM** — Used for drafting and summarization. All LLM calls must be wrapped in try/except with fallback to pre-written templates. If OpenAI is unavailable, the agent must continue functioning with template-based responses.

4. **SQLite for persistence** — Zero config, single file (`memory.db`), ships with Python. Schema has three tables: `contacts`, `message_history`, `scheduled_tasks`. Database lock errors should be retried with exponential backoff (3 attempts, 1s/2s/4s + jitter).

## Error Handling Patterns

Follow these established patterns when adding or modifying error handling:

| Scenario | Required Behavior |
|----------|-------------------|
| LLM API timeout / 403 | Log as ERROR; use fallback template for drafts; continue processing remaining items |
| IMAP connection failure | Raise `RuntimeError`; log error; exit with code 1 |
| SMTP auth failure | Log as ERROR; notify user; preserve draft for retry |
| Rate limit exceeded | Block send; log WARNING; notify user |
| Database locked | Retry with exponential backoff (3 attempts, 1s/2s/4s delay + jitter) |
| Unknown email format | `extract_body_preview()` returns empty string; classify as ARCHIVE |

## Coding Style & Naming Conventions

Follow existing Python style: 4-space indentation, `snake_case` for functions and variables, `UPPER_CASE` for module constants, and short module-level docstrings for runnable scripts. Keep modules focused and reuse helpers across entry points instead of duplicating IMAP, SMTP, or triage logic. There is no enforced formatter in the repo today, so match surrounding style and keep imports grouped as standard library, third-party, then local.

Frontend (dashboard): Vanilla HTML/CSS/JS — no frameworks. Single-page app served by Flask.

## Testing Guidelines

This repository uses script-based integration tests rather than a formal `pytest` suite. Add new test scenarios under `tests/` with descriptive names such as `send_scenario_test3.py` or Markdown fixtures like `latest_test.md`. Prefer safe runs with `--dry-run` when a script can send email or call external services. Before opening a PR, run the entry point affected by your change and verify console output, generated digest content, or dashboard behavior.

## Commit & Pull Request Guidelines

Recent history favors short, imperative commit messages, often with a `feat:` prefix for user-facing work, for example `feat: add daily report generator`. Keep each commit scoped to one change area. Pull requests should include a brief summary, impacted modules, manual test steps, and screenshots for dashboard or Telegram-facing changes. Link the relevant milestone or issue when applicable.

## Environment Variables

All secrets are stored in `.env` (never committed). See `.env.example` for the full template.

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API access (primary LLM) |
| `EMAIL_ADDRESS` | Yes | IMAP/SMTP email account |
| `EMAIL_PASSWORD` | Yes | Gmail app-specific password |
| `IMAP_SERVER` | Yes | Incoming mail server (default: `imap.gmail.com`) |
| `SMTP_SERVER` | Yes | Outgoing mail server (default: `smtp.gmail.com`) |
| `SMTP_PORT` | Yes | SMTP port (default: `587`) |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram bot token (needed only for Telegram channel) |
| `ANTHROPIC_API_KEY` | Optional | Anthropic API (fallback LLM) |

## Security & Configuration Tips

Store secrets only in `.env`; never commit credentials, `memory.db`, or live logs. Use `.env.example` as the template. The `.env` file exists at both the repo root and `project/` level — the `project/.env` is the one used at runtime.
