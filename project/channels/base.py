"""
base.py — Channel base class (the "universal adapter").

Every communication channel must inherit from this class and implement
the fetch_messages() and send_message() methods. This abstraction
allows the agent's core logic (classify → draft → respond) to work
identically regardless of the underlying platform.

CEM501 — Milestone M6: Multi-Channel Integration
"""


class Channel:
    """Base class — every communication channel must implement these methods."""

    def fetch_messages(self) -> list[dict]:
        """
        Pull new incoming messages from this channel.

        Returns a list of dicts, each containing at minimum:
            - "sender": str — who sent the message
            - "text": str — the message content
            - "channel": str — which channel it came from
        """
        raise NotImplementedError("Subclasses must implement fetch_messages()")

    def send_message(self, recipient: str, text: str) -> bool:
        """
        Send a message through this channel.

        Args:
            recipient: The target (email address, chat ID, etc.)
            text: The message body to send.

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement send_message()")

    @property
    def channel_name(self) -> str:
        """Human-readable name of this channel (e.g., 'email', 'telegram')."""
        raise NotImplementedError("Subclasses must define channel_name")
