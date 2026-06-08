# Channels - Multi-Channel Communication Layer

This directory implements the Week 11 channel abstraction pattern. The agent can communicate through different platforms while reusing the same triage and drafting foundations.

All channels use `reader.py` for semantic OpenAI triage. Triage results and generated drafts are cached under `logs/`, so the same message content is not reclassified or redrafted on every refresh.

## Architecture

```text
Email / IMAP ----+
                 |
                 v
          +--------------+       +------------------+
          | reader.py    | ----> | OpenAI Drafter   |
          | classifier   |       | gpt-4o-mini      |
          +--------------+       +---------+--------+
                 ^                        |
                 |                        v
Telegram Bot ----+              Email SMTP / Telegram Bot
```

## Implemented Channels

### 1. Email (`email_channel.py`)
- Receives messages via IMAP.
- Sends replies via SMTP.
- Wraps the existing `reader.py` semantic LLM triage logic.
- Config: `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `IMAP_SERVER`, `SMTP_SERVER`, `SMTP_PORT`.

### 2. Telegram (`telegram_channel.py`)
- Receives messages through Telegram Bot API polling.
- Sends replies directly through the Bot API.
- Classifies messages using `reader.py` semantic LLM triage.
- Drafts responses using OpenAI `gpt-4o-mini`.
- Logs received and sent Telegram messages to SQLite memory.
- Config: `TELEGRAM_BOT_TOKEN` and `OPENAI_API_KEY`.

## Setup

### Prerequisites

```powershell
pip install python-telegram-bot python-dotenv openai
```

### Configuration

Add these to your `project/.env` file:

```env
# Email channel
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Telegram channel
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# OpenAI drafting
OPENAI_API_KEY=your_openai_api_key
```

### Running the Telegram Bot

```powershell
cd project
py run_telegram_bot.py
```

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| `/help` | List of supported message types |
| `/status` | Number of messages processed this session |

## Adding a New Channel

1. Create a new file, for example `slack_channel.py`.
2. Inherit from `Channel` in `base.py`.
3. Implement `fetch_messages()` and `send_message()`.
4. Add credentials to `.env`.

The core classifier and drafter remain untouched; only the I/O layer changes.

## File Structure

```text
channels/
  __init__.py
  base.py
  email_channel.py
  telegram_channel.py
  README.md
```
