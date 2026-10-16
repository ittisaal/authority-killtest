# Private execution gate for Paper 1's three September extensions

**Status: NOT EXECUTED ON GITHUB.** This note tracks input requirements; it is not an experiment result.

The existing `ittisaal/authority-killtest` repository is public and also contains unrelated research. Do not commit the original frozen TEP model checkpoint, process telemetry, full HAI data, or third-party notebooks here without a separate release/privacy review.

A dedicated **private Paper 1 repository** is needed before staging these assets. Connected GitHub operations do not offer a create-private-repository action.

## Requested computations

1. **Stronger TEP concealment:** use the already-frozen Step44 data, port the September `02_TEP_stronger_attack_exact_audit.ipynb` search, and compare with original rows. Shard by independent (seed, attack configuration, protected subset) case, with explicit timeouts. Any failed or timed-out optimizer attempt is inconclusive.
2. **Cross-detector transfer:** train one separate TCN with normal train seeds 101/103/107/109/113, validation 127, calibration 131. Freeze its calibration and evaluate AE-derived protected sets on fresh 269/271/277; development data is needed to derive independent TCN placement. Fix the best-weight snapshot bug and avoid cross-seed windows.
3. **HAI frozen random baseline:** exact frozen seeds 283/293/307/311/313, budgets 1/2/3/5, 12 heldout episodes; load original FULL86 frozen detector and preserve 120-second contiguous causal replay. Raw HAI 22.04 inputs (test CSV files plus train6 references) are large, so plan an authenticated download rather than GitHub Contents API uploads.

## Already independently checked

- 27/27 original TEP behavioral outcomes reproduced locally, *not new robustness results*.
- One **local** stronger-search pilot (`XMV10_minus__severity_high`, seed 271, original security-path-blocking budget 3, beam=2, branch=2, restarts=2) remained unconcealable in about 22 seconds. Not a substitute for the preplanned beam=4/restarts=4 experiment.
- No source/data upload or GitHub Actions scientific execution is claimed here.

**Owner action:** create a separate private repo for Security+AI Paper 1 in the `ittisaal` org, grant access to the connected GitHub app, and share its URL. Keep the existing public branch and main branch unchanged.
