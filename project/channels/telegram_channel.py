"""
telegram_channel.py - Telegram channel implementation.

Connects the Telegram Bot API to the agent pipeline:
    receive text/voice -> transcribe voice if needed -> triage -> log to memory

Normal Telegram project messages are processed silently. The bot does not
send automatic draft replies; Message History is the visible output.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from channels.base import Channel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from memory.memory import DB_PATH, add_contact, log_message
from reader import triage_email


DEFAULT_TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"


class TelegramChannel(Channel):
    """
    Telegram channel using Bot API polling.

    Credentials:
        - TELEGRAM_BOT_TOKEN
        - OPENAI_API_KEY
        - OPENAI_TRANSCRIPTION_MODEL, optional
    """

    channel_name = "telegram"

    def __init__(self):
        load_dotenv()
        self._token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self._transcription_model = (
            os.getenv("OPENAI_TRANSCRIPTION_MODEL", DEFAULT_TRANSCRIPTION_MODEL).strip()
            or DEFAULT_TRANSCRIPTION_MODEL
        )
        if not self._token:
            raise RuntimeError(
                "Missing TELEGRAM_BOT_TOKEN in .env. "
                "Create a bot with @BotFather and add the token."
            )
        self._app = None
        self._message_count = 0

    def fetch_messages(self) -> list[dict]:
        """
        Telegram uses polling callbacks instead of batch fetching.
        """
        return []

    def send_message(self, recipient: str, text: str) -> bool:
        """
        Send an explicit Telegram message. Not used for automatic triage replies.
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
        Start the Telegram bot in polling mode. This blocks until Ctrl+C.
        """
        self._app = ApplicationBuilder().token(self._token).build()

        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(CommandHandler("help", self._cmd_help))
        self._app.add_handler(CommandHandler("status", self._cmd_status))

        self._app.add_handler(MessageHandler(filters.VOICE, self._handle_voice_message))
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message)
        )

        print("=" * 50)
        print("CEM501 Agent Bot - Telegram Channel")
        print("=" * 50)
        print("Bot is running in silent triage mode... press Ctrl+C to stop.")
        print()

        self._app.run_polling()

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "CEM501 Construction Agent Bot\n\n"
            "Send text or voice construction updates. I will transcribe voice, "
            "classify the message, and save it to Message History.\n\n"
            "Normal messages are processed silently; no draft reply is sent.\n\n"
            "Commands:\n"
            "/help - What messages I can handle\n"
            "/status - How many messages processed this session"
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "I can silently classify these construction messages:\n\n"
            "URGENT - Safety incidents, stop-work orders, delay notices\n"
            "ACTION - RFIs, submittals, approvals, meeting requests\n"
            "FYI - Daily reports, progress updates, meeting minutes\n"
            "ARCHIVE - Newsletters, personal messages, spam\n\n"
            "Text and voice messages are stored in Message History with their category."
        )

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Session Stats\n"
            f"Messages processed: {self._message_count}"
        )

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Classify an incoming text message and log one received history row.
        """
        incoming_text = (update.message.text or "").strip()
        sender_name = self._sender_name(update)
        if not incoming_text:
            return

        category, triage_reason = self._classify_and_log(
            sender_name=sender_name,
            message_text=incoming_text,
            message_type="Text",
        )
        self._message_count += 1
        print(f"[telegram] {sender_name} text -> {category} (reason: {triage_reason})")

    async def _handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Transcribe an incoming voice message, classify it, and log one history row.
        """
        sender_name = self._sender_name(update)
        transcript = await self._transcribe_voice(update)

        if transcript:
            body = f"Voice transcript: {transcript}"
            category, triage_reason = self._classify_and_log(
                sender_name=sender_name,
                message_text=body,
                message_type="Voice",
            )
        else:
            body = "Voice transcript failed; review manually."
            category = "ACTION"
            triage_reason = "review manually"
            self._log_triaged_message(
                sender_name=sender_name,
                message_type="Voice",
                category=category,
                body=body,
            )

        self._message_count += 1
        print(f"[telegram] {sender_name} voice -> {category} (reason: {triage_reason})")

    def _sender_name(self, update: Update) -> str:
        user = update.message.from_user
        if not user:
            return "Telegram User"

        display_name = " ".join(
            part for part in [user.first_name or "", user.last_name or ""] if part
        ).strip()
        return display_name or user.username or "Telegram User"

    def _classify_and_log(
        self,
        sender_name: str,
        message_text: str,
        message_type: str,
    ) -> tuple[str, str]:
        category, triage_reason = triage_email(
            subject=f"Telegram {message_type}",
            sender=sender_name,
            body=message_text,
        )
        self._log_triaged_message(
            sender_name=sender_name,
            message_type=message_type,
            category=category,
            body=message_text,
        )
        return category, triage_reason

    def _log_triaged_message(
        self,
        sender_name: str,
        message_type: str,
        category: str,
        body: str,
    ) -> None:
        try:
            contact_id = self._get_or_create_contact(sender_name)
            log_message(
                contact_id=contact_id,
                direction="received",
                subject=f"Telegram {message_type} ({category})",
                body=body,
                channel="telegram",
            )
        except Exception as exc:
            print(f"[telegram] Failed to log to memory: {exc}", file=sys.stderr)

    async def _transcribe_voice(self, update: Update) -> str:
        if not update.message.voice:
            return ""

        temp_path = ""
        try:
            voice_file = await update.message.voice.get_file()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as handle:
                temp_path = handle.name

            await voice_file.download_to_drive(custom_path=temp_path)

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            with open(temp_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model=self._transcription_model,
                    file=audio_file,
                    response_format="text",
                    prompt=(
                        "Construction project communication. Preserve Turkish or "
                        "English wording, project names, RFIs, delays, safety "
                        "issues, quantities, dates, and responsibilities."
                    ),
                )

            if isinstance(transcription, str):
                return transcription.strip()
            return str(getattr(transcription, "text", "")).strip()
        except Exception as exc:
            print(f"[telegram] Voice transcription failed: {exc}", file=sys.stderr)
            return ""
        finally:
            if temp_path:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def _get_or_create_contact(self, name: str) -> int:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT id FROM contacts WHERE name = ?", (name,)).fetchone()
        conn.close()
        if row:
            return row[0]
        return add_contact(name=name, notes="Telegram User")
