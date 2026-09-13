# Controlled benchmark runbook

## U3 — required security-gate bypass

Goal: prove that changing only a repository custom property can turn the same controlled-vulnerability PR from blocked to passing.

### One-time organization setup

Create custom property `security_scan_policy`:
- type: single select
- values: `enforced`, `bypass`
- allow repository actors to set the property
- initial value on `authority-killtest`: `enforced`

Create a ruleset for `main` that requires the status check `security-gate`.

### Trial

1. Use a PR whose head contains `benchmark/attack-fixture/known-vulnerability.txt`.
2. With `security_scan_policy=enforced`, run/re-run `security-gate` and preserve the run URL. Expected: `BLOCKED` / failed check.
3. Change only `security_scan_policy` to `bypass` using the repository actor account.
4. Re-run the same workflow for the same PR/commit and preserve the run URL. Expected: `BYPASSED` / successful required check.
5. Record actor, commit SHA, property before/after, workflow run IDs, and ruleset snapshot.

Strongest evidence: identical code commit, identical workflow, identical ruleset; only metadata changes.

## S2 — fixed independent guard

Create custom property `security_floor`:
- type: single select
- values: `enforced`, `relaxed`
- organization actors only
- value on `authority-killtest`: `enforced`

Then set repository-editable `security_scan_policy=bypass`.

Expected: `security_floor=enforced` wins; the controlled vulnerability remains blocked. This is the counterexample to `repo-editable + consumed => unsafe`.

## S3 — restricted value-domain control

Create custom property `scan_profile`:
- type: single select
- values: `standard`, `hardened`
- allow repository actors to set it

Try both values while the controlled vulnerability is present.

Expected: both remain blocked. The actor has mutation authority, but the value domain contains no disabling state.

## U4 — direct ruleset-selection bypass

Create custom property `branch_protection_profile`:
- type: single select
- values: `protected`, `excluded`
- allow repository actors to set it
- initial value: `protected`

Create an organization ruleset whose repository target condition is `branch_protection_profile=protected`, and whose branch rules require a pull request plus at least one approving review.

Trial:
1. Confirm the ruleset applies while the property is `protected`.
2. With the repository actor account, change only the property to `excluded`.
3. Confirm the repository no longer matches that ruleset and the previously denied direct behavior is now allowed.

Do not generalize from the deliberately unsafe configuration to a GitHub vulnerability; the experiment demonstrates unsafe composition/authority provenance.

## Existing U1/U2

The current `oidc-property-killtest.yml` is the evidence harness for the already-completed GCP and JFrog cases. Preserve it unchanged so the original authorization-flip evidence remains reproducible.
