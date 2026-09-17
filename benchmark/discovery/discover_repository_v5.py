#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urlparse

V4_PATH = Path(__file__).with_name("discover_repository_v4.py")
spec = importlib.util.spec_from_file_location("discover_repository_v4_for_v5", V4_PATH)
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

core = v4.core

REFERENCE_PARTS = {
    "test", "tests", "testing", "testdata", "fixtures", "fixture", "mocks", "mock",
    "examples", "example", "docs", "doc", "documentation", "reference", "references",
    "generated", "gen", ".generated-specs", "specs", "sdk",
}
REFERENCE_NAME_MARKERS = (
    "_test.", ".test.", ".spec.", "generated.", ".generated.", "mock_", "fixture_",
)
GENERIC_CANONICAL = {
    "array", "boolean", "legacy", "untouched", "update", "values", "value", "workflow",
    "archived", "staging", "property", "properties", "customproperties", "repository",
}


def _repo_path(url: str) -> str:
    path = urlparse(url).path
    m = re.search(r"/blob/[^/]+/(.*)$", path)
    if m:
        return m.group(1)
    return path.lstrip("/")


def is_reference_path(url: str) -> bool:
    path = _repo_path(url)
    low = path.lower()
    parts = {p.lower() for p in Path(path).parts}
    if parts & REFERENCE_PARTS:
        return True
    name = Path(path).name.lower()
    return any(marker in name for marker in REFERENCE_NAME_MARKERS)


def deployment_docs(docs):
    return [(url, text) for url, text in docs if not is_reference_path(url)]


def _windows(prop: str, docs, radius: int = 900):
    names = core.extract.variants(prop)
    for url, text in docs:
        for window in core.extract.windows(text, names, radius):
            yield url, window


def deployed_authority(prop: str, docs, mode: str) -> list[str]:
    """Return non-reference files that concretely bind this property to GitHub editability."""
    assert mode in {"repo", "org"}
    wanted = "org_and_repo_actors" if mode == "repo" else "org_actors"
    hits = set()
    for url, window in _windows(prop, deployment_docs(docs), 1000):
        low = window.lower()
        github_context = any(token in low for token in (
            "organizationcustomproperties", "github_organization_custom", "/properties/schema/",
            "repository custom propert", "organization custom propert", "values_editable_by",
        ))
        if not github_context:
            continue
        pat = r"values_editable_by[\"']?\s*[=:]\s*[\"']?" + re.escape(wanted) + r"\b"
        if re.search(pat, low):
            hits.add(url)
    return sorted(hits)


def deployed_consumer(prop: str, docs) -> list[str]:
    """Require a concrete non-reference use of this named repository property/claim."""
    hits = set()
    variants = core.extract.variants(prop)
    canon = core.canonical(prop)
    for url, text in deployment_docs(docs):
        low = text.lower()
        for name in variants:
            n = re.escape(name.lower())
            patterns = (
                rf"github\.event\.repository\.custom_properties\.{n}\b",
                rf"github\.event\.repository\.custom_properties\s*\[\s*['\"]{n}['\"]\s*\]",
                rf"repository\.custom_properties\.{n}\b",
                rf"repository\.custom_properties\s*\[\s*['\"]{n}['\"]\s*\]",
                rf"customproperties\s*\[\s*['\"]{n}['\"]\s*\]",
                rf"custom_properties\s*\[\s*['\"]{n}['\"]\s*\]",
                rf"\brepo_property_{n}\b",
            )
            if any(re.search(p, low, re.I) for p in patterns):
                hits.add(url)
                break
        if url in hits:
            continue
        # Ruleset property conditions often name the property separately from the condition type.
        if any(v.lower() in low for v in variants) and (
            "repository_property" in low or "property_values" in low or "custom_property_condition" in low
        ):
            hits.add(url)
    return sorted(hits)


def _nonreference_evidence(urls: list[str]) -> list[str]:
    return sorted(url for url in urls if not is_reference_path(url))


def classify_candidate(prop: str, docs):
    base = v4.classify_candidate(prop, docs)
    direct_consumer = deployed_consumer(prop, docs)
    repo_authority = deployed_authority(prop, docs, "repo")
    org_authority = deployed_authority(prop, docs, "org")
    semantic_files = _nonreference_evidence(base.get("evidence_files", {}).get("semantics", []))
    guard_files = semantic_files if base.get("extracted", {}).get("independent_guard_observed") else []

    canon = core.canonical(prop)
    weak_generic = canon in GENERIC_CANONICAL and not direct_consumer
    provenance = {
        "direct_deployed_consumer_files": direct_consumer,
        "repo_editable_schema_files": repo_authority,
        "org_only_schema_files": org_authority,
        "nonreference_semantics_files": semantic_files,
        "nonreference_guard_files": guard_files,
        "generic_name_without_direct_consumer": weak_generic,
    }

    original_label = base["label"]
    final = original_label
    reason = base["reason"]

    if weak_generic:
        final = "N"
        reason = "generic property token lacks a direct deployed GitHub custom-property/claim consumer"
    elif original_label == "U":
        if not (repo_authority and direct_consumer and semantic_files):
            final = "N"
            reason = (
                "raw U evidence does not survive deployment-provenance gating: a concrete non-reference "
                "repo-editable schema, named consumer, and protection-reducing effect are all required"
            )
    elif original_label == "S":
        actor = base.get("extracted", {}).get("actor_can_modify")
        bounded = bool(base.get("bounded_snapshot_safe"))
        no_edge = base.get("extracted", {}).get("consumer_relation") == "confirmed_no_policy_edge"
        fixed_guard = bool(base.get("extracted", {}).get("independent_guard_observed"))
        safe_supported = False
        if actor is False and org_authority:
            safe_supported = True
        elif bounded and direct_consumer:
            safe_supported = True
        elif no_edge and direct_consumer:
            safe_supported = True
        elif fixed_guard and direct_consumer and guard_files:
            safe_supported = True
        if not safe_supported:
            final = "N"
            reason = (
                "raw S evidence does not survive deployment-provenance gating: the apparent safe case is "
                "reference/test/generated material or lacks a direct deployed named consumer"
            )

    base["raw_v4_label"] = original_label
    base["label"] = final
    base["reason"] = reason
    base["deployment_provenance"] = provenance
    base["deployment_evidence_complete"] = (
        bool(repo_authority and direct_consumer and semantic_files) if final == "U" else
        bool(final == "S") if final == "S" else False
    )
    return base


def discover(repository: str, commit: str):
    docs, scan = v4.repository_documents(repository, commit)
    candidates = v4.combine_candidates(docs)
    classified = []
    for candidate in candidates:
        row = classify_candidate(candidate["property"], docs)
        row.update({
            "canonical": candidate["canonical"],
            "discovery_signals": candidate["signals"],
            "discovery_files": candidate["discovery_files"],
            "discovery_sources": candidate["discovery_sources"],
        })
        classified.append(row)
    return {
        "repository": repository,
        "commit": commit,
        "scan": scan,
        "candidate_count": len(classified),
        "candidates": classified,
        "claim_boundary": (
            "Blind-v5 is a deployment-provenance hardening of frozen V4 derived only from the predeclared "
            "broad-evaluation failure classes: generated SDK/spec material, tests/fixtures, documentation/examples, "
            "generic same-named fields, and unrelated domain custom_properties. U/S promotion now requires concrete "
            "non-reference GitHub property/claim evidence. Private organization state and absent downstream policy "
            "are still not inferred."
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
