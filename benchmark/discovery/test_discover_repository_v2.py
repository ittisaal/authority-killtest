#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).with_name("discover_repository_v2.py")
spec = importlib.util.spec_from_file_location("discover_repository_v2", HERE)
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)


def names(rows):
    return {row["property"] for row in rows}


def test_quoted_property_name():
    docs = [("https://example/x.js", 'const x = [{"property_name": "Technology-Pillar", "value": "AI"}];')]
    assert "Technology-Pillar" in names(v2.extra_candidates(docs))


def test_rust_constructor():
    docs = [("https://example/x.rs", 'CustomPropertySetter::new_single_select("portfolio", None, false, values)')]
    assert "portfolio" in names(v2.extra_candidates(docs))


def test_custom_prop_env():
    docs = [("https://example/x.md", 'custom property team=t-platform becomes CUSTOM_PROP_TEAM=t-platform')]
    assert "team" in names(v2.extra_candidates(docs))


def test_benign_consumer():
    docs = [("https://example/x.yml", 'slack-channel: ${{ github.event.repository.custom_properties.ci_slack_channel }}')]
    assert v2.benign_snapshot_use("ci_slack_channel", docs) is True


def test_security_consumer_not_benign():
    docs = [("https://example/x.yml", "if: ${{ github.event.repository.custom_properties.skip_scan != 'true' }} # security scan")]
    assert v2.benign_snapshot_use("skip_scan", docs) is False


if __name__ == "__main__":
    test_quoted_property_name()
    test_rust_constructor()
    test_custom_prop_env()
    test_benign_consumer()
    test_security_consumer_not_benign()
    print("5 blind-v2 unit tests passed")
