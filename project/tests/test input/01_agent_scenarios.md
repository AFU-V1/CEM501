# agent.py Scenarios

## Scenario A: Full Week 14 Demo

- Channel: `demo`
- Command: `py agent.py`
- Expected result:
  - Reads 3 realistic construction scenarios
  - Shows message triage summary
  - Drafts responses for RFI, Delay, and Safety
  - Logs activity to `logs/agent.log`

## Scenario B: Email Dry Run

- Channel: `email`
- Command: `py agent.py --channel email --dry-run`
- Input:
  - Inbox contains one RFI email and one delay notice
- Expected result:
  - No real email is sent
  - Drafts are displayed
  - Categories and construction types are shown

## Scenario C: Summary Only

- Command: `py agent.py --summary`
- Expected result:
  - Prints triage table only
  - No drafting or sending step
