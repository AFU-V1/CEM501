"""Base interface for communication channel adapters."""


class Channel:
    """Every communication channel must implement the same small contract."""

    def fetch_messages(self) -> list[dict]:
        """Return standardized incoming messages for the shared pipeline."""
        raise NotImplementedError("Subclasses must implement fetch_messages()")

    def send_message(
        self,
        recipient: str,
        text: str,
        subject: str = "",
        dry_run: bool = False,
    ) -> bool:
        """Send a message back through the underlying channel."""
        raise NotImplementedError("Subclasses must implement send_message()")

    @property
    def channel_name(self) -> str:
        """Human-readable channel name such as 'email' or 'telegram'."""
        raise NotImplementedError("Subclasses must define channel_name")
