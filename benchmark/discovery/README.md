# Repository-level target-blind discovery evaluation

This directory evaluates a stricter input condition than the frozen-evidence corpus.

The discoverer receives only:

- a public GitHub repository name; and
- an exact frozen commit.

It does **not** receive the target custom-property name or a hand-selected evidence-file list. It enumerates the repository tree at that commit, selects up to 500 text files using path-only priority, discovers candidate policy-bearing properties from generic syntax patterns, and then applies the conservative U/S/N semantic decision layer.

## Development regression

Eight repositories were used while debugging generic discovery patterns. After the generic fixes, the regression result is:

- target-property discovery: 8/8;
- end-to-end U/S/N outcome match: 8/8;
- fetch errors: 0;
- recursive-tree truncations: 0;
- file cap reached: 2/8 repositories.

This set is a development regression and must not be presented as held-out accuracy.

## Predeclared public holdout

Before any further algorithm changes, four additional repositories from the already-frozen public corpus were placed in `holdout.json`. They were not part of the eight-case discovery tuning set. The first holdout run produced:

- target-property discovery: 4/4;
- end-to-end U/S/N outcome match: 4/4;
- fetch errors: 0;
- recursive-tree truncations: 0;
- file cap reached: 1/4 repositories.

The holdout is still small and drawn from the same manually curated public corpus. It is evidence that the discovery stage can operate without target-property or evidence-file hints on these frozen snapshots; it is **not** a claim of ecosystem-wide accuracy or prevalence.

## Claim boundary

The current pass sees only evidence encoded in the public repository snapshot. Private organization settings, live custom-property definitions not represented in public files, organization rulesets that are not represented in repository-visible evidence, and external authorization systems absent from the repository remain outside this target-blind pass. Such missing evidence should lead to N rather than being guessed.
