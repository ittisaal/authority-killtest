#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

SOURCEGRAPH_STREAM = "https://sourcegraph.com/.api/search/stream"

DOC_TEST_SEGMENTS = {
    "doc", "docs", "documentation",
    "example", "examples", "sample", "samples",
    "demo", "demos", "tutorial", "tutorials",
    "test", "tests", "__tests__", "testdata",
    "fixture", "fixtures", "mock", "mocks",
}
GENERATED_SEGMENTS = {
    "node_modules", "vendor", "vendors", "dist", "build", "target",
    ".venv", "venv", "site-packages", "third_party", "third-party",
    "generated", "gen",
}
DOC_FILENAMES = {
    "readme", "readme.md", "readme.rst", "readme.txt",
    "changelog", "changelog.md", "contributing", "contributing.md",
}
LOCK_FILENAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "cargo.lock", "go.sum",
}


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path_filter_reason(path: str) -> str | None:
    low = path.lower().strip("/")
    parts = [p for p in low.split("/") if p]
    if not parts:
        return "empty-path"
    if any(p in GENERATED_SEGMENTS for p in parts[:-1]):
        return "generated-or-vendored-path"
    if any(p in DOC_TEST_SEGMENTS for p in parts[:-1]):
        return "docs-test-example-path"
    filename = parts[-1]
    if filename in DOC_FILENAMES or filename in LOCK_FILENAMES:
        return "documentation-or-lockfile"
    if filename.startswith("readme."):
        return "documentation-or-lockfile"
    return None


def _read_sse(url: str, timeout: int = 900):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "text/event-stream",
            "User-Agent": "authority-provenance-candidate-harvest/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        event = None
        data_lines = []
        for raw in resp:
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if not line:
                if event is not None:
                    yield event, "\n".join(data_lines)
                event = None
                data_lines = []
                continue
            if line.startswith("event:"):
                event = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_lines.append(line.split(":", 1)[1].lstrip())
        if event is not None:
            yield event, "\n".join(data_lines)


def run_query(spec: dict, timeout: int = 900) -> dict:
    query = spec["query"].strip()
    count = int(spec.get("count", 10000))
    # Sourcegraph.com excludes forks and archived repositories by default.
    sg_query = f"context:global {query} patternType:literal count:{count}"
    params = urllib.parse.urlencode({"q": sg_query, "v": "V3"})
    url = f"{SOURCEGRAPH_STREAM}?{params}"

    matches = []
    alerts = []
    progress = []
    last_error = None
    for attempt in range(4):
        try:
            for event, data_text in _read_sse(url, timeout=timeout):
                if not data_text:
                    continue
                try:
                    data = json.loads(data_text)
                except json.JSONDecodeError:
                    alerts.append({"event": event, "unparsed": data_text[:1000]})
                    continue
                if event == "matches":
                    for item in data:
                        if item.get("type") != "content":
                            continue
                        repository = item.get("repository", "")
                        if not repository.startswith("github.com/"):
                            continue
                        repo = repository[len("github.com/"):]
                        path = item.get("path") or ""
                        commit = item.get("commit") or ""
                        if not repo or not path or not commit:
                            continue
                        line_matches = item.get("lineMatches") or []
                        snippets = []
                        for lm in line_matches[:4]:
                            text = lm.get("line")
                            if text:
                                snippets.append(text[:500])
                        matches.append(
                            {
                                "signature_id": spec["id"],
                                "signature_query": query,
                                "repository": repo,
                                "path": path,
                                "commit": commit,
                                "language": item.get("language"),
                                "repo_stars": item.get("repoStars"),
                                "repo_last_fetched": item.get("repoLastFetched"),
                                "branches": item.get("branches") or [],
                                "snippets": snippets,
                            }
                        )
                elif event == "progress":
                    progress.append(data)
                elif event == "alert":
                    alerts.append(data)
            return {
                "id": spec["id"],
                "query": query,
                "requested_count": count,
                "sourcegraph_query": sg_query,
                "matches": matches,
                "progress": progress[-5:],
                "alerts": alerts,
                "error": None,
            }
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt == 3:
                break
            time.sleep(5 * (attempt + 1))
    return {
        "id": spec["id"],
        "query": query,
        "requested_count": count,
        "sourcegraph_query": sg_query,
        "matches": matches,
        "progress": progress[-5:],
        "alerts": alerts,
        "error": last_error or "unknown error",
    }


def dedupe_hits(query_results: list[dict]):
    by_file = {}
    raw_rows = []
    for result in query_results:
        for row in result["matches"]:
            raw_rows.append(row)
            key = (row["repository"], row["commit"], row["path"])
            dst = by_file.setdefault(
                key,
                {
                    "repository": row["repository"],
                    "commit": row["commit"],
                    "path": row["path"],
                    "languages": set(),
                    "signature_ids": set(),
                    "signature_queries": set(),
                    "repo_stars": row.get("repo_stars"),
                    "repo_last_fetched": row.get("repo_last_fetched"),
                    "branches": set(),
                    "snippets": [],
                },
            )
            if row.get("language"):
                dst["languages"].add(row["language"])
            dst["signature_ids"].add(row["signature_id"])
            dst["signature_queries"].add(row["signature_query"])
            dst["branches"].update(row.get("branches") or [])
            for snippet in row.get("snippets") or []:
                if snippet not in dst["snippets"] and len(dst["snippets"]) < 8:
                    dst["snippets"].append(snippet)

    deduped = []
    excluded = []
    for row in by_file.values():
        row = dict(row)
        row["languages"] = sorted(row["languages"])
        row["signature_ids"] = sorted(row["signature_ids"])
        row["signature_queries"] = sorted(row["signature_queries"])
        row["branches"] = sorted(row["branches"])
        reason = path_filter_reason(row["path"])
        row["filter_reason"] = reason
        if reason:
            excluded.append(row)
        else:
            deduped.append(row)
    deduped.sort(key=lambda r: (r["repository"].lower(), r["commit"], r["path"].lower()))
    excluded.sort(key=lambda r: (r["repository"].lower(), r["commit"], r["path"].lower()))
    return raw_rows, deduped, excluded


def repository_candidates(deduped: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in deduped:
        grouped[(row["repository"], row["commit"])].append(row)

    out = []
    for (repo, commit), rows in grouped.items():
        signature_ids = sorted({s for row in rows for s in row["signature_ids"]})
        languages = sorted({s for row in rows for s in row["languages"]})
        stars = max((row.get("repo_stars") or 0) for row in rows)
        evidence = []
        for row in rows[:30]:
            evidence.append(
                {
                    "path": row["path"],
                    "signature_ids": row["signature_ids"],
                    "languages": row["languages"],
                }
            )
        out.append(
            {
                "repository": repo,
                "commit": commit,
                "repo_stars": stars,
                "signature_ids": signature_ids,
                "languages": languages,
                "surviving_file_hits": len(rows),
                "evidence": evidence,
                "evidence_truncated": len(rows) > len(evidence),
            }
        )
    out.sort(key=lambda r: (-r["surviving_file_hits"], -r["repo_stars"], r["repository"].lower(), r["commit"]))
    return out


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--output-dir", default="benchmark/harvest/out")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    specs = manifest["signatures"]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    query_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(run_query, spec): spec for spec in specs}
        for future in concurrent.futures.as_completed(futures):
            spec = futures[future]
            result = future.result()
            query_results.append(result)
            print(
                f"{spec['id']}: matches={len(result['matches'])} error={result['error']}",
                flush=True,
            )

    query_results.sort(key=lambda r: r["id"])
    raw_rows, surviving_file_hits, excluded_file_hits = dedupe_hits(query_results)
    candidates = repository_candidates(surviving_file_hits)

    raw_path = output_dir / "raw-sourcegraph-hits.jsonl"
    with raw_path.open("w", encoding="utf-8") as f:
        for row in raw_rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    deduped_path = output_dir / "deduped-surviving-file-hits.json"
    excluded_path = output_dir / "excluded-obvious-doc-test-example-hits.json"
    candidate_path = output_dir / "candidate-repositories-v1.json"
    candidate_tsv = output_dir / "candidate-repositories-v1.tsv"

    write_json(deduped_path, surviving_file_hits)
    write_json(excluded_path, excluded_file_hits)

    frozen = {
        "schema_version": 1,
        "experiment": manifest.get("experiment", "candidate-harvest-v1"),
        "source": "Sourcegraph.com public stream API over Sourcegraph-indexed GitHub repositories",
        "claim_boundary": (
            "Candidate discovery only. This is not a GitHub-wide prevalence sample and does not imply "
            "that Sourcegraph indexes every public GitHub repository."
        ),
        "manifest": manifest,
        "candidates": candidates,
    }
    write_json(candidate_path, frozen)
    with candidate_tsv.open("w", encoding="utf-8") as f:
        f.write("repository\tcommit\tsurviving_file_hits\tsignature_ids\n")
        for row in candidates:
            f.write(
                f"{row['repository']}\t{row['commit']}\t{row['surviving_file_hits']}\t"
                f"{','.join(row['signature_ids'])}\n"
            )

    filter_counts = Counter(row["filter_reason"] for row in excluded_file_hits)
    query_stats = []
    for result in query_results:
        last_progress = result["progress"][-1] if result["progress"] else {}
        query_stats.append(
            {
                "id": result["id"],
                "query": result["query"],
                "raw_content_matches": len(result["matches"]),
                "error": result["error"],
                "final_progress": last_progress,
                "alerts": result["alerts"][:10],
            }
        )

    candidate_hash = sha256_bytes(canonical_json(frozen))
    tsv_hash = sha256_bytes(candidate_tsv.read_bytes())
    summary = {
        "schema_version": 1,
        "experiment": manifest.get("experiment", "candidate-harvest-v1"),
        "duration_seconds": round(time.time() - started, 3),
        "signatures": len(specs),
        "query_failures": sum(1 for r in query_results if r["error"]),
        "raw_signature_hit_rows": len(raw_rows),
        "deduped_file_hits_before_path_filter": len({(r["repository"], r["commit"], r["path"]) for r in raw_rows}),
        "excluded_obvious_hits": len(excluded_file_hits),
        "excluded_by_reason": dict(sorted(filter_counts.items())),
        "surviving_file_hits": len(surviving_file_hits),
        "surviving_repo_commit_candidates": len(candidates),
        "distinct_surviving_repositories": len({r["repository"] for r in candidates}),
        "candidate_list_sha256_canonical_json": candidate_hash,
        "candidate_tsv_sha256": tsv_hash,
        "query_stats": query_stats,
        "notes": [
            "Forks and archived repositories are excluded by Sourcegraph.com default search behavior.",
            "Only repositories whose Sourcegraph repository name starts with github.com/ are retained.",
            "Cheap filtering removes obvious docs/tests/examples/demos/tutorials/fixtures/mocks, vendored/generated paths, README-style docs, and lockfiles.",
            "No V4 semantic classification is run in this stage.",
            "Counts describe this reproducible candidate-search universe, not ecosystem prevalence.",
        ],
    }
    write_json(output_dir / "harvest-summary-v1.json", summary)
    (output_dir / "candidate-repositories-v1.sha256").write_text(
        f"{candidate_hash}  candidate-repositories-v1.json\n"
        f"{tsv_hash}  candidate-repositories-v1.tsv\n",
        encoding="utf-8",
    )

    print(json.dumps({k: summary[k] for k in (
        "raw_signature_hit_rows",
        "deduped_file_hits_before_path_filter",
        "excluded_obvious_hits",
        "surviving_file_hits",
        "surviving_repo_commit_candidates",
        "distinct_surviving_repositories",
        "query_failures",
        "candidate_list_sha256_canonical_json",
    )}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
