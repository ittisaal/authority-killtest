# Blind discovery evaluation v1

This experiment freezes the repository discoverer before evaluating a larger candidate-enriched public set.

## Design

- The analyzer is frozen at commit `e56207986fdc1410c4c166abcf8b6e80cdd470c3`; `FREEZE_V1.json` records the exact Git blob IDs of the semantic files.
- `blind-v1-input.json` contains only case ID, public repository, and exact commit.
- A 21-case target-property manifest was predeclared separately. Its canonical SHA-256 digest is committed in `blind-v1-target-commitment.json`, while the target names themselves are withheld from the discovery workflow.
- No expected U/S/N labels are predeclared. Manual semantic adjudication happens only after the raw target-blind run is complete.
- Analyzer misses, fetch errors, and N outputs are outcomes. The frozen analyzer must not be tuned during this experiment.

The 21 repositories span 13 owners and several use patterns (workflow gates, workflow/release inputs, aggregate property reads, property management, and a security-tool input). Selection is intentionally candidate-enriched from public search, not random. Therefore this experiment measures discovery/classification behavior on a broader public snapshot set; it does **not** estimate ecosystem prevalence.

## Two-phase scoring

Phase 1 writes raw discovery output without target names or labels. After that artifact exists, the committed target digest is opened by adding the exact predeclared target manifest. Manual evidence review then assigns U/S/N (and authority-observation qualifiers where needed), and a separate scorer measures:

- target-property discovery recall;
- semantic agreement on adjudicated targets;
- abstention/N behavior under incomplete evidence;
- U precision / false-U rate among analyzer U outputs;
- repository count and distinct-owner count separately.

Any analyzer change after the phase-1 run belongs to a new experiment version.
