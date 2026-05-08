# classifier.py Scenarios

## Scenario A: RFI

- Subject: `RFI-042 Beam connection detail`
- Body: `Please confirm whether Detail 5 on S-204 governs the beam connection.`
- Expected:
  - Category: `ACTION`
  - Type: `RFI`

## Scenario B: Delay Notice

- Subject: `Notice of delay for concrete pour`
- Body: `Delivery will slip by 24 hours due to plant maintenance.`
- Expected:
  - Category: `URGENT`
  - Type: `DELAY`

## Scenario C: Safety Escalation

- Subject: `Stop work at Grid C7`
- Body: `Crew exposed an unidentified live utility line.`
- Expected:
  - Category: `URGENT`
  - Type: `SAFETY`

## Scenario D: Approval Request

- Subject: `Shop drawing approval required`
- Body: `Please review and return with approval comments by 17:00.`
- Expected:
  - Category: `ACTION`
  - Type: `APPROVAL`

## Scenario E: Non-project Message

- Subject: `Occupational health appointment`
- Body: `Schedule your annual health checkup.`
- Expected:
  - Category: `ARCHIVE`
  - Type: `GENERAL`
