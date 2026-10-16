# Paper 1 — frozen-results CPU statistical audit

This directory analyzes **aggregated, already-frozen** Tennessee Eastman Process (TEP) results from the August 2026 study. It neither loads raw process sensor data nor runs a detector or concealment attack.

- Original frozen 6,048-row Step44 CSV SHA-256: `81fe7b3e2187b48d10f0607e494001afd1d23a46913823f71cb159d727581a2d`.
- Frozen Step44 protocol SHA-256: `9f0118d17ad66e7a2c9f8aa0980affc5a41a3d2f9e5a624abfa9890d13f6b263`.
- The 36-row anonymized input gives **balanced minus security-path-blocking** deltas by 12 actuator-family groups and protected-channel budget 1, 3, or 5; each group/budget contains 18 actual frozen trajectories.
- `delta_auc_sum` is the sum of per-trajectory concealment-loss differences; `delta_blocked` counts the difference in nonconcealable trajectories; `delta_primary_sum` and `delta_robust_sum` are differences in impact-weighted loss sums. The mass denominators are identical for both defender methods.
- The program performs a **descriptive 12-family paired cluster bootstrap**, 5,003 resamples with seed 317, using Python's standard library only.

Lower is better for concealment AUC and impact-mass AUC. Higher is better for the nonconcealable fraction. Intervals describe sensitivity to resampling these 12 family groups; they are **not** confidence guarantees about industrial control systems in general.

The original HAI/TEP experiments, trusted placements, frozen thresholds, and models are untouched. This job is a **genuine audit of empirical frozen results** but **NOT** a new attack experiment or validation of the September extension notebooks. No attack code, model weights, sensor traces, or per-case sensor compromise orders are stored here. The related `paper1-cpu-manifests.yml` is infrastructure-only and remains manual dispatch.

Run locally: `cd paper1_compute/analysis && python3 report_paired.py`.
