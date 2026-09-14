# Scale Manual Evaluation Protocol v1

Status: **frozen before manual case labels are recorded**.

## Purpose

This protocol evaluates the frozen V4 analyzer on the candidate-enriched 699-case harvest without turning that harvest into an ecosystem-prevalence claim.

The broad harvest has two purposes:

1. test whether the analyzer remains conservative on noisy public repositories; and
2. characterize the kinds of public evidence that produce U, S, N, or unresolved outcomes.

It is **not** a random sample of GitHub, and no percentage from the 699 cases may be reported as prevalence.

## Frozen inputs

- Harvest-v2 canonical union SHA-256: `7e2165033973435aee0bd50a78839c2476d2dffd3d3f89a562171f0a380ba891`.
- Recovered aggregate artifact: Actions artifact `10357985407`.
- Aggregate artifact digest: `sha256:dc3e49643218db3fcce5d247d671092f8dcb7958b5f719c9cd9799e795d79b45`.
- Frozen analyzer implementation: `benchmark/discovery/FREEZE_V4.json`.
- Manual-evaluation selection: `benchmark/evaluation/scale-manual-eval-v1-selection.json`.
- Selection SHA-256 (UTF-8 JSON file): `baf261a6ce45ffbb5bb9d55a9afea8d9dd2fd6b8f07bf5a24585c6f7b843cdc3`.

No V4 semantic rule may be changed after seeing these scale outputs for this evaluation.

## Unit of evaluation

The primary manual unit is a **repository+commit case**.

Automatic case label is aggregated from candidate labels:

- U if any candidate is U;
- otherwise S if any candidate is S;
- otherwise N.

This aggregation is used only to compare V4 output with manual adjudication. Candidate-level parser labels remain available for diagnostic analysis.

## Manual strict labels

### U — unsafe

Use U only when public evidence supports the full bounded-authority chain:

1. a bounded repository-scoped actor is publicly authorized to mutate the relevant property/configuration;
2. that mutation reaches a concrete security/authorization/protection consumer; and
3. a new effective privilege or a real protection loss follows.

A theoretical possibility, security-sounding name, SDK schema, test fixture, generated client, or undocumented deployment assumption is not enough.

### S — positively safe/relevant

Use S when the case contains a concrete relevant control-plane edge but public evidence establishes a safety boundary, including one or more of:

- repository-level mutation authority is absent;
- an independent required guard remains;
- the allowed value domain cannot reach a protection-reducing state;
- the concrete consumer is bounded presentation/notification/telemetry with no authority/protection consequence;
- another positive fact blocks marginal privilege/protection change.

S requires positive evidence. Mere absence of an unsafe witness is not enough.

### N — insufficient or irrelevant

Use N for:

- docs/reference material without a deployed chain;
- SDK/generated schema/examples/tests/mocks/fixtures;
- generic vocabulary false positives;
- no concrete security/authorization/protection effect;
- missing decisive provenance/deployment facts;
- hypothetical downstream policy composition.

N is the conservative class for incomplete public evidence.

## Narrative U*

U* is **not** a benchmark label and never replaces strict N in the confusion matrix.

A strict-N case may be described as U* only when:

1. a concrete real security/authorization/protection effect is publicly demonstrated;
2. the relevant property/configuration feeds that effect; and
3. exactly one decisive public fact needed for strict U is unavailable, such as deployed `values_editable_by`, exact live schema, or a private downstream policy.

Security-sounding metadata, theoretical effects, or cases missing multiple decisive facts do not qualify.

The U* threshold is frozen before this manual pass.

## Selection

Manual review contains 50 cases:

1. every case with at least one automatic U or S candidate: 19 cases;
2. the known actor-authority boundary case `HV4-0233` (`github/actions-migrations-via-copilot`): 1 case;
3. 30 deterministic residual-N cases:
   - 10 with a protection-reducing state signal,
   - 10 with a concrete consumer signal but no protection-reducing state signal,
   - 10 residual/noise cases.

Residual sampling uses prime seed `101` solely as a reproducibility convention.

The selection was fixed before recording manual labels.

## Adjudication procedure

For each selected case:

1. inspect the frozen repository commit;
2. inspect the analyzer evidence paths and discovery signals;
3. identify whether the apparent property is a real GitHub repository custom property/configuration variable or unrelated vocabulary;
4. determine bounded actor mutation authority from public evidence;
5. identify the concrete consumer and whether it affects authorization/protection;
6. check independent guards and reachable value/domain restrictions;
7. assign strict U/S/N;
8. separately record U* only if the frozen narrative threshold is satisfied;
9. record a short rationale and the decisive evidence class.

Generated/test/reference material is not promoted to a deployed case without separate deployment evidence.

## Metrics that may be reported

For this 50-case **manual audit sample**:

- case-level confusion matrix;
- U precision/recall only if the manual sample contains manual-U cases;
- S precision/recall only within this selected audit sample;
- N agreement within this selected audit sample;
- overall agreement on the selected audit sample;
- false-U count;
- false-S count;
- abstention/conservatism observations.

For the **full 699-case harvest**:

- cases present/success/error;
- candidate count and raw automatic label count;
- number of repositories/owners;
- number of automatically flagged cases;
- number of manually established U/U* found during the predeclared high-signal/public-case review.

Do **not** report full-harvest accuracy or prevalence unless every case has manual ground truth under a separately frozen protocol.

## Infrastructure errors

Infrastructure/fetch/analyzer errors remain a separate outcome and are never mapped to N.

The recovered aggregate currently has 699/699 case IDs present, 698 successful V4 cases, and one remaining error case (`HV4-0154`). That case may be manually characterized for missed-discovery risk, but it is excluded from automatic-classification metrics.

## Known harvest recall limitation

The confirmed public strict-U case `mcp-research/mcp-security-scans` is absent from the 699-case search universe. Therefore the harvest cannot support an exhaustiveness or prevalence claim, regardless of manual-audit performance.
