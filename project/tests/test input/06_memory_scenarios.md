# memory.py Scenarios

## Scenario A: Create Contact

- Input:
  - Name: `Ayse Ozkan`
  - Email: `ayse@riverfront.com`
  - Role: `Owner's Representative`
- Expected result:
  - Contact row added to SQLite

## Scenario B: Log Message

- Input:
  - Direction: `received`
  - Subject: `Meeting minutes`
  - Channel: `email`
- Expected result:
  - Row appears in `message_history`

## Scenario C: Add Task

- Input:
  - Description: `Follow up on RFI-042`
  - Due date: two days ahead
- Expected result:
  - Pending task appears in `scheduled_tasks`

## Scenario D: Seed Database

- Command:
  - Call `seed_database()`
- Expected result:
  - Realistic construction contacts, messages, and tasks are present
