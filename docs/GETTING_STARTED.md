# Getting started

## Requirements

- Python 3.10 or newer
- A machine that can run Chromium (Playwright installs its own)
- Optional: an Anthropic API key for LLM planning and element choice

## Install

```bash
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env     # optional: add ANTHROPIC_API_KEY
```

On Linux CI use `python -m playwright install --with-deps chromium`.

## First run

```bash
python scripts/run_local_demo.py
```

This serves `demo_app/` on port 8765, runs the pipeline against it, and prints the path of the report. Open `projects/local_demo/outputs/report.html`.

## Your own app

1. Pick a staging URL you are allowed to test. Never point `--security` at systems you do not own or have permission to test.
2. Put test credentials in `.env` or the environment, not in files (see "Credentials and secrets" below).
3. Write the goal like a manual test step list: "Log in, open Billing, verify the plan name is shown".
4. Run:

```bash
python orchestrator.py --project projects/my_app --base_url "https://staging.example.com" --goal "..." --security
```

5. Read `outputs/report.md`. If a step failed during exploration, the report says which step and why.
6. Edit `projects/my_app/tests/test_main.py` if you want extra assertions, then run it alone:

```bash
cd projects/my_app && python -m pytest tests/test_main.py -q --headed
```

## Credentials and secrets

Passwords and API keys never go in `config.json` or in any committed file. Pick one:

**A. A `.env` file (easiest, local)**

```powershell
# Windows PowerShell
Copy-Item .env.example .env; notepad .env
```
```bash
# Mac/Linux Terminal
cp .env.example .env && nano .env
```

Fill in `QA_USERNAME`, `QA_PASSWORD` and, if you use it, `ANTHROPIC_API_KEY`. `.env` is already in `.gitignore`. The orchestrator and the generated tests both read it, so `python -m pytest tests/test_main.py` works on its own.

**B. Terminal variables (last until you close the terminal)**

```powershell
# Windows PowerShell
$env:QA_USERNAME="test@yourapp.com"; $env:QA_PASSWORD="your-test-password"; $env:ANTHROPIC_API_KEY="sk-ant-..."
```
```bash
# Mac/Linux Terminal
export QA_USERNAME="test@yourapp.com" QA_PASSWORD="your-test-password" ANTHROPIC_API_KEY="sk-ant-..."
```

**C. GitHub Actions secrets (for CI)**

1. For the demo CI: repo page, **Settings**, **Secrets and variables**, **Actions**, **New repository secret**, then add `ANTHROPIC_API_KEY` (optional).
2. For a real product: **Settings**, **Environments**, **New environment** named `staging`, then **Add environment secret** for `BASE_URL`, `API_BASE_URL`, `QA_EMAIL` and `QA_PASSWORD`. Environment secrets can be limited to chosen branches and can require a reviewer before a job runs.
3. Reference them in the job's `env:` block as `${{ secrets.NAME }}`. `qa-regression.yml` already does this with `environment: staging`.

How the workflows keep secrets out of the run:
- `persist-credentials: false` on checkout, so the git token is not left in `.git/config` where an uploaded artifact could expose it.
- `permissions: contents: read`, so the job token cannot write to the repo.
- Artifacts upload only report folders, never the repo root, `.git` or `.env`.
- GitHub masks secret values in logs, but only exact matches. Never `echo` a secret or print config files.

Order of precedence: terminal variable, then `.env`, then `config.json`. Credentials from the environment are used at run time and are not written back to `config.json`. The credentials in the bundled demo projects are public demo logins and are safe to commit.

If you ever commit a real key by mistake, revoke it at the provider immediately. Deleting the file later does not remove it from Git history.

## Running one phase

```bash
python orchestrator.py --project projects/my_app --phase planning
python orchestrator.py --project projects/my_app --phase exploration
python orchestrator.py --project projects/my_app --phase execution
python orchestrator.py --project projects/my_app --phase security --security
```

## Docker

```bash
docker build -t qa-autopilot .
docker run --rm -v "$PWD/projects:/app/projects" qa-autopilot --project projects/local_demo --security
```

(The demo app must be reachable from the container, so use a public or staging URL for Docker runs.)

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `no element on the page matches: <step>` | The step wording shares no words with any element on the page. Rename the step to use the visible label, or set an API key |
| Clicked the wrong element | Two elements shared the step's words. Be more specific ("add the backpack to the cart") |
| `net::ERR_...` during exploration | The site is unreachable from this machine or behind a proxy |
| Test passes but `Self-heals used` is above 0 | A primary locator changed. Check `outputs/heals.jsonl` and update the UI test ids |
| Slow first run | Failed candidates wait 2.5s each before the next is tried. That cost only appears when something has changed |
| `ModuleNotFoundError: yaml` | Run `pip install -r requirements.txt` |
