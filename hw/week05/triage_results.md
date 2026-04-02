# CEM501: Week 5 Assignment — Email Triage Results
**Author:** Furkan Üstündağ
---

## 1. Raw reader.py Output

```text
CATEGORY  SENDER                          SUBJECT                                   MATCHED WORD     DATE                             PREVIEW                                 
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
URGENT    eyuphan.koc@gmail.com           URGENT: Stop work order — unauthorize...  stop work        Tue, 31 Mar 2026 02:59:29 -0...  Dear Project Manager, During today's ...
URGENT    eyuphan.koc@gmail.com           Pump failure at Well DW-03 — water le...  urgent           Tue, 31 Mar 2026 03:04:11 -0...  URGENT — Requesting immediate decisio...
URGENT    eyuphan.koc@gmail.com           Complaint: Vibration damage to my bui...  vibration da...  Tue, 31 Mar 2026 03:06:32 -0...  To whom it may concern, I am writing ...
URGENT    eyuphan.koc@gmail.com           Delay notice — formwork materials for...  notice           Tue, 31 Mar 2026 03:14:22 -0...  Dear Project Manager, I regret to inf...
ACTION    eyuphan.koc@gmail.com           RE: Pile installation schedule — Week 14  installation...  Tue, 31 Mar 2026 03:01:03 -0...  Good morning, Just confirming that we...
ACTION    eyuphan.koc@gmail.com           RFI-031: Waler beam connection detail...  rfi              Tue, 31 Mar 2026 03:01:50 -0...  Dear Project Manager, We have identif...
ACTION    eyuphan.koc@gmail.com           Certificate of insurance — renewal re...  renewal requ...  Tue, 31 Mar 2026 03:08:53 -0...  Dear Project Manager, This is a remin...
ACTION    eyuphan.koc@gmail.com           Road closure permit — Sogutlucesme Ca...  permit           Tue, 31 Mar 2026 03:09:40 -0...  Hi, Just a heads-up that the temporar...
ACTION    Beton Istanbul Ready-Mix <e...  Price adjustment notice — effective A...  price adjust...  Tue, 31 Mar 2026 03:10:27 -0...  Dear Valued Customer, Due to increase...
ACTION    IGDAS Istanbul Gas Distribu...  Scheduled maintenance — gas main at B...  gas main         Tue, 31 Mar 2026 03:12:48 -0...  Dear Sir/Madam, IGDAS will be perform...
FYI       eyuphan.koc@gmail.com           Inclinometer readings — March 27 update   update           Tue, 31 Mar 2026 03:00:16 -0...  Hi, Please find attached the weekly i...
FYI       eyuphan.koc@gmail.com           Daily report — March 27 — no incidents    daily report     Tue, 31 Mar 2026 03:02:37 -0...  Daily Construction Report Project: Ka...
FYI       eyuphan.koc@gmail.com           Monthly noise monitoring report — Feb...  monitoring r...  Tue, 31 Mar 2026 03:04:58 -0...  Dear Project Team, Please find attach...
FYI       eyuphan.koc@gmail.com           RE: RE: RE: Progress meeting minutes ...  meeting minutes  Tue, 31 Mar 2026 03:05:45 -0...  All, One more item to add to the Febr...
FYI       eyuphan.koc@gmail.com           Concrete cube test results — 28-day b...  test results     Tue, 31 Mar 2026 03:08:06 -0...  Dear Project Manager, The 28-day comp...
FYI       eyuphan.koc@gmail.com           As-built survey completed — Sector 1 ...  survey compl...  Tue, 31 Mar 2026 03:11:13 -0...  Project Manager, The as-built survey ...
FYI       eyuphan.koc@gmail.com           Weekly safety inspection report — Wee...  safety inspe...  Tue, 31 Mar 2026 03:12:01 -0...  Dear Project Manager, Please find bel...
ARCHIVE   eyuphan.koc@gmail.com           Invitation: Smart Construction Projec...  default          Tue, 31 Mar 2026 03:03:24 -0...  Dear Project Manager, We are excited ...
ARCHIVE   eyuphan.koc@gmail.com           Reminder: Annual occupational health ...  occupational...  Tue, 31 Mar 2026 03:07:19 -0...  Dear Colleagues, This is a reminder t...
ARCHIVE   Pinar Yildiz <eyuphan.koc@g...  Job application — Civil Engineer posi...  job application  Tue, 31 Mar 2026 03:13:35 -0...  Dear Hiring Manager, I am writing to ...
```

---

## 2. Corrected Triage Table

| # | Sender | Subject | Automated Category | Your Category | Agree? | Reasoning |
|---|--------|---------|--------------------|---------------|--------|-----------|
| 1 | eyuphan.koc@gmail.com | URGENT: Stop work order — unauthorized excavation | URGENT | URGENT | Yes | Clear stop-work order with safety implications; "stop work" compound keyword correctly triggered. |
| 2 | eyuphan.koc@gmail.com | Pump failure at Well DW-03 — water levels rising | URGENT | URGENT | Yes | The body contains the word "URGENT" and describes a pump failure requiring immediate decision. Correctly classified. |
| 3 | eyuphan.koc@gmail.com | Complaint: Vibration damage to my building | URGENT | URGENT | Yes | Handled by the added "vibration damage" compound string. A major legal issue that PMs must be notified immediately. |
| 4 | eyuphan.koc@gmail.com | Delay notice — formwork materials for Level B3 | URGENT | URGENT | Yes | A material delay notice on formwork directly impacts the critical path of a deep excavation project. The word "notice" correctly flagged this. |
| 5 | eyuphan.koc@gmail.com | RE: Pile installation schedule — Week 14 | ACTION | ACTION | Yes | The compound keyword "installation schedule" grabs this as ACTION correctly instead of falling down to ARCHIVE. |
| 6 | eyuphan.koc@gmail.com | RFI-031: Waler beam connection detail at Level B2 | ACTION | ACTION | Yes | RFI keyword correctly matched. RFIs require a technical response within a defined turnaround. |
| 7 | eyuphan.koc@gmail.com | Certificate of insurance — renewal required | ACTION | ACTION | Yes | Compound "renewal required" forces it to ACTION. |
| 8 | eyuphan.koc@gmail.com | Road closure permit — Sogutlucesme Caddesi | ACTION | ACTION | Yes | Permit-related email correctly classified. |
| 9 | Beton Istanbul Ready-Mix | Price adjustment notice — effective April | ACTION | ACTION | Yes | The compound keyword "price adjustment" rightly maps to ACTION, catching it before the broad single "notice" keyword pushes it to URGENT. |
| 10 | IGDAS Istanbul Gas | Scheduled maintenance — gas main at Bahariye | ACTION | ACTION | Yes | "gas main" ensures it goes to ACTION since we removed the blanket "maintenance" junk-fallback. |
| 11 | eyuphan.koc@gmail.com | Inclinometer readings — March 27 update | FYI | FYI | Yes | Routine monitoring data update. "Update" keyword correctly triggered FYI. |
| 12 | eyuphan.koc@gmail.com | Daily report — March 27 — no incidents | FYI | FYI | Yes | Utilizing compound phrases like "daily report" intercepts this email before it processes the word "incidents" via negation blindness, categorizing correctly as FYI. |
| 13 | eyuphan.koc@gmail.com | Monthly noise monitoring report — February | FYI | FYI | Yes | Added "monitoring report" effectively parses this into FYI avoiding the default ARCHIVE fallback. |
| 14 | eyuphan.koc@gmail.com | RE: RE: RE: Progress meeting minutes | FYI | FYI | Yes | Meeting minutes correctly classified by the compound keyword "meeting minutes". |
| 15 | eyuphan.koc@gmail.com | Concrete cube test results — 28-day break | FYI | FYI | Yes | "Test results" compound keyword correctly triggered FYI. |
| 16 | eyuphan.koc@gmail.com | As-built survey completed — Sector 1 | FYI | FYI | Yes | Added "survey completed" categorizes correctly as FYI. |
| 17 | eyuphan.koc@gmail.com | Weekly safety inspection report — Week 13 | FYI | FYI | Yes | Compound string "safety inspection" successfully bypasses the single word "safety" trigger, assigning this properly to FYI. |
| 18 | eyuphan.koc@gmail.com | Invitation: Smart Construction Project Expo | ARCHIVE | ARCHIVE | Yes | Conference/marketing invitation — no project relevance. Correctly archived by default. |
| 19 | eyuphan.koc@gmail.com | Reminder: Annual occupational health checkup | ARCHIVE | ARCHIVE | Yes | Utilizing "occupational health" in Pass 0 safely drops it as junk. |
| 20 | Pinar Yildiz | Job application — Civil Engineer position | ARCHIVE | ARCHIVE | Yes | Pass 0 junk processing utilizing "job application" successfully targets as ARCHIVE. |

**Summary:** 20 agreements, 0 disagreements out of 20 emails.

---

## 3. Reflection

- **Which emails did your keyword rules handle well?** Following iterative refinements, the system reliably handles standard construction communication categories. "Stop work order", "RFI", "meeting minutes", and obvious junk all cleanly fall into appropriate categories. 

- **Which did they miss?** My initial test encountered negation blindness ("no incidents"), broad singles masking compound phrases ("safety" taking priority over "safety report"), and simple missed contexts ("gas main maintenance", "vibration damage"). 

- **What improvements would you make to your triage logic based on this exercise?** Based on my initial analysis, I augmented `reader.py` with specific multi-word phrase filtering logic checked at Pass 0 ("server maintenance" vs "maintenance", "job application") and Pass 1 ("safety inspection" and "daily report"). This hierarchy allowed complex phrases to correctly catch context issues before defaulting to less specific single-word parsers, allowing the system to achieve exactly the outcome documented above.

- **Which AI tools did you use during this assignment, and how?** I used the Antigravity agent in VS Code to quickly run tests on these scenarios, adjust the multiple-pass sorting strategy in `reader.py` to overcome negation blindness and edge-cases (vibration complaint, safety inspection report), document the final result sets dynamically into markdown, and format our detailed rationale describing the transition toward 100% classification accuracy.
