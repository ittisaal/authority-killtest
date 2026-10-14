#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).with_name("discover_repository_v3.py")
spec = importlib.util.spec_from_file_location("discover_repository_v3", HERE)
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)


def names(rows):
    return {row["property"] for row in rows}


def test_direct_dot():
    docs = [("https://example/x.yml", "x: ${{ github.event.repository.custom_properties.project_pretty_name }}")]
    assert "project_pretty_name" in names(v3.fallback_candidates(docs))


def test_direct_bracket():
    docs = [("https://example/x.js", "const title = repository.custom_properties['human-title'] ?? repository.name")]
    assert "human-title" in names(v3.fallback_candidates(docs))


def test_property_value_getter():
    docs = [("https://example/x.rs", 'self.get_property_value("portfolio")')]
    assert "portfolio" in names(v3.fallback_candidates(docs))


def test_yaml_property_definition():
    docs = [("https://example/x.yml", "customProperties:\n  - property_name: fleet-managed\n    values_editable_by: org_actors\n")]
    assert "fleet-managed" in names(v3.fallback_candidates(docs))


def test_oidc_claim():
    docs = [("https://example/x.md", "claims['repo_property_team'] == 'platform'")]
    assert "team" in names(v3.fallback_candidates(docs))


def test_custom_prop_env():
    docs = [("https://example/x.md", "CUSTOM_PROP_TEAM=t-platform")]
    assert "team" in names(v3.fallback_candidates(docs))


def test_v2_benign_semantics_kept():
    docs = [("https://example/x.yml", "slack-channel: ${{ github.event.repository.custom_properties.ci_slack_channel }}")]
    row = v3.classify_candidate("ci_slack_channel", docs)
    assert row["label"] == "S"


if __name__ == "__main__":
    test_direct_dot()
    test_direct_bracket()
    test_property_value_getter()
    test_yaml_property_definition()
    test_oidc_claim()
    test_custom_prop_env()
    test_v2_benign_semantics_kept()
    print("7 blind-v3 unit tests passed")
