# Blind-v5 adjudication

Blind-v5 evaluates the deployment-provenance hardening of frozen V4 on a fresh
candidate-enriched set of 14 public repository snapshots from 14 distinct owners.
V5 was frozen before selecting the cases. The analyzer received only case id,
repository, and exact commit.

## Integrity and execution

- V5 freeze commit: `464467fba9a8baffa28bf53a4740e1fab27751a1`
- fresh input-set commit: `c82a52aba4a8f3333a44d5f377834d4bb6267847`
- historical pre-run gold-commitment commit:
  `4e480a266f0b8471ee3e18626e1e7a1948c59a30`
- historical gold SHA-256 commitment:
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

### Gold-preimage limitation and superseding reference set

The repository contains the timestamped SHA-256 commitment made before the raw
run, but the full committed gold-manifest preimage was not durably retained in
the repository or retained run artifacts. The historical commitment therefore
cannot now be opened and byte-for-byte verified.

After that loss was identified, all 14 frozen snapshots were independently
re-adjudicated from scratch under the already-frozen strict U/S/N rules, with
the adjudicator blind to V5 predictions. That independent adjudication is
recorded in `blind-v5-gold-superseding.json` and is the definitive reference
set used below.

This superseding set is **not claimed to be the recovered preimage** of the
historical commitment. Blind-v5 is therefore a frozen-analyzer diagnostic
validation with independent blind reference labels, while blind-v4 remains the
primary fully reveal-verifiable blind benchmark.

## Raw V5 result

Both recorded workflow attempts produced the same case-level outcome.

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

## Superseding independent blind labels

| Case | Repository | V5 case output | Manual strict | Rationale |
|---|---|---:|---:|---|
| V501 | `alphazede/bran` | N | S | `delivery_profile` is consumed by `bran-fast.yml`, but the skip condition also requires immutable `github.repository == 'alphazede/bran-dev'`; for the evaluated repository `alphazede/bran` that guard is false, so the property cannot suppress the check. |
| V502 | `meshery-extensions/.github` | S | S | The `support` schema sets `values_editable_by: "org_actors"`; if that schema is active, the bounded repository actor cannot directly edit the value. The visible consumers manage support metadata/topics/badges rather than privilege-bearing authorization. |
| V503 | `grandchallenge/MATH-PROGRAMME` | N | N | Governance/routing evidence is present, but the frozen snapshot does not establish a decisive bounded-repository-actor property-mutation-to-protection-delta chain. |
| V504 | `mindclade-old-2/github-config-old` | S | S | `mindclade_repository_class` is explicitly defined with `values_editable_by: org_actors` while feeding governance/ruleset machinery; the bounded repository actor is excluded from the mutation step. |
| V505 | `aj-foster/open-api-github` | N | N | GitHub OpenAPI client/schema implementation; no deployed repository-specific authority-to-protection composition. |
| V506 | `Yuunano108/soenneker.github.openapiclient` | N | N | Generated Kiota GitHub API client material, not a deployed policy composition. |
| V507 | `sous-chefs/yum-fedora` | N | N | Security-sensitive release automation exists, but no local custom-property selector with a proven bounded-repository-actor authority chain is established. |
| V508 | `eseidel/analyzer_crash` | N | N | Relevant material is generated GitHub API model/client code, not deployed repository policy. |
| V509 | `mlops-club/sagemaker-exploration` | N | N | Relevant material is vendored PyGithub code in a Lambda layer; no repository-specific authorization decision is linked to it. |
| V510 | `iq220/octokit` | N | N | Generated .NET/Octokit API client models, not deployed repository-specific policy. |
| V511 | `dex2dot0/ODCForgeAssets` | N | N | No concrete GitHub repository custom-property authority-to-policy chain is established. |
| V512 | `awaisstack/Coral-CFO` | E | N | Automatic scan errored; manual evidence is vendored PyGithub under `.venv-camel/Lib/site-packages`, not deployed policy. |
| V513 | `QCDIS/kms-elasticsearch-api` | E | N | Automatic scan errored; manual evidence is vendored PyGithub under `.indexer/.../site-packages`, not deployed policy. |
| V514 | `fa22-bse-058-droid/forge` | N | N | Relevant custom-property material is vendored PyGithub in a backend virtual environment, not deployed repository policy. |

Manual strict distribution:

- U: **0**
- S: **3**
- N: **11**

The earlier post-run reconstruction of **0 U / 2 S / 12 N** is superseded by
this independent blind re-adjudication. The substantive correction is V501:
the fixed repository-identity guard is sufficient for strict S even though
property editability itself is not established.

## Diagnostic score

On the **12 cases that completed automatically**:

- strict-label agreement: **11/12 = 91.7%**
- false U: **0**
- false S: **0**
- false N: **1** (`V501`)

Infrastructure coverage:

- completed automatically: **12/14 = 85.7%**
- completed-and-correct: **11/14 = 78.6%**
- semantic miss among all cases: **1/14 = 7.1%**
- unresolved automatic errors: **2/14 = 14.3%**

These percentages are **not general GitHub accuracy estimates**. The set is
small, candidate-enriched, and deliberately selected after V5 was frozen to
exercise the failure classes exposed by the earlier broad evaluation.

## What V5 actually fixed, and what it still missed

The clearest fresh regression improvement is V503. Raw V4 classified three
candidates S from test/reference-style authority evidence. V5 demoted all three
to N because the safe evidence did not survive deployment-provenance gating.

V5 also retained the two deployment-supported S cases:

- V502: explicit org-only `support` property schema plus benign visible consumers;
- V504: deployed org-only governance/property boundary.

The remaining semantic miss is V501. V5 found `delivery_profile` but returned N;
the independent blind adjudication is S because a fixed repository-identity guard
makes the skip path unreachable for the evaluated repository. Thus V5 improves
deployment-provenance handling without fully recognizing all independent
immutable guards.

## Reporting boundary

Use blind-v5 as evidence that deployment-provenance gating addresses the
specific false-positive classes that motivated V5, while preserving a documented
conservative false-N on V501. Do **not** report 91.7% as ecosystem-wide accuracy,
do not count the two transport errors as N, and do not claim the historical gold
preimage was recovered.

No further semantic tuning of V5 is justified from this set. V5 is closed.
