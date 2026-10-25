# QA Run Report

**Goal:** Log in, add the first item to the cart, open the cart, verify "Canvas Backpack" is in the cart  
**URL:** http://127.0.0.1:8765/login.html  
**Domain:** auth  
**Planner:** heuristic  
**Verdict:** PASS WITH SECURITY FINDINGS

## Steps

| # | Intent | Kind | Result |
|---|---|---|---|
| 1 | log in | login | ok |
| 2 | add the first item to the cart | action | ok |
| 3 | open the cart | action | ok |
| 4 | verify "Canvas Backpack" is in the cart | verify | ok |

## Execution

1/1 passed in 0.64s. Self-heals used: 0.


## Security (passive)

- **HIGH** Site is served over HTTP. Final URL http://127.0.0.1:8765/login.html is not HTTPS. Credentials and tokens travel in clear text.
- **MEDIUM** Missing header: content-security-policy. No Content-Security-Policy. Injected scripts are not restricted.
- **MEDIUM** Clickjacking protection missing. Neither X-Frame-Options nor CSP frame-ancestors is set.
- **LOW** Missing header: x-content-type-options. X-Content-Type-Options: nosniff is missing.
- **LOW** Missing header: referrer-policy. No Referrer-Policy. Full URLs may leak to third parties.
- **LOW** Server version disclosed. Server header reveals: SimpleHTTP/0.6 Python/3.13.17
