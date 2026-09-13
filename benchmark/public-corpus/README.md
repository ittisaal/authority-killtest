# Frozen public semantic corpus

This directory contains the frozen 11-case public corpus used to exercise the authority-provenance semantics. It is a case-study/regression corpus, not a prevalence sample.

## Files

- `corpus.json` — exact repositories, frozen commit SHAs, normalized semantic facts, expected tri-state labels, and evidence paths.
- `evaluate_corpus.py` — label computation plus two simple comparison rules.
- `results.json` — deterministic output from `python evaluate_corpus.py corpus.json`.

## Label semantics

The evaluator does not read `expected_label` when deriving a case result. It reasons from normalized facts:

1. If a repository-scoped actor cannot modify the controlling state, the case is safe for that actor model.
2. If mutation authority is unknown, the case remains unknown.
3. If the evaluated configuration confirms no policy edge, the case is safe.
4. An independent fixed guard or a demonstrated absence of marginal privilege/protection change yields safe.
5. Incomplete composition evidence yields unknown rather than being forced to safe/unsafe.
6. Unsafe requires actor-authorized mutation, a real policy edge, a reachable security-reducing state, no independent guard, and a marginal protection/privilege delta.

## Frozen aggregate

Gold labels: 1 unsafe, 5 safe, 5 unknown.

On the six known binary cases, the semantic evaluator yields TP=1, FP=0, TN=5, FN=0. This is a regression result for the frozen cases, not an accuracy or ecosystem claim.

Simple comparison rules:

- `repo-editable` only: TP=1, FP=2, TN=3, FN=0.
- `repo-editable + consumed`: TP=1, FP=1, TN=4, FN=0.

The false positives are the point of the comparison: mutability or mutability-plus-consumption alone does not establish a new effective privilege/protection state.

## Reproducibility

Run:

```bash
python benchmark/public-corpus/evaluate_corpus.py benchmark/public-corpus/corpus.json
```

The expected output is committed as `results.json`.
