# Controlled matrix evidence — 2026-09-13

This record preserves the completed GitHub-native controlled comparisons. The purpose is causal evidence under fixed code/configuration where practical, not ecosystem prevalence.

## U3 — required-check result flip

- PR: #3
- fixed head commit: `4678f73bb0b953e96ecf17f53d016bbb00992ee8`
- required check: `security-gate`
- property: `security_scan_policy`
- `enforced` state: job `103688967980`, result `BLOCKED`
- repository actor changed only the property value `enforced -> bypass`
- same PR/commit rerun: job `103689271407`, check succeeded via the bypass path

Interpretation: code, workflow, PR commit, and required-check rule were held fixed; the metadata value changed the effective check result.

## S2 — fixed independent guard

- mutable property: `security_scan_policy=bypass`
- organization-controlled guard: `security_floor=enforced`
- job: `103690360163`
- result: `BLOCKED`

Interpretation: editability plus consumption is not sufficient when an independent fixed guard prevents the disabling state.

## S3 — allowed-value-domain control

- property: `scan_profile`
- repository actor may select only `standard` or `hardened`
- `standard`: job `103691060202`, result `BLOCKED`
- `hardened`: job `103691189657`, result `BLOCKED`

Interpretation: editability alone is not sufficient when no allowed value reaches the disabling state.

## U4 — property-selected organization rule

- organization ruleset id: `23150600`
- name: `u4-property-selected-protection`
- selector: `branch_protection_profile=protected`
- default-branch rule: require pull request with one approving review
- repository-local ruleset `23143969` was disabled during the comparison to avoid a second independent rule
- exact no-content-change probe commit: `b9ed6e403b49566ac5b91b2ffc0173b5b0402990`

Protected state:

- `branch_protection_profile=protected`
- organization ruleset matched the repository
- direct update of `main` to the probe commit was rejected with: `Changes must be made through a pull request.`

Excluded state:

- repository actor changed only `branch_protection_profile: protected -> excluded`
- organization ruleset no longer matched the repository
- the exact same commit was accepted as a direct update of `main`

Post-test cleanup:

- property restored to `protected`
- organization ruleset is active again
- repository-local ruleset remains disabled

Interpretation: same repository, exact same commit, and same organization rule definition; changing only the repository metadata changed whether the organization rule applied and whether the direct update was allowed.

## Matrix status

| Case | Class | Status |
|---|---|---|
| U1 GCP | unsafe | complete |
| U2 JFrog | unsafe | complete |
| U3 required check | unsafe | complete |
| U4 rule selection | unsafe | complete |
| S1 org-only selector | safe | optional / not run |
| S2 fixed guard | safe | complete |
| S3 value domain | safe | complete |

Do not interpret this matrix as an estimate of how common these configurations are. It establishes controlled feasibility, causality, and semantic distinctions for the analyzer/evaluation.