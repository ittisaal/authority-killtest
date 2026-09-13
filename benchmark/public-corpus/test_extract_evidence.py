import importlib.util
from pathlib import Path

p = Path(__file__).with_name('extract_evidence.py')
spec = importlib.util.spec_from_file_location('extract_evidence', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def docs(text):
    return [('x', text)]


def test_authority_modes():
    assert m.authority('tier', docs('property_name="tier"\nvalues_editable_by="org_and_repo_actors"'))[0] is True
    assert m.authority('tier', docs('property_name="tier"\nvalues_editable_by="org_actors"'))[0] is False
    assert m.authority('tier', docs('tier exists'))[0] is None


def test_reduction_and_guard():
    red, guard, _ = m.semantics('policy', docs('policy=bypass causes skipping required scan'))
    assert red is True and guard is False
    red, guard, _ = m.semantics('automerge-humans', docs('automerge-humans=true; all required checks are green AND an approving review exists'))
    assert guard is True


def test_iac_no_edge():
    text = '''resource "github_organization_ruleset" "r" { conditions { repository_name { include=["x"] } } }
resource "github_organization_custom_properties" "p" { property_name="docs" values_editable_by="org_and_repo_actors" }'''
    assert m.explicit_no_edge('docs', docs(text))[0] is True


def test_conservative_unknown():
    assert m.classify(True, 'policy_edge', None, None, False)[0] == 'unknown'
    assert m.classify(None, 'policy_edge', True, False, False)[0] == 'unknown'


def test_no_case_specific_branches():
    source = p.read_text().lower()
    for forbidden in ('c01', 'c02', 'spicelabshq', 'mcp-research', 'dryvist', 'goharbor'):
        assert forbidden not in source
