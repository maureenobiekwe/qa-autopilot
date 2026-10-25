---
name: qa-bug-report
description: Use when logging, rewriting, triaging or compiling bugs/defects into a bug log, including severity and priority assignment, business impact, and next steps, in Vee's standard CSV bug report format.
---

# Bug Report

A developer must be able to reproduce the bug from your steps alone, without messaging you.

## Columns (fixed order — matches Vee's bug logs)
`Bug ID,Category,Title,Type,Preconditions,Steps to Reproduce,Actual Result,Expected Result,Evidence,Status,Environment,QA Comment,Business Impact,Next Steps,Linked TC,Linked Req,Severity,Priority,Assigned to,Retest Comment,Reporter`

## How to fill each
- **Title**: what + where + symptom. `Add-on / token purchase broken - checkout 403 / 500`
- **Category**: feature area (Access, Billing, AI drafting, Guided Roadmap, Settings…)
- **Type**: Urgent / Major bug / Minor bug / UI / Content / Enhancement (or team scale)
- **Preconditions**: account, plan tier, data state. `League workspace. Settings > Addons.`
- **Steps**: numbered in one cell, `1 … 2 … 3 …`, with exact input values
- **Actual vs Expected**: observable facts. Quote UI text. Include status codes and endpoint (`POST /functions/v1/create-addon-checkout -> 403`). Expected cites the spec (`per PRD v0.2.0 §3.1`)
- **Evidence**: path/link to screenshot, recording, HAR, console log
- **Environment**: `Staging, Chrome desktop, <plan/role>`; add build/version if known
- **QA Comment**: your read of root cause or related bugs ("ROOT CAUSE of the AI-token failures"; "per-template sender config, since reset email works")
- **Business Impact**: one founder-level sentence — who is hurt and what it costs
- **Next Steps**: the concrete fix direction
- **Status**: New → Confirmed → In Progress → Fixed → Retest → Verified / Reopened / Won't Fix / Risk Accepted

## Severity guide
| Severity | Means | Examples |
|---|---|---|
| Critical / Urgent | Core flow, money, security or data broken; no workaround | Paid tokens never credited; checkout 500; restriction bypass; tokens leak |
| High / Major | Important feature broken, workaround exists or subset of users | Signup email never arrives (OAuth works); delete account dead |
| Medium | Feature works but wrong/misleading | Wrong nag message; filter doesn't filter |
| Low / Minor | Cosmetic, copy, minor UX | Password reveal icon state |
Auth, payments, PII, data loss → at least High.

## Rules
- One bug per row. If one root cause explains several, log them and cross-reference in QA Comment.
- Check for duplicates before adding.
- Don't log documented intentional behaviour.
- After compiling, give a summary: count by severity, top 3 by business impact.

Template: `bug-log-template.csv` in this folder.
