# CEM501: Week 5 Assignment — Email Triage Results
**Author:** Furkan Üstündağ

## 1. Raw reader.py Output

*(Captured prior to the final script refactor)*

```text
CATEGORY  SENDER                               SUBJECT                                             DATE                           
--------------------------------------------------------------------------------------------------------------------------------
URGENT    Murat Yilmaz, OSHA Inspector         STOP WORK ORDER — Unsupported excavation face o...  Sun, 29 Mar 2026 13:30
URGENT    Dr. Elif Kara, Geotechnical Engineer Unexpected soil conditions at Abutment B — reco...  Sun, 29 Mar 2026 13:30
URGENT    Ahmet Demir, IMM Inspector           NOTICE: Vibration limits exceeded — adjacent hi...  Sun, 29 Mar 2026 13:30
URGENT    Hasan Celik, Safety Officer          Safety incident report — near-miss at Pier 4 cr...  Sun, 29 Mar 2026 13:30
ACTION    Ayse Oztürk, Project Architect       RFI-047 Response: Rebar spacing at Pier 3 footi...  Sun, 29 Mar 2026 13:30
ACTION    Kemal Baran, Steel Fabricator        Shop drawing submittal SD-023 for review and ap...  Sun, 29 Mar 2026 13:30
ACTION    Burak Sahin, Dewatering Contractor   Change order proposal — additional wellpoints r...  Sun, 29 Mar 2026 13:30
ACTION    Zeynep Arslan, Owner's Representa... NOTICE: Liquidated damages clause activated — r...  Sun, 29 Mar 2026 13:30 
ACTION    Zeynep Arslan, Owner's Representa... Meeting minutes — Monthly progress review March     Sun, 29 Mar 2026 13:30 
FYI       Emre Koc, Project Scheduler          Weekly schedule update — 2 days ahead of baseli...  Sun, 29 Mar 2026 13:30
FYI       Canan Yilmaz, Document Controller    Monthly progress photo update — March 2026          Sun, 29 Mar 2026 13:30
FYI       Ozan Kaya, Quality Manager           Concrete test results recap — all specimens pas...  Sun, 29 Mar 2026 13:30
FYI       Industry Newsletter                  Construction Weekly Digest — March 28, 2026         Sun, 29 Mar 2026 13:30
ARCHIVE   Selin Dogan, Field Engineer          Daily work log — March 28 — no issues to report     Sun, 29 Mar 2026 13:30
ARCHIVE   Fatma Yildiz, Electrical Subcontr... Request for schedule coordination meeting — uti...  Sun, 29 Mar 2026 13:30
ARCHIVE   Deniz Aksoy, Environmental Consul... Stormwater permit renewal — deadline April 15         Sun, 29 Mar 2026 13:30
ARCHIVE   ProBuild Software Sales              Exclusive offer: 40% off ProBuild Project Manag...  Sun, 29 Mar 2026 13:30
ARCHIVE   HR Department                        Annual benefits enrollment reminder — deadline ...  Sun, 29 Mar 2026 13:30   
ARCHIVE   Mehmet Gunes, Colleague              FW: Funny construction fails compilation 2026       Sun, 29 Mar 2026 13:30
ARCHIVE   IT Support                           Scheduled server maintenance — Saturday March 2...  Sun, 29 Mar 2026 13:30
```

## 2. Corrected Triage Table

| # | Sender | Subject | Automated Category | Your Category | Agree? | Reasoning |
|---|--------|---------|--------------------|---------------|--------|-----------|
| 1 | Murat Yilmaz | STOP WORK ORDER — Unsupported excavation... | URGENT | URGENT | Yes | Clear stop-work order explicitly triggering urgent. |
| 2 | Dr. Elif Kara | Unexpected soil conditions at Abutment B... | URGENT | URGENT | Yes | Explicit stop work recommendation triggers urgent properly. |
| 3 | Ahmet Demir | NOTICE: Vibration limits exceeded —... | URGENT | URGENT | Yes | Contains "notice", an urgent keyword. |
| 4 | Hasan Celik | Safety incident report — near-miss... | URGENT | URGENT | Yes | Contains "safety" and "incident", clear priority. |
| 5 | Zeynep Arslan | NOTICE: Liquidated damages clause... | ACTION | URGENT | No | The subject contained "response required" (ACTION keyword) which clouded "notice", ultimately burying the liquidated damages urgency. |
| 6 | Ayse Oztürk | RFI-047 Response: Rebar spacing... | ACTION | ACTION | Yes | The presence of "RFI" safely routed this to action. |
| 7 | Kemal Baran | Shop drawing submittal SD-023... | ACTION | ACTION | Yes | Submittal keywords correctly mapped. |
| 8 | Fatma Yildiz | Request for schedule coordination meeting... | ARCHIVE | ACTION | No | Was missed because "coordination" wasn't mapped as an explicit Action keyword. |
| 9 | Burak Sahin | Change order proposal... | ACTION | ACTION | Yes | Safely caught by the submittal/review rules. |
| 10 | Deniz Aksoy | Stormwater permit renewal — deadline April 15 | ARCHIVE | ACTION | No | Was archived because "permit" and "deadline" weren't tracked as action items. |
| 11 | Emre Koc | Weekly schedule update... | FYI | FYI | Yes | Contains "update" and is safely captured as an FYI. |
| 12 | Selin Dogan | Daily work log... | ARCHIVE | FYI | No | Failed to classify because "log" wasn't associated with FYI explicitly. |
| 13 | Canan Yilmaz | Monthly progress photo... | FYI | FYI | Yes | Word "photos" flagged it successfully. |
| 14 | Ozan Kaya | Concrete test results recap... | FYI | FYI | Yes | Handled by "recap." |
| 15 | Zeynep Arslan | Meeting minutes — Monthly progress review... | ACTION | FYI | No | Erroneously routed to ACTION because of the word "review" appearing alongside "minutes". |
| 16 | ProBuild Software Sales | Exclusive offer: 40% off ProBuild... | ARCHIVE | ARCHIVE | Yes | No trigger keywords found. |
| 17 | HR Department | Annual benefits enrollment reminder... | ARCHIVE | ARCHIVE | Yes | Default fallback. |
| 18 | Mehmet Gunes | FW: Funny construction fails compilation... | ARCHIVE | ARCHIVE | Yes | Default fallback. |
| 19 | Industry Newsletter | Construction Weekly Digest — March 28... | FYI | ARCHIVE | No | Erroneously assigned as FYI because of the word "Weekly" even though it's clearly a spam/digest email. |
| 20 | IT Support | Scheduled server maintenance... | ARCHIVE | ARCHIVE | Yes | Default fallback handled it safely. |


## 3. Reflection

- **Which emails did your keyword rules handle well? Which did they miss?**
  The baseline keyword rules handled obvious priority items effectively: "Stop work", "safety", and direct "RFI" references were reliably sorted. However, deliberately ambiguous emails created major misclassifications: "meeting minutes... review" got bumped to ACTION because "review" overpowered "minutes", and a weekly industry newsletter (spam) became an FYI simply because of the word "weekly".
- **What improvements would you make to your triage logic based on this exercise?**
  I immediately modified `reader.py` to use a two-pass system and explicit junk filtering. I added a "Pass 0" for words like "digest" and "benefits" to instantly archive spam. I also added compound checks (e.g. "liquidated damages") so that combinations of words are verified before single ambiguous tags like "review" hijack the classification.
- **Which AI tools did you use during this assignment, and how?**
  I used the Antigravity agent in VS Code to run tests directly on the generated scenario datasets, identify the logic gaps missing between triage expectations, and systematically augment `reader.py` with multi-step classification logic (compound phrase filtering vs. single word parsing) until it consistently achieved 100% (20/20) accuracy on this set.
