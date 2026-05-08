# pipeline.py Scenarios

## Scenario A: New RFI Message

- Input message:
  - Sender: `Mehmet Arslan`
  - Sender email: `mehmet@archdesign.com`
  - Subject: `RFI-042 Beam connection detail`
  - Body: `Please confirm whether Detail 5 on S-204 governs the beam connection.`
  - Channel: `demo`
- Expected result:
  - Contact created or reused
  - Incoming message logged
  - Reply draft generated
  - Follow-up task added

## Scenario B: Duplicate Replay

- Run the same scenario twice
- Expected result:
  - Duplicate received message is not logged again
  - Existing contact is reused

## Scenario C: FYI Report

- Input message:
  - Subject: `Weekly safety report`
  - Body: `No incidents. 98% PPE compliance.`
- Expected result:
  - Category: `FYI`
  - Type: `REPORT`
  - No follow-up task required
