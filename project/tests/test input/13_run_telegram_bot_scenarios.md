# run_telegram_bot.py Scenarios

## Scenario A: Bot Startup

- Command: `py run_telegram_bot.py`
- Preconditions:
  - Valid `TELEGRAM_BOT_TOKEN`
- Expected result:
  - Bot starts polling
  - Terminal shows startup banner

## Scenario B: Missing Token

- Remove or blank `TELEGRAM_BOT_TOKEN`
- Expected result:
  - Clear runtime error on startup
