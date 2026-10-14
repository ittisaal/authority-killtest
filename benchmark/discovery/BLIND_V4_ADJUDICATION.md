# Blind-v4 adjudication

Blind-v4 froze V4 before evaluating a fresh candidate-enriched set of 14 public repository snapshots from 14 distinct owners. The analyzer received only repository + exact commit. Target properties and labels were withheld until the raw artifact existed.

## Integrity

- frozen head: `399652d21071ba603dea6b7fd22ea2d0ec057fa9`
- workflow run: `34764564755`
- job: `103743120129`
- raw artifact: `10320746444`
- raw artifact ZIP SHA-256: `60c09addb5460610a6524fae0f9a6980fa3bfd8e680fb4a58b7e4aec70edf21b`
- precommitted target-manifest SHA-256: `8caca968ab7bde612fa2184c962ac5ef70c3b6d116d418d9ec4f0f3922379c57`
- target commitment verified after the raw run: yes
- execution errors: 0

## Result

- exact target discovery: **14/14 = 100%**
- strict manual labels: **0 U / 3 S / 11 N**
- predictions on the 14 found targets: **0 U / 2 S / 12 N**
- semantic agreement conditional on discovery: **13/14 = 92.9%**
- end-to-end target-found + strict-label-correct: **13/14 = 92.9%**
- false U: **0**
- false S: **0**
- false N: **1**

The only semantic error is V413 (`property_1`): V4 returned N, while a captured GitHub organization-schema response explicitly states `values_editable_by=org_actors`, which is enough for strict S because repository-level actors cannot change the value.

## Interpretation

V4 fixes the three failure classes exposed by blind-v3 on this fresh set: the predeclared target was found in every case, the previous token-backed-destination false-S pattern did not recur, and no false-U output occurred. The remaining error is conservative abstention where authority absence was encoded in replay/captured schema data but not recognized by the semantic extractor.

This is still a candidate-enriched benchmark, not a random ecosystem sample. The 100% discovery and 92.9% end-to-end result must not be presented as prevalence or general GitHub-wide accuracy.
