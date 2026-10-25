---
name: qa-retest-regression
description: Use after developers report fixes (bug fix summary, PR merged, new build) to verify each fix independently, decide Verified/Reopened/Partially Addressed, scope regression from the changeset, and run a smoke pass.
---

# Retest, Regression & Smoke

Dev saying "fixed" is a claim. QA verifying it is the fact.

## Inputs
- Dev fix summary / PR list / release notes, new build number
- `docs/06-bug-log.csv`

## Steps
1. **Map each claimed fix to its bug.** Note the dev's disposition: Fixed / Fixed (code) + Ops / Justified (deferred) / Won't fix.
2. **Retest the original steps exactly**, then 2–3 variations around it (the fix often only covers the reported path).
3. **Assign a retest verdict:**
   - `Verified` — original + variations pass
   - `Partially Addressed` — symptom improved, capability gap remains (e.g. message fixed, preview still unsupported)
   - `Reopened` — still fails; attach new evidence
   - `Justified – needs risk acceptance` — dev deferred with reason; QA agrees/disagrees, owner must accept in writing
   - `Ops dependency` — code done, env config (DNS, SMTP, SPF/DKIM, env vars) still missing
4. **Scope regression from the changeset.** Read the PR diff / changed files. Anything sharing that module, endpoint, auth middleware, DB migration, or component gets re-run. Auth/billing changes → re-run the full auth + billing sets.
5. **Smoke pass** on the critical journeys from the product brief.
6. **Look for new bugs the fix introduced** and log them as new IDs.

## Output: `docs/07-retest-log.csv`
`Bug ID,Title,Original Severity,Dev Disposition,Build,Retest Steps,Retest Result,Retest Verdict,Evidence,Retested By,Date,Notes`
Also update `Status` and `Retest Comment` in the bug log.

Summary: X claimed fixed → Y verified, Z partial, W reopened; regression A/B pass; smoke pass/fail. Next: `qa-release-readiness`.
