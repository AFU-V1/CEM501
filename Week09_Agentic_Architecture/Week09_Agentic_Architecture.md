# CEM501: Communication Skills for CEM
## Week 9: Agentic Architecture & Design
**Spring 2026 | Dr. Eyuphan Koc | Bogazici University**

---

### Learning Objectives

- Explain what makes software "agentic" and identify the sense-decide-act loop in your own email agent
- Name the core components of a communication agent and describe each one's role
- Write a clear ARCHITECTURE.md document that a teammate (or future you) can follow
- Draw a system diagram (even text-based) showing data flow between components
- Apply modular design principles so your agent can be extended in later weeks

---

### Session Plan (120 min)

| # | Block | Time | Mode |
|---|---|---|---|
| 0 | Opening: Spot the Agent | 5 min | Poll |
| 1 | Part I — What Makes Software "Agentic" | 22 min | Lecture + 2 prompts |
| 2 | Part II — Your Agent's Architecture | 18 min | Lecture + diagram walk |
| — | **Break** | 5 min | — |
| 3 | Part III — Architecture Documents & ADRs | 18 min | Lecture + live ADR |
| 4 | Part IV — System Diagrams | 10 min | Lecture + critique |
| 5 | Part V — Designing for Extensibility | 7 min | Lecture |
| 6 | Tool Demo — Generating ARCHITECTURE.md | 12 min | Live demo |
| 7 | In-Class Activity — Whiteboard Architecture | 18 min | Solo + Pair + Share |
| 8 | Wrap & Exit Ticket | 5 min | Recap |

**How this session runs:** Short lecture bursts → discussion → recap, repeat. Expect to be called on. Bring something to write on.

**Callout legend** (used throughout):

| Marker | Meaning |
|---|---|
| `[POLL]` | Vote with hands or sticky-notes — instant signal |
| `[DISCUSS]` | 1–2 min open discussion |
| `[QUICK CHECK]` | Cold-call comprehension question |
| `[THINK-PAIR-SHARE]` | Solo think → pair → report out |
| `[LIVE]` | Short hands-on exercise at your seat |
| `[EXIT TICKET]` | Brief written reflection at the end |
| `CASE STUDY` | Real-world example with verified numbers |
| `WAR STORY` | Cautionary tale (sometimes composite) |
| `CEM Analogy` | Bridge to construction practice |
| `Key Insight` | The line you should write down |
| `Takeaway` | The line you should remember tomorrow |

---

## Opening: Spot the Agent
**(~5 min)**

Before we define anything, let's see what your intuition says.

> **[POLL]** I will name five systems. For each one, raise your hand if you think it is an **agent**. Keep your answer to yourself first; we will compare.
>
> 1. A Roomba vacuum cleaner
> 2. Outlook's autocomplete (the grey-text suggestion that finishes your sentence)
> 3. ChatGPT in a browser tab
> 4. A home thermostat
> 5. A CI/CD pipeline that runs your tests every time you push code

Hold your answer. We'll come back to this at the end of Part I — by then you should be able to defend it using the sense-decide-act criterion.

> **Takeaway:** "Agent" is a spectrum, not a label. The interesting question is not *is it an agent?* but *what makes it more or less agentic?*

---

## Part I: What Makes Software "Agentic"?
**(~22 min — 14 lecture / 8 interactive)**

### 1.1 From Scripts to Agents

Vocabulary you need this week:

- **LLM (Large Language Model):** An AI system like ChatGPT or Claude that reads and generates text. Think of it as very sophisticated autocomplete — you give it a prompt, it produces a response. The "large" refers to the billions of parameters learned from training data.
- **API (Application Programming Interface):** A way for your code to talk to another service over the internet. When your Python script calls the Claude API, an HTTP request travels to Anthropic's servers and a response comes back — no human touching a chatbot.
- **IMAP / SMTP:** The two protocols email uses. **IMAP** (Internet Message Access Protocol) is for *reading* email; **SMTP** (Simple Mail Transfer Protocol) is for *sending*. Think IMAP = checking your mailbox, SMTP = dropping a letter in the outgoing slot.

So far in Strand C you have built pieces — a prompt library, an email reader, a classifier. Each runs when you tell it to and stops when it finishes. That is a **script**: press a button, do one thing, done.

```
SCRIPT vs. AGENT — same email, two worlds

SCRIPT:                                AGENT:
  You wake up.                           At 3:17 AM an urgent RFI arrives.
  You run classify_email.py.             Agent classifies it. Pulls project
  You read the output.                   context from memory. Drafts a holding
  You write a reply.                     reply. Queues it for your review.
  You send it.                           You wake up. The draft is waiting.
  ───────────────────────                ───────────────────────
  YOU did the watching, the              AGENT did the watching, the thinking,
  thinking, and the work.                and the prep. YOU verify and approve.
```

An **agent** is different from a script because it operates in a loop. It watches for new information, decides what to do, acts, and goes back to watching. It runs while you sleep. It can handle situations you did not explicitly program, because the LLM at its core can reason about novel inputs.

Anthropic's December 2024 guide *Building Effective Agents* draws a useful distinction:

- **Workflows** — LLMs and tools orchestrated through predefined code paths. *You* decide the sequence; the LLM fills in blanks. Like a factory assembly line.
- **Agents** — LLMs dynamically direct their own processes and tool usage. Like giving a smart intern a goal ("handle my inbox overnight") and letting them choose the steps.

Most real systems live on a spectrum:

```
Script ←————————— Workflow ←————————— Agent
(no LLM,          (LLM fills in       (LLM decides
 fixed steps)      fixed steps)        its own steps)
```

Your email agent this semester sits between Workflow and Agent. The pipeline (read → classify → draft → send) is a workflow you defined. But within classification and drafting the LLM exercises judgment on emails it has never seen. That is the agentic part.

> **[DISCUSS] (90 sec)** Pick one task in your current job that is a script today (something you do manually, the same way, every week). What would it take to make it agentic — and **should** it be? Be ready to defend either side.

> **Key Insight:** Anthropic's core recommendation: *"find the simplest solution possible, and only increase complexity when needed."* Start with a workflow. Add autonomy only where it earns its keep.

> **CASE STUDY: Klarna's AI assistant**
>
> Klarna deployed an OpenAI-powered customer service assistant in early 2024.
>
> - **2.3 million conversations** in its first month
> - **Two-thirds** of all customer service chats handled by the AI
> - **Resolution time**: 11 minutes → under **2 minutes**
> - Equivalent throughput of an estimated **700 full-time agents**
> - Projected **$40M USD** profit improvement for 2024
>
> *Architecturally interesting bit:* it is **not** a fully autonomous agent. It is a well-designed workflow with LLM-powered steps and tightly scoped tools. Simplicity won.

---

### 1.2 The Sense-Decide-Act Loop

The foundational model for intelligent agents comes from Russell & Norvig's *Artificial Intelligence: A Modern Approach*, which defines an agent as *"anything that perceives its environment through sensors and acts upon that environment through actuators."*

- **Sensors** — how the agent gets information. Self-driving car: cameras and radar. Your email agent: the IMAP connection.
- **Actuators** — how the agent does things. Self-driving car: steering wheel and brakes. Your email agent: the SMTP connection.
- **The agent function** — the brain in between, taking what was sensed and deciding what to do.

Every agent — thermostat, self-driving car, your email assistant — follows three phases:

| Phase | What It Does | Your Agent Example | Everyday Example |
|-------|-------------|-------------------|------------------|
| **Sense** | Perceive the environment | Fetch unread emails via IMAP; extract sender, subject, body | A thermostat reads room temperature |
| **Decide** | Choose a response | LLM classifies intent; rules pick a template | Thermostat compares temperature to target |
| **Act** | Execute the choice | Draft a reply; send or queue; log the interaction | Thermostat turns on the heater |

The loop runs continuously (or on a schedule). After acting, the agent senses again. That is what makes it a **loop** rather than a one-shot script.

```
    ┌──────────┐
    │  SENSE   │ ◄── "Are there new emails?"
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │  DECIDE  │ ◄── "What kind of email is this? What should I say?"
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │   ACT    │ ◄── "Send the draft / queue for review"
    └────┬─────┘
         │
         └──────── loop back to SENSE ──────►
```

> **CEM Analogy:** A site superintendent doing a morning walk-through. She **senses** site conditions — weather, crew readiness, deliveries, hazards. She **decides** — reassign the concrete crew, expedite missing rebar, close off an unsafe area. She **acts** — calls, schedule updates, signage. Then does it again tomorrow morning. Your email agent is doing the same thing for your inbox.

**Why simplicity matters — compounding error:** Chip Huyen's 2025 analysis of agent systems shows that accuracy compounds across steps. If the model is 95% accurate at one step:

- **3 steps:** 0.95³ ≈ **86%**
- **5 steps:** 0.95⁵ ≈ **77%**
- **10 steps:** 0.95¹⁰ ≈ **60%**
- **100 steps:** 0.95¹⁰⁰ ≈ **0.6%**

Every step you add is another place to fail. If you can do it in 3 steps instead of 7, do it in 3.

> **[QUICK CHECK]** Cold call. If each step in your pipeline is **90% accurate** (worse than the 95% above), what is overall accuracy after **5 steps**? After **10**?
>
> *Worked answer:* 0.9⁵ ≈ **59%**. 0.9¹⁰ ≈ **35%**. This is why Anthropic's "start simple" advice is non-negotiable — every extra step compounds the failure rate.

---

### 1.3 Why This Matters for CEM

Construction is one of the industries most poised for — and most behind on — AI adoption. The Royal Institution of Chartered Surveyors (RICS) *AI in Construction 2025* report surveyed more than **2,200 professionals globally**:

- **45%** report **no AI implementation** at all in their organizations
- **34%** are in **early pilot** phases
- **70%** of project managers and quantity surveyors believe AI will help them deliver greater value
- Top barriers: lack of skilled personnel (46%), system integration challenges (37%), poor data quality (30%)

The interest is there. The capability is not.

> **Key Insight:** You are learning to build agentic systems at exactly the right time. The construction industry knows it needs AI but does not yet know how to adopt it. CEM professionals who can design, document, and deploy even simple AI agents will have a real competitive advantage.

> **[THINK-PAIR-SHARE] (3 min)** Pair up. Pick one CEM workflow you both know — RFI logging, submittal review, daily reports, change-order tracking. On paper, sketch what the **Sense**, **Decide**, and **Act** phases would look like for an agent that helps with it. Be ready to share in 30 seconds.

---

### Callback: "Spot the Agent" — answers

Returning to the opening poll, scored against the sense-decide-act criterion:

| System | Verdict | Why |
|---|---|---|
| Roomba vacuum | **Agent** | Senses (bump, dust), decides (turn, stop), acts (drive), in a loop |
| Outlook autocomplete | **Not an agent** | One-shot LLM call. No loop, no acting on the world |
| ChatGPT in a browser | **Not an agent** (in that form) | Answers when you press Enter, then waits. No autonomous loop |
| Home thermostat | **Agent** | Classical example — senses temperature, decides, acts on the heater, loops |
| CI/CD pipeline | **Workflow** (not agentic) | Predefined steps, no LLM judgment — fits the "workflow" box on the spectrum |

If your intuition matched this, good. If not, the difference is almost always the **loop** plus **judgment under novelty**.

---

## Part II: Your Agent's Architecture
**(~18 min — 12 lecture / 6 interactive)**

### 2.1 The Six Components

Your communication agent has six core components. Think of them like departments in a company — each has a specific job, and they pass work to each other. You do not need to build all six at once. But you need to understand what each one does and how they connect.

**1. Reader** — Connects to the inbox (IMAP), pulls new messages, extracts metadata. The agent's *sensor*. Without it, the agent is blind. In code terms, a Python function that logs in, finds unread messages, and returns them as structured data with fields like `sender`, `subject`, `body`, `date`.

**2. Classifier** — Sends the email body to an LLM with a system prompt and returns a category (RFI, submittal, schedule update, informal, urgent). First half of *decide*. Why not keyword matching? Real emails are messy: *"quick question about the rebar specs for Level 3"* is an RFI but never says "RFI." An LLM understands intent, not just words.

**3. Drafter** — Combines the classification, email text, prompt-library templates, and project context from Memory to generate a draft reply. Second half of *decide*. It answers: *"what should we say back?"*

**4. Sender** — Pushes the approved draft via SMTP, or holds it in a review queue. The agent's *actuator*.
**Important safety note:** In your initial builds, the Sender should *always* queue drafts for human review rather than sending automatically. A "human-in-the-loop" design means the agent prepares the work but a person approves it. You don't want your agent emailing a client at 3 AM with a hallucinated commitment.

**5. Memory** — Stores past interactions, sender profiles, project context, user corrections. Without Memory, every email from "John at ABC Construction" starts from zero. With Memory: *"John is the PM for Highway 101. He usually sends RFIs. Last time, the user corrected my classification from 'informal' to 'urgent.' Be more careful with his messages."* Memory can be a JSON file or a database.

**6. Scheduler** — Triggers the loop on a defined interval (every 5 min, every hour, every morning at 6 AM). Without it, you still have to press the button. Can be a `cron` job or the Python `schedule` library. The Scheduler doesn't think — it just rings the bell.

> **[QUICK CHECK]** Cover the section above. From memory, name the six components and one sentence each. Two of you will be called on.

**Construction-site analogy** — useful when you're explaining your project to a non-technical reviewer:

| Component | Site role analogy |
|---|---|
| Reader | Mailroom clerk — opens incoming mail, sorts by sender |
| Classifier | Coordinator who triages: RFI? submittal? safety? |
| Drafter | Junior engineer drafting the response |
| Sender | PM who reviews, signs, and sends |
| Memory | Project filing cabinet + lessons-learned log |
| Scheduler | The morning standup bell |

> **Key Insight — recommended build order:**
>
> 1. **Reader + Classifier** — read and categorize. Start here.
> 2. **+ Drafter** — write a draft reply.
> 3. **+ Sender** — queue or send. Now you have a complete pipeline.
> 4. **+ Memory** — get smarter over time.
> 5. **+ Scheduler** — run without you. Truly autonomous.
>
> Ship something small that works, then improve. Incremental delivery is how real software gets built.

---

### 2.2 Architecture Diagram

A text-based diagram you can paste into your ARCHITECTURE.md — no special tools required.

```
                        +-----------+
                        | Scheduler |  (triggers every N minutes)
                        +-----+-----+
                              |
                              v
    +-------+           +----------+         +-----------+
    | IMAP  |---------->|  Reader  |-------->| Classifier|
    | Inbox |  (fetch)  +----------+  (raw   +-----------+
    +-------+                          email)      |
                                          (category + email)
                                                   |
                                                   v
    +----------+        +-----------+        +---------+
    |  Memory  |<------>|  Drafter  |------->| Sender  |
    +----------+ (context+-----------+ (draft)+----+----+
                 + logs)                          |
                                                  v
                                            +----------+
                                            |   SMTP   |
                                            |  Outbox  |
                                            +----------+
```

**Read it top-to-bottom.** Scheduler wakes the Reader on a timer. Reader pulls from IMAP. Classifier labels. Drafter writes (pulling context from Memory). Sender delivers via SMTP. That is the complete sense-decide-act loop.

**What travels along each arrow:** raw headers/body (IMAP→Reader); cleaned email object (Reader→Classifier); category + confidence + email (Classifier→Drafter); project context + sender history (Memory↔Drafter, bidirectional); draft text + recipient (Drafter→Sender); final email (Sender→SMTP); a "wake up" trigger (Scheduler→Reader).

> **[DISCUSS] (90 sec)** Where is the **single point of failure** in this diagram? What happens if the LLM API goes down for 30 minutes — does your agent fail loudly, fail silently, or queue? (We'll come back to this in §3 when we write error-handling decisions.)

> **Tip for beginners:** If this looks complicated, trace just the main path: IMAP → Reader → Classifier → Drafter → Sender → SMTP. Memory and Scheduler are supporting components.

---

### 2.3 Anthropic's Composable Patterns (Reference)

The *Building Effective Agents* guide identifies five composable workflow patterns. Mix and match them like LEGO bricks.

| Pattern | Description | Plain-English Analogy | Your Agent Uses It? |
|---------|------------|----------------------|-------------------|
| **Prompt Chaining** | Sequential steps; each LLM call processes the previous output | Assembly line — Step 1's output is Step 2's input | Yes — Reader → Classifier → Drafter |
| **Routing** | Classify input and direct to specialized handlers | Hospital triage desk | Yes — different email types → different templates |
| **Parallelization** | Run the same task multiple times or split into parallel subtasks | Multiple cashiers serving customers simultaneously | Not yet — could classify and summarize in parallel |
| **Orchestrator-Workers** | Central LLM decomposes work and delegates to sub-agents | GC assigning tasks to electricians, plumbers, painters | Future — multi-channel coordination |
| **Evaluator-Optimizer** | One LLM generates, another evaluates, loop until quality threshold met | Writer + editor working in rounds | Future — draft quality checking |

**Prompt chaining in your agent:** `Email → [Reader extracts text] → [Classifier labels "RFI"] → [Drafter writes RFI reply]`

**Routing in your agent:** Classifier says "RFI" → RFI template; "submittal" → submittal acknowledgment; "informal" → casual reply.

> **Takeaway:** You are already using established agent design patterns. Naming them gives you a shared vocabulary to discuss your design with teammates and reviewers.

---

### Recap So Far

You should now be able to answer:

1. Difference between script, workflow, and agent?
2. Three phases of the agent loop?
3. The six components of your email agent?
4. Why does simplicity matter? (Compounding error.)

If any of these feel shaky, flag it now — Part III builds on them.

---

> **BREAK — 5 min.** Stretch. Top up coffee. Be back at the top of the next block.

---

## Part III: How to Write an Architecture Document
**(~18 min — 12 lecture / 6 interactive)**

### 3.1 Why Documentation Matters — Even When AI Writes the Code

You might think: *"If Claude Code writes my code and I can ask it to explain things, why do I need a separate architecture document?"*

Three reasons:

**1. Maintenance is most of the cost.** The "60/60 Rule" of software economics: roughly **60% of a software system's total lifecycle cost goes to maintenance**, not initial development — and within that maintenance budget, roughly **60% goes to enhancements driven by changing requirements**, not bug fixes. Documentation is what makes maintenance possible without the original developer (or the original AI conversation) present.

Think of a house: building takes months, maintaining takes decades. Software is the same. If the maintainer doesn't understand *why* the original builder made certain choices, they'll make mistakes — expensive ones.

**2. AI tools work better with documentation.** Give Claude Code or Cursor an ARCHITECTURE.md and the AI can understand your system's *intent*, not just its syntax. Without it, AI guesses. With it, AI knows what you were trying to do and can help you do more of it.

**3. Communication is the point.** This is a communication course. An architecture document is technical writing. It communicates the *why* behind your design decisions to a future reader — your teammate, your instructor, or yourself in six months. Code says *what*; documentation says *why*.

> **WAR STORY** *(composite, but every bit of it has happened on real projects)*
>
> A regional GC wins a hospital wing job. The MEP design specifies a particular variable-refrigerant-flow system. Two years in, the equipment has a known firmware defect. The owner demands a swap to a competing brand and files for a $200K change order. The original PM has left the firm. No one can find a written rationale for choosing the original brand. In litigation, the GC cannot prove the choice was driven by the owner's own MEP consultant's recommendation. They eat the change.
>
> A two-paragraph ADR — *"Decision: Brand X. Context: owner's MEP consultant required compatibility with existing Phase 1 chiller plant. Consequences: locked into Brand X service network for warranty period."* — would have settled it.

> **Key Insight:** The most common complaint in software teams is not *"we don't have enough code."* It is *"we don't know why the code is the way it is."* Documentation answers that question.

---

### 3.2 What Goes in ARCHITECTURE.md

An architecture document is not about beautiful prose. It answers the questions a new person (or future-you) will have:

1. **What does this system do?** (Overview — one paragraph. If you cannot explain it in one paragraph, you may not fully understand it yet.)
2. **What are its parts?** (One section per component.)
3. **How do the parts connect?** (Data flow diagram.)
4. **Why did you make these choices?** (Design decisions — the most valuable part.)
5. **What could be added later?** (Roadmap.)

This maps to a simplified version of Simon Brown's **C4 model**, which structures architecture documentation into four hierarchical levels — like zooming in on a map, from country to street level:

| C4 Level | What It Shows | Your Equivalent |
|----------|--------------|----------------|
| **Context** | The system as a whole and its external users/systems | Overview section — who uses your agent, what it connects to |
| **Container** | The major deployable units | Your six components |
| **Component** | Internal building blocks of each container | Individual functions within each component |
| **Code** | Classes, functions, implementation details | Your actual Python files |

For this course you only need the first two: Context and Container.

---

### 3.3 Architecture Decision Records (ADRs) — Simplified

When you build software, you make dozens of decisions: *"poll every 5 minutes or use push notifications?" "Claude or GPT for classification?" "auto-send or human approval?"* Six months from now, you won't remember why. An **Architecture Decision Record (ADR)** captures one design choice and its rationale so future-you doesn't have to guess.

Each entry has three parts. **Decision. Context. Consequences.**

```
**Decision:** We chose polling (check every 5 minutes) instead of push.

**Context:** Push requires a webhook server (a publicly accessible URL that
Gmail/Outlook can post to), which adds deployment complexity. Our use case
(overnight RFI triage) does not need real-time response — a 5-minute delay
is perfectly acceptable.

**Consequences:** Slight delay (up to 5 min) before new emails are processed.
Simpler deployment — no public server needed. Easy to change interval later.
```

A second example to lock the format in:

```
**Decision:** All draft replies go to a human review queue before sending.

**Context:** The LLM sometimes generates responses that are too informal,
miss technical details, or hallucinate project facts. In construction
communication, an incorrect reply to an RFI could have legal and safety
implications.

**Consequences:** No emails sent without approval — slower but safer.
Requires the user to check the queue at least once a day. Builds trust:
users can verify quality before granting more autonomy.
```

> **Key Insight:** The value of an ADR is not the decision — it is the *context* and *consequences*. Six months from now, you will not remember why you chose polling. The ADR remembers for you. As the ADR community puts it: *"Keep records pithy, assertive, on-topic, and factual."*

> **[LIVE — 4 min]** Open a blank doc or notebook page. Write **one** ADR right now for a real decision you made this week — in any project, not just this course. Three short sentences: **Decision. Context. Consequences.** Two volunteers will read theirs aloud.

---

## Part IV: System Diagrams — Thinking Visually
**(~10 min — 6 lecture / 4 interactive)**

### 4.1 Why Diagrams Matter

Visual representations help developers understand systems faster than prose. Simon Brown created C4 because he observed that *"many development teams don't have any software architecture diagrams at all"* — and the teams that do often produce diagrams that are confusing, inconsistent, or at the wrong level of abstraction.

A text-based ASCII diagram in a Markdown file has one enormous advantage: **it lives in version control alongside your code.** No Visio, Figma, or special tool. Update it in the same commit that changes the code.

> **[DISCUSS] (60 sec)** Pull up your Week 8 code mentally. Could you draw its data flow on a napkin in 60 seconds? If not, that is the gap M5 will close.

---

### 4.2 Diagram Checklist

When you draw your architecture diagram, verify it passes these:

- [ ] Every component is labeled with a clear name
- [ ] Arrows show **direction of data flow** (not just "connected to")
- [ ] Each arrow is **labeled** with what travels along it
- [ ] External systems (IMAP, SMTP, LLM API) are visually distinguished
- [ ] The diagram fits on one page — if not, the architecture may be too tightly coupled
- [ ] A classmate unfamiliar with your code understands it in under two minutes

---

### 4.3 Bad vs. Good Diagram

```
BAD — unlabeled, ambiguous direction         GOOD — labeled arrows, named data
+--------+     +-----------+                  +--------+ raw email +-----------+
| Reader |-----| Classifier|                  | Reader |---------->| Classifier|
+--------+     +-----------+                  +--------+           +-----------+
     |              |                             | unread msgs         | label
     |              |                             v                     v
+--------+     +-----------+                  +--------+ draft reply +---------+
| Memory |-----|  Drafter  |                  | Memory |<----------->| Drafter |
+--------+     +-----------+                  +--------+ context     +---------+
```

**What changed:** every arrow is named, direction is unambiguous, and a stranger can guess what each box does. Labeling arrows is the single biggest upgrade you can make.

---

## Part V: Designing for Extensibility
**(~7 min)**

### 5.1 What "Modular" Means

**Modular** = code organized into separate, independent pieces (modules), each doing one thing, with clear inputs and outputs. Modules can be developed, tested, and replaced independently.

The opposite is **monolithic** — one big file where everything is tangled. Picture a recipe with appetizer, main, and dessert steps shuffled randomly. That is a monolithic script. A modular design is three recipe cards.

Your agent is not done after this week:

- **Week 11:** Add a new messaging channel (Telegram or Slack) alongside email
- **Week 12:** Add persistent memory so the agent learns from corrections

Monolithic? Adding a channel means rewriting everything. Modular? Write one new component and plug it in.

---

### 5.2 Two Principles

**1. Separation of Concerns.** Each component does one job. The Classifier does not also send. The Reader does not also classify.

> **[QUICK CHECK]** One-sentence test: can you describe each component **without using the word "and"**? *"The Reader fetches new emails"* — good. *"The Reader fetches new emails and classifies them"* — that is two jobs; split it.

**2. Channel Abstraction.** Define a common interface. All your Readers (email, Telegram, Slack) should produce the same kind of output — a standardized message object with `sender`, `body`, `timestamp`. The rest of your system doesn't care *where* the message came from.

```python
# BAD — Classifier tightly coupled to email
def classify(imap_message):
    subject = imap_message.get("Subject")     # IMAP-specific
    body    = imap_message.get_payload()      # IMAP-specific
    ...

# GOOD — Classifier works with any message source
def classify(message):
    subject = message["subject"]   # Standard format — email, Telegram, Slack
    body    = message["body"]      # Reader already converted it
    ...
```

> **CEM Analogy:** A building with rigid load-bearing walls everywhere is expensive to renovate. A building with a structural frame and non-load-bearing partitions can be reconfigured without demolition. Software easy to modify mirrors construction reality — scope changes are inevitable, so design for them.

**Adding Telegram in Week 11 will look like this:**

```
Current:
  [IMAP Reader] --> [Classifier] --> [Drafter] --> [SMTP Sender]

After Week 11:
  [IMAP Reader]     ---+
                       +--> [Classifier] --> [Drafter] --+--> [SMTP Sender]
  [Telegram Reader] ---+                                 +--> [Telegram Sender]
```

Classifier and Drafter do not change. Only the Reader and Sender gain a sibling. That is the payoff of modular design.

---

## Tool Demo: Generating ARCHITECTURE.md with Cursor / Claude Code
**(~12 min live demo)**

> **[LIVE DEMO — watch the projected screen]** Do not type along. Watch and critique.

### Steps

1. Open the project in Cursor (or launch `claude` in the terminal).
2. Prompt: *"Look at my project structure and generate an ARCHITECTURE.md describing each component, its responsibility, inputs, outputs, and how data flows between them. Include a text-based diagram and at least two design decisions."*
3. Review critically.
4. Commit: `git add ARCHITECTURE.md && git commit -m "Add architecture doc (M5)"`.

### Your job during the demo

While the AI generates, watch for:

1. **One factual error** in the AI's draft — wrong filename, wrong responsibility, wrong arrow direction.
2. **One missing component** the AI overlooked.
3. **One ADR the AI should have written but didn't** (e.g., model choice, polling interval, human-in-the-loop).

> **[DISCUSS] (2 min, post-demo)** What did the AI get right? What did it get wrong? **Whose responsibility is it to catch the wrong parts?**

> **Key Insight:** The AI gives you a starting draft in minutes — without it, this would take hours. But the AI is **not** the architect. **You** are. The AI drafts; you verify, correct, improve. This mirrors how AI shows up in CEM practice: AI generates the first draft of an RFI response, but the engineer signs it.

---

## ARCHITECTURE.md Template

The structure your M5 submission should follow.

```markdown
# Architecture — [Your Agent Name]

## Overview
One-paragraph summary: what the agent does, who it serves, what it connects to.

## Components
For each component (Reader, Classifier, Drafter, Sender, Memory, Scheduler):
- **Responsibility:** One sentence
- **Input:** What data it receives
- **Output:** What data it produces
- **File:** Which source file implements it

## Data Flow Diagram
(Text-based diagram — see Section 2.2 for format)

## Design Decisions (ADR-style, at least two)
For each: **Decision**, **Context**, **Consequences**.
Examples: polling vs. push, model selection, human-in-the-loop.

## Error Handling
What happens when the LLM API times out? When classification confidence is low?
When the IMAP connection fails?

## Future Extensions
Channels, memory, attachment summarization, etc.
```

---

## In-Class Activity: Whiteboard Architecture Session
**(~18 min)**

### Instructions

**[PHASE 1 — Solo sketch — 5 min]**
On paper or a whiteboard, draw your agent's architecture from memory. **Do not look at the template.** Label every component, every arrow, and what data flows along each arrow.

**[PHASE 2 — Pair review — 6 min]**
Swap with a neighbor. Your job is to **find confusion**. For every part you do not immediately understand, mark it with a "?" sticky note. Be specific: *"What format is this data in?"* or *"What happens if this step fails?"*

**[PHASE 3 — Revise — 3 min]**
Address the "?" notes on your own diagram. Add labels, clarify names, note error paths.

**[PHASE 4 — Group share — 4 min]**
One volunteer presents. Class critiques together using these focus questions:

- Can someone unfamiliar with your code understand this in under two minutes?
- Where is the single point of failure? What happens if the LLM API goes down?
- Is any component doing more than one job? Should it be split?
- Could a new team member start contributing code from this diagram alone?

---

## Wrap-Up & Looking Ahead
**(~5 min)**

**Three things to walk out remembering:**

1. **The loop is the point.** Sense → Decide → Act, repeating. Anything that doesn't loop is a script.
2. **Six components, one job each.** Reader, Classifier, Drafter, Sender, Memory, Scheduler. Build them in that order; do not build all six at once.
3. **ADRs save futures from pasts.** Decision. Context. Consequences. Three sentences are enough.

**Where this goes next:**
- **Week 11** — you add a second channel (Telegram or Slack). The modular design you document this week is what makes that a one-evening job instead of a one-week rebuild.
- **Week 12** — you add persistent memory. Your Drafter starts to *learn* from corrections.

> **[EXIT TICKET]** On a sticky note: **one thing that clicked, one thing still fuzzy.** Hand it to me on the way out — I will use them to shape Week 10.

---

## Milestone M5 — Due Before Week 10

**Deliverable:** `project/ARCHITECTURE.md` committed to your repository.

### Requirements

| Criterion | Weight | What We Look For |
|-----------|--------|-----------------|
| **Completeness** | 40% | All template sections filled in |
| **Clarity** | 30% | Professional English. A reader unfamiliar with your code understands it. No jargon without definition. |
| **Accuracy** | 30% | Document matches your actual code. Component names match file names. Diagram reflects real data flow, not aspirational design. |

**Specific requirements:**
- Follows the template structure (all sections present)
- Includes a data flow diagram (text or image)
- Lists at least **two** ADR-style design decisions with context and consequences
- Written in clear, professional English
- Committed with a meaningful commit message

> **Key Insight:** ARCHITECTURE.md is graded partly on *accuracy to your actual code*. Do not describe a six-component system if you have only built three. Describe what exists, note what is planned, be honest about current state. In construction, **as-built drawings are more valuable than design drawings** because they reflect reality.

---

## References

**Agentic AI architecture**
- Anthropic (2024). [*Building Effective Agents.*](https://www.anthropic.com/research/building-effective-agents) — The most practical guide to agent design patterns. Read at least the prompt chaining and routing sections.
- Huyen, C. (2025, Jan 7). [*Agents.*](https://huyenchip.com/2025/01/07/agents.html) — Excellent overview, including the compounding-accuracy analysis cited in §1.2.
- OpenAI (2025). [*A Practical Guide to Building Agents.*](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf) — OpenAI's perspective on agent architecture; covers their Agents SDK and multi-agent patterns.
- Russell, S. & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach*, 4th ed. Pearson. — Chapter 2, "Intelligent Agents," is the foundational sense-decide-act framework.

**Software architecture documentation**
- Brown, S. [*The C4 Model for Visualising Software Architecture.*](https://c4model.com/) — Standard for simple, developer-friendly architecture diagrams.
- Nygard, M. (2011, Nov 15). [*Documenting Architecture Decisions.*](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — The original ADR blog post.
- AWS (2024). [*Master Architecture Decision Records (ADRs): Best Practices for Effective Decision Making.*](https://aws.amazon.com/blogs/architecture/master-architecture-decision-records-adrs-best-practices-for-effective-decision-making/) — AWS's take on writing effective ADRs.
- Google Cloud. [*Architecture decision records overview.*](https://cloud.google.com/architecture/architecture-decision-records) — Google Cloud Architecture Center.

**The 60/60 Rule and software economics**
- Wood, D. (2009). "The 60/60 Rule." In Davis, B. (ed.) [*97 Things Every Project Manager Should Know.*](https://www.oreilly.com/library/view/97-things-every/9780596805425/ch34.html) O'Reilly. — Original source of the 60/60 figure.

**Construction & AI**
- RICS (2025). [*Artificial Intelligence in Construction Report.*](https://www.rics.org/news-insights/artificial-intelligence-in-construction-report) — Global survey of 2,200+ professionals on AI adoption in construction.

**Klarna case study**
- Klarna (2024, Feb 27). [*Klarna AI assistant handles two-thirds of customer service chats in its first month.*](https://www.klarna.com/international/press/klarna-ai-assistant-handles-two-thirds-of-customer-service-chats-in-its-first-month/)
- OpenAI. [*Klarna case study.*](https://openai.com/index/klarna/)

---

**Dr. Eyuphan Koc** | eyuphan.koc@bogazici.edu.tr
