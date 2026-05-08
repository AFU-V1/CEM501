"""Demo channel for reliable final-presentation scenarios."""

from __future__ import annotations

import json
import os

from channels.base import Channel

DEFAULT_SCENARIO_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scenarios",
    "demo_scenarios.json",
)


class DemoChannel(Channel):
    """Load realistic construction scenarios from JSON for live demos."""

    channel_name = "demo"

    def __init__(self, scenario_file: str | None = None):
        self._scenario_file = scenario_file or DEFAULT_SCENARIO_FILE
        if not os.path.exists(self._scenario_file):
            raise RuntimeError(f"Scenario file not found: {self._scenario_file}")

    def fetch_messages(self) -> list[dict]:
        with open(self._scenario_file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        messages = []
        for item in payload.get("scenarios", []):
            sender_email = item.get("sender_email", "")
            messages.append({
                "sender": item.get("sender", sender_email or "Unknown Sender"),
                "sender_email": sender_email,
                "reply_to": sender_email,
                "subject": item.get("subject", "No subject"),
                "text": item.get("body", ""),
                "channel": self.channel_name,
                "scenario_name": item.get("name", "Unnamed scenario"),
                "scenario_notes": item.get("notes", ""),
            })
        return messages

    def send_message(
        self,
        recipient: str,
        text: str,
        subject: str = "",
        dry_run: bool = False,
    ) -> bool:
        mode = "DRY RUN" if dry_run else "DEMO"
        print("\n" + "=" * 60)
        print(f">>> {mode} RESPONSE")
        print("=" * 60)
        print(f"  To:      {recipient or 'demo-contact'}")
        print(f"  Subject: Re: {subject}")
        print("-" * 60)
        print(text)
        print("-" * 60)
        print("  [OK] Demo response displayed.")
        return True
