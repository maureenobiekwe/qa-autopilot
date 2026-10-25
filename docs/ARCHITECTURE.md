# Architecture

## Data contracts

Each phase reads one file and writes one file. Nothing passes through memory except the orchestrator's loop, so any phase can be re-run alone with `--phase`.

| Producer | File | Shape |
|---|---|---|
| planner | `workflow.json` | `{goal, base_url, domain, planner, steps:[{n, kind, intent, expect}]}` |
| explorer | `outputs/trace.json` | `{base_url, complete, storage_keys, steps:[{n, intent, ok, error?, screenshot, actions:[{action, value, candidates}]}]}` |
| generator | `tests/test_main.py` | pytest-playwright test using `smart_locator.resolve` |
| executor | `execution.json` | `{total, passed, failed, failures:[{test, message, detail}], healed:[...]}` |
| feedback | `qa_session_logs.json`, `knowledge/sites/<host>.json` | failure classes, lessons, locators to avoid |
| security | `outputs/security.json` | `{findings:[{severity, title, detail}], counts}` |
| reporter | `outputs/report.md`, `report.html` | human report |

`kind` is `login`, `action` or `verify`. A `login` step is solved by finding the username field, the password field and the submit button together. Placeholders like `{{credentials.username}}` keep secrets out of generated tests; they are filled from `config.json` or environment at run time.

## Element choice

1. The explorer mines every visible interactive element (`core/lib/browser.py`, `MINE_JS`): tag, role, accessible name, label, placeholder, id, name, test-id attributes, a short CSS path.
2. With an API key, the model gets the step and up to 70 elements and answers with an action and element index.
3. Without a key, or if the answer is unusable, `heuristic_action` scores elements by word overlap with the step. An element with zero overlap scores zero, so the explorer fails loudly instead of clicking a guess.
4. `build_candidates` turns the chosen element into an ordered locator list. Locators on the site's `avoid` list are dropped first.

## The feedback loop

```
execution fails
   -> classify(message): locator | timeout | assertion | network | unknown
   -> locator   : store lesson, add failed locators to avoid list, re-explore
   -> timeout   : store lesson, raise timeout to 90s, re-explore
   -> assertion : store lesson, STOP (treat as a product failure)
   -> network   : store lesson, STOP (not a test problem)
   -> self-heals seen in the run are stored as lessons too
```

The stop rules matter. A framework that retries until green hides real defects.

## Checkpoints

`.checkpoint.json` records finished phases. Without `--force`, planning is skipped when `workflow.json` exists. The exploration and execution loop always re-runs when a prior run failed.

## Extending

- **New domain:** drop `knowledge/domains/<name>.yaml` with `keywords`, `default_assertions` and `rules`. Detection is keyword overlap against the goal and URL.
- **New agent:** write `core/agents/<name>.py` with a function that reads and writes the files above, then call it from `orchestrator.py`.
- **New locator strategy:** add a kind to `build_candidates` and `_locator_for` in `smart_locator.py`, and place it in the stability order.
