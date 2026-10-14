# Blind-v5 adjudication

Blind-v5 evaluates the deployment-provenance hardening of frozen V4 on a fresh
candidate-enriched set of 14 public repository snapshots from 14 distinct owners.
V5 was frozen before selecting the cases. The analyzer received only case id,
repository, and exact commit.

## Integrity and execution

- V5 freeze commit: `464467fba9a8baffa28bf53a4740e1fab27751a1`
- fresh input-set commit: `c82a52aba4a8f3333a44d5f377834d4bb6267847`
- pre-run gold-commitment commit: `4e480a266f0b8471ee3e18626e1e7a1948c59a30`
- pre-run gold SHA-256 commitment:
  `b95a219fd74461408af82b3fc9ad7de740d98505ad6834bce6aefebb05fc594d`
- launch head: `b700be1472115a60752bfd822ea99ed1b0fb58a7`
- workflow run: `35190536442`
- attempt 1 artifact: `10495999664`
- attempt 1 artifact digest:
  `sha256:f2639d0c33566a141667dce7a0e1c70a711d861c3564513fe187b04cf1253076`
- attempt 2 artifact: `11861237880`
- attempt 2 artifact digest:
  `sha256:dad8432a24d4536f2d3eb76afac4bbff0ca76f86f73299d99b54f00bed0a3aa5`

The frozen V5 implementation and unit tests were unchanged between attempts.

### Gold-preimage limitation

The repository contains the timestamped SHA-256 commitment made before the raw
run, but the full committed gold-manifest preimage was not durably retained in
the repository or retained run artifacts. The case labels below were therefore
reconstructed from the same frozen public snapshots under the already-frozen
strict U/S/N rules after the raw artifact existed.

The reconstruction is **not claimed to cryptographically verify** the pre-run
gold commitment. Consequently, blind-v5 should be treated as a fresh,
frozen-analyzer diagnostic validation, not as the paper's primary auditable
blind benchmark. Blind-v4 remains the primary fully reveal-verifiable blind
evaluation.

## Raw V5 result

Both workflow attempts produced the same case-level outcome.

Candidate-level V5 output on the 12 successfully scanned cases:

- U: **0**
- S: **14**
- N: **33**

The corresponding raw-V4 candidate labels on those same discovered candidates
were:

- U: **0**
- S: **17**
- N: **30**

At case level, using `U if any U; else S if any S; else N`:

- automatic U: **0**
- automatic S: **2**
- automatic N: **10**
- infrastructure errors: **2**

The two errors were:

- `V512` — `awaisstack/Coral-CFO`
- `V513` — `QCDIS/kms-elasticsearch-api`

Both failed while reading large GitHub repository/tree data with
`IncompleteRead`. A full unchanged rerun reproduced the errors with different
partial byte counts. They remain **E/error** in automatic scoring.

Manual inspection of the exact snapshots found that the relevant matches in
those two repositories are vendored PyGithub code under
`.venv-camel/Lib/site-packages/...` and
`.indexer/lib64/python3.12/site-packages/...`, respectively. That supports
manual N adjudication but does not convert an automatic infrastructure error
into an automatic N.

## Reconstructed strict manual labels

| Case | Repository | V5 case output | Manual strict | Rationale |
|---|---|---:|---:|---|
| V501 | `alphazede/bran` | N | N | `delivery_profile` is directly consumed by a workflow, but the public snapshot does not establish bounded repository-actor mutation authority. |
| V502 | `meshery-extensions/.github` | S | S | The `support` schema explicitly sets `values_editable_by: org_actors`; the bounded repository actor cannot change it. |
| V503 | `grandchallenge/MATH-PROGRAMME` | N | N | Apparent org-only/property-policy evidence is anchored in tests and administration machinery; no deployed bounded-repository-actor authority-to-protection chain is established. |
| V504 | `mindclade-old-2/github-config-old` | S | S | Deployed governance configuration keeps relevant custom-property values org-only while properties feed governance/ruleset machinery. |
| V505 | `aj-foster/open-api-github` | N | N | GitHub OpenAPI client/schema implementation; no deployed repository-specific authority-to-protection composition. |
| V506 | `Yuunano108/soenneker.github.openapiclient` | N | N | Generated Kiota GitHub API client material, not a deployed policy composition. |
| V507 | `sous-chefs/yum-fedora` | N | N | No concrete GitHub repository custom-property authority-to-policy chain is established. |
| V508 | `eseidel/analyzer_crash` | N | N | Relevant material is generated GitHub API model/client code, not deployed repository policy. |
| V509 | `mlops-club/sagemaker-exploration` | N | N | Relevant material is vendored PyGithub code in a Lambda layer; no repository-specific authority/protection chain. |
| V510 | `iq220/octokit` | N | N | Generated GitHub/Octokit API client models, not deployed repository-specific policy. |
| V511 | `dex2dot0/ODCForgeAssets` | N | N | No concrete GitHub repository custom-property authority-to-policy chain is established. |
| V512 | `awaisstack/Coral-CFO` | E | N | Automatic scan errored; manual evidence is vendored PyGithub under `.venv-camel/Lib/site-packages`, not deployed policy. |
| V513 | `QCDIS/kms-elasticsearch-api` | E | N | Automatic scan errored; manual evidence is vendored PyGithub under `.indexer/.../site-packages`, not deployed policy. |
| V514 | `fa22-bse-058-droid/forge` | N | N | No concrete GitHub repository custom-property authority-to-policy chain is established. |

Manual strict distribution:

- U: **0**
- S: **2**
- N: **12**

## Diagnostic score

On the **12 cases that completed automatically**:

- strict-label agreement: **12/12 = 100%**
- false U: **0**
- false S: **0**
- false N: **0**

Including infrastructure coverage as an end-to-end requirement:

- completed-and-correct: **12/14 = 85.7%**
- unresolved automatic errors: **2/14 = 14.3%**

These percentages are **not general GitHub accuracy estimates**. The set is
small, candidate-enriched, and deliberately selected after V5 was frozen to
exercise the failure classes exposed by the earlier broad evaluation.

## What V5 actually fixed

The clearest fresh regression is V503. Raw V4 classified three candidates S from
test/reference-style authority evidence. V5 demoted all three to N because the
safe evidence did not survive deployment-provenance gating.

At the same time V5 retained the two meaningful S cases:

- V502: explicit deployed org-only authority boundary;
- V504: deployed org-only governance/property boundary.

Thus, on the completed cases, the deployment-provenance gate removed the
observed fresh reference/test false-S behavior without erasing the two
deployment-supported safe cases.

## Reporting boundary

Use blind-v5 as evidence that deployment-provenance gating addresses the
specific false-positive classes that motivated V5. Do **not** report 100% as
ecosystem-wide accuracy, do not count the two transport errors as N, and do not
claim the lost gold preimage was verified.

No further semantic tuning of V5 is justified from this set. V5 is closed.
