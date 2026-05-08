# reader.py Scenarios

## Scenario A: Normal Inbox Read

- Preconditions:
  - `.env` contains valid `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `IMAP_SERVER`
- Input:
  - Inbox contains recent construction emails
- Expected result:
  - Returns parsed sender, sender_email, subject, date, body

## Scenario B: HTML Email

- Input email body:
  - HTML with `<p>`, `<br>`, and inline formatting
- Expected result:
  - `html_to_text()` strips tags and returns readable text

## Scenario C: Missing Credentials

- Remove one required env variable
- Expected result:
  - `require_env()` raises a clear runtime error
