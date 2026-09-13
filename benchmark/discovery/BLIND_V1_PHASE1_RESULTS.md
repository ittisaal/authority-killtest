# Blind discovery v1 — phase 1 result

The frozen analyzer was evaluated on 21 predeclared public repository snapshots spanning 13 distinct owners. The workflow verified the exact analyzer Git blobs before execution and verified that the runtime input contained no target-property or expected-label fields.

Raw run: GitHub Actions run `34752802736`, job `103712063590`, artifact `10316711983` (artifact ZIP SHA-256 `01220305fea7a7db9c20c2c00b5b55b024878bd082d184c681ec5fa441d338a5`). All 21 repository scans completed without an execution error.

Before the run, the post-run target manifest was committed only by SHA-256 digest. After the raw artifact existed, that manifest was revealed and its canonical digest reproduced the committed value `4eef1734a8035399046158d87d9515c3f32dbd756b243981fc6f51685592bb0a`.

Target discovery result: **18/21 = 85.7%**. The frozen discoverer missed B01 (`maintenance`, Genero), B10 (`VPC`, aggregate-property read), and B21 (`Technology-Pillar`, producer-side property management). It discovered the predeclared target in every other case.

The raw semantic layer returned N for all 18 discovered targets (and for all 21 candidates overall), primarily because repository-level write authority was not established from repository-visible evidence. This is an important boundary result rather than a tuned-away failure: the analyzer remains frozen. Manual semantic adjudication is the next phase and will distinguish true N from cases where broader evidence supports S or a qualified/conditional U assessment.

This set was selected from public search because it contained relevant custom-property usage or management patterns. It is candidate-enriched, not random, and must not be used to estimate ecosystem prevalence.
