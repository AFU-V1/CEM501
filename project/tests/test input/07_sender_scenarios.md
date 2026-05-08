# sender.py Scenarios

## Scenario A: Dry Run Review

- Command path:
  - Called through `py agent.py --channel email --dry-run`
- Expected result:
  - Draft displayed
  - No real send
  - Guardrail warnings visible if applicable

## Scenario B: Unknown Recipient Warning

- Recipient:
  - `newvendor@example.com`
- Expected result:
  - Warning that recipient is not in known contacts

## Scenario C: Suspicious Domain

- Recipient:
  - `supplier@gmial.com`
- Expected result:
  - Suspicious domain warning

## Scenario D: Placeholder Detection

- Body:
  - `Please review [TODO] and reply.`
- Expected result:
  - Placeholder warning shown
