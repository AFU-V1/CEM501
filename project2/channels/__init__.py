"""
channels — Multi-channel communication abstraction layer.

Provides a unified interface for receiving and sending messages
across different platforms (email, Telegram, etc.).
"""

from channels.base import Channel

__all__ = ["Channel"]
