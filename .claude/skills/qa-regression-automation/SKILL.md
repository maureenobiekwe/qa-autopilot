---
name: qa-regression-automation
description: Use when turning manual test cases into automated Playwright UI tests or Newman API runs, setting up GitHub Actions CI for tests, or deciding what to automate first.
---

# Regression Automation

Goal: anyone clones the repo, runs one command, sees pass/fail. CI runs it on every push without a human.

## What to automate first (in order)
1. Smoke of critical journeys (signup → login → core action)
2. Auth suite (see `qa-auth-testing` — rate limits, token expiry, protected routes)
3. API regression via Newman (fast, stable, catches most backend breaks)
4. Bugs that were Critical/High and got fixed — each becomes a test so it can't come back
5. Billing/plan-tier enforcement
Don't automate: one-off exploratory, visual judgement, things that change weekly.

## Conventions
- Playwright + TypeScript in `tests/`, config `playwright.config.ts`, base URL from `BASE_URL` env
- Test title starts with the case ID: `test('PROJ-TC-012 login rejects wrong password', …)`
- Use role/label selectors (`getByRole`, `getByLabel`), never brittle CSS
- Each test creates its own data (unique `qa+<timestamp>@` email)
- No `test.skip` / `.only` without a comment explaining why
- Traces + screenshots on failure (already in config)

## Converting a manual case
Steps → actions; Expected Result → `expect(...)`; Preconditions → `beforeEach` or fixture.

## CI
`.github/workflows/qa-regression.yml` runs Playwright + Newman on push, PR, and a nightly schedule; uploads the HTML report as an artifact. Secrets (`BASE_URL`, `QA_EMAIL`, `QA_PASSWORD`) go in GitHub → Settings → Secrets.

## Commands
```bash
npm i -D @playwright/test && npx playwright install --with-deps
npx playwright test            # all
npx playwright test --ui       # debug
npx playwright show-report
```
Starter files are in the kit's `automation/` folder.
