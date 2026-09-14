#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).with_name("discover_repository_v4.py")
spec = importlib.util.spec_from_file_location("discover_repository_v4", HERE)
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)


def names(rows):
    return {row["property"] for row in rows}


def test_mjs_is_scanned():
    assert v4.eligible_v4(".github/workflows/fill-in-scaffold.mjs", 1000)


def test_documented_examples_are_discovered():
    docs = [("https://example/openid-connect.md", "An admin creates custom properties (for example, `business_unit`, `data_classification`, or `environment_tier`) and adds repo_property_* claims.")]
    found = names(v4.documentation_example_candidates(docs))
    assert {"business_unit", "data_classification", "environment_tier"} <= found


def test_human_title_is_benign():
    docs = [("https://example/fill.mjs", "const title = repository.custom_properties['human-title'] ?? repository.name; replacements = {'EXAMPLE_REPO_NAME': title};")]
    row = v4.classify_candidate("human-title", docs)
    assert row["label"] == "S"


def test_slack_channel_is_benign():
    docs = [("https://example/workflow.yml", "slack-bot-token: ${{ secrets.SLACK_BOT_TOKEN }}\nslack-channel: ${{ github.event.repository.custom_properties.ci_slack_channel }}")]
    row = v4.classify_candidate("ci_slack_channel", docs)
    assert row["label"] == "S"


def test_token_backed_publish_destination_is_not_s():
    docs = [("https://example/release.yml", "uses: vendor/publish@v2\nwith:\n  token: ${{ secrets.PUBLISH_TOKEN }}\n  project: ${{ github.event.repository.custom_properties.modrinth_id }}\n  release: ${{ github.ref_name }}")]
    row = v4.classify_candidate("modrinth_id", docs)
    assert row["label"] == "N"


def test_print_only_demo_is_s():
    docs = [("https://example/fruit.yml", "if: ${{ github.event.repository.custom_properties.fruit == 'Apple' }}\nrun: echo Hello, world!\nif: ${{ github.event.repository.custom_properties.fruit == 'Banana' }}\nrun: echo Add other actions later")]
    row = v4.classify_candidate("fruit", docs)
    assert row["label"] == "S"


def test_security_selector_stays_n_without_authority():
    docs = [("https://example/ci.yml", "if: ${{ github.event.repository.custom_properties.skip_scan != 'true' }}\nrun: security-scan")]
    row = v4.classify_candidate("skip_scan", docs)
    assert row["label"] == "N"


if __name__ == "__main__":
    test_mjs_is_scanned()
    test_documented_examples_are_discovered()
    test_human_title_is_benign()
    test_slack_channel_is_benign()
    test_token_backed_publish_destination_is_not_s()
    test_print_only_demo_is_s()
    test_security_selector_stays_n_without_authority()
    print("7 blind-v4 unit tests passed")
