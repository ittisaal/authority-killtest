# Authority Provenance paper

Target: ACM CODASPY 2027 research-paper track.

- Format: ACM `sigconf`, anonymized review manuscript.
- Limit: 12 pages including references, plus up to 2 appendix pages.
- Abstract registration: 2026-11-16 AoE.
- Full paper: 2026-11-23 AoE.

Build:

```bash
latexmk -pdf main.tex
```

Primary empirical reporting rules:

- Blind V4 is the primary fully reveal-verifiable blind benchmark.
- Blind V5 is diagnostic only; its superseding 0U/3S/11N reference set was independently adjudicated blind to V5 predictions, but is not claimed to recover the historical gold-manifest preimage.
- The 699-case harvest is candidate-enriched and not a prevalence sample.
- Infrastructure errors are never mapped to N.
- U* is narrative-only and remains strict N in benchmark metrics.
