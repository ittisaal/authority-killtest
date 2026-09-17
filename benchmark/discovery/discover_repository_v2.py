#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

V1_PATH = Path(__file__).with_name("discover_repository_tree.py")
spec = importlib.util.spec_from_file_location("discover_repository_tree_v1", V1_PATH)
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)

core = v1.core

GENERIC_NAMES = {
    "custom", "properties", "property", "value", "values", "name", "schema",
    "repository", "repo", "custom_properties",
}

BENIGN_TERMS = (
    "slack", "discord", "notification", "notify", "pretty name", "display name",
    "resource attribute", "telemetry", "metric", "observability", "logging",
    "log event", "metadata", "channel", "modrinth", "portfolio", "service line",
    "splunk", "hec event", "validation", "reporting", "report",
)

SECURITY_TERMS = (
    "skip", "bypass", "disable", "exclude", "scan", "security", "signature",
    "provenance", "review", "ruleset", "protection", "required check", "gate",
    "oidc", "repo_property_", "iam", "authorization", "permission", "credential",
    "trust policy", "federated", "federation", "deployment", "production",
)


def _merge(rows, name, signal, url):
    if not name or not core.acceptable_name(name):
        return
    if name.lower() in GENERIC_NAMES:
        return
    key = core.canonical(name)
    row = rows.setdefault(
        key,
        {"canonical": key, "property": name, "signals": set(), "discovery_files": set()},
    )
    if row["property"].isupper() and not name.isupper():
        row["property"] = name
    row["signals"].add(signal)
    row["discovery_files"].add(url)


def extra_candidates(docs):
    """Blind-v2 candidate patterns derived only from blind-v1 failure classes."""
    rows = {}

    quoted_property_name = re.compile(
        r'["\']property_name["\']\s*:\s*["\']([A-Za-z0-9_.-]{3,100})["\']'
    )
    yaml_property_name = re.compile(
        r'(?m)^\s*property_name\s*:\s*["\']?([A-Za-z0-9_.-]{3,100})["\']?\s*$'
    )
    rust_constructor = re.compile(
        r'CustomPropertySetter::new(?:_single_select)?\s*\(\s*["\']([A-Za-z0-9_.-]{3,100})["\']'
    )
    prose_property = re.compile(
        r'(?i)\bcustom propert(?:y|ies)\s+(?:named\s+|`|["\'])?([A-Za-z][A-Za-z0-9_.-]{2,99})(?:`|["\'])?(?=[\s=,:])'
    )
    custom_prop_env = re.compile(r'\bCUSTOM_PROP_([A-Z][A-Z0-9_]{2,99})\b')
    jq_key = re.compile(
        r'(?:jq\b[^\n]{0,180}|fromJSON\([^\n]{0,180})[.\[\]"\']*([A-Za-z][A-Za-z0-9_.-]{2,99})'
    )

    for url, text in docs:
        low = text.lower()

        for pattern, signal in (
            (quoted_property_name, "quoted-property-name"),
            (yaml_property_name, "yaml-property-name"),
            (rust_constructor, "custom-property-constructor"),
        ):
            for m in pattern.finditer(text):
                _merge(rows, m.group(1), signal, url)

        if "custom propert" in low:
            for m in prose_property.finditer(text):
                name = m.group(1)
                if name.lower() not in {"is", "are", "can", "the", "this", "with", "as"}:
                    _merge(rows, name, "prose-property-example", url)

        for m in custom_prop_env.finditer(text):
            _merge(rows, m.group(1).lower(), "custom-prop-env", url)

        if "github.event.repository.custom_properties" in low or "/properties/values" in low:
            for m in jq_key.finditer(text):
                _merge(rows, m.group(1), "aggregate-property-key", url)

    out = []
    for row in rows.values():
        out.append(
            {
                "canonical": row["canonical"],
                "property": row["property"],
                "signals": sorted(row["signals"]),
                "discovery_files": sorted(row["discovery_files"]),
            }
        )
    return out


def combine_candidates(docs):
    base = v1.augment_candidates(docs, core.discover_candidates(docs))
    extra = extra_candidates(docs)
    merged = {}

    for candidate in base + extra:
        key = core.canonical(candidate["property"])
        row = merged.setdefault(
            key,
            {
                "canonical": key,
                "property": candidate["property"],
                "signals": set(),
                "discovery_files": set(),
            },
        )
        if row["property"].isupper() and not candidate["property"].isupper():
            row["property"] = candidate["property"]
        row["signals"].update(candidate.get("signals", candidate.get("discovery_signals", [])))
        row["discovery_files"].update(candidate.get("discovery_files", []))

    out = []
    for row in merged.values():
        out.append(
            {
                "canonical": row["canonical"],
                "property": row["property"],
                "signals": sorted(row["signals"]),
                "discovery_files": sorted(row["discovery_files"]),
            }
        )
    out.sort(key=lambda r: (-len(r["signals"]), r["property"].lower()))
    return out


def benign_snapshot_use(prop: str, docs):
    """Narrow bounded-snapshot S rule for obviously non-security consumers."""
    ws = []
    names = core.extract.variants(prop)
    for _, text in docs:
        ws.extend(core.extract.windows(text, names, 650))

    if not ws:
        return False

    joined = "\n".join(ws).lower()
    if any(term in joined for term in SECURITY_TERMS):
        return False
    return any(term in joined for term in BENIGN_TERMS)


def classify_candidate(prop: str, docs):
    row = v1.classify_candidate(prop, docs)
    if row["label"] == "N" and benign_snapshot_use(prop, docs):
        row["label"] = "S"
        row["reason"] = (
            "all concrete repository-visible uses found for this property are benign "
            "notification/telemetry/reporting metadata, with no protection or authorization edge observed"
        )
        row["bounded_snapshot_safe"] = True
    else:
        row["bounded_snapshot_safe"] = False
    return row


def discover(repository: str, commit: str):
    docs, scan = v1.repository_documents(repository, commit)
    candidates = combine_candidates(docs)
    classified = []
    for candidate in candidates:
        row = classify_candidate(candidate["property"], docs)
        row.update(
            {
                "canonical": candidate["canonical"],
                "discovery_signals": candidate["signals"],
                "discovery_files": candidate["discovery_files"],
            }
        )
        classified.append(row)

    return {
        "repository": repository,
        "commit": commit,
        "scan": scan,
        "candidate_count": len(classified),
        "candidates": classified,
        "claim_boundary": (
            "Blind-v2 target-blind discovery over repository-visible files at an exact commit. "
            "It adds generic patterns for aggregate property-map reads, producer-side property "
            "definitions, and narrow benign-consumer recognition learned from blind-v1 failure "
            "classes. It still does not infer private organization settings or external policy."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repository")
    ap.add_argument("commit")
    ap.add_argument("--output", default="-")
    args = ap.parse_args()
    result = discover(args.repository, args.commit)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output == "-":
        print(text)
    else:
        Path(args.output).write_text(text + "\n")


if __name__ == "__main__":
    main()
