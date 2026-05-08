# channels/email_channel.py Scenarios

## Scenario A: Fetch Standardized Messages

- Command path:
  - Used through `py agent.py --channel email --dry-run`
- Expected result:
  - Email adapter returns normalized dicts with sender, reply_to, subject, text, channel

## Scenario B: Send Through Guarded Sender

- Input:
  - Valid recipient and generated draft
- Expected result:
  - Delegates sending to `sender.py`
  - Reuses the same review guardrails
