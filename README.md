# qa-autopilot

**Related repositories:** [qa-automation-framework](https://github.com/maureenobiekwe/qa-automation-framework) (UI, API, accessibility, performance and CI tests) · [qa-playbook](https://github.com/maureenobiekwe/qa-playbook) (method, templates and checklists for spec review and test planning)

Goal in, tested and reported out. Describe a user journey in plain language and the pipeline plans it, drives a real browser to find the elements, writes a readable Playwright test with self-healing locators, runs it, learns from failures, optionally audits the site passively for security gaps, and writes the report.

Built by a Senior QA Engineer, so the defaults come from how QA actually works: no guessed passes, evidence for every failure, and a failed run that tells you *why* it failed.

```
python orchestrator.py --project projects/local_demo --security
```

```
[2] planning        domain=auth planner=heuristic steps=4
[3] exploration     (real browser, DOM mining, screenshots)
[4] execution       1/1 passed, 0 self-heals
[5] passive security audit
[report] projects/local_demo/outputs/report.md
```

A committed example of that run is in [`docs/example-run/`](docs/example-run/): the plan, the generated test and the report.

---

## How it works

```
                  GOAL + URL
                      |
                orchestrator.py
                      |
   +------------------+------------------+
   |                  |                  |
 [1] Discovery     [2] Planner      [3] Explorer
 crawl + sitemap   goal -> steps    mine DOM, act, screenshot
 (--deep)          domain rules     ranked locator candidates
   |                  |                  |
   +------------------+------------------+
                      |
                [3b] Generator --> tests/test_main.py (plain pytest-playwright)
                      |
                [4] Executor ----> junit + execution.json
                      |
           pass? ---- no ----> Feedback agent --> knowledge/sites/<host>.json
            |                       |                    |
           yes                      +---- retry <--------+   (up to 2x)
            |
     [5] Security auditor (--security, passive, read-only)
            |
     [6] Reporter --> report.md + report.html
```

| Phase | File | What it does |
|---|---|---|
| 1 Discovery | `core/agents/discovery.py` | Same-origin crawl, forms and elements per page, `sitemap.json` |
| 2 Planning | `core/agents/planner.py` | Goal to ordered steps. Uses a domain blueprint (`knowledge/domains/*.yaml`). LLM when a key is set, rule-based otherwise |
| 3 Exploration | `core/agents/explorer.py` | Runs the steps in Chromium, mines the live DOM, picks elements, records a trace |
| 3b Generation | `core/agents/generator.py` | Trace to a readable `test_main.py` |
| 4 Execution | `core/agents/executor.py` | Runs pytest, parses junit, records self-heals |
| Feedback | `core/agents/feedback_agent.py` | Classifies failures (locator, timeout, assertion, network), stores lessons, decides whether to re-explore |
| 5 Security | `core/agents/security_auditor.py` | Headers, HTTPS redirect, cookie flags, tokens in web storage |
| 6 Report | `core/agents/reporter.py` | Markdown and HTML with screenshots |

Design notes:

- **Self-healing locators** (`core/lib/smart_locator.py`). Each element gets an ordered candidate list: test id, role and name, label, placeholder, id, name attribute, text, CSS. At run time the first candidate that matches exactly one visible element wins. If the primary one broke, the fallback runs and the heal is logged. This is covered in the repo by a run where id, label and placeholder were all changed and the test still passed through the `name` attribute.
- **Real failures are not retried away.** A failed assertion stops the loop and goes in the report as a product failure. Only locator and timeout problems trigger re-exploration.
- **It works without an API key.** Offline, planning and element choice use deterministic heuristics. With `ANTHROPIC_API_KEY` set, planning and element choice go through Claude. Every agent falls back to its heuristic if the model returns nothing usable.
- **Passive security only.** One GET, header and cookie checks, and storage inspection from the browser session. No payloads, no brute force, no other hosts. Run it only on systems you are authorised to test.

## Quick start

```bash
git clone <this repo> && cd qa-autopilot
pip install -r requirements.txt
python -m playwright install chromium

# 1. runs against the bundled demo shop, no internet needed
python scripts/run_local_demo.py

# 2. your own app
python orchestrator.py \
  --project projects/my_app \
  --base_url "https://staging.example.com/login" \
  --goal "Log in, open Settings, change the display name, verify the new name is shown" \
  --security
```

Credentials come from `.env` or terminal variables (`QA_USERNAME`, `QA_PASSWORD`, see `.env.example` and [Credentials and secrets](docs/GETTING_STARTED.md#credentials-and-secrets)). They are used at run time and never written back to `config.json`.

## Flags

| Flag | Meaning |
|---|---|
| `--project` | Required. Project folder, created if missing |
| `--goal`, `--base_url` | Objective and root URL. Saved to `config.json` so later runs need only `--project` |
| `--deep` | Crawl first and write `sitemap.json` |
| `--force` | Ignore checkpoints, run every phase |
| `--headed` | Show the browser |
| `--security` | Run the passive security audit |
| `--phase` | Run one phase: `planning`, `exploration`, `execution`, `security` |
| `--max-retries` | Feedback-loop retries, default 2 |

## What a project folder holds

```
projects/<name>/
  config.json        URL, goal, credentials reference
  workflow.json      planned steps
  tests/test_main.py generated Playwright test (readable, editable)
  outputs/           trace.json, junit.xml, security.json, report.md, report.html
  screenshots/       one image per step
  execution.json     pass/fail, durations, self-heals
  qa_session_logs.json  failures and what the feedback agent concluded
```

## The QA Agent Kit

The repo also carries the QA operating system I use with AI agents, so the same rules apply when an agent works inside this repo:

- [`AGENTS.md`](AGENTS.md) and `CLAUDE.md`: non-negotiables (never fabricate a result, evidence for every failure, business impact on every bug), hard stops, file locations, definition of done.
- [`.claude/skills/`](.claude/skills): 11 skills, one repeatable QA job each: discovery, spec review, test plan, test case design, auth testing, API testing, exploratory testing, bug reports, retest and regression, release readiness, regression automation.
- [`.mcp.json`](.mcp.json): Playwright and filesystem MCP servers.
- [`automation/`](automation): a starter Playwright and Newman regression suite, run nightly by `.github/workflows/qa-regression.yml`.
- [`docs/AGENT_KIT.md`](docs/AGENT_KIT.md): how the pieces connect and what to add next.

## Tests

```bash
python -m pytest unit_tests -q     # 15 offline tests, no browser or key needed
```

CI runs the unit tests, then the full pipeline against the local demo app, and uploads the report as an artifact.

## Limits

- The offline planner understands plain imperative goals ("log in, add the first item to the cart, verify ..."). Vague goals need an API key.
- Exploration drives one linear journey per run. It does not branch, and it does not cover iframes or shadow DOM yet.
- The security audit is a first-pass checklist, not a penetration test.

## Layout

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for module contracts and [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) for setup and troubleshooting.

**Built with** Python, Playwright, pytest, Claude (optional). **License** MIT.
