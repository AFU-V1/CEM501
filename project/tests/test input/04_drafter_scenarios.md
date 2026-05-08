# drafter.py Scenarios

## Scenario A: RFI Reply Draft

- Input:
  - Category: `ACTION`
  - Type: `RFI`
  - Subject: `RFI-042 Beam connection detail`
  - History: prior architect coordination messages
- Expected result:
  - Professional acknowledgment
  - States review and response timing

## Scenario B: Delay Reply Draft

- Input:
  - Category: `URGENT`
  - Type: `DELAY`
  - Subject: `Notice of delay for raft foundation concrete pour`
- Expected result:
  - Immediate acknowledgment
  - Mentions rescheduling or impact review

## Scenario C: Fallback Mode

- Preconditions:
  - Invalid or missing `OPENAI_API_KEY`
- Expected result:
  - Uses fallback template without crashing
