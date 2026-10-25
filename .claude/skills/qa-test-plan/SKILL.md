---
name: qa-test-plan
description: Use when asked for a test plan, test strategy, QA proposal scope, or entry/exit criteria for a product, feature, sprint or engagement. Produces an ISO/IEC/IEEE 29119-3 aligned plan.
---

# Test Plan

Anyone on the team should be able to read it and know exactly what is covered and what is deliberately not.

## Inputs
`docs/01-product-brief.md`, `docs/02-requirements.csv`, `docs/02-ambiguity-log.csv`, timeline, team size.

## Sections (keep this order)
1. **Identification** — product, version/build, author, date, related docs
2. **Context & objectives** — what quality question this plan answers
3. **Scope** — In scope (feature list mapped to Req IDs) / Out of scope (with reason)
4. **Test items & journeys** — critical flows from the brief
5. **Risk-based priorities** — table: Area | Risk | Likelihood | Impact | Test depth. Test security/billing/auth/core-value first.
6. **Test types & why** — pick only what the product needs: functional, API, auth/security (OWASP), integration, UI/exploratory, accessibility (WCAG 2.2 AA, axe), performance (k6: load/stress/slow 3G), compatibility (browsers/devices), regression.
7. **Design techniques** — BVA, equivalence partitioning, decision tables, state transition, error guessing, use-case/scenario testing (29119-4)
8. **Environment & data** — URLs, accounts per role/plan tier, test cards, email inbox, devices
9. **Entry criteria** — build on staging, accounts provisioned, blocking ambiguities answered
10. **Exit criteria / Definition of Done** — 0 open Critical, all High fixed or risk-accepted in writing, 100% of P1 cases executed, 0 "Not Executed"
11. **Suspension & resumption** — e.g. auth broken = suspend dependent suites
12. **Deliverables** — test cases + RTM, execution report, bug log, risk assessment, release-readiness summary
13. **Schedule** — Testing → Dev fix window → Retest/Regression/Smoke → Sign-off. If the client compresses the timeline, record the original recommendation.
14. **Roles & ownership boundary** — QA recommends; product owner decides go/no-go and accepts residual risk
15. **Assumptions, dependencies, blockers** — link the ambiguity log

## Output
`docs/03-test-plan.md`. If Vee wants a Word/Docs version, produce from this markdown.
Next: `qa-test-case-design`.
