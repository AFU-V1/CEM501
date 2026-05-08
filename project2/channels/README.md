# Channels — Multi-Channel Communication Layer

This directory implements the **channel abstraction pattern** from Week 11, allowing the CEM501 agent to communicate across multiple platforms through a unified interface.

## Architecture

```
        ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
        │  Email      │────▶│              │────▶│  Email      │
        │  (IMAP)     │     │  Classifier  │     │  (SMTP)     │
        └─────────────┘     │  (reader.py) │     └─────────────┘
                            │              │
        ┌─────────────┐     │  Drafter     │     ┌─────────────┐
        │  Telegram   │────▶│  (Gemini)    │────▶│  Telegram   │
        │  (Bot API)  │     │              │     │  (Bot API)  │
        └─────────────┘     └──────────────┘     └─────────────┘
```

## Implemented Channels

### 1. Email (`email_channel.py`)
- **Receives** via IMAP (Gmail)
- **Sends** via SMTP (Gmail)
- Wraps the existing `reader.py` triage logic
- **Config:** `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `IMAP_SERVER` in `.env`

### 2. Telegram (`telegram_channel.py`)
- **Receives** via Bot API polling (no server needed)
- **Sends** replies directly through the Bot API
- Classifies messages using `reader.py` triage keywords
- Drafts responses using Gemini (`gemini-2.5-flash`)
- **Config:** `TELEGRAM_BOT_TOKEN` in `.env`

## Setup

### Prerequisites
```bash
pip install python-telegram-bot python-dotenv google-genai
```

### Configuration

Add these to your `project/.env` file:

```env
# Email channel
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
IMAP_SERVER=imap.gmail.com

# Telegram channel
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# Gemini (for response drafting)
GEMINI_API_KEY=your_gemini_api_key
```

### Running the Telegram Bot
```bash
cd project
python run_telegram_bot.py
```

### Bot Commands
| Command | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| `/help` | List of supported message types |
| `/status` | Number of messages processed this session |

## Adding a New Channel

1. Create a new file (e.g., `slack_channel.py`)
2. Inherit from `Channel` in `base.py`
3. Implement `fetch_messages()` and `send_message()`
4. Add credentials to `.env`

The core classifier and drafter remain untouched — only the I/O layer changes.

## File Structure

```
channels/
├── __init__.py              # Package init
├── base.py                  # Channel base class (adapter pattern)
├── email_channel.py         # Email via IMAP/SMTP
├── telegram_channel.py      # Telegram via Bot API
└── README.md                # This file
```
