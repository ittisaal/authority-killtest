#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).with_name("discover_repository_v5.py")
spec = importlib.util.spec_from_file_location("discover_repository_v5", HERE)
v5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v5)


def test_test_fixture_u_is_suppressed():
    docs = [
        ("https://github.com/x/y/blob/abc/tests/test_custom_property.py", "property_name='language'\nvalues_editable_by='org_and_repo_actors'"),
        ("https://github.com/x/y/blob/abc/src/repository.py", "language required checks skip scan"),
    ]
    row = v5.classify_candidate("language", docs)
    assert row["label"] == "N"


def test_generated_sdk_authority_is_suppressed():
    docs = [
        ("https://github.com/x/y/blob/abc/sdk/python/organization_custom_properties.py", "property_name='staging'\nvalues_editable_by='org_and_repo_actors'"),
        ("https://github.com/x/y/blob/abc/.github/workflows/release.yml", "if: staging\nrun: skip release verification scan"),
    ]
    row = v5.classify_candidate("staging", docs)
    assert row["label"] == "N"


def test_unrelated_domain_custom_property_is_n():
    docs = [("https://github.com/x/y/blob/abc/src/actor.py", "actor.custom_properties['language'] = 'Python'")]
    row = v5.classify_candidate("language", docs)
    assert row["label"] == "N"


def test_direct_benign_workflow_consumer_is_s():
    docs = [("https://github.com/x/y/blob/abc/.github/workflows/push.yml", "REPO_NAME: ${{ github.event.repository.custom_properties.project_pretty_name }}\nrun: echo $REPO_NAME")]
    row = v5.classify_candidate("project_pretty_name", docs)
    assert row["label"] == "S"


def test_deployed_org_only_ruleset_selector_is_s():
    docs = [
        ("https://github.com/x/y/blob/abc/infra/custom_properties.py", "github.OrganizationCustomProperties('tier', property_name='tier', values_editable_by='org_actors')"),
        ("https://github.com/x/y/blob/abc/infra/rulesets.py", "repository_property name='tier' property_values=['protected'] ruleset required status check"),
    ]
    row = v5.classify_candidate("tier", docs)
    assert row["label"] == "S"


def test_deployed_repo_editable_scan_bypass_is_u():
    docs = [
        ("https://github.com/x/y/blob/abc/infra/custom_properties.py", "github.OrganizationCustomProperties('scan_policy', property_name='scan_policy', values_editable_by='org_and_repo_actors')"),
        ("https://github.com/x/y/blob/abc/.github/workflows/security.yml", "if: ${{ github.event.repository.custom_properties.scan_policy != 'bypass' }}\nrun: security scan\n# bypass skips scan check"),
    ]
    row = v5.classify_candidate("scan_policy", docs)
    assert row["label"] == "U"


def test_generic_token_without_direct_consumer_is_n():
    docs = [
        ("https://github.com/x/y/blob/abc/src/provider.py", "property_name='archived' values_editable_by='org_and_repo_actors'"),
        ("https://github.com/x/y/blob/abc/.github/workflows/release.yml", "archived release skip verification scan"),
    ]
    row = v5.classify_candidate("archived", docs)
    assert row["label"] == "N"


if __name__ == "__main__":
    test_test_fixture_u_is_suppressed()
    test_generated_sdk_authority_is_suppressed()
    test_unrelated_domain_custom_property_is_n()
    test_direct_benign_workflow_consumer_is_s()
    test_deployed_org_only_ruleset_selector_is_s()
    test_deployed_repo_editable_scan_bypass_is_u()
    test_generic_token_without_direct_consumer_is_n()
    print("7 blind-v5 deployment-provenance tests passed")
