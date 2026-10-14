# Frozen raw-evidence extraction regression

Run date: 2026-09-13

This evaluation derives repository-write authority, consumer relation, protection-reducing state, and independent-guard signals from the exact frozen evidence files. The manually normalized `facts` in `corpus.json` are not used to derive the prediction; `expected_label` is consulted only after extraction for regression scoring.

## Result

- Cases: 11
- Predicted: 1 unsafe / 5 safe / 5 unknown
- Frozen-label matches: 11/11
- Known binary subset (6 cases): TP 1 / FP 0 / TN 5 / FN 0
- Frozen unknowns forced to binary: 0/5
- Evidence fetch failures: 0
- Unit/regression tests: 11 passed

CI evidence:
- workflow run: 34748500267
- job: 103700652912
- result artifact: 10314902940 (`raw-extraction-results`)
- artifact SHA-256: `c1725bb3f7c5271d65401a732aa4c93c245e4fe90306eb3cffcf683d7ba2342f`

## Case decisions

| Case | Decision | Key extracted distinction |
|---|---|---|
| C01 | unsafe | repository write established + concrete policy edge + reachable protection-reducing state + no independent guard |
| C02 | unknown | repository write established, but evidence is an integrity/rollout marker rather than a concrete privilege/protection consumer |
| C03 | safe | mutable and consumed, but an independent review/check guard remains |
| C04 | safe | repository-level write authority absent |
| C05 | unknown | mutable property found, but no concrete consuming policy edge established |
| C06 | safe | repository-level write authority absent |
| C07 | safe | repository-level write authority absent in retained readback evidence |
| C08 | safe | property and ruleset coexist, but the ruleset selects by a different repository criterion |
| C09 | unknown | consumer behavior visible; property write authority not established |
| C10 | unknown | consumer behavior visible; property write authority not established |
| C11 | unknown | policy effect visible; live property write authority not established |

## Scope limit

This is a **frozen-evidence extraction regression**, not arbitrary-repository discovery and not ecosystem accuracy. The corpus construction process already selected the relevant repositories, target property names, exact commits, and evidence URLs. This test measures how much semantic structure can be recovered from those less-normalized source artifacts while preserving honest unknowns.

A separate discovery evaluation is required before claiming that the system can start from an arbitrary repository or organization and find every relevant source automatically.
