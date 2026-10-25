---
name: qa-exploratory-browser
description: Use when asked to click through, explore, execute UI test cases, reproduce a bug, or grab screenshots on a web app using the Playwright MCP browser (or Claude in Chrome), capturing console errors and failed network calls as evidence.
---

# Exploratory & UI Execution via Browser MCP

The Playwright MCP lets the agent drive a real browser: navigate, click, type, read the page, screenshot, and read console + network. This replaces most manual clicking.

## Before
- Confirm env is staging (AGENTS.md hard stops). Load URLs/accounts from `.env`.
- Decide the charter: "Explore <area> for <risk> for 30 minutes" or "Execute test set <X>".

## Loop per case / charter
1. Navigate to the start URL. Snapshot the page (accessibility tree) before acting.
2. Perform the steps exactly as written in the case.
3. After each meaningful action, check:
   - page content matches expected result
   - **console**: any red errors
   - **network**: any 4xx/5xx, especially on buttons that "do nothing" (dead buttons often fire a failing call or no call at all — both are findings)
4. Screenshot the final state to `evidence/<TC-ID>.png`. On failure, also save console + failing request/response to `evidence/<BUG-ID>/`.
5. Write Actual Result + Status back to `docs/04-test-cases.csv`.

## Exploratory heuristics (things that broke in past products)
- Buttons with no handler (Update/Restore, Delete account, Filter)
- Counters and balances that don't match plan (tokens, seats, storage)
- Features that work in one place and not another (AI Draft works, Assistant says out of tokens)
- Stale data after an upstream change (edit A, then check what depends on A)
- Messages that describe the wrong state ("complete your profile" when the profile is complete and only a toggle is off)
- Desktop vs mobile differences (share to WhatsApp, file previews)
- Back button, refresh, second tab, slow 3G (DevTools throttling)
- Empty, very long, and emoji inputs everywhere

## Accessibility quick pass
Keyboard-only navigation, visible focus, labels on inputs, colour contrast; run axe if available (`npx @axe-core/cli <url>`).

## Output
Updated statuses in the test case CSV, evidence files, and a list of new findings handed to `qa-bug-report`.
