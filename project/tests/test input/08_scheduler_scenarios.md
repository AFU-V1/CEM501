# scheduler.py Scenarios

## Scenario A: Single Run

- Command: `py scheduler.py`
- Expected result:
  - Morning summary printed
  - Weekly summary printed
  - Pending and overdue tasks shown

## Scenario B: Continuous Loop

- Command: `py scheduler.py --loop`
- Expected result:
  - Periodic overdue checks
  - Daily and weekly jobs scheduled

## Scenario C: Seed First

- Command: `py scheduler.py --seed`
- Expected result:
  - Database seeded before scheduler output
