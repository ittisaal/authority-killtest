# Security+AI Paper 1 CPU compute branch

Temporary public experiment orchestration branch. The unrelated repository main branch is untouched.

This initial workflow **only generates and validates workload manifests**. It does not execute concealment attacks or produce research findings. All outputs are marked `MANIFEST_ONLY_NOT_SCIENTIFIC_RESULTS`.

Planned jobs: TEP cross-detector transfer, stronger attacker/selective sound audit, HAI pre-frozen random baseline, TEP b1 exhaustive and bounded b3/b5 hindsight, and HAI exact b1/b2 defender enumeration.

Real evaluations require frozen model checkpoints, HAI/TEP caches, and the exact reference attacker code. They must not silently be replaced by simulations or approximations. No personal Drive credentials, unrelated notes, or private source files should be published.

Run workflow: `.github/workflows/paper1-cpu-manifests.yml` on branch `paper1-cpu-compute`.


## Frozen-result statistical audit (2026-10-16)

A separate **real CPU calculation over anonymized summaries of the already-frozen empirical results** is now available in [analysis/](analysis/README.md). Its workflow `.github/workflows/paper1-frozen-results-audit.yml` computes paired, exploratory 12-family bootstrap comparisons on standard CPU hardware. It is not a new sensor-attack evaluation.

The manifest workload matrix above remains a planning/scheduling tool, not 1,067 completed scientific results. The actual attack detector, model weights, frozen trajectories, and executable concealment code have **not** been published to this public repository. No new September robustness experiment has run on GitHub.
