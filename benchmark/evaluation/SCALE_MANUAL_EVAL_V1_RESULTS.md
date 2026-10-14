# Scale Manual Evaluation v1 — Results

## Scope

This report summarizes the frozen 50-case manual audit defined in `SCALE_MANUAL_EVAL_PROTOCOL_V1.md` and `scale-manual-eval-v1-selection.json`.

The 699-case harvest is candidate-enriched and search-signature-driven. It is **not** a random sample of GitHub and these results must not be interpreted as ecosystem prevalence.

The purpose of this audit is to measure how the frozen V4 raw-evidence extractor behaves when moved from the small target-blind evaluation into a broad, noisy public-code search universe.

## Recovered scale run

| Quantity | Result |
|---|---:|
| Harvest repo+commit cases | 699 |
| Case IDs present after recovery | 699 |
| Successful V4 cases | 698 |
| Automatic error cases | 1 |
| Discovered candidate records | 1,993 |
| Raw candidate U | 9 |
| Raw candidate S | 53 |
| Raw candidate N | 1,931 |
| Automatic case-level U | 4 |
| Automatic case-level S | 15 |
| Automatic case-level N | 679 |
| Automatic case-level ERROR | 1 |

The remaining automatic error is `HV4-0154` (`databrickslabs/ontos`). Errors remain separate and are never mapped to N.

## Manual audit selection

The frozen manual audit contains 50 cases:

- all 19 cases automatically labeled U or S at case level;
- `HV4-0233` (`github/actions-migrations-via-copilot`) as a preselected authority-without-security-delta boundary case;
- 30 deterministic automatic-N cases, split into 10 protection-signal N, 10 consumer-signal N, and 10 residual/noise N cases.

Prime seed `101` is used only as a reproducibility convention for deterministic residual sampling.

## Manual strict labels

| Manual label | Count |
|---|---:|
| U | 0 |
| S | 3 |
| N | 47 |
| Narrative U* among selected cases | 0 |

The three manual-S cases are:

| Case | Repository | Why S |
|---|---|---|
| HV4-0404 | `mitodl/ol-infrastructure` | `tier` selects organization rulesets, but its frozen schema explicitly uses `values_editable_by="org_actors"`, so the bounded repository actor cannot retier the repository. |
| HV4-0454 | `open-telemetry/opentelemetry-collector-contrib` | Repository custom properties are consumed as OpenTelemetry resource/service metadata. The concrete effect is telemetry labeling, not new privilege or protection loss. |
| HV4-0623 | `Team-Immersive-Intelligence/ImmersiveIntelligence` | `project_pretty_name` is consumed from `github.event.repository.custom_properties` only as a Discord/display name. |

No selected case satisfies strict U, and no selected strict-N case clears the frozen U* threshold.

## Confusion matrix

Rows are manual strict labels; columns are automatic V4 case-level labels.

| Manual \\ Auto | U | S | N | Total |
|---|---:|---:|---:|---:|
| U | 0 | 0 | 0 | 0 |
| S | 0 | 3 | 0 | 3 |
| N | 4 | 12 | 31 | 47 |
| **Total** | **4** | **15** | **31** | **50** |

Agreement on this deliberately positive-enriched audit sample is **34/50 = 68.0%**.

This 68.0% number is **not** a general analyzer-accuracy estimate. The sample intentionally includes every automatic U/S case, so it overweights precisely the cases most likely to require deployment-aware manual adjudication.

## Diagnostics

| Diagnostic | Result |
|---|---:|
| Automatic U cases | 4 |
| Manual U among automatic U | 0 |
| False-U count | 4 |
| U precision in selected audit | 0/4 = 0% |
| U recall | Undefined: selected audit contains no manual U |
| Automatic S cases | 15 |
| Manual S among automatic S | 3 |
| False-S count | 12 |
| S precision in selected audit | 3/15 = 20.0% |
| S recall in selected audit | 3/3 = 100% |
| Automatic N cases in audit | 31 |
| Manual N among automatic N | 31 |
| N precision in selected audit | 31/31 = 100% |
| N recall in selected audit | 31/47 ≈ 66.0% |

The strongest positive result from the broad audit is therefore **conservatism of raw N**, not precision of raw U/S. Every selected automatic-N case remained manual N, while positive raw labels were substantially contaminated by non-deployment evidence.

## Why the raw positive labels were noisy

The false-positive modes cluster into five recurring classes:

1. **Generated SDK/API material.** Examples include `pulumi/pulumi-github`, `alchemy-run/distilled`, and `yanyongyu/githubkit`. These files accurately describe GitHub custom-property capabilities but do not establish that the repository itself deploys a property-to-security-policy composition.
2. **Tests and fixtures.** `eclipse-csi/otterdog`, `github/github-mcp-server`, and `octokit/webhooks.net` contain realistic custom-property schemas or values in tests, but those fixtures are not evidence of a live protection-changing deployment.
3. **Provider/reference implementations.** `integrations/terraform-provider-github`, `crossplane-contrib/provider-upjet-github`, and `google/go-github` implement or document the GitHub API but do not by themselves instantiate the downstream security edge needed for U or S.
4. **Unrelated domain custom properties.** Repositories such as `aidotse/PASEOS`, `dfki-ric/phobos`, and `jamesscottbrown/pyyed` use the phrase “custom properties” for simulation, robotics, or graph metadata unrelated to GitHub repository custom properties.
5. **Generic vocabulary/prose.** Security-like or property-like words can appear in workflows, documentation, generated schemas, or ordinary application configuration without forming the authority-provenance chain.

These failure modes explain why broad-code-search candidate extraction should be treated as **triage**, not final semantic adjudication.

## Automatic-U cases

All four case-level automatic-U outputs are manual N:

| Case | Repository | Manual reason |
|---|---|---|
| HV4-0019 | `alchemy-run/distilled` | Generated GitHub API/spec material; no deployed authority-to-protection chain. |
| HV4-0191 | `eclipse-csi/otterdog` | Repo-editable property appears in explicit test model data; no deployed protection consumer. |
| HV4-0237 | `github/github-mcp-server` | Custom-property tests/tool schemas and generic consumers; no deployed authorization/protection chain. |
| HV4-0523 | `pulumi/pulumi-github` | Generated Pulumi SDK code; no deployed property-to-protection composition. |

This is a useful negative result: a static extractor that recognizes mutation authority and security-like consumers still needs **provenance/deployment semantics** before a broad public-code hit can be promoted to a real unsafe composition.

## Boundary case: real automation without security delta

`HV4-0233` (`github/actions-migrations-via-copilot`) is retained as an important negative boundary.

The repository publicly defines a repo-editable `GH_MIGRATION_TYPE` property and uses it to select real migration/Copilot automation. This establishes actor authority plus a real downstream automation effect. It remains manual N because the frozen evidence does not establish a **new security privilege or protection loss**.

This case directly supports the paper's decision to compare effective privilege/protection change rather than treating all metadata-controlled automation as unsafe.

## Relationship to the public U/U* evidence

The manually established public evidence remains:

| Category | Count |
|---|---:|
| Strict public U | 1 |
| Established public U* | 4 |
| U + U* | 5 |

The four established U* cases remain Genero `maintenance`, StepSecurity `skip-harden-runner`, GoHarbor `SKIP_PROXY_CACHE`, and `callmegreg-demo-org/codeql-central-config` `Application_Business_Criticality`.

GoHarbor is represented in the 699-case harvest and remains strict N / narrative U* because the concrete protection effect is public but the decisive deployed editability fact is not public.

The confirmed strict-U repository `mcp-research/mcp-security-scans` is **not present in the 699-case search universe**. Therefore the harvest is demonstrably non-exhaustive and cannot support a prevalence claim.

## Interpretation for the paper

The scale study should be presented as a **broad public-code realism and triage study**, not as a conventional benchmark with a single accuracy number.

Together, the evaluations establish different things:

- **Controlled U1–U4/S2–S3:** causal evidence that the authority-provenance failure mode is real and that guards/domains change the outcome.
- **Synthetic semantic kill suite:** regression evidence that the formal semantics distinguish intentionally constructed unsafe and safe cases better than a “mutable + consumed = unsafe” baseline.
- **Blind-v4:** target-blind discovery/classification behavior on a small, frozen, fresh-owner evaluation.
- **699-case harvest + 50-case manual audit:** realism under noisy public-code search, including generated-code/test/reference false positives, strong N conservatism, and the need for deployment-aware provenance before promoting raw positive candidates.
- **Public strict U/U* corpus:** real-world evidence while preserving missing-public-fact uncertainty rather than forcing every case binary.

These components should not be collapsed into one headline accuracy value because they answer different scientific questions.

## Locked reporting rules

For this study:

- never report 699 as a prevalence denominator;
- never call the selected 68.0% agreement ecosystem-wide accuracy;
- never map the remaining automatic error to N;
- never promote generated/test/reference evidence to deployed U without independent deployment evidence;
- keep U* narrative-only and strict N in benchmark metrics;
- state explicitly that the known strict-U public case was missed by the harvest search universe;
- preserve V4 as frozen rather than tuning it against these scale results.

The machine-readable adjudications are in `scale-manual-eval-v1-results.csv`, and `summarize_scale_manual_eval.py` reproduces the selected-sample counts, confusion matrix, agreement, and per-label diagnostics.
