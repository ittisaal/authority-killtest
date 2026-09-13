# Adjacent-tool capability comparison

Snapshot date: 2026-09-13

This file records a source-level capability comparison, not a benchmark-accuracy claim. The tools have different intended scopes, so absence below means the capability was not found in the inspected public source/docs, not that the project is deficient.

## Summary

| Capability | This work | gamesapeca/gha-oidc-auditor | unified-systems-com/tap-plugin-github-core | mindclade/github-config |
|---|---|---|---|---|
| GitHub custom-property values/editability | yes | custom-property OIDC claim format present; no `values_editable_by` handling found | yes, explicitly models `allowed_values` and `values_editable_by` | yes |
| Who may mutate the property is part of the decision | yes | not found | collected as graph/model data | editability widening is classified as protection weakening |
| Custom property used as OIDC claim | yes | yes: synthesizes `repo_property_<name>` claim | GitHub federation modeled, but repository OIDC subject customization is documented as not collected today | manages OIDC subject-claim customization, but no end-to-end property-authority join found |
| GitHub property-selected ruleset/protection semantics | yes | not found | rules/settings collection exists; no composed property-authority-to-effective-protection analysis found | rulesets and custom properties are managed, but editability is classified at configuration-change level |
| Cloud-side trust conditions and resulting permissions | yes for modeled GCP/JFrog/AWS patterns | yes, major focus | documentation explicitly says cloud-side trust policy, subject conditions, and permissions are not observable from GitHub | external/cloud controls are explicitly outside this repository's owned boundary |
| Marginal effective privilege/protection delta | yes | workflow/OIDC findings and trust-policy checks, but property-writer-to-delta composition not found | not found | not found as a generic composed reachability calculation |
| Multi-step evolving authority | yes | exploit-chain logic exists for workflow/OIDC patterns; generic custom-property authority propagation not found | graph edges exist; generic reachability over changing property authority not found | no generic cross-control-plane reachability found |
| Safe mutable-property distinction via fixed guard/value domain/no-edge | yes | not found as the target abstraction | not found | broad `values_editable_by != org_actors` change is marked `protection_weakening` |
| First-class `unknown/incomplete` when composition evidence is missing | yes | findings are rule-based; equivalent tri-state composition output not found | observability states exist, but no equivalent composed decision found | incomplete connected evidence is modeled/fail-closed, but not the same per-path tri-state analysis |
| Shortest witness path | yes | exploit chains for its supported patterns | graph representation, no matching shortest authority-provenance witness found | not found |
| Multi-cut / low-cost repair synthesis | target contribution | least-privilege policy generation/remediation for OIDC scope | not found | plan/policy remediation machinery exists, but no generic path-cut optimizer found |

## Evidence inspected

### `gamesapeca/gha-oidc-auditor`

Inspected snapshot: `d86257b70d84c628466602aad2b8ec19db590f0b`.

- README describes a sophisticated GitHub Actions OIDC analyzer, exploit-chain correlator, and least-privilege cloud trust-policy generator.
- `pkg/remediation/claims.go` explicitly synthesizes repository custom-property OIDC claims as `token.actions.githubusercontent.com:repo_property_<property>`.
- Repository search for `values_editable_by` returned no source hits in the inspected snapshot.

Interpretation: this is the closest OIDC-specific neighbor. It understands the *claim* and downstream trust-policy side, but the inspected source did not show the upstream custom-property mutation-authority join that is central here.

### `unified-systems-com/tap-plugin-github-core`

Inspected snapshot: `a163c29c028c0e2632ac31ccb1f3df1f3738cab6`.

- The custom-property model and collector explicitly store `allowed_values` and `values_editable_by`.
- The project models GitHub federation and documents a real GitHub-to-AWS federation edge.
- `FEDERATES_VIA_PROVIDER.md` explicitly states that the cloud-side trust policy, subject conditions, and permissions are not observable from GitHub, and that GitHub OIDC subject customization is not collected today.

Interpretation: this is the closest graph/collector neighbor. It captures important upstream facts, but its own documentation identifies the missing downstream half needed to decide the effective privilege produced by the federation.

### `mindclade/github-config`

Inspected snapshot: `d2071e9e477b9a5a9cd655308db38bb8b395789f`.

- The repository is a declarative GitHub governance control plane with strong fail-closed validation, observation, plan evidence, and connected-evidence requirements.
- `compiler/internal/evidence/plan_evidence.go` classifies a change to `github_organization_custom_properties.values_editable_by` away from `org_actors` as `protection_weakening`, with the explanation that repository actors gain authority to edit organization-governed property values.
- README says cloud infrastructure, WIF providers, and related external controls are outside this repository's owned boundary.

Interpretation: this is a strong configuration-governance neighbor and a useful conservative baseline. The editability rule is intentionally broad; the present work asks the narrower semantic question of whether that authority actually reaches a new effective privilege/protection state, which is why safe mutable cases and unknown cases matter.

## Current novelty boundary after this comparison

Do not claim novelty for recognizing custom-property OIDC claims, collecting `values_editable_by`, flagging widened editability, building cloud trust-policy checks, or representing federation edges. Those capabilities already exist in adjacent tools.

The surviving delta is the **composition**:

`mutation authority -> policy-bearing metadata/configuration -> consumer/claim/policy selection -> downstream decision -> marginal effective privilege/protection delta`

with transitive reachability, honest unknowns, shortest witnesses, and repair cuts. The frozen corpus now provides direct counterexamples to reducing this composition to editability alone.
