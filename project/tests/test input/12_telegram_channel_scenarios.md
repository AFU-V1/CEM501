# channels/telegram_channel.py Scenarios

## Scenario A: Telegram RFI Message

- Message:
  - `RFI: Please confirm whether Detail 5 on S-204 governs the beam connection at Grid B4.`
- Expected result:
  - Category: `ACTION`
  - Type: `RFI`
  - Draft response returned in chat

## Scenario B: Telegram Safety Alert

- Message:
  - `Stop work at Grid C7 due to exposed live utility line.`
- Expected result:
  - Category: `URGENT`
  - Type: `SAFETY`
  - Escalated draft response

## Scenario C: Telegram Status Check

- Command:
  - `/status`
- Expected result:
  - Returns processed message count
