---
name: qa-test-case-design
description: Use when writing test cases, test sets, or a requirements traceability matrix (RTM) for any feature. Covers positive, negative, edge and security cases with fixed CSV columns.
---

# Test Case Design

Every requirement maps to at least one case. High-risk features get negative + edge + security cases, not just happy paths.

## Steps
1. Load `docs/02-requirements.csv` and the test plan's risk table.
2. Group cases into **test sets** by feature (Auth, Onboarding, Billing, Sharing, Settings, Admin…).
3. For each requirement, derive cases with these techniques:
   - **Positive** — happy path per role and plan tier
   - **Negative** — empty, wrong type, wrong format, unauthorised role, expired/used token
   - **Edge / BVA** — min-1, min, max, max+1; zero; very long strings (5,000 chars); unicode/emoji; leading/trailing spaces; whitespace-only
   - **State transition** — every allowed and forbidden move (Pending → Approved → Revoked; Draft → Shared → Finalized → reopen?)
   - **Security** — IDOR (change the ID), missing/tampered token, XSS `<script>alert(1)</script>`, SQLi `' OR 1=1 --`, rate limits, enumeration via different messages
   - **Integration** — email actually arrives, webhook fires, third party down
4. Mark cases blocked by open ambiguities as `Blocked – Spec` with the AMB ID. Features not built yet: `Blocked – Build Pending`.
5. Build the RTM.

## Output: `docs/04-test-cases.csv`
Columns (fixed):
`TC ID,Test Set,Ticket ID,Req ID,Type,Category,Priority,Title,Preconditions,Test Data,Steps,Expected Result,Actual Result,Status,Bug ID,Environment,Executed By,Date,Notes`
- Type: Positive / Negative / Edge / Security / Integration / Accessibility / Performance
- Priority: P1 / P2 / P3
- Status (blank until run): Pass / Fail / Blocked – <reason> / Not Executed
- Steps: numbered `1 … 2 … 3 …` in one cell
- Expected Result: observable and specific ("shows 'Invalid email or password' and stays on /login"), never "works correctly"

`docs/04-rtm.csv`: `Req ID,Requirement,TC IDs,Coverage (Full/Partial/None),Open AMB`

## Quality check before handing over
- Any requirement with 0 cases? Any P1 feature with no negative case? Any expected result that a stranger couldn't judge? Fix those.
- Report counts per test set and per type.
