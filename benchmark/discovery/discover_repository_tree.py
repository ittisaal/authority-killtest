#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

CORE_PATH = Path(__file__).with_name("discover_repository.py")
spec = importlib.util.spec_from_file_location("discover_repository_core", CORE_PATH)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

MAX_FILES = 500
FETCH_WORKERS = 16
GENERIC_ALIAS_KEYS = {"prop", "propname", "property", "propertyname"}


def request(url: str):
    headers = {"User-Agent": core.UA, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def api_json(url: str):
    with urllib.request.urlopen(request(url), timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_raw(repository: str, commit: str, path: str):
    safe_path = quote(path, safe="/")
    url = f"https://raw.githubusercontent.com/{repository}/{commit}/{safe_path}"
    req = urllib.request.Request(url, headers={"User-Agent": core.UA})
    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read(core.MAX_FILE_BYTES + 1)
    if len(raw) > core.MAX_FILE_BYTES or b"\x00" in raw[:8192]:
        return None
    return f"https://github.com/{repository}/blob/{commit}/{path}", raw.decode("utf-8", errors="replace")


def repository_documents(repository: str, commit: str):
    commit_api = api_json(f"https://api.github.com/repos/{repository}/git/commits/{commit}")
    tree_sha = commit_api["tree"]["sha"]
    tree = api_json(f"https://api.github.com/repos/{repository}/git/trees/{tree_sha}?recursive=1")

    eligible = []
    for entry in tree.get("tree", []):
        if entry.get("type") != "blob":
            continue
        path = entry.get("path", "")
        size = entry.get("size") or 0
        if core.eligible(path, size):
            eligible.append((core.path_priority(path), path))
    eligible.sort(key=lambda row: row[0])
    selected = eligible[:MAX_FILES]

    docs = []
    errors = []
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        futures = {pool.submit(fetch_raw, repository, commit, path): path for _, path in selected}
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
        "file_cap_reached": len(eligible) > MAX_FILES,
        "fetch_errors": len(errors),
        "fetch_error_examples": errors[:10],
    }


def typed_constants(docs):
    """Resolve simple uppercase string constants, including Python type annotations."""
    constants = {}
    pattern = re.compile(
        r"(?m)^\s*(?:export\s+)?([A-Z][A-Z0-9_]{2,})"
        r"(?:\s*:\s*[^=\n]+)?\s*=\s*['\"]([^'\"\n]{1,120})['\"]"
    )
    for _, text in docs:
        for match in pattern.finditer(text):
            value = match.group(2).strip()
            if core.acceptable_name(value):
                constants[match.group(1)] = value
    return constants


def augment_candidates(docs, candidates):
    """Resolve aliases and add fixed property aliases tied to concrete property reads."""
    constants = typed_constants(docs)
    merged = {}

    def merge_candidate(name, signals, files):
        if not name or not core.acceptable_name(name):
            return
        key = core.canonical(name)
        if key in GENERIC_ALIAS_KEYS:
            return
        row = merged.setdefault(key, {
            "canonical": key,
            "property": name,
            "signals": set(),
            "discovery_files": set(),
        })
        if row["property"].isupper() and not name.isupper():
            row["property"] = name
        row["signals"].update(signals)
        row["discovery_files"].update(files)

    for candidate in candidates:
        name = constants.get(candidate["property"], candidate["property"])
        merge_candidate(name, candidate["signals"], candidate["discovery_files"])

    # A common reusable-workflow shape stores the fixed custom-property name in an
    # environment alias and then compares API readback `.property_name` against it.
    alias_pattern = re.compile(
        r"(?m)^\s*(PROP|PROP_NAME|PROPERTY|PROPERTY_NAME)\s*:\s*"
        r"['\"]?([A-Za-z][A-Za-z0-9_.-]+)['\"]?\s*(?:#.*)?$"
    )
    for url, text in docs:
        low = text.lower()
        concrete_read = "/properties/values" in low and (
            "property_name" in low or "custom properties" in low or "custom_properties" in low
        )
        if not concrete_read:
            continue
        for match in alias_pattern.finditer(text):
            merge_candidate(match.group(2), {"fixed-property-alias"}, {url})

    rows = []
    for row in merged.values():
        rows.append({
            "canonical": row["canonical"],
            "property": row["property"],
            "signals": sorted(row["signals"]),
            "discovery_files": sorted(row["discovery_files"]),
        })
    rows.sort(key=lambda r: (-len(r["signals"]), r["property"].lower()))
    return rows


def classify_candidate(prop: str, docs):
    row = core.classify_property(prop, docs)
    # Integrity/rollout state alone is not a concrete policy edge. Preserve an S
    # result established by an independent guard; only demote a would-be U result.
    if row["label"] == "U" and row["extracted"]["consumer_relation"] == "integrity_marker":
        row["label"] = "N"
        row["reason"] = "integrity/rollout evidence alone does not establish a concrete policy edge"
    return row


def discover(repository: str, commit: str):
    docs, scan = repository_documents(repository, commit)
    candidates = augment_candidates(docs, core.discover_candidates(docs))
    classified = []
    for candidate in candidates:
        row = classify_candidate(candidate["property"], docs)
        row.update({
            "canonical": candidate["canonical"],
            "discovery_signals": candidate["signals"],
            "discovery_files": candidate["discovery_files"],
        })
        classified.append(row)
    return {
        "repository": repository,
        "commit": commit,
        "scan": scan,
        "candidate_count": len(classified),
        "candidates": classified,
        "claim_boundary": (
            "Target-blind discovery over a bounded set of text files selected only from repository paths at the exact commit. "
            "No target property name or hand-selected evidence file is supplied to discovery. Private organization state and "
            "external policy systems absent from the snapshot remain outside this pass."
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
