---
name: qa-product-discovery
description: Use when starting QA on a new or unfamiliar product, or when asked "where do i start", to build a product brief, critical user journeys, tech stack map, and risk map before any test design.
---

# Product Discovery

Goal: understand the product well enough to explain it in 3 sentences and name its 5 most important flows without looking anything up.

## Inputs to gather (ask Vee only for what you can't find)
- PRD / FRD / TRD / tickets / designs (check `docs/input/`, the Project, Drive, ClickUp/Jira if connected)
- Staging URL, test accounts (`.env`)
- API docs: OpenAPI URL or Postman collection

## Steps
1. **Use it like a real user.** With the Playwright MCP, open staging, sign up, walk every top-level nav item. Capture a screenshot per screen into `evidence/discovery/`. Note console errors and failed network calls as you go.
2. **Map the stack.** Frontend, backend, DB, auth provider (Supabase, Keycloak, Auth0, custom JWT), third parties (Stripe, Paystack, MPGS, email/SMS, AI APIs, storage). Read it off network calls + TRD.
3. **Name the users and their jobs.** Who pays, who administers, who is invited.
4. **List critical user journeys** (5–8). E.g. signup → verify → onboard → core action → pay → invite → delete account.
5. **Risk map.** Score each area High/Med/Low on: money, auth/session, PII, data integrity, external dependency, AI output, plan/tier enforcement, email deliverability. Past projects show these break most often: plan-tier/token crediting, checkout edge functions, transactional email templates, OTP lockout, token storage, one-time/restricted links, dead buttons (delete account, version restore).

## Output: `docs/01-product-brief.md`
```
# <Product> — QA Product Brief
**In 3 sentences:** ...
**Users:** ...
**Stack:** FE … | BE … | Auth … | DB … | Third parties …
**Critical journeys:** 1. … 2. …
**Risk map:**
| Area | Risk | Why | Test first? |
**Unknowns to chase:** (feeds qa-spec-review)
```
Keep it to one page. Next skill: `qa-spec-review`.
