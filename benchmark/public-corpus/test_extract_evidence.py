import importlib.util
from pathlib import Path

p = Path(__file__).with_name('extract_evidence.py')
spec = importlib.util.spec_from_file_location('extract_evidence', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def docs(text, url='x.py'):
    return [(url, text)]


def test_authority_modes():
    assert m.authority('tier', docs('property_name="tier"\nvalues_editable_by="org_and_repo_actors"'))[0] is True
    assert m.authority('tier', docs('property_name="tier"\nvalues_editable_by="org_actors"'))[0] is False
    assert m.authority('tier', docs('"property_name": "tier", "values_editable_by": "org_actors"'))[0] is False
    assert m.authority('tier', docs('tier exists'))[0] is None


def test_schema_cli_and_helper_authority():
    cli = "gh api -X PUT /orgs/acme/properties/schema/tier -f value_type=string -f values_editable_by=org_and_repo_actors"
    assert m.authority('tier', docs(cli, 'setup.md'))[0] is True
    helper = 'create_property "$GHAS_STATUS_UPDATED" "last update" "string" "false" "" "" "org_and_repo_actors"'
    assert m.authority('GHAS_Status_Updated', docs(helper, 'setup.sh'))[0] is True


def test_conditional_prose_is_not_authority_proof():
    prose = "Repo admins can set Application_Business_Criticality if the property is values_editable_by: org_and_repo_actors."
    assert m.authority('Application_Business_Criticality', docs(prose, 'README.md'))[0] is None


def test_reduction_and_guard():
    red, guard, _ = m.semantics('policy', docs('policy=bypass causes skipping required scan'))
    assert red is True and guard is False
    red, guard, _ = m.semantics('automerge-humans', docs('automerge-humans=true; all required checks are green AND an approving review exists', 'README.md'))
    assert guard is True


def test_cross_file_callable_link():
    linked = [
        ('a.py', 'if should_scan_repository(props, GHAS_STATUS_UPDATED, 7):\n    run_scan()'),
        ('b.py', 'def should_scan_repository(props, key, days):\n    if recent(props.get(key)):\n        print("Skipping required scan")\n        return False\n    return True\n\ndef other():\n    pass\n'),
    ]
    red, guard, _ = m.semantics('GHAS_Status_Updated', linked)
    assert red is True and guard is False


def test_tight_markdown_window_does_not_borrow_unrelated_reduction():
    text = 'settings_version records rollout state.\n' + ('ordinary documentation ' * 80) + '\nA different feature can skip required scan.'
    red, _, _ = m.semantics('settings_version', docs(text, 'README.md'))
    assert red is None


def test_iac_no_edge():
    text = '''resource "github_organization_ruleset" "r" { conditions { repository_name { include=["x"] } } }
resource "github_organization_custom_properties" "p" { property_name="docs" values_editable_by="org_and_repo_actors" }'''
    assert m.explicit_no_edge('docs', docs(text, 'main.tf'))[0] is True


def test_conservative_unknown():
    assert m.classify(True, 'policy_edge', None, None, False)[0] == 'unknown'
    assert m.classify(None, 'policy_edge', True, False, False)[0] == 'unknown'


def test_no_case_specific_branches():
    source = p.read_text().lower()
    for forbidden in ('c01', 'c02', 'spicelabshq', 'mcp-research', 'dryvist', 'goharbor', 'callmegreg'):
        assert forbidden not in source
