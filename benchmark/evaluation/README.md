# Evaluation artifacts

This directory contains the frozen publication-grade manual audit for the broad V4 harvest.

## Files

- `SCALE_MANUAL_EVAL_PROTOCOL_V1.md` — predeclared strict U/S/N and narrative U* rules, sample construction, allowed metrics, and reporting limits.
- `scale-manual-eval-v1-selection.json` — frozen 50-case case-ID selection. Repository/commit metadata is resolved from the recovered aggregate artifact rather than duplicated here.
- `scale-manual-eval-v1-results.csv` — machine-readable manual adjudications and rationales.
- `SCALE_MANUAL_EVAL_V1_RESULTS.md` — publication-oriented results, confusion matrix, false-positive taxonomy, and interpretation.
- `summarize_scale_manual_eval.py` — standard-library script that reproduces the selected-sample counts, confusion matrix, agreement, and per-label diagnostics from the CSV.

## Frozen scale source

- Harvest union SHA-256: `7e2165033973435aee0bd50a78839c2476d2dffd3d3f89a562171f0a380ba891`
- Recovered aggregate Actions artifact: `10357985407`
- Aggregate artifact digest: `sha256:dc3e49643218db3fcce5d247d671092f8dcb7958b5f719c9cd9799e795d79b45`
- Analyzer freeze: `benchmark/discovery/FREEZE_V4.json`

## Scope warning

The 699-case harvest is a signature-driven, candidate-enriched public-code search universe. It is not a random GitHub sample and must not be used to estimate prevalence.

The 50-case manual audit deliberately contains every automatic case-level U/S result, so its 68.0% agreement is not a general analyzer-accuracy estimate. It is a diagnostic stress test of raw positive triage plus a deterministic residual-N audit.

The known confirmed strict-U public repository `mcp-research/mcp-security-scans` is absent from the harvest, which independently demonstrates that the search universe is non-exhaustive.
