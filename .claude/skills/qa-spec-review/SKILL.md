---
name: qa-spec-review
description: Use when reading a PRD, TRD, FRD, tickets or acceptance criteria to extract testable requirements with IDs and hunt for ambiguities and contradictions between documents before testing starts (shift-left review).
---

# Spec Review & Ambiguity Hunt

A contradiction caught here saves a sprint. This is the step that separates senior QA from test executors.

## Steps
1. **Collect every source doc.** List them with version/date at the top of the output.
2. **Extract requirements.** One row per testable statement. Give each `<PROJ>-REQ-###`. Split compound sentences ("must validate email and send OTP" = 2 reqs).
3. **Mark testability.** Not testable = no number, no threshold, no defined behaviour ("fast", "secure", "user-friendly", "appropriate error").
4. **Cross-check documents pairwise.** PRD vs TRD, PRD vs tickets, TRD vs API spec, designs vs PRD copy. Look specifically for:
   - different numbers (token expiry 24h vs 60 min, OTP 5 vs 10 min, cooldowns, rate limits, password length)
   - different flows (auto-redirect after reset vs manual; auto-login after signup vs verify first)
   - cookie/storage attributes (httpOnly, SameSite, Secure, localStorage vs memory)
   - plan/tier entitlements that don't match billing logic
   - missing error states, empty states, and limits (max length, file size, pagination)
5. **Classify each ambiguity:** Blocking (can't write an expected result) / Non-blocking (can test, assumption noted).
6. **Draft anticipatory bugs** for contradictions that will certainly produce a defect whichever way it's built.
7. **Write the dev-facing message.** Plain language, one line per item, no QA jargon: "PRD says reset link lasts 60 min, TRD says 15 min. which one do we build to?"

## Outputs
`docs/02-requirements.csv` — columns:
`Req ID,Source Doc,Section,Requirement,Category,Testable (Y/N),Priority,Notes`

`docs/02-ambiguity-log.csv` — columns:
`AMB ID,Summary,Doc A (section),Doc B (section),What each says,Blocks Req IDs,Blocking (Y/N),Assumption if unresolved,Raised To,Status,Resolution`

## Rules
- Quote section numbers. Never paraphrase a number.
- If something is intentional per a doc (e.g. "JWT in memory per TRD §3.4"), record it as a decision, not a bug.
- Report: X requirements, Y ambiguities (Z blocking). Next: `qa-test-plan`.
