---
name: qa-release-readiness
description: Use when asked for a release-readiness report, go/no-go recommendation, sign-off, MVP coverage summary, or end-of-engagement QA report.
---

# Release Readiness

A PM should read one page and know whether it's safe to ship and what risk they're accepting.

## Verdict options
- **GO** — 0 Critical, 0 High open, exit criteria met
- **CONDITIONAL SIGN-OFF** — 0 Critical; High items open but each has fix-and-retest plan or written risk acceptance
- **NO-GO** — any Critical open, or a core journey fails

QA recommends. The product owner decides and owns residual risk. Say that in the report.

## Structure (`docs/08-release-readiness.md`)
1. **Release decision** — verdict in a box + 2–3 sentence reason
2. **Engagement timeline & scope integrity** — planned vs actual; note any client-directed compression and the original recommendation (factual, not defensive)
3. **Coverage** — cases executed per test set: total / pass / fail / blocked, pass rate; critical journeys tested end to end
4. **Defect summary** — open counts by severity; headline fixes verified (e.g. "all 14 Critical verified fixed incl. refresh token rotation")
5. **Open items requiring risk acceptance** — ID | Title | Severity | Status | Risk if shipped
6. **Top risks** — max 5, plain language
7. **Ops / environment dependencies** — DNS, email deliverability, env vars, custom auth domain, etc.
8. **Recommendations** — ordered
9. **Artifacts** — test plan, case register, bug log, Postman collection link, automation repo

## Rules
- Numbers must come from the CSVs, computed, not estimated.
- Never call it GO yourself if anything is unresolved — mark it CONDITIONAL and list conditions.
