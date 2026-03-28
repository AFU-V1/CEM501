# CEM501: Week 5 Assignment — Email Triage Live Test
## Spring 2026 | Dr. Eyuphan Koc | Bogazici University

---

### Overview

You built `reader.py` in class today — a tool that connects to an email inbox, fetches recent messages, and assigns triage categories using keyword rules. Now it is time to prove that it works on emails you have never seen before.

Over the next few days, you will receive **20 realistic project emails** in your inbox from fictional stakeholders on a construction project. Your job: run your `reader.py` against those emails, review the automated triage results, and submit a corrected analysis.

---

### The Scenario

**Project:** Istanbul Kadikoy Metro Station — Deep Excavation Support System
**Contract Value:** $28M (~900M TRY)
**Duration:** 24 months
**Location:** Kadikoy district, Istanbul

**Scope:** Design-build of a 22-meter-deep excavation with secant pile retaining walls, a dewatering system, and temporary decking over a major urban intersection. The project involves coordination with Istanbul Metropolitan Municipality (IMM), utility relocations, and strict noise/vibration limits due to adjacent historic buildings.

**Your role:** You are the **Project Manager** for the general contractor. All 20 emails are addressed to you.

---

### Timeline

| Step | Date | Action |
|------|------|--------|
| 1 | **Saturday, March 28** (today) | You receive this assignment. Reply to the instructor's email with your chosen email address. |
| 2 | **Sunday, March 29 at 23:59** | Deadline to submit your email address. |
| 3 | **Monday–Tuesday, March 30–31** | You will receive 20 scenario emails in your chosen inbox. |
| 4 | **Sunday, April 5 at 23:59** | Submit your triage results. |

---

### Privacy Option

You are **not required** to use your personal or work email for this exercise. If you prefer to keep your primary inbox private, you may create a **free, dedicated Gmail account** specifically for this assignment (e.g., `yourname.cem501@gmail.com`).

**Requirements for your chosen email:**
- It must support IMAP access (Gmail, Outlook, and most providers do)
- You must be able to generate an App Password for it (Gmail: Settings > Security > App Passwords)
- You must have it set up and working with your `reader.py` **before** the scenario emails arrive

If you use a new account, make sure to test your `reader.py` against it before the deadline by sending yourself a test email first.

---

### What You Will Receive

You will receive **20 individual emails** from fictional project stakeholders. Each email will arrive separately in your chosen inbox over the course of approximately one hour.

The emails will come from the instructor's Gmail account, but the **sender display name** will show the fictional character (e.g., "Ahmet Demir, IMM Inspector"). Your triage logic should use the display name and subject line — not the underlying email address.

The emails span all four triage categories from the lecture:
- **URGENT** — requires immediate action
- **ACTION** — requires a substantive response
- **FYI** — informational, no action needed
- **ARCHIVE** — no value for your workflow

Some emails are straightforward. Others are deliberately ambiguous — the subject line may suggest one category while the body content suggests another. This is by design: real project inboxes are messy, and your triage tool (and your judgment) must handle that.

---

### Deliverables

Submit the following file to your course repository:

**`hw/week05/triage_results.md`**

Your file must contain:

**1. Raw reader.py output (copy-paste from terminal)**

Run your `reader.py` against your inbox after all 20 scenario emails have arrived. Copy the full terminal output showing each email's automated triage category, sender, subject, and date.

**2. Corrected triage table**

Create a markdown table with the following columns:

```
| # | Sender | Subject | Automated Category | Your Category | Agree? | Reasoning |
```

For each of the 20 emails:
- Record what your script assigned (**Automated Category**)
- Record what you believe the correct category is (**Your Category**)
- Mark whether you agree with the automated result
- For any email where you **disagree** with your script, explain in 1–2 sentences why the automated triage was wrong and what signal in the email content changed the category

**3. Brief reflection (3–5 sentences)**

- Which emails did your keyword rules handle well? Which did they miss?
- What improvements would you make to your triage logic based on this exercise?
- Which AI tools did you use during this assignment, and how?

---

### Grading

| Criterion | Weight |
|-----------|--------|
| `reader.py` successfully fetches and displays all 20 scenario emails | 40% |
| Triage categories are assigned automatically via keyword rules | 30% |
| Manual review: you identify and correctly explain misclassifications | 20% |
| Formatting, clarity, AI tool attribution | 10% |

**Scale:** Pass / Needs Revision (one resubmission allowed)

**Important:** Simply running `reader.py` and pasting the output earns at most 70%. The remaining 30% requires human judgment — reviewing what your tool got wrong and explaining why. This is the same principle from the lecture: **you are the decision-maker; the AI is the typist.**

---

### Connection to M2

This assignment is the **practical validation** of your M2 milestone. If your `reader.py` from M2 works correctly, this assignment requires minimal additional code — you simply point it at your chosen inbox and capture the output.

If you have not yet completed M2, use this assignment as motivation to finish it. You cannot complete this assignment without a working `reader.py`.

Your triage output from this exercise will also become useful input data for **Week 6**, where we build a digest generator that summarizes project email threads.

---

### Submission

Push `hw/week05/triage_results.md` to your course repository before **Sunday, April 5 at 23:59**.

---

**Dr. Eyuphan Koc** | eyuphan.koc@bogazici.edu.tr
