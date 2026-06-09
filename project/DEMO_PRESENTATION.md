# CEM501 Final Demo — AI-Powered Construction Communication Agent

**Student:** A. Furkan Ustundag  
**Course:** CEM501 Communication Skills for CEM — Spring 2026  
**Instructor:** Dr. Eyuphan Koc — Bogazici University  

---

## Slide 1 — The Problem (Minute 0–1)

### Construction PMs Are Drowning in Email

A project manager on a multi-subcontractor construction project like the **Bogazici Library Project** receives **30–50 project emails every day**:

- RFI responses with tight deadlines  
- Delay notices with contractual consequences  
- Safety stop-work orders requiring immediate action  
- Insurance renewals, inspection reports, meeting requests  

**Each email has a different urgency, a different stakeholder, and a different deadline.**

| The Cost of Missing One Email | Impact |
|-------------------------------|--------|
| Missed OSHA safety notice | Site shutdown + fines |
| Late RFI response | Weeks of schedule delay |
| Wrong recipient on delay notice | Contractual liability |
| Ignored insurance renewal | Work stoppage |

> **The average PM spends 2–3 hours per day just sorting and responding to email.**  
> My agent reduces that to **under 5 minutes**.

---

## Slide 2 — Architecture Overview (Minute 1–2)

### One Unified Pipeline — Two Input Channels

```
+-------------+      +--------------+      +------------------+
| IMAP Inbox  |----->| Email Reader |----->| Shared Triage    |
| Gmail       |      | reader.py    |      | Gate + Cache     |
+-------------+      +--------------+      +----+--------+----+
                                             |        |
                                  cache hit  |        | cache miss
                                             |        v
+------------------+  text/voice/photo  +------------------+
| Telegram Bot API |------------------->| OpenAI APIs      |
| text / voice /   |                    | triage/drafting  |
| photo messages   |                    | transcription    |
+------------------+                    | photo vision     |
                                        +--------+---------+
                                             |           |
                                             |           | category/reason
                                             v           v
                                     +-------------------------+
                                     | Classified Message      |
                                     | sender/subject/body     |
                                     | category/reason/summary |
                                     +-----------+-------------+
                                                 |
                                                 v
                                     +-------------------------+
                                     | Web Dashboard           |
                                     | Triage Inbox            |
                                     | Approval Flow           |
                                     | Message History         |
                                     | Daily Reports / Digests |
                                     +-----+-------------+-----+
                                           |             |
                                           v             v
                                     +-----------+   +------------------+
                                     | SMTP Send |   | SQLite Memory    |
                                     | (approved)|   | contacts/history |
                                     +-----------+   +------------------+
```

**Three key design principles:**

1. **Semantic triage, not keywords** — OpenAI understands context (e.g., a concrete test failure → URGENT, even without the word "urgent")
2. **Human-in-the-loop** — The agent drafts, but the PM approves. Nothing is sent automatically.
3. **One pipeline** — Email and Telegram messages use the same AI classification engine

---

## Slide 3 — Live Demo: Scenario 1 (Minutes 2–3)

### "The PM's Morning" — Triage Inbox

**Action:** Open dashboard → Click **"Load Demo Snapshot"** or **"Refresh Live Inbox"**

**What happens:**
- 11 emails appear, already classified by OpenAI:
  - 🔴 **URGENT (2):** OSHA fall protection deficiency, Pier 5 delay notice
  - 🟠 **ACTION (3):** RFI-047 response, delivery schedule change, meeting agenda
  - 🔵 **FYI (4):** Safety stats, insurance renewal, photo album, newsletter
  - ⚪ **ARCHIVE (2):** Low-priority items

**Key point to show:**
> "The OSHA email is flagged URGENT because the AI understood it is a safety stop-work order — not because it contains the word 'urgent.' This is semantic classification."

**Also show:** The reason text next to each email (e.g., *"Stop work order due to safety risk"*)

---

## Slide 4 — Live Demo: Scenario 2 (Minutes 3–4.5)

### "Reviewing and Approving a Reply" — Approval Flow

**Action:** Click on the **OSHA fall protection** email in the Review Queue

**What to demonstrate:**

| Step | What to Show |
|------|-------------|
| 1 | Original email body (the inspector's message) |
| 2 | AI-drafted reply (acknowledges deficiency, references Level 4 east scaffolding, commits to corrective action plan within 24 hours) |
| 3 | Edit the **CC** field — add the site safety officer |
| 4 | Click **"Approve Dry Run"** |
| 5 | Status changes to "approved" — no real email sent |

**Key point:**
> "The draft is professional and context-aware, but I can still edit the recipient, CC, subject, and body. Nothing gets sent without my explicit approval. This is the human-in-the-loop principle."

---

## Slide 5 — Live Demo: Scenario 3 (Minutes 4.5–5)

### "End of Day" — Daily Report Generation

**Action:** Go to **Message History** → Select relevant rows → Click **"Generate Daily Report"**

**What to demonstrate:**

- Select 3–4 messages from today's communication
- Click "Generate Daily Report"
- Show the generated report:
  - **Report No:** DR-001 (auto-incrementing)
  - **Date:** Today's date (auto-filled)
  - **Project:** Bogazici Library Project
  - **Location:** Besiktas/Istanbul
  - **Prepared by:** A. Furkan Ustundag
  - **Contract No:** B-2026-1234
  - **Shift:** Day Shift / 08:00–18:00

**Key point:**
> "The daily report is generated from actual project communication — not from a template with placeholder data. Report numbers increment automatically."

---

## Slide 6 — Lessons Learned (Minute 5–6)

### Technical Lesson: Caching Changes Everything

> "The first time I refreshed the inbox, every email went to OpenAI — it took 30 seconds and cost real money. I built a **triage cache** that stores results by content hash. Now, refreshing a 20-email inbox takes **2 seconds** because only new or changed emails hit the API. This taught me that in production, you need to think about **cost and latency from day one**, not as an optimization later."

### Communication Lesson: Making Implicit Rules Explicit

> "Building this agent forced me to articulate rules I never thought about consciously. When should an RFI response be sent within 24 hours versus 3 days? When does a delay notice need formal contractual language versus a conversational tone? I had to encode these as AI prompts. That process made me realize how much **unwritten professional knowledge** goes into a single construction email."

---

## Slide 7 — What's Next + Closing (Minute 6–7)

### Future Improvements

| Feature | Why It Matters |
|---------|---------------|
| **PDF/DOCX attachment parsing** | RFIs, submittals, and inspection reports arrive as attachments — the agent should read them |
| **Turkish-English bilingual support** | Istanbul projects switch between languages constantly |
| **Production Cron scheduler** | Daily digests at 08:00 without pressing a button |
| **Confidence-aware routing** | Low-confidence classifications get flagged for manual review |

### Closing Statement

> **"This agent gives a construction project manager their mornings back. Instead of spending two hours sorting through email, they spend five minutes reviewing AI-classified messages and approving drafts. That is ten hours a week returned to actual project management. Thank you."**

---

## Q&A Preparation (3 Minutes)

### Technical Questions

| Likely Question | Answer |
|----------------|--------|
| "Why gpt-4o-mini instead of gpt-4o?" | Cost and speed. For triage, the smaller model gives equally accurate categories at 1/10th the cost. For 50 emails/day, that matters. |
| "What if OpenAI is down?" | Every AI operation has a fallback. Failed triage → ACTION with "review manually." Failed draft → template. The PM always sees the email. |
| "How do you handle misclassification?" | The approval flow catches it. No email goes out based on classification alone — the human decides. |
| "Why SQLite not PostgreSQL?" | Clone-and-run simplicity. Zero config needed. For a single-PM tool, SQLite concurrency is not a problem. |

### Communication Questions

| Likely Question | Answer |
|----------------|--------|
| "How did this change how you think about email?" | I used to think urgency was obvious. Building triage rules showed me urgency is contextual — a concrete test result is routine until it fails spec, then it is a stop-work situation. |
| "Could this replace a project coordinator?" | No. The agent handles classification and drafting, but judgment — when to escalate, how to negotiate, which relationships to protect — requires human experience. |

### If You Don't Know

> "That's a good question. I haven't tested that scenario, but based on how the system works, my hypothesis is [brief answer]. I would need to investigate further to confirm."

---

## Bonus Features (for +0.2)

- ✅ **Telegram integration** — text, voice transcription, and photo vision analysis
- ✅ **Exceptional logging** — `agent.log` with full audit trail
- ✅ **Overdue task projection** — unanswered URGENT/ACTION emails from prior days

---

*CEM501 — Spring 2026 — Dr. Eyuphan Koc — Bogazici University*
