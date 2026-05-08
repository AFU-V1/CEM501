"""
run_telegram_bot.py — Launch the Telegram agent bot.

This is the entry point to start the Telegram channel.
It loads credentials from .env and starts polling for messages.

Usage:
    py run_telegram_bot.py
"""

from channels.telegram_channel import TelegramChannel


def main():
    bot = TelegramChannel()
    bot.run()


if __name__ == "__main__":
    main()
