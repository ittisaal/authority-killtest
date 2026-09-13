# Controlled authority-provenance benchmark

This directory contains deliberately constructed research fixtures for testing whether repository-level authority over metadata can propagate into new effective privilege or loss of protection.

The benchmark is intentionally small and auditable. It is not a vulnerability disclosure against GitHub, GCP, JFrog, or any third party.

## Existing end-to-end unsafe cases

1. `security_tier=restricted -> open` changes the GitHub OIDC claim and flips GCP project-read authorization from denied to allowed.
2. The same property mutation flips JFrog repository-read authorization from denied to allowed.

## Planned GitHub-native cases

- U3: repo-editable `security_scan_policy` can change a required security gate from enforced to bypass, causing the required check to report success without evaluating the fixture.
- U4: repo-editable `branch_protection_profile` can move a repository out of an organization ruleset that requires PR review.
- S1: an org-only security selector feeds the same kind of downstream control but cannot be changed by the repository actor.
- S2: a repo-editable selector is blocked by an independent fixed guard.
- S3: allowed values exclude the dangerous downstream value.

`scenarios.yml` records the exact authority path and the manual organization-level prerequisites.
