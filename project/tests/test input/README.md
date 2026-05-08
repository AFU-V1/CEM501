# Test Input Scenarios

This folder contains scenario inputs for the main Python modules in `project/`.

Goal:

- Give you repeatable test cases for each module
- Support Week 13 and Week 14 demo preparation
- Keep the inputs realistic for construction communication use cases

Recommended order for testing:

1. `01_agent_scenarios.md`
2. `03_classifier_scenarios.md`
3. `04_drafter_scenarios.md`
4. `05_pipeline_scenarios.md`
5. `06_memory_scenarios.md`
6. `07_sender_scenarios.md`
7. `08_scheduler_scenarios.md`
8. `10_email_channel_scenarios.md`
9. `11_demo_channel_scenarios.md`
10. `12_telegram_channel_scenarios.md`

Suggested commands in this environment:

```powershell
py agent.py
py agent.py --channel email --dry-run
py scheduler.py
py run_telegram_bot.py
```

Notes:

- Use the `demo` channel for the most reliable presentation flow.
- Use the `email` channel only after confirming your `.env` values.
- Telegram tests require a valid `TELEGRAM_BOT_TOKEN`.
