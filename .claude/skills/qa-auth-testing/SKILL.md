---
name: qa-auth-testing
description: Use when testing login, sign-up, email/phone verification, OTP, OAuth (Google, GitHub, LinkedIn, Apple), password reset, sessions, JWT/refresh tokens, logout, idle timeout, rate limiting or account deletion on any product.
---

# Auth Testing (reusable across products)

This is the checklist so you never reprompt auth from scratch. Run it against the product's own spec numbers — the spec wins over the defaults below. Where the spec is silent, use the default and flag it in the ambiguity log.

## 0. Before you start
- Pull the product's auth numbers into a table: password policy, OTP length/expiry/attempts, lockout, reset-link expiry, access/refresh token lifetime, idle timeout, rate limits, cookie attributes, where the token is stored.
- Check if any behaviour is **intentional** (e.g. JWT in memory → session lost on refresh). Record it, don't log it.
- Accounts needed: new email, existing verified, existing unverified, OAuth-only, locked, each role/plan tier.

## 1. Sign-up
- Valid signup → verification sent → can't reach app before verifying (if spec says so)
- Duplicate email (same case, different case `User@` vs `user@`, with `+alias`) → one account only
- Same email via OAuth after password signup, and reverse → linked or clearly rejected, never two accounts
- Password policy: min-1, min, max, max+1; spaces-only; leading/trailing spaces; no special char; common password; unicode
- Email: missing @, spaces, 255+ chars, SQLi/XSS strings → 400 + friendly message, nothing rendered
- Max-length on every field (name, company, bio) — client AND server (send via API to bypass the UI)

## 2. Verification / OTP
- Email/OTP actually arrives (check inbox, spam). Note sender domain — raw provider domains (e.g. `xyz.supabase.co`) look like phishing
- Expiry: at expiry-1 min works, at expiry+1 fails
- Wrong code N times → lockout at the documented N; lockout survives **resend** and page refresh
- Resend cooldown matches spec; resend invalidates old code (or spec says otherwise)
- Code reuse after success → rejected

## 3. Login
- Valid / wrong password / unknown email → **same message and similar response time** (no enumeration). Compare timing over ~10 tries each
- Rate limit / lockout after threshold → 429 with Retry-After or lockout message; CAPTCHA if specced
- Unverified user login → blocked with resend option
- SQLi / XSS in both fields
- "Remember me", redirect back to the deep link after login

## 4. OAuth
- Each provider: happy path, cancel on consent screen, deny permissions, provider email already registered
- Callback with tampered/replayed `state` or `code` → rejected
- Redirect URI fixed (can't be pointed elsewhere)
- Provider down/slow → graceful error
- Branded domain on consent screen

## 5. Password reset
- Request for known and unknown email → identical response (anti-enumeration)
- Email arrives; link single-use; expires at spec time; old link dead after a new request
- New password must follow policy; can't equal old if specced
- After reset: other sessions invalidated? auto-login or redirect to login? (common spec contradiction — check for race conditions on auto-redirect)
- Rate limit on reset requests

## 6. Session & tokens (DevTools → Application + Network)
- Where is the token? localStorage = flag XSS risk unless documented; cookie → check httpOnly, Secure, SameSite
- Access token expiry honoured; refresh rotates (old refresh token rejected after use)
- Tampered JWT (edit payload, keep signature) → 401
- Expired token → 401 and clean redirect to login, not a blank page
- Logout kills the token server-side (replay old token → 401), clears storage, back button doesn't show data
- Idle timeout: warning + forced logout at spec time
- Multi-tab / multi-device behaviour matches spec
- Protected routes and APIs without a token → 401/redirect, never data

## 7. Authorisation
- Role A calls Role B's endpoints → 403 (enforced at API, not just hidden in UI)
- IDOR: swap user/workspace/document IDs in URLs and payloads
- Plan-tier features enforced server-side

## 8. Account lifecycle
- Change email / password requires current password or step-up
- **Delete account**: confirmation, actually deletes, can't log in after, data gone (GDPR/NDPR). Dead delete buttons are a recurring bug — always test it

## Output
Write cases into `docs/04-test-cases.csv` under Test Set `Auth` using the `qa-test-case-design` columns. Every failure → `qa-bug-report`. Anything here worth keeping green forever → `qa-regression-automation` (start with `tests/auth.spec.ts`).
