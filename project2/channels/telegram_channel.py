"""
telegram_channel.py — Telegram channel implementation.

Connects the Telegram Bot API to the agent pipeline:
    receive message → classify (reader.py) → draft response (OpenAI) → reply

Uses python-telegram-bot library in polling mode (no server needed).

CEM501 — Milestone M6: Multi-Channel Integration
"""

import os
import sys

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from channels.base import Channel

# Import triage from reader.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from reader import triage_email

# Import OpenAI for drafting responses
from openai import OpenAI


class TelegramChannel(Channel):
    """
    Telegram channel using the Bot API in polling mode.

    Credentials loaded from environment variables:
        - TELEGRAM_BOT_TOKEN: Bot token from @BotFather

    The bot listens for messages, classifies them using the project's
    triage logic, drafts a professional response via Gemini, and replies.
    """

    channel_name = "telegram"

    def __init__(self):
        """Initialize the Telegram channel with bot token from .env."""
        load_dotenv()
        self._token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not self._token:
            raise RuntimeError(
                "Missing TELEGRAM_BOT_TOKEN in .env. "
                "Create a bot with @BotFather and add the token."
            )
        self._app = None
        self._message_count = 0

    def fetch_messages(self) -> list[dict]:
        """
        Telegram uses push-based polling — messages are handled by
        callbacks, not fetched in bulk. This method is not used directly.
        Use run() to start the polling loop instead.
        """
        return []

    def send_message(self, recipient: str, text: str) -> bool:
        """
        Send a message to a Telegram chat.

        Args:
            recipient: The chat_id (as string) to send to.
            text: The message text.

        Returns:
            True if sent successfully, False otherwise.
        """
        import asyncio
        from telegram import Bot

        try:
            bot = Bot(token=self._token)
            asyncio.get_event_loop().run_until_complete(
                bot.send_message(chat_id=int(recipient), text=text)
            )
            print(f"[telegram] Sent message to chat {recipient}")
            return True
        except Exception as exc:
            print(f"[telegram] Failed to send: {exc}", file=sys.stderr)
            return False

    def run(self):
        """
        Start the Telegram bot in polling mode.
        This is a blocking call — it runs until Ctrl+C.
        """
        self._app = ApplicationBuilder().token(self._token).build()

        # Command handlers
        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(CommandHandler("help", self._cmd_help))
        self._app.add_handler(CommandHandler("status", self._cmd_status))

        # Message handler — routes through the agent pipeline
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )

        print("=" * 50)
        print("CEM501 Agent Bot — Telegram Channel")
        print("=" * 50)
        print("Bot is running... press Ctrl+C to stop.")
        print()

        self._app.run_polling()

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command — welcome message."""
        await update.message.reply_text(
            "👷 CEM501 Construction Agent Bot\n\n"
            "Send me any construction project message and I will:\n"
            "1. Classify it (URGENT / ACTION / FYI / ARCHIVE)\n"
            "2. Draft a professional response\n\n"
            "Commands:\n"
            "/help — What messages I can handle\n"
            "/status — How many messages processed this session"
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command — list supported message types."""
        await update.message.reply_text(
            "📋 I can handle these types of construction messages:\n\n"
            "🔴 URGENT — Safety incidents, stop-work orders, delay notices\n"
            "🟡 ACTION — RFIs, submittals, approvals, meeting requests\n"
            "🔵 FYI — Daily reports, progress updates, meeting minutes\n"
            "⚫ ARCHIVE — Newsletters, personal messages, spam\n\n"
            "Just paste or type any project-related message and I'll "
            "classify it and draft a response."
        )

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command — show processing stats."""
        await update.message.reply_text(
            f"📊 Session Stats\n"
            f"Messages processed: {self._message_count}"
        )

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Main handler: classify incoming message → draft response → reply.

        Pipeline:
            1. Classify using reader.py's triage_email()
            2. Draft a response using Gemini
            3. Send the response back through Telegram
        """
        incoming_text = update.message.text
        sender_name = update.message.from_user.first_name or "User"

        # Step 1: Classify the message
        category, matched_keyword = triage_email(
            subject="",  # Telegram messages don't have subjects
            sender=sender_name,
            body=incoming_text,
        )

        # Step 2: Draft a response using OpenAI
        draft = self._draft_response(incoming_text, category)

        # Step 3: Reply with classification + draft
        emoji_map = {"URGENT": "🔴", "ACTION": "🟡", "FYI": "🔵", "ARCHIVE": "⚫"}
        emoji = emoji_map.get(category, "⚪")

        response = (
            f"{emoji} **{category}** (matched: _{matched_keyword}_)\n\n"
            f"📝 **Draft Response:**\n{draft}"
        )

        await update.message.reply_text(response, parse_mode="Markdown")

        self._message_count += 1
        print(f"[telegram] {sender_name} → {category} (keyword: {matched_keyword})")

    def _draft_response(self, message_text: str, category: str) -> str:
        """
        Use OpenAI to draft a professional construction response.

        Args:
            message_text: The original message from the user.
            category: The triage category (URGENT, ACTION, FYI, ARCHIVE).

        Returns:
            A drafted response string.
        """
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            prompt = (
                f"You are a construction project manager's AI assistant. "
                f"A message was received and classified as {category}.\n\n"
                f"Original message:\n{message_text}\n\n"
                f"Draft a brief, professional response appropriate for a "
                f"construction project context. Keep it to 2-3 sentences. "
                f"Be direct and action-oriented."
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[telegram] OpenAI draft failed: {e}", file=sys.stderr)
            # Fallback: simple acknowledgment based on category
            fallbacks = {
                "URGENT": "⚠️ This has been flagged as urgent. Escalating to the project team immediately.",
                "ACTION": "Acknowledged. This item requires action and has been added to the task queue.",
                "FYI": "Noted. This has been logged for reference.",
                "ARCHIVE": "Received. No action required at this time.",
            }
            return fallbacks.get(category, "Message received.")
