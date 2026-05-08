# digest.py — Test Output

**Test mode:** Hardcoded sample emails (default, no inbox required)
**Command:** `py digest.py`
**Date:** April 07, 2026 at 23:06

---

```
==================================================
=== PROJECT MORNING DIGEST ===
Generated: April 07, 2026 at 23:06
Covering: 11 emails
==================================================

--- URGENT (2) ---
[1] From: OSHA Inspector <inspector@osha.gov>
    Subject: URGENT: Fall protection deficiency — immediate correction required
    Summary: Cease all work above Level 3 at the Kadikoy Bridge project due to missing guardrails on Level 4 east side scaffolding and submit a corrective action plan within 24 hours.

[2] From: Kaya Steel <mehmet@kayasteel.com>
    Subject: Notice of Delay — Pier 5 foundation work
    Summary: Pier 5 bearing installation is halted due to unresolved RFI-018 on anchor bolt specifications, prompting a request for immediate Architect escalation.

--- ACTION (3) ---
[3] From: Project Architect <arslan@archdesign.com>
    Subject: RFI-047 Response: Rebar spacing at Pier 3
    Summary: The design team approves Option B (150mm spacing) for rebar at Pier 3 and instructs to proceed with installation per revised detail SK-047-R1.

[4] From: Beton Plus <hasan@betonplus.com.tr>
    Subject: Updated delivery schedule for Week 12
    Summary: The Thursday concrete pour is moved to Friday due to plant maintenance, requiring formwork crew scheduling adjustments and a 07:00 pump truck arrival.

[5] From: Owner's Rep <ozkan@riverfront.com>
    Subject: Schedule review meeting — agenda items needed
    Summary: Submit agenda items by EOD Wednesday for the confirmed Friday 10:00 OAC meeting.

--- FYI (4) ---
  - Weekly safety stats — February summary
  - Subcontractor insurance cert renewal (Demir AS)
  - Project photo album updated
  - Industry newsletter: New OSHA silica dust rules

--- ARCHIVE (2 emails skipped) ---
==================================================
=== END DIGEST ===

REMINDER: URGENT and ACTION summaries are AI-generated drafts. Always verify against the original email before taking action.
```

---

## Test Summary

| Check | Result |
|-------|--------|
| Script runs without errors | ✅ Exit code 0 |
| 11 hardcoded emails categorized | ✅ 2 URGENT, 3 ACTION, 4 FYI, 2 ARCHIVE |
| LLM summaries generated (URGENT + ACTION) | ✅ 5 one-sentence Gemini summaries |
| FYI shows subject lines only | ✅ |
| ARCHIVE shows count only | ✅ |
| Date/time header present | ✅ "April 07, 2026 at 23:06" |
| AI disclaimer included | ✅ |
