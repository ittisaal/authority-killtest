#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

V1_PATH = Path(__file__).with_name("discover_repository_tree.py")
V2_PATH = Path(__file__).with_name("discover_repository_v2.py")

spec1 = importlib.util.spec_from_file_location("discover_repository_tree_v1_for_v3", V1_PATH)
v1 = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(v1)

spec2 = importlib.util.spec_from_file_location("discover_repository_v2_for_v3", V2_PATH)
v2 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(v2)

core = v1.core

BASE_FILE_CAP = 500
EXTRA_HINT_CAP = 300
PATH_HINTS = (
    "custom", "propert", "oidc", "ruleset", "workflow", "security",
    "policy", "trust", "github", "auth", "permission", "protect",
)
GENERIC_NAMES = {
    "custom", "properties", "property", "value", "values", "name", "schema",
    "repository", "repo", "custom_properties", "key", "field", "example",
}


def repository_documents(repository: str, commit: str):
    """V1 path-ranked scan plus a bounded hint-path supplement for large repositories."""
    commit_api = v1.api_json(f"https://api.github.com/repos/{repository}/git/commits/{commit}")
    tree_sha = commit_api["tree"]["sha"]
    tree = v1.api_json(f"https://api.github.com/repos/{repository}/git/trees/{tree_sha}?recursive=1")

    eligible = []
    for entry in tree.get("tree", []):
        if entry.get("type") != "blob":
            continue
        path = entry.get("path", "")
        size = entry.get("size") or 0
        if core.eligible(path, size):
            eligible.append((core.path_priority(path), path))
    eligible.sort(key=lambda row: row[0])

    base = eligible[:BASE_FILE_CAP]
    selected_paths = {path for _, path in base}
    hinted = []
    if len(eligible) > BASE_FILE_CAP:
        for priority, path in eligible[BASE_FILE_CAP:]:
            low = path.lower()
            if any(h in low for h in PATH_HINTS):
                hinted.append((priority, path))
        hinted.sort(key=lambda row: row[0])
        for row in hinted[:EXTRA_HINT_CAP]:
            selected_paths.add(row[1])

    selected = sorted(
        ((core.path_priority(path), path) for path in selected_paths),
        key=lambda row: row[0],
    )

    docs = []
    errors = []
    with ThreadPoolExecutor(max_workers=v1.FETCH_WORKERS) as pool:
        futures = {pool.submit(v1.fetch_raw, repository, commit, path): path for _, path in selected}
        for future in as_completed(futures):
            path = futures[future]
            try:
                result = future.result()
                if result is not None:
                    docs.append(result)
            except Exception as exc:
                errors.append({"path": path, "error": f"{type(exc).__name__}: {exc}"})

    docs.sort(key=lambda row: row[0])
    return docs, {
        "tree_sha": tree_sha,
        "tree_truncated": bool(tree.get("truncated")),
        "eligible_text_files": len(eligible),
        "selected_text_files": len(selected),
        "scanned_text_files": len(docs),
        "base_file_cap": BASE_FILE_CAP,
        "hint_file_cap": EXTRA_HINT_CAP,
        "hint_supplement_files": max(0, len(selected) - min(len(eligible), BASE_FILE_CAP)),
        "file_cap_reached": len(eligible) > len(selected),
        "fetch_errors": len(errors),
        "fetch_error_examples": errors[:10],
    }


def _add(rows, name: str, signal: str, url: str):
    name = (name or "").strip()
    if not name or name.lower() in GENERIC_NAMES or not core.acceptable_name(name):
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


def fallback_candidates(docs):
    """Generic literal patterns added after blind-v2; no test-v3 target names are encoded."""
    rows = {}
    patterns = [
        (
            re.compile(r"(?:github\.event\.repository|repository)\.custom_properties\.([A-Za-z_][A-Za-z0-9_.-]{2,99})"),
            "direct-custom-property-dot",
        ),
        (
            re.compile(r"(?:github\.event\.repository|repository)\.custom_properties\s*\[\s*['\"]([^'\"\]]{2,100})['\"]\s*\]"),
            "direct-custom-property-bracket",
        ),
        (
            re.compile(r"\brepo_property_([A-Za-z][A-Za-z0-9_.-]{2,99})\b"),
            "oidc-repo-property-claim",
        ),
        (
            re.compile(r"get_property_value\s*\(\s*['\"]([^'\"\n]{2,100})['\"]\s*\)"),
            "property-value-getter",
        ),
        (
            re.compile(r"(?m)^\s*-?\s*property_name\s*:\s*['\"]?([A-Za-z0-9_.-]{2,100})['\"]?"),
            "yaml-property-definition",
        ),
        (
            re.compile(r"['\"]property_name['\"]\s*:\s*['\"]([A-Za-z0-9_.-]{2,100})['\"]"),
            "json-property-definition",
        ),
        (
            re.compile(r"\bCUSTOM_PROP_([A-Z][A-Z0-9_]{2,99})\b"),
            "custom-property-env",
        ),
        (
            re.compile(r"(?i)\bcustom propert(?:y|ies)\s+(?:named\s+)?[`'\"]([A-Za-z][A-Za-z0-9_.-]{2,99})[`'\"]"),
            "explicit-property-prose",
        ),
    ]

    for url, text in docs:
        for pattern, signal in patterns:
            for match in pattern.finditer(text):
                name = match.group(1)
                if signal == "custom-property-env":
                    name = name.lower()
                _add(rows, name, signal, url)

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
    """Union V1 discovery, V2 extensions, and generic post-v2 literal fallbacks."""
    v1_rows = v1.augment_candidates(docs, core.discover_candidates(docs))
    v2_rows = v2.extra_candidates(docs)
    fallback_rows = fallback_candidates(docs)
    merged = {}

    for source, rows in (("v1", v1_rows), ("v2", v2_rows), ("fallback", fallback_rows)):
        for candidate in rows:
            name = candidate["property"]
            if not name or not core.acceptable_name(name):
                continue
            key = core.canonical(name)
            row = merged.setdefault(
                key,
                {
                    "canonical": key,
                    "property": name,
                    "signals": set(),
                    "discovery_files": set(),
                    "discovery_sources": set(),
                },
            )
            if row["property"].isupper() and not name.isupper():
                row["property"] = name
            row["signals"].update(candidate.get("signals", candidate.get("discovery_signals", [])))
            row["discovery_files"].update(candidate.get("discovery_files", []))
            row["discovery_sources"].add(source)

    out = []
    for row in merged.values():
        out.append(
            {
                "canonical": row["canonical"],
                "property": row["property"],
                "signals": sorted(row["signals"]),
                "discovery_files": sorted(row["discovery_files"]),
                "discovery_sources": sorted(row["discovery_sources"]),
            }
        )
    out.sort(
        key=lambda r: (
            -len(r["discovery_sources"]),
            -len(r["signals"]),
            r["property"].lower(),
        )
    )
    return out


def classify_candidate(prop: str, docs):
    # Keep Blind-v2's improved conservative U/S/N semantics unchanged.
    return v2.classify_candidate(prop, docs)


def discover(repository: str, commit: str):
    docs, scan = repository_documents(repository, commit)
    candidates = combine_candidates(docs)
    classified = []
    for candidate in candidates:
        row = classify_candidate(candidate["property"], docs)
        row.update(
            {
                "canonical": candidate["canonical"],
                "discovery_signals": candidate["signals"],
                "discovery_files": candidate["discovery_files"],
                "discovery_sources": candidate["discovery_sources"],
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
            "Blind-v3 combines V1 target discovery with V2 semantic classification, adds only "
            "generic literal discovery patterns derived from prior failure classes, and uses a bounded "
            "hint-path supplement for large repositories. It still does not infer private organization "
            "settings or external policy absent from the public snapshot."
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
