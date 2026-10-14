#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

V3_PATH = Path(__file__).with_name("discover_repository_v3.py")
spec = importlib.util.spec_from_file_location("discover_repository_v3_for_v4", V3_PATH)
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)

v2 = v3.v2
v1 = v3.v1
core = v3.core

BASE_FILE_CAP = 700
HINT_FILE_CAP = 700
EXTRA_TEXT_EXTENSIONS = {
    ".mjs", ".cjs", ".mts", ".cts", ".properties", ".tmpl", ".template",
    ".adoc", ".graphql", ".gql", ".gradle", ".groovy",
}
PATH_HINTS = (
    "custom", "propert", "oidc", "openid", "ruleset", "workflow", "security",
    "policy", "trust", "github", "auth", "permission", "protect", "action",
    "claim", "federat", "identity", "readme", "docs", "reference", "config",
)
GENERIC_NAMES = v3.GENERIC_NAMES | {
    "example", "examples", "custom_property_name", "custompropertyname", "repository_name",
}


def eligible_v4(path: str, size: int) -> bool:
    if core.eligible(path, size):
        return True
    if size > core.MAX_FILE_BYTES:
        return False
    parts = set(Path(path).parts)
    if parts & core.SKIP_PARTS:
        return False
    return Path(path).suffix.lower() in EXTRA_TEXT_EXTENSIONS


def repository_documents(repository: str, commit: str):
    """Wider but bounded snapshot scan derived from blind-v3 misses."""
    commit_api = v1.api_json(f"https://api.github.com/repos/{repository}/git/commits/{commit}")
    tree_sha = commit_api["tree"]["sha"]
    tree = v1.api_json(f"https://api.github.com/repos/{repository}/git/trees/{tree_sha}?recursive=1")

    eligible = []
    for entry in tree.get("tree", []):
        if entry.get("type") != "blob":
            continue
        path = entry.get("path", "")
        size = entry.get("size") or 0
        if eligible_v4(path, size):
            eligible.append((core.path_priority(path), path))
    eligible.sort(key=lambda row: row[0])

    selected_paths = {path for _, path in eligible[:BASE_FILE_CAP]}
    hinted = []
    for priority, path in eligible[BASE_FILE_CAP:]:
        low = path.lower()
        if any(h in low for h in PATH_HINTS):
            hinted.append((priority, path))
    hinted.sort(key=lambda row: row[0])
    for _, path in hinted[:HINT_FILE_CAP]:
        selected_paths.add(path)

    selected = sorted(((core.path_priority(path), path) for path in selected_paths), key=lambda r: r[0])
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
        "hint_file_cap": HINT_FILE_CAP,
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


def documentation_example_candidates(docs):
    """Recover named custom-property examples embedded in prose/reference docs."""
    rows = {}
    fenced_name = re.compile(r"[`'\"]([A-Za-z][A-Za-z0-9_.-]{2,99})[`'\"]")
    for url, text in docs:
        low = text.lower()
        starts = [m.start() for m in re.finditer(r"custom propert(?:y|ies)", low)]
        for start in starts:
            window = text[max(0, start - 120): min(len(text), start + 700)]
            wlow = window.lower()
            if not any(k in wlow for k in ("for example", "e.g.", "property_name", "repo_property_", "claims")):
                continue
            for match in fenced_name.finditer(window):
                name = match.group(1)
                if name.lower() in {
                    "string", "true", "false", "single_select", "multi_select",
                    "org_actors", "org_and_repo_actors", "repository", "organization",
                }:
                    continue
                _add(rows, name, "documented-property-example", url)
    return [
        {
            "canonical": row["canonical"],
            "property": row["property"],
            "signals": sorted(row["signals"]),
            "discovery_files": sorted(row["discovery_files"]),
        }
        for row in rows.values()
    ]


def combine_candidates(docs):
    base = v3.combine_candidates(docs)
    doc_examples = documentation_example_candidates(docs)
    merged = {}
    for source, rows in (("v3", base), ("doc-example", doc_examples)):
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
            row["discovery_sources"].update(candidate.get("discovery_sources", []))
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
    out.sort(key=lambda r: (-len(r["discovery_sources"]), -len(r["signals"]), r["property"].lower()))
    return out


def occurrence_windows(prop: str, docs, radius: int = 420):
    names = core.extract.variants(prop)
    windows = []
    for url, text in docs:
        for w in core.extract.windows(text, names, radius):
            windows.append((url, w))
    return windows


def external_effect_sink(prop: str, docs) -> bool:
    """Do not call a token-backed external destination selector benign."""
    pname = prop.lower()
    role_hint = any(t in pname for t in ("project", "destination", "target", "registry", "package", "repo", "environment", "modrinth"))
    for _, window in occurrence_windows(prop, docs, 500):
        low = window.lower()
        credential = any(t in low for t in ("secrets.", "token:", "credential", "api_key", "apikey"))
        effect = any(t in low for t in ("publish", "release", "deploy", "upload", "registry", "package", "project:"))
        selector = role_hint or any(t in low for t in ("project:", "destination:", "target:", "registry:", "repository:"))
        if credential and effect and selector:
            return True
    return False


def clearly_benign_sink(prop: str, docs) -> bool:
    if external_effect_sink(prop, docs):
        return False
    pname = prop.lower()
    windows = [w.lower() for _, w in occurrence_windows(prop, docs, 320)]
    if not windows:
        return False

    # Presentation and notification-routing metadata.
    if any(t in pname for t in ("slack", "channel", "pretty", "human-title", "human_title", "display", "notification", "notify")):
        if any(any(t in w for t in ("slack", "discord", "notification", "webhook", "display", "template", "readme", "replacements")) for w in windows):
            return True

    # Tiny starter/demo branches that only print text and do not select an external action.
    demo = all(any(t in w for t in ("run: echo", "echo hello", "print(", "console.log")) for w in windows)
    dangerous = any(any(t in w for t in ("secrets.", "token:", "publish", "deploy", "upload", "permissions:", "id-token:")) for w in windows)
    if demo and not dangerous:
        return True

    return False


def classify_candidate(prop: str, docs):
    # Start from the pre-benign-promotion V1 semantic layer. This keeps U logic and
    # independent-guard S logic while avoiding blind-v3's over-broad S promotion.
    row = v1.classify_candidate(prop, docs)
    if row["label"] == "N" and clearly_benign_sink(prop, docs):
        row["label"] = "S"
        row["reason"] = (
            "all concrete repository-visible uses found for this property are bounded "
            "presentation/notification/demo behavior with no privilege or protection edge observed"
        )
        row["bounded_snapshot_safe"] = True
    else:
        row["bounded_snapshot_safe"] = False
    if row["label"] == "S" and external_effect_sink(prop, docs) and not row["extracted"].get("independent_guard_observed"):
        row["label"] = "N"
        row["reason"] = (
            "property selects a credential-backed external publish/deploy destination; public evidence is insufficient "
            "to establish the reachable authority delta"
        )
        row["bounded_snapshot_safe"] = False
    return row


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
            "Blind-v4 changes only failure classes exposed by blind-v3: wider bounded file coverage, "
            "named-property extraction from custom-property documentation examples, narrower benign-sink "
            "recognition, and an explicit guard against calling credential-backed external destination selectors S. "
            "Private organization state and external policy absent from the public snapshot are still not inferred."
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
