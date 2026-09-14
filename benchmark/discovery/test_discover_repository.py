import importlib.util
from pathlib import Path

core_path = Path(__file__).with_name("discover_repository.py")
core_spec = importlib.util.spec_from_file_location("discover_repository", core_path)
core = importlib.util.module_from_spec(core_spec)
core_spec.loader.exec_module(core)

tree_path = Path(__file__).with_name("discover_repository_tree.py")
tree_spec = importlib.util.spec_from_file_location("discover_repository_tree", tree_path)
tree = importlib.util.module_from_spec(tree_spec)
tree_spec.loader.exec_module(tree)


def docs(text, url="https://github.com/acme/repo/blob/abc/config.py"):
    return [(url, text)]


def names(rows):
    return {row["canonical"] for row in rows}


def test_direct_event_property_discovery():
    rows = core.discover_candidates(docs("x = github.event.repository.custom_properties.security_tier"))
    assert core.canonical("security_tier") in names(rows)


def test_bracket_property_discovery():
    rows = core.discover_candidates(docs("x = github.event.repository.custom_properties['automerge-humans']"))
    assert core.canonical("automerge-humans") in names(rows)


def test_constant_backed_property_name_discovery():
    text = '''
TIER_PROPERTY_NAME = "tier"
tier_property = github.OrganizationCustomProperties(
    "custom-tier",
    property_name=TIER_PROPERTY_NAME,
    allowed_values=["standard", "unmanaged"],
    values_editable_by="org_actors",
)
'''
    rows = core.discover_candidates(docs(text))
    assert core.canonical("tier") in names(rows)


def test_shell_variable_alias_normalizes_to_same_property():
    text = 'create_property "$GHAS_STATUS_UPDATED" "timestamp" "string" "false" "" "" "org_and_repo_actors"'
    rows = core.discover_candidates(docs(text, "https://github.com/acme/repo/blob/abc/setup.sh"))
    assert core.canonical("GHAS_Status_Updated") in names(rows)


def test_oidc_claim_discovers_property_name():
    rows = core.discover_candidates(docs("claim = repo_property_environment_tier"))
    assert core.canonical("environment_tier") in names(rows)


def test_generic_property_name_without_github_context_is_ignored():
    rows = core.discover_candidates(docs('property_name="display_name"\nprint(property_name)'))
    assert core.canonical("display_name") not in names(rows)


def test_typed_constant_alias_is_resolved():
    evidence = docs('''
SELECTOR_PROPERTY_NAME: Final = "governance-tier"
thing = github.OrganizationCustomProperties(
    "selector",
    property_name=SELECTOR_PROPERTY_NAME,
    values_editable_by="org_actors",
)
''')
    base = core.discover_candidates(evidence)
    rows = tree.augment_candidates(evidence, base)
    assert core.canonical("governance-tier") in names(rows)
    assert core.canonical("SELECTOR_PROPERTY_NAME") not in names(rows)


def test_fixed_alias_tied_to_property_read_is_discovered():
    evidence = docs('''
      PROP: workload_tier
      run: |
        value="$(gh api "/repos/${GITHUB_REPOSITORY}/properties/values" \\
          --jq '.[] | select(.property_name == env.PROP) | .value')"
''', "https://github.com/acme/repo/blob/abc/.github/workflows/shared.yml")
    rows = tree.augment_candidates(evidence, core.discover_candidates(evidence))
    assert core.canonical("workload_tier") in names(rows)


def test_fixed_alias_without_property_read_is_ignored():
    evidence = docs('PROP: workload_tier\nrun: echo "$PROP"')
    rows = tree.augment_candidates(evidence, core.discover_candidates(evidence))
    assert core.canonical("workload_tier") not in names(rows)


def test_integrity_marker_is_not_promoted_to_u(monkeypatch):
    monkeypatch.setattr(tree.core, "classify_property", lambda prop, evidence: {
        "property": prop,
        "label": "U",
        "reason": "candidate",
        "extracted": {
            "actor_can_modify": True,
            "consumer_relation": "integrity_marker",
            "protection_reducing_state_observed": True,
            "independent_guard_observed": False,
        },
        "evidence_files": {},
    })
    row = tree.classify_candidate("rollout_marker", docs("x"))
    assert row["label"] == "N"


def test_guarded_integrity_marker_stays_s(monkeypatch):
    monkeypatch.setattr(tree.core, "classify_property", lambda prop, evidence: {
        "property": prop,
        "label": "S",
        "reason": "guard remains",
        "extracted": {
            "actor_can_modify": True,
            "consumer_relation": "integrity_marker",
            "protection_reducing_state_observed": True,
            "independent_guard_observed": True,
        },
        "evidence_files": {},
    })
    row = tree.classify_candidate("rollout_marker", docs("x"))
    assert row["label"] == "S"


def test_no_case_specific_discovery_branches():
    source = (core_path.read_text() + "\n" + tree_path.read_text()).lower()
    for forbidden in ("mcp-research", "spicelabshq", "verjson", "dryvist", "callmegreg", "mitodl"):
        assert forbidden not in source
