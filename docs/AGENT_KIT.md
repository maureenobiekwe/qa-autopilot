# QA Agent Kit

Drop this folder into any product repo (or keep it as its own "qa" repo). Open it in Claude Code or ZCode. Instead of re-explaining how you test every time, the agent reads your rules and skills and just does it.

---

## 1. The pieces, in plain English

| File | What it is | Analogy |
|---|---|---|
| `AGENTS.md` | Your standing rules for any AI agent: how you work, hard stops, naming, where files go, definition of done. Read automatically by ZCode, Codex, Cursor and others. | Your onboarding handbook for a new junior tester |
| `CLAUDE.md` | Same idea, but the filename Claude Code looks for. Here it just says `@AGENTS.md` so you maintain one file. | A sticky note pointing to the handbook |
| `.claude/skills/<name>/SKILL.md` | One skill = one repeatable job (e.g. auth testing). The agent only sees the one-line `description` until a task matches, then loads the full instructions. That's why you can have 50 skills without clogging context. | Your SOPs / playbooks, one per task |
| `.mcp.json` | Lists MCP servers the agent can use. MCP = a standard plug that gives the agent hands: a browser (Playwright), files, GitHub, ClickUp, Jira, Postman, Slack. | The tools on your desk |
| `README.md` | For humans. What this repo is and how to use it. | The label on the box |
| `automation/` | Real test code + CI that runs with nobody watching. | Your robot tester that works nights |
| `.env.example` | Which URLs/accounts are needed. Copy to `.env` (never commit). | Access card list |

### How they interconnect
```
You: "test auth on staging.example"
        │
        ▼
Agent reads AGENTS.md / CLAUDE.md  ──► knows your rules, hard stops, file paths
        │
        ▼
Matches task to skill description ──► loads qa-auth-testing/SKILL.md (the checklist)
        │
        ▼
Uses MCP tools from .mcp.json     ──► Playwright opens the browser, clicks, screenshots,
        │                              reads console + network
        ▼
Writes outputs where AGENTS.md says ──► docs/04-test-cases.csv, docs/06-bug-log.csv, evidence/
        │
        ▼
qa-regression-automation turns the passing checks into automation/tests/*.spec.ts
        │
        ▼
GitHub Actions runs them on every push + nightly ──► no human needed next time
```
AGENTS.md = **how you behave**. Skills = **how to do a specific job**. MCP = **what you can touch**. Automation/CI = **what runs without you**.

---

## 2. The 11 jobs the skills cover

| # | Job | Skill | What good looks like |
|---|---|---|---|
| 1 | Understand the product and map where risk lives | `qa-product-discovery` | Risk map before any test case; highest-risk areas first |
| 2 | Read specs adversarially, log contradictions before code exists | `qa-spec-review` | PRD vs TRD conflicts caught in review, blocking ambiguities flagged with owners |
| 3 | Write a scoped, risk-based test plan with entry/exit criteria | `qa-test-plan` | ISO/IEC/IEEE 29119-3 shape, one page of scope and exit criteria |
| 4 | Design positive/negative/edge/security cases with traceability | `qa-test-case-design` | Every case linked to a requirement; blocked cases say why |
| 5 | Break auth: signup, OTP, OAuth, reset, tokens, sessions | `qa-auth-testing` | OTP lockout, refresh rotation, token storage, enumeration checks |
| 6 | Test APIs directly (Postman/Newman) | `qa-api-testing` | Status, schema and auth checks per endpoint, runnable in CI |
| 7 | Explore the UI with DevTools open | `qa-exploratory-browser` | Console and network errors, dead buttons, stale state, with evidence |
| 8 | Log bugs a developer can reproduce alone, with business impact | `qa-bug-report` | QA Comment, Business Impact and Next Steps on every bug |
| 9 | Retest fixes independently, scope regression, smoke | `qa-retest-regression` | Each fix marked verified, partially addressed or justified |
| 10 | Give an evidence-based Go / Conditional / No-Go | `qa-release-readiness` | Conditional sign-off with a risk-acceptance list |
| 11 | Automate what matters and run it in CI | `qa-regression-automation` | Passing P1 checks become Playwright tests that run nightly |

Cross-cutting, baked into the skills: performance (k6, slow 3G), accessibility (axe), OWASP basics (IDOR, XSS, SQLi, rate limits), and your rule *never fabricate a result*.

---

## 3. What can run without you vs what stays yours

| Fully automatable (agent/CI does it) | Agent does the legwork, you review | Stays human |
|---|---|---|
| Regression + smoke on every push/nightly | Extracting requirements, first-pass ambiguity log | Deciding what "correct" means when specs conflict |
| API contract/status/auth checks (Newman) | Drafting test plans and cases from PRDs | Severity calls on borderline bugs |
| Auth attack checklist (rate limits, tampered tokens, enumeration) | Exploratory runs via Playwright MCP with screenshots | Go/No-Go sign-off and risk conversations |
| Screenshots, console/network capture, evidence folders | Writing bug reports from findings | Stakeholder politics ("works on my machine") |
| Converting CSV results into summaries/counts | Retesting claimed fixes, scoping regression from PR diffs | Judging UX, trust, "this feels like phishing" |
| Performance baselines (k6 in CI) | Release-readiness draft | Final wording that goes out under your name |

Rule of thumb: if you've done the same steps 3 times, it becomes a skill. If the skill's steps have fixed expected results, it becomes a test in CI.

---

## 4. Setup

### A) Claude Code (you already have it with Playwright MCP)
1. Put this kit in a folder, e.g. `~/qa/my-product-qa/`, and `cd` into it.
2. Skills are already in `.claude/skills/` — Claude Code finds them automatically. To make them available in **every** project, copy them to your user folder: `cp -r .claude/skills/* ~/.claude/skills/` (Windows PowerShell: `Copy-Item -Recurse .claude\skills\* $HOME\.claude\skills\`).
3. `.mcp.json` registers Playwright for this project. Or add globally (terminal): `claude mcp add playwright -- npx @playwright/mcp@latest`
4. `cp .env.example .env` and fill it in.
5. Run `claude` and type a task (examples below). Type `/skills` or ask "what skills do you have" to check they loaded.

### B) ZCode (Z.ai's desktop coding agent — the app in your screenshot)
1. Download from **zcode.z.ai** (macOS, Windows; Linux in beta).
2. Sign in / start the trial, then Settings → Model Providers → paste your Z.ai **GLM Coding Plan** API key, pick the model (e.g. GLM-5.x) from the model menu.
3. Open this kit folder as the project. ZCode reads `AGENTS.md` .
4. MCP servers and skills in ZCode are added through its Plugin Marketplace / plugin settings — point it at the same Playwright MCP command (`npx @playwright/mcp@latest`) and add the skill folders if it asks for a skills path. Check ZCode's docs for the exact screen, it changes often.
5. Needs Node.js 18+ installed for `npx` MCP servers.

### C) Automation repo
```bash
cd automation
npm install
npx playwright install --with-deps
cp ../.env.example .env   # fill it
npx playwright test
```
Push to GitHub, add secrets `BASE_URL`, `API_BASE_URL`, `QA_EMAIL`, `QA_PASSWORD`, and `.github/workflows/qa-regression.yml` runs on every push + nightly.

---

## 5. Prompts that now work without re-explaining
- "new product. docs are in docs/input. do discovery and spec review."
- "run the auth checklist against staging using the spec in docs/input/TRD.pdf. log everything."
- "the devs sent docs/input/bug-fix-summary.pdf. retest every item and update the bug log."
- "draft the release readiness report from the CSVs."
- "turn every passing P1 auth case into playwright tests and open a PR."

---

## 6. What to add next (in this order)
1. **Tracker MCP** — ClickUp or Jira connector so bugs go straight into tickets (`QA-###`) instead of CSV → import.
2. **GitHub MCP** — agent reads PR diffs to scope regression and opens PRs for new tests.
3. **Postman MCP** — generate/run collections from the OpenAPI spec.
4. **Product-specific skills** — e.g. `product-context` or `registry-context` with that product's spec numbers, roles, test accounts, known intentional behaviours. Keep product facts there, not in the general skills.
5. **More domain skills** as you repeat them: `qa-performance-k6`, `qa-accessibility`, `qa-payments-billing`, `qa-ai-feature-testing` (stale context, token metering, hallucination), `qa-mobile-adb` (Android debug bridge + reading builds from terminal).
6. **Hooks** (Claude Code) — e.g. auto-run `npx playwright test` after the agent edits a test file.

Keep skills short, one job each, with a sharp `description` line — that line is what decides whether the agent picks it up.
