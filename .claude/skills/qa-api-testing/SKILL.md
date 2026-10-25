---
name: qa-api-testing
description: Use when testing REST or GraphQL endpoints, importing an OpenAPI spec into Postman, building or running a Postman collection with Newman, or checking status codes, schemas, auth, rate limits and OWASP API risks.
---

# API Testing

## Setup
1. Get the spec: OpenAPI URL (`/openapi.json`, `/docs`, `/swagger`) or existing Postman collection.
2. Import into Postman (or generate a collection from the spec). Environment vars: `baseUrl`, `accessToken`, `refreshToken`, test user ids. Never hardcode secrets in the collection.
3. Add a login request that saves the token to the environment in its test script.

## Per endpoint, check
- **Happy path**: status code, response schema, required fields, types, response time
- **Auth**: no token → 401; bad/expired/tampered token → 401; wrong role → 403
- **Validation**: missing required field, wrong type, extra fields, max length, empty body → 400/422 with a useful message, never 500
- **IDOR**: another user's id → 403/404, never their data
- **Idempotency**: repeat the POST (payments, invites, checkout) → no duplicate
- **Rate limits**: hammer login/reset/OTP → 429 + Retry-After
- **Pagination / filters**: page 0, negative, huge page size
- **Errors**: no stack traces, SQL, or internal hostnames in responses
- **Side effects**: DB/state actually changed (GET after POST), email/webhook fired

## Postman test snippet
```js
pm.test("status 200", () => pm.response.to.have.status(200));
pm.test("under 800ms", () => pm.expect(pm.response.responseTime).to.be.below(800));
pm.test("has id", () => pm.expect(pm.response.json()).to.have.property("id"));
```

## Run headless (no human needed)
```bash
npx newman run api/collection.json -e api/staging.env.json -r cli,htmlextra --reporter-htmlextra-export evidence/api-report.html
```
Wire this into CI via `qa-regression-automation`.

## Output
Cases in `docs/04-test-cases.csv` (Test Set `API`), bugs via `qa-bug-report` with the request/response pasted in Evidence (redact tokens). Share the collection link in the release report.
