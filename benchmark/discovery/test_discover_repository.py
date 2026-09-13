import importlib.util
from pathlib import Path

p = Path(__file__).with_name("discover_repository.py")
spec = importlib.util.spec_from_file_location("discover_repository", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def docs(text, url="https://github.com/acme/repo/blob/abc/config.py"):
    return [(url, text)]


def names(rows):
    return {row["canonical"] for row in rows}


def test_direct_event_property_discovery():
    rows = m.discover_candidates(docs("x = github.event.repository.custom_properties.security_tier"))
    assert m.canonical("security_tier") in names(rows)


def test_bracket_property_discovery():
    rows = m.discover_candidates(docs("x = github.event.repository.custom_properties['automerge-humans']"))
    assert m.canonical("automerge-humans") in names(rows)


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
    rows = m.discover_candidates(docs(text))
    assert m.canonical("tier") in names(rows)


def test_shell_variable_alias_normalizes_to_same_property():
    text = 'create_property "$GHAS_STATUS_UPDATED" "timestamp" "string" "false" "" "" "org_and_repo_actors"'
    rows = m.discover_candidates(docs(text, "https://github.com/acme/repo/blob/abc/setup.sh"))
    assert m.canonical("GHAS_Status_Updated") in names(rows)


def test_oidc_claim_discovers_property_name():
    rows = m.discover_candidates(docs("claim = repo_property_environment_tier"))
    assert m.canonical("environment_tier") in names(rows)


def test_generic_property_name_without_github_context_is_ignored():
    rows = m.discover_candidates(docs('property_name="display_name"\nprint(property_name)'))
    assert m.canonical("display_name") not in names(rows)


def test_no_case_specific_discovery_branches():
    source = p.read_text().lower()
    for forbidden in ("mcp-research", "spicelabshq", "verjson", "dryvist", "callmegreg", "mitodl"):
        assert forbidden not in source
