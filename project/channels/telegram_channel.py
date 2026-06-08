"""
telegram_channel.py - Telegram channel implementation.

Connects the Telegram Bot API to the agent pipeline:
    receive text/voice -> transcribe voice if needed -> triage -> log to memory

Normal Telegram project messages are processed silently. The bot does not
send automatic draft replies; Message History is the visible output.
"""

from __future__ import annotations

import base64
import mimetypes
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
from time_utils import tr_now


DEFAULT_TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_VISION_MODEL = "gpt-4o-mini"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TELEGRAM_MEDIA_DIR = os.path.join(BASE_DIR, "logs", "telegram_media")


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
        self._vision_model = (
            os.getenv("OPENAI_VISION_MODEL", DEFAULT_VISION_MODEL).strip()
            or DEFAULT_VISION_MODEL
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

        self._app.add_handler(MessageHandler(filters.PHOTO, self._handle_photo_message))
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
            "Send text, voice, or site photos. I will transcribe voice, analyze photos, "
            "classify the message, and save it to Message History. Photos are also "
            "queued as reviewed email drafts with the image attached.\n\n"
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
            "Text and voice messages are stored in Message History with their category. "
            "Photos are analyzed, stored in Message History, and added to the dashboard "
            "Review Queue as email drafts with the image attached."
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

    async def _handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Analyze an incoming photo, classify it, log it, and queue an email draft.
        """
        sender_name = self._sender_name(update)
        caption = (update.message.caption or "").strip()
        photo_path = await self._download_photo(update)

        if photo_path:
            analysis = self._describe_photo(photo_path, caption)
            body = self._photo_body(caption=caption, analysis=analysis, photo_path=photo_path)
            category, triage_reason = triage_email(
                subject="Telegram Photo",
                sender=sender_name,
                body=body,
            )
            self._log_triaged_message(
                sender_name=sender_name,
                message_type="Photo",
                category=category,
                body=body,
            )
            self._queue_photo_email(
                sender_name=sender_name,
                category=category,
                triage_reason=triage_reason,
                body=body,
                photo_path=photo_path,
            )
        else:
            body = "Telegram photo download failed; review manually."
            category = "ACTION"
            triage_reason = "review manually"
            self._log_triaged_message(
                sender_name=sender_name,
                message_type="Photo",
                category=category,
                body=body,
            )

        self._message_count += 1
        print(f"[telegram] {sender_name} photo -> {category} (reason: {triage_reason})")

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

    async def _download_photo(self, update: Update) -> str:
        if not update.message.photo:
            return ""

        os.makedirs(TELEGRAM_MEDIA_DIR, exist_ok=True)
        photo = update.message.photo[-1]
        stamp = tr_now().strftime("%Y%m%d_%H%M%S")
        safe_id = "".join(ch for ch in photo.file_unique_id if ch.isalnum() or ch in ("-", "_"))[:40]
        filename = f"telegram_photo_{stamp}_{safe_id}.jpg"
        path = os.path.join(TELEGRAM_MEDIA_DIR, filename)

        try:
            photo_file = await photo.get_file()
            await photo_file.download_to_drive(custom_path=path)
            return path
        except Exception as exc:
            print(f"[telegram] Photo download failed: {exc}", file=sys.stderr)
            return ""

    def _describe_photo(self, photo_path: str, caption: str = "") -> str:
        try:
            content_type = mimetypes.guess_type(photo_path)[0] or "image/jpeg"
            with open(photo_path, "rb") as handle:
                image_data = base64.b64encode(handle.read()).decode("ascii")

            prompt = (
                "Analyze this construction site photo for a construction project manager. "
                "Write 2-4 concise sentences. Mention visible safety issues, delays, "
                "work progress, materials, equipment, document/RFI relevance, and any "
                "immediate action needed. Do not invent facts that are not visible. "
            )
            if caption:
                prompt += f"Telegram caption/context: {caption}"

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=self._vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{content_type};base64,{image_data}",
                                    "detail": "low",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=220,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            print(f"[telegram] Photo vision analysis failed: {exc}", file=sys.stderr)
            return "Image analysis failed; review the attached photo manually."

    def _photo_body(self, caption: str, analysis: str, photo_path: str) -> str:
        filename = os.path.basename(photo_path)
        parts = []
        if caption:
            parts.append(f"Telegram photo caption: {caption}")
        parts.append(f"Image analysis: {analysis}")
        parts.append(f"Attached photo: {filename}")
        return "\n".join(parts)

    def _queue_photo_email(
        self,
        sender_name: str,
        category: str,
        triage_reason: str,
        body: str,
        photo_path: str,
    ) -> None:
        try:
            from dashboard_store import queue_synthetic_draft

            filename = os.path.basename(photo_path)
            recipient = (
                os.getenv("TELEGRAM_PHOTO_FORWARD_TO", "").strip()
                or os.getenv("EMAIL_ADDRESS", "").strip()
                or "project@example.com"
            )
            content_type = mimetypes.guess_type(photo_path)[0] or "image/jpeg"
            draft = (
                "Hello,\n\n"
                "Please review the attached Telegram site photo.\n\n"
                f"Sender: {sender_name}\n"
                f"Triage: {category}\n"
                f"Reason: {triage_reason}\n\n"
                f"{body}\n\n"
                "Best regards,\n"
                "CEM501 Agent"
            )
            queue_synthetic_draft(
                subject=f"Telegram Photo ({category}) - {sender_name}",
                body=body,
                draft=draft,
                sender_email=recipient,
                category=category,
                keyword=triage_reason or "telegram photo",
                sender_name=f"Telegram Photo from {sender_name}",
                attachments=[
                    {
                        "path": photo_path,
                        "filename": filename,
                        "content_type": content_type,
                        "source": "telegram_photo",
                    }
                ],
            )
        except Exception as exc:
            print(f"[telegram] Failed to queue photo email draft: {exc}", file=sys.stderr)

    def _get_or_create_contact(self, name: str) -> int:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT id FROM contacts WHERE name = ?", (name,)).fetchone()
        conn.close()
        if row:
            return row[0]
        return add_contact(name=name, notes="Telegram User")
