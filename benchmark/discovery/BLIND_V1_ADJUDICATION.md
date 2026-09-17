# Blind discovery v1 — post-run adjudication

The analyzer remained frozen after the raw run. Manual adjudication was performed only after the precommitted target manifest was revealed.

## Results

- Public snapshots: **21 repositories / 13 distinct owners**.
- Runtime failures: **0/21**.
- Predeclared target property discovered: **18/21 (85.7%)**.
- Missed targets: B01 `maintenance`, B10 `VPC`, B21 `Technology-Pillar`.
- Manual strict target labels: **0 U / 12 S / 9 N**.
- Among the 18 targets the analyzer actually discovered: **11 S / 7 N** by manual adjudication.
- Frozen semantic output on those 18: **18 N**.
- Strict semantic agreement conditional on target discovery: **7/18 (38.9%)**.
- End-to-end target-found + strict-label-correct: **7/21 (33.3%)**.
- False-U count: **0**. The dominant error is conservative abstention: **11 manually-S targets were returned as N**.

Two cases receive a separate qualified annotation without changing their strict labels. B01 (Genero `maintenance`) is **U* operational**: the security-scan suppression effect is public, but deployed repo-level editability is not. B11 (`skip-harden-runner`) is **U* demo**: the real Harden-Runner skip behavior is public, but repo-level editability is not established for the demo property.

## Interpretation

The larger blind test exposed a real limitation that the earlier 8-case development + 4-case holdout did not: repository-only evidence is often sufficient to **find the relevant property**, but insufficient to prove its authority provenance. In addition, the current semantic heuristics over-abstain on benign metadata/notification consumers instead of establishing S.

This result is intentionally preserved rather than tuned away. Any changes that add aggregate-property patterns, producer-side discovery, better consumer semantics, or organization-level authority retrieval must be evaluated as **blind-v2**, not retroactively applied to blind-v1.

The set is candidate-enriched from public search and is not a prevalence sample.
