# CEM501: Communication Skills for CEM
## Week 5: Reading & Triaging Email with AI Tools (Strand B)
**Spring 2026 | Dr. Eyuphan Koc | Bogazici University**

---

### Session Plan (150 min)

| Block | Time | Duration |
|-------|------|----------|
| **Lecture: Parts I–II** (Email overload problem, four-bucket triage framework) | 0:00 – 0:35 | 35 min |
| **Lecture: Part III** (How IMAP works under the hood) | 0:35 – 0:45 | 10 min |
| **Lecture: Part IV** (AI-assisted workflow, describe-review-test-iterate) | 0:45 – 0:55 | 10 min |
| **Tool Demo** — live Claude Code session building `reader.py` | 0:55 – 1:10 | 15 min |
| **Activity 1: Email Triage Drill** — pairs categorize 15 project emails | 1:10 – 1:30 | 20 min |
| **Activity 2: Build Session** — students build their own `reader.py` | 1:30 – 2:10 | 40 min |
| **Wrap-up** — summary, M2 milestone review, Week 6 preview | 2:10 – 2:25 | 15 min |
| **Buffer** | 2:25 – 2:30 | 5 min |

---

### Learning Objectives

- Quantify the email overload problem in CEM using real industry data
- Understand why construction emails carry unique contractual and legal weight
- Apply a four-bucket triage framework (URGENT / ACTION / FYI / ARCHIVE) to categorize project emails
- Understand IMAP at a conceptual level — just enough to know what your code will do
- Use the describe-review-test-iterate workflow with Claude Code to build an email reader module
- Complete the foundation for Milestone M2

---

## Part I: The Email Overload Problem in CEM
**(~20 min lecture)**

### 1.1 The Numbers: How Much Email Do Professionals Handle?

Email is not going away. Despite Slack, Teams, WhatsApp, and every other messaging tool, email remains the backbone of professional communication — especially in industries where documentation matters.

Here is what the data tells us:

| Statistic | Value | Source |
|-----------|-------|--------|
| Global daily email volume | ~361 billion emails/day | Statista (2024) |
| Business emails per user per day | ~120-126 sent and received | Radicati Group, Email Statistics Report (2024-2028) |
| Percentage of workweek spent on email | **28%** (~13 hours/week) | McKinsey Global Institute (2012) |
| Annual hours spent on email per worker | ~580 hours/year | Derived from McKinsey data |
| Time to refocus after an email interruption | 23 minutes | Gloria Mark, UC Irvine research |
| Percentage of emails that are spam | ~49% | EmailToolTester (2024) |
| Email volume growth trend | 73% of professionals say volume increased in last 12 months | Mailbird Survey (2024) |
| CEM-specific email load | **3 to 3.5 hours per day** on emails alone | CooperLink / RICS (2023) |

Think about the McKinsey number: **28% of your workweek**. That is more than one full day per week — Monday plus Tuesday morning — spent reading, writing, and responding to email. For construction project managers who already work 50-60 hour weeks, this translates to 14-17 hours per week on email alone.

*Sources: McKinsey Global Institute (2012). ["The Social Economy: Unlocking Value and Productivity through Social Technologies."](https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/the-social-economy) Radicati Group (2024). ["Email Statistics Report, 2024-2028."](https://www.radicati.com/?p=18519)*

---

### 1.2 The CEM-Specific Challenge: Emails Have Contractual Weight

For most professionals, a missed email is an inconvenience. For construction professionals, a missed email can be a **legal liability**.

This is the fundamental difference that makes email management in CEM uniquely high-stakes. Construction law firm Smith, Currie & Hancock puts it bluntly: **every email you send or receive on a project becomes part of the project record** and may have to be produced to an opposing party if there is a construction dispute, litigation, or arbitration.

Consider the unique CEM email environment:

- **Multi-stakeholder communication.** A single project involves owners, architects, engineers, general contractors, subcontractors, suppliers, inspectors, and regulators. Each stakeholder generates emails daily, and the project manager sits at the hub of all of it.
- **Contractual documentation.** An email confirming a change in scope, acknowledging a delay, or directing additional work can create or modify contractual obligations — whether you intended it to or not.
- **The "24-hour rule" problem.** Smith Currie advises construction professionals to wait 24 hours before responding to adversarial emails to avoid emotionally charged language that becomes a permanent record. But urgent project issues do not always allow that luxury.
- **Discovery in disputes.** When a $60 million construction dispute goes to arbitration (recall the Arcadis 2025 data from Week 1), lawyers will comb through *every email* on the project. Your casual Friday afternoon reply is now Exhibit 47.

> **Key Insight:** In most professions, email is a communication tool. In CEM, email is simultaneously a communication tool, a contractual instrument, and a legal record. Every email you send could be read aloud in an arbitration hearing. Write accordingly.

*Source: Smith, Currie & Hancock LLP. ["Effective Use of Email for Construction Project Communications and Documentation."](https://www.smithcurrie.com/publications/common-sense-contract-law/effective-use-of-email-for-construction-project-communications-and-documentation/)*

> **[DISCUSS]** Have you encountered — or heard of — a situation where a casual email on a construction project took on contractual or legal significance? What would you do differently knowing that every email becomes part of the project record?

---

### 1.3 The Information Overload Spiral

The sheer volume of project correspondence is staggering. Recall from Week 1:

- A $50 million project may generate **~500 RFIs**, each consuming an average of **8 hours** to process.
- Daily reports, submittals, meeting minutes, change orders, safety briefings, schedule updates, and claims correspondence pile up alongside routine emails.
- Documents shared via email threads are not searchable across the project team — critical information ends up trapped in individual inboxes.

Research by Tam et al. (2006) on information overload in the construction industry found that excessive information gathering subjects project managers to cognitive overload, which **distracts rather than concentrates their attention**. Their study of construction project teams concluded that the core problem is not too much information per se, but too little *high-value* information — managers drown in noise while critical signals go unnoticed.

> **Key Insight:** The real cost of email overload is not the time spent reading — it is the critical email you *missed* because it was buried between a vendor marketing blast and a 15-reply CC chain. An unanswered RFI stalls the schedule. An unread stop-work notice creates a safety hazard. An overlooked change-order discussion costs real money.

*Sources: Aljassmi, H. & Han, S. (2013). "Analysis of Causes of Construction Defects Using Fault Trees and Risk Importance Measures." Journal of Construction Engineering and Management, 139(11). See also: Tam, C.M. et al. (2006). ["Overload of Information or Lack of High Value Information: Lessons Learnt from Construction."](https://www.researchgate.net/publication/48353142_Overload_of_information_or_lack_of_high_value_information_Lessons_learnt_from_construction)*

---

## Part II: Triage Strategies — The Four-Bucket Framework
**(~15 min lecture)**

### 2.1 The Eisenhower Principle, Adapted for CEM

The Eisenhower Matrix — originally a decision-making tool attributed to President Dwight D. Eisenhower, who reportedly said *"What is important is seldom urgent and what is urgent is seldom important"* — divides tasks into four quadrants based on urgency and importance. We adapt this into a **Four-Bucket Framework** specifically designed for construction project email:

| Bucket | Definition | CEM Examples | Target Response Time |
|--------|-----------|--------------|---------------------|
| **URGENT** | Requires immediate action; safety, contractual deadlines, or critical-path impact | Stop-work notice from inspector; safety incident report; notice of delay with contractual time-bar deadline; concrete pour cancellation due to weather | **Within hours** |
| **ACTION** | Requires a substantive response or task from you, but not immediately | RFI from architect requesting rebar spacing clarification; submittal review request with 10-day turnaround; subcontractor requesting schedule coordination meeting | **Within 24 hours** |
| **FYI** | Informational — you should be aware, but no action required | Weekly progress photo update; meeting recap you attended; daily log acknowledgment; project newsletter from owner | **Read when able** |
| **ARCHIVE** | No value for your current workflow | Vendor marketing email; outdated thread replies; company HR announcements unrelated to your project; spam | **File or delete** |

---

### 2.2 Triage Rules of Thumb for CEM

Not every email announces its priority in the subject line. Here are heuristics that experienced project managers use:

**Rule 1: Sender hierarchy matters.**
An email from the owner, architect-of-record, or a regulatory inspector defaults to at least ACTION, regardless of subject. An email from a vendor you have never worked with defaults to ARCHIVE until proven otherwise.

**Rule 2: Subject-line keywords are signals.**
Words like "urgent," "stop work," "safety," "notice," "time extension," "claim," "change order," and "RFI" should trigger elevated attention. Your email reader can look for these programmatically.

**Rule 3: Attachments raise priority.**
Emails with drawings, specifications, schedules, or contractual documents attached are almost never ARCHIVE. If someone took the time to attach a PDF, they expect you to read it.

**Rule 4: CC depth is inversely correlated with urgency to you.**
If you are one of 15 people CC'd on a long thread, it is likely FYI. If you are the sole recipient, it is likely ACTION or URGENT.

**Rule 5: Time-bar language is always URGENT.**
Any email containing phrases like "within 7 days," "failure to respond will constitute acceptance," or "per Section 4.3.1 of the General Conditions" is contractually significant and demands immediate attention.

> **Key Insight:** Triage is not about reading every email thoroughly. It is about spending 3-5 seconds per email to put it in the right bucket, then processing each bucket in priority order. The goal is to make sure nothing URGENT sits unread while you craft a perfect reply to an FYI.

> **[DISCUSS]** Which of the five triage rules above do you find most intuitive? Which is most surprising? Can you think of a sixth rule specific to your own experience or field of interest?

---

### 2.3 What the Research Says About Triage

Research on email management productivity — including data from the McKinsey Global Institute and the Radicati Group reports cited above — suggests that only about **40% of emails demand same-day action**, while over a third can be ignored entirely. Experts recommend dedicating **15-30 minutes, one to three times daily**, to triage your inbox — rather than checking email continuously throughout the day.

The concept of "Inbox Zero" — popularized by productivity consultant Merlin Mann — is often misunderstood. It does not mean having zero emails. It means having **zero unprocessed emails**: every message has been triaged into a bucket and will be handled at the appropriate time.

For CEM professionals, the stakes of getting triage wrong are higher than for most knowledge workers, which is precisely why we want to build a tool that helps automate the initial classification.

---

We now have a clear picture of the problem (Part I) and a framework for solving it (Part II). To automate that framework, we need to understand just enough about how email actually works under the hood to know what our code will do.

## Part III: How Email Works Under the Hood
**(~10 min lecture)**

### 3.1 IMAP — The Window Into Your Mailbox

You do **not** need to become a networking expert. But to understand what your email reader code will do, you need one simple mental model.

> **Analogy:** Imagine your email inbox is a mailbox at the post office. **IMAP** (Internet Message Access Protocol) is like having a window into that mailbox. You can look through the window, read the letters, organize them into folders, and flag important ones — but the letters stay at the post office. You can look through the window from your phone, your laptop, or your office computer, and you always see the same letters.
>
> The older protocol, **POP3**, works differently: it is like reaching into the mailbox, taking the letters out, and bringing them home. Once you take them, they are gone from the post office. If you check from another device, the letters are not there anymore.
>
> For our purposes, IMAP is what we want — we read and categorize emails without removing them from the server.

### 3.2 The IMAP Conversation in Plain Language

Here is the mental model for what your Python script will do. Study this diagram — it maps directly to the code you will build in Part IV:

```
┌──────────────────┐                              ┌─────────────────────────┐
│   Your Python    │                              │      Mail Server        │
│     Script       │                              │   (imap.gmail.com)      │
│                  │                              │                         │
│                  │   1. CONNECT (SSL, port 993) │  ┌───────────────────┐  │
│                  │  ──────────────────────────►  │  │     INBOX         │  │
│                  │                              │  │  ┌───┐┌───┐┌───┐ │  │
│                  │   2. AUTH (email + app pass)  │  │  │ ✉ ││ ✉ ││ ✉ │ │  │
│                  │  ──────────────────────────►  │  │  └───┘└───┘└───┘ │  │
│                  │                              │  │    ... N msgs     │  │
│                  │   3. SELECT "INBOX"          │  └───────────────────┘  │
│                  │  ──────────────────────────►  │                         │
│                  │                              │  ┌───────────────────┐  │
│                  │   4. SEARCH (last 20)        │  │  [Sent]           │  │
│                  │  ──────────────────────────►  │  │  [Drafts]         │  │
│                  │                              │  │  [Trash]          │  │
│  From: ...       │   5. FETCH headers + body    │  └───────────────────┘  │
│  Subject: ...    │  ◄──────────────────────────  │                         │
│  Date: ...       │                              │  ┌───────────────────┐  │
│                  │   6. DISCONNECT              │  │  Messages STAY on │  │
│                  │  ──────────────────────────►  │  │  the server. IMAP │  │
│                  │                              │  │  only looks — it  │  │
│                  │                              │  │  never removes.   │  │
└──────────────────┘                              │  └───────────────────┘  │
                                                  └─────────────────────────┘
```

The same conversation, now as a table — useful for quick reference:

When your Python script connects to a mail server via IMAP, here is what happens step by step:

| Step | What Happens | Plain-Language Equivalent |
|------|-------------|--------------------------|
| 1. Connect | Script opens a secure connection to the mail server (e.g., `imap.gmail.com` on port 993) | You walk up to the post office window |
| 2. Authenticate | Script sends your email address and app password | You show your ID to the clerk |
| 3. Select folder | Script opens a specific mailbox folder (e.g., "INBOX") | You say "I want to look at my inbox, please" |
| 4. Search | Script asks for specific messages (e.g., "the 20 most recent") | "Show me the last 20 letters" |
| 5. Fetch | Script downloads the header fields (From, To, Subject, Date) and optionally the body | You read each letter through the window |
| 6. Disconnect | Script closes the connection | You walk away from the window |

Python has a built-in library called `imaplib` that handles all of this. You do not need to install anything extra. Your AI coding agent will use this library when it writes your email reader.

### 3.3 What You Need to Provide

To connect your script to your email, you need three pieces of information:

| Item | Example | Where to Find It |
|------|---------|-------------------|
| IMAP server address | `imap.gmail.com` (Gmail) or `outlook.office365.com` (Outlook/Hotmail) | Google/Microsoft documentation |
| Your email address | `student@gmail.com` | You know this |
| App password | A 16-character generated code | Gmail: Settings > Security > App Passwords; Outlook: Security > Advanced > App Passwords |

> **Key Insight:** An **app password** is not your regular Gmail/Outlook password. It is a special single-purpose password that lets your script access email without exposing your main account credentials. Think of it as a guest key to your apartment — it opens the door, but you can revoke it any time without changing your main lock. We will set this up together in class.

---

You now understand the six steps your script will take when it talks to the mail server. In Part IV, we focus on how to direct an AI coding assistant to write that script for you — without needing to memorize the `imaplib` API.

## Part IV: The AI-Assisted Workflow
**(~10 min lecture)**

### 4.1 The Describe-Review-Test-Iterate Pattern

By now you have used this pattern in previous weeks. Let's make it explicit for today's task:

```
    DESCRIBE                REVIEW                 TEST                 ITERATE
   (plain English)    (read the code)        (run the code)       (refine with AI)
        |                    |                     |                     |
  "Build me an        Does it use             Did it connect?      "Now add a
   email reader       imaplib? Does it        Are emails listed    triage function
   that fetches       handle credentials      correctly? Any       that categorizes
   20 recent          safely?"                errors?              by keyword rules"
   emails"                                                              |
        |                    |                     |                     |
        +-----> loop back as needed <--------------+---------------------+
```

The key principle: **you are the decision-maker; the AI is the typist.** You decide *what* to build and *whether* the output is correct. The AI handles the *how* — the syntax, the library calls, the boilerplate.

> **[DISCUSS]** You have been using the describe-review-test-iterate pattern since Week 2. What has worked well? Where have you gotten stuck? Has your prompting style changed from your first session to now?

### 4.2 Concrete Prompts for Today's Build

Here are the exact prompts you will give Claude Code (or your preferred AI agent) during the build session. Each prompt builds on the previous one:

**Prompt 0 — Environment check (do this first):**
```
Check that Python 3.10+ is installed, that the python-dotenv package is
available (install it if not), and that there is a .env file in the
current directory with EMAIL_ADDRESS, EMAIL_PASSWORD, and IMAP_SERVER
defined. Print the values (mask the password) so I can verify they
are correct.
```

**Prompt 1 — Basic email reader:**
```
Create a Python file called reader.py that connects to a Gmail inbox
via IMAP using imaplib, fetches the 20 most recent emails, and prints
the sender, subject, and date of each one. Read credentials from
environment variables EMAIL_ADDRESS and EMAIL_PASSWORD. Use
python-dotenv to load a .env file.
```

**Prompt 2 — Add triage logic:**
```
Add a function called triage_email that takes a subject line and
sender as input, and returns one of four categories: URGENT, ACTION,
FYI, or ARCHIVE. Use keyword-based rules: "stop work", "safety",
"incident", "notice of delay" map to URGENT. "RFI", "submittal",
"review", "approval" map to ACTION. "update", "recap", "photos",
"minutes" map to FYI. Everything else defaults to ARCHIVE.
```

**Prompt 3 — Formatted output:**
```
Update the main function to print a formatted table showing each
email's triage category, sender, subject, and date. Sort by category
priority: URGENT first, then ACTION, then FYI, then ARCHIVE.
Use color coding if the terminal supports it (red for URGENT, yellow
for ACTION, blue for FYI, gray for ARCHIVE).
```

**Prompt 4 — Body preview:**
```
Add a function that extracts the first 200 characters of the email
body as a plain-text preview. Include this preview in the output.
Handle both plain-text and HTML emails — strip HTML tags for the
preview.
```

### 4.3 What to Review in the Generated Code

After each prompt, before you run anything, check for these items:

| Check | Why It Matters |
|-------|---------------|
| Does it use `imaplib` and `email` from the standard library? | These are built-in — no extra installation needed |
| Are credentials loaded from environment variables or `.env`? | Hardcoded passwords are a security failure |
| Does it close the IMAP connection after fetching? | Open connections can lock your mailbox |
| Does it handle encoding properly (RFC 2047 decoding)? | Non-ASCII sender names will look garbled otherwise |
| Does it use `IMAP4_SSL` (not plain `IMAP4`)? | Plain IMAP sends your password unencrypted |

> **Key Insight:** The Claude Code workflow is always the same loop: **describe, review, test, iterate.** You will use this pattern for every coding task in this course — and in your career. The specific technology changes; the workflow does not.

---

## Tool Demo: Step-by-Step Claude Code Session
**(In-class walkthrough, ~15 min)**

Follow along on your own machine. The instructor will demonstrate on screen.

**Step 1 — Open your terminal and navigate to your project folder:**
```bash
cd ~/cem501-agent/project
```

**Step 2 — Create a `.env` file for credentials (do this manually, not through Claude Code):**
```
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
IMAP_SERVER=imap.gmail.com
```

**Step 3 — Make sure `.env` is in your `.gitignore`:**
```bash
echo ".env" >> .gitignore
```

**Step 4 — Launch Claude Code:**
```bash
claude
```

**Step 5 — Give Prompt 1 from Section 4.2.** Watch as Claude Code generates `reader.py`. Read through the generated code — does it match the checks from Section 4.3?

**Step 6 — Exit Claude Code and test:**
```bash
python reader.py
```

If it works, you should see 20 email entries printed. If it fails, go back into Claude Code and describe the error:
```
I got this error when running reader.py: [paste the error].
Fix the issue.
```

**Step 7 — Give Prompt 2.** Review the triage function. Does the keyword logic make sense? Would you add any CEM-specific keywords?

**Step 8 — Give Prompts 3 and 4.** Test after each.

**Step 9 — Commit your work:**
```bash
git add reader.py .gitignore
git commit -m "M2: add email reader with triage"
git push origin main
```

> **Key Insight:** Notice what you did *not* do: you did not write Python from scratch, memorize library documentation, or debug syntax errors manually. You described what you wanted, reviewed the output, tested it, and iterated. That is the AI-assisted workflow — and it is a legitimate professional skill.

---

## In-Class Activity
**(~60 min total)**

### Activity 1: Email Triage Drill (20 min)

You will receive a printed list of 15 email subject lines and senders from a fictional **highway bridge rehabilitation project ($12M, 18-month duration)**. Working in pairs, categorize each into URGENT / ACTION / FYI / ARCHIVE.

> **Instructor note:** Give pairs 10 minutes to categorize all 15 emails, then spend 10 minutes on whole-class discussion. Focus discussion on the ambiguous cases (#2, #10, #13, #14) where reasonable people disagree — this reinforces that triage involves judgment, not just rules. Do not reveal "correct" answers; instead, ask pairs to defend their reasoning.

| # | From | Subject |
|---|------|---------|
| 1 | OSHA Inspector | Re: Fall protection deficiency at Pier 3 — immediate correction required |
| 2 | Concrete Supplier | Updated delivery schedule for Week 12 pours |
| 3 | Project Architect | RFI-047 Response: Rebar spacing at Pier 3 footing |
| 4 | Marketing Dept | Webinar: New Project Management Software Demo |
| 5 | Owner's Rep | NOTICE: Liquidated damages clause activated — response required within 7 calendar days |
| 6 | Subcontractor (Electrical) | Daily work log 03/15 — no issues |
| 7 | Geotechnical Engineer | Unexpected soil conditions at Abutment B — recommend stop work pending review |
| 8 | Project Scheduler | Weekly schedule update — 2 days ahead of baseline |
| 9 | Structural Engineer | RE: RE: RE: RE: Beam camber tolerances (FYI — see thread below) |
| 10 | Environmental Consultant | Stormwater permit renewal — deadline March 30 |
| 11 | Steel Fabricator | Shop drawing submittal SD-023 for review and approval |
| 12 | Company HR | Annual benefits enrollment reminder |
| 13 | Owner | Meeting request: Monthly progress review — March 22 |
| 14 | Testing Lab | Compressive strength test results — 7-day break — BELOW specification |
| 15 | Colleague (internal) | FW: Funny construction fails video |

After the drill, we discuss disagreements as a class. Some emails are genuinely ambiguous — for example, is #2 ACTION (you need to confirm receipt) or FYI (the supplier is just informing you)? Is #10 ACTION or URGENT (how close is the deadline)? **Triage involves judgment, not just rules.** That is why a human reviews what the AI categorizes.

---

### Activity 2: Build Session (40 min)

Follow along with the Tool Demo in Section 5 to build your `reader.py` using Claude Code. By the end of this session, your script should:

1. Connect to your email inbox via IMAP
2. Fetch the 20 most recent emails
3. Display sender, subject, date, and body preview for each
4. Assign a triage category using keyword rules
5. Print a sorted, formatted summary

If you finish early, try extending the triage rules with CEM-specific keywords from the drill exercise.

---

## Security Reminder

- **Never** commit passwords or app passwords to your repository
- Store credentials in a `.env` file and add `.env` to `.gitignore` **before your first commit**
- If you accidentally commit a password, revoke the app password immediately and generate a new one — the old one is permanently in your Git history
- Claude Code can help you set up `python-dotenv` for safe credential loading

**Recommended pattern:** Commit a `.env.example` file (with placeholder values) so collaborators know which variables are needed, while keeping the real `.env` gitignored:

```
# .env.example — commit this file (no real credentials)
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
IMAP_SERVER=imap.gmail.com
```

---

## Milestone: M2 — Email Reader Module

**Due:** Before Week 6

**Deliverable:** `project/reader.py` pushed to your course repository

**Requirements:**

1. Connects to an IMAP inbox and fetches recent emails (configurable count, default 20)
2. Extracts sender, subject, date, and a body preview (first 200 characters, HTML stripped)
3. Assigns a triage category (URGENT / ACTION / FYI / ARCHIVE) to each email using keyword rules
4. Prints a formatted, sorted summary to the terminal (URGENT first)
5. Credentials loaded from environment variables via `.env` (no hardcoded secrets)
6. Connection is properly closed after fetching (use `try/finally` or context manager)

**Stretch goals (optional, for students who finish early):**
- Add sender-based priority: maintain a configurable whitelist of high-priority senders (e.g., owner, inspector) that automatically elevates emails to at least ACTION
- Export triage results to a CSV file for archival or further analysis
- Add a `--since` command-line flag to fetch only emails from the last N days

**Grading:** Pass / Needs Revision (you may resubmit once)

**Evaluation criteria:**
- Does the script run without errors on the grader's machine (with their own `.env`)?
- Are all six requirements met?
- Is the code reasonably readable (meaningful variable names, basic comments)?

---

### Summary: The Five Things to Remember

| # | Principle | Source |
|---|-----------|--------|
| 1 | CEM professionals spend 3–3.5 hours/day on email — and every message may carry contractual weight | CooperLink/RICS, Smith Currie & Hancock |
| 2 | Use the four-bucket framework (URGENT / ACTION / FYI / ARCHIVE) to triage every email in 3–5 seconds | Eisenhower Matrix, adapted for CEM |
| 3 | IMAP lets your script read email without removing it from the server — like looking through a window at the post office | IMAP protocol fundamentals |
| 4 | The AI workflow is always the same loop: describe → review → test → iterate. You decide *what*; the AI handles *how* | Describe-Review-Test-Iterate pattern |
| 5 | Never hardcode credentials — use `.env` + `.gitignore` from day one | Security best practices |

---

## Further Reading

**Email Overload and Productivity:**
- McKinsey Global Institute (2012). ["The Social Economy: Unlocking Value and Productivity through Social Technologies."](https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/the-social-economy)
- Radicati Group (2024). ["Email Statistics Report, 2024-2028."](https://www.radicati.com/?p=18519)
- Readless Blog (2026). ["15 Email Overload Statistics Every Knowledge Worker Should Know."](https://www.readless.app/blog/email-overload-statistics)

**Construction Email and Documentation:**
- Smith, Currie & Hancock LLP. ["Effective Use of Email for Construction Project Communications and Documentation."](https://www.smithcurrie.com/publications/common-sense-contract-law/effective-use-of-email-for-construction-project-communications-and-documentation/)
- Construction Dive. ["Securing Full Project Clarity with Email Management."](https://www.constructiondive.com/spons/securing-full-project-clarity-with-email-management/696640/)

**Technical References:**
- Cloudflare. ["What Is IMAP?"](https://www.cloudflare.com/learning/email-security/what-is-imap/) — Clear explanation of IMAP vs. POP3
- Python Docs. [`imaplib` module reference](https://docs.python.org/3/library/imaplib.html) — for those who want to understand the internals
- Google. ["Sign in with app passwords."](https://support.google.com/accounts/answer/185833) — Setup guide for Gmail app passwords

**AI Email Triage:**
- Microsoft Learn. ["Triage Incoming Emails with Power Automate."](https://learn.microsoft.com/en-us/azure/ai-services/language-service/custom-text-classification/tutorials/triage-email)
- InfoWorld. ["Using AI-Powered Email Classification to Accelerate Help Desk Responses."](https://www.infoworld.com/article/3824287/using-ai-powered-email-classification-to-accelerate-help-desk-responses.html)

---

### What's Next — Week 6 Preview

This week we tackled **reading** and **triaging** email (Strand B). Next week we move to **reports and summarization**: the daily reports, inspection logs, and progress records that serve as primary evidence in construction claims and disputes.

- **What we will cover:** How to summarize long email threads and project reports using LLMs. We will build a digest generator that takes the email data your `reader.py` fetches and produces concise, actionable summaries — turning a 50-message thread into a one-paragraph brief.
- **Why it matters:** In construction law, "if it was not documented, it did not happen." Reports are not busywork — they are risk management. Learning to generate and summarize them efficiently is a core professional skill.
- **Bring to class:** Your working `reader.py` from M2. We will use its output as the data source for the Week 6 build session.

---

**Dr. Eyuphan Koc** | eyuphan.koc@bogazici.edu.tr
