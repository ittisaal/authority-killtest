# Blind-v2 adjudication

Blind-v2 was frozen and run before target names were revealed. The raw run completed successfully on 14 public repository snapshots from 14 owners.

## Raw run

- Workflow run: `34754127136`
- Job: `103715511501`
- Frozen head: `879f6404e80e80c8d43c573d4940998963a274e1`
- Artifact: `10317006525` (`blind-discovery-v2-raw-results`)
- Artifact SHA-256: `d8e65a3ad471cbfb63b9412b5dc34b22bb2d4d200fb7ef97fff07c9d08e8a250`
- Predeclared target-manifest SHA-256: `7d0d095a0c8538683230baf8ae88a57e735ba9a7cd34bf89755e712c2bd81b87`
- Execution errors: **0/14**

The raw run produced 81 candidate properties overall: 0 U, 4 S, and 77 N. Candidate counts are not prevalence.

## Target scoring

The frozen discoverer found the exact predeclared target in **9/14 (64.3%)** repositories.

Manual strict adjudication after the raw artifact was fixed gave:

- **0 U**
- **5 S**
- **9 N**

Among the 9 targets actually found, the frozen analyzer got **8/9 (88.9%)** strict U/S/N labels correct. End-to-end, requiring both target discovery and the correct strict label, it got **8/14 (57.1%)**. It produced **0 false U** results.

The only semantic error after finding the correct target was `V206/testproperty`: the analyzer returned N, while manual review classified the snapshot S because the repository only demonstrates retrieving/exposing the property and shows no protection or authorization consumer.

## Discovery misses

The five exact-target misses were:

- V202 `portfolio`
- V203 `fleet-managed`
- V208 `team`
- V209 `environment_tier`
- V210 `environment_tier`

These misses are preserved as blind-v2 results and must not be repaired in-place. Any discovery changes belong in a later fresh blind evaluation.

## U* annotations

Strict scoring keeps incomplete public cases as N. Separately:

- **V201 `skip-harden-runner` — U***: effect is visible in code; deployed repository-level editability is not publicly established.
- **V211 `SKIP_PROXY_CACHE` — U***: the workflow effect is visible; repository-level editability is not publicly established.

U* is an evidence qualifier, not a replacement for the strict benchmark label.

## What changed from blind-v1

Blind-v1 found more targets (**18/21 = 85.7%**) but was too cautious after discovery (**7/18 = 38.9% semantic agreement**). Blind-v2 found fewer exact targets (**9/14 = 64.3%**) on this more heterogeneous fresh set, but when it found the target its semantic decision was much better (**8/9 = 88.9%**).

The clean conclusion is therefore: **semantic classification improved strongly; automatic target discovery is still the bottleneck and did not generalize as well as hoped.**

This candidate-enriched set is not a prevalence sample.
