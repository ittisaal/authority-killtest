#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import time
from collections import Counter
from pathlib import Path


def load_v1_module():
    path = Path(__file__).with_name("harvest_candidates_v1.py")
    spec = importlib.util.spec_from_file_location("harvest_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V1 = load_v1_module()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def prior_hash(obj) -> str:
    return V1.sha256_bytes(V1.canonical_json(obj))


def make_combined(prior_obj: dict, v2_obj: dict) -> list[dict]:
    by_key: dict[tuple[str, str], dict] = {}

    for row in prior_obj["candidates"]:
        key = (row["repository"], row["commit"])
        by_key[key] = {
            "repository": row["repository"],
            "commit": row["commit"],
            "sources": ["harvest-v1"],
            "v1_surviving_file_hits": row.get("surviving_file_hits", 0),
            "v1_signature_ids": row.get("signature_ids", []),
            "v2_surviving_file_hits": 0,
            "v2_signature_ids": [],
        }

    for row in v2_obj["candidates"]:
        key = (row["repository"], row["commit"])
        if key not in by_key:
            by_key[key] = {
                "repository": row["repository"],
                "commit": row["commit"],
                "sources": ["harvest-v2"],
                "v1_surviving_file_hits": 0,
                "v1_signature_ids": [],
                "v2_surviving_file_hits": row.get("surviving_file_hits", 0),
                "v2_signature_ids": row.get("signature_ids", []),
            }
        else:
            dst = by_key[key]
            dst["sources"] = sorted(set(dst["sources"] + ["harvest-v2"]))
            dst["v2_surviving_file_hits"] = row.get("surviving_file_hits", 0)
            dst["v2_signature_ids"] = row.get("signature_ids", [])

    out = list(by_key.values())
    out.sort(key=lambda r: (r["repository"].lower(), r["commit"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--prior-candidates", required=True)
    ap.add_argument("--expected-prior-hash", required=True)
    ap.add_argument("--output-dir", default="benchmark/harvest/out-v2")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    specs = manifest["signatures"]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prior_path = Path(args.prior_candidates)
    prior_obj = load_json(prior_path)
    observed_prior_hash = prior_hash(prior_obj)
    if observed_prior_hash != args.expected_prior_hash:
        raise SystemExit(
            "Frozen Harvest-v1 candidate hash mismatch: "
            f"expected {args.expected_prior_hash}, got {observed_prior_hash}"
        )

    started = time.time()
    query_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(V1.run_query, spec): spec for spec in specs}
        for future in concurrent.futures.as_completed(futures):
            spec = futures[future]
            result = future.result()
            query_results.append(result)
            print(
                f"{spec['id']}: matches={len(result['matches'])} error={result['error']}",
                flush=True,
            )

    query_results.sort(key=lambda r: r["id"])
    raw_rows, surviving_file_hits, excluded_file_hits = V1.dedupe_hits(query_results)
    candidates = V1.repository_candidates(surviving_file_hits)

    raw_path = output_dir / "raw-sourcegraph-hits-v2.jsonl"
    with raw_path.open("w", encoding="utf-8") as f:
        for row in raw_rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    V1.write_json(output_dir / "deduped-surviving-file-hits-v2.json", surviving_file_hits)
    V1.write_json(output_dir / "excluded-obvious-doc-test-example-hits-v2.json", excluded_file_hits)

    v2_frozen = {
        "schema_version": 1,
        "experiment": manifest.get("experiment", "candidate-harvest-v2"),
        "source": "Sourcegraph.com public stream API over Sourcegraph-indexed GitHub repositories",
        "claim_boundary": (
            "Candidate discovery only. This is not a GitHub-wide prevalence sample and does not imply "
            "that Sourcegraph indexes every public GitHub repository."
        ),
        "manifest": manifest,
        "candidates": candidates,
    }
    V1.write_json(output_dir / "candidate-repositories-v2.json", v2_frozen)

    combined_candidates = make_combined(prior_obj, v2_frozen)
    combined = {
        "schema_version": 1,
        "experiment": "candidate-harvest-v1-v2-union",
        "prior_harvest_v1_canonical_sha256": observed_prior_hash,
        "v2_manifest": manifest,
        "claim_boundary": (
            "Frozen candidate union for later unchanged V4 analysis. Counts describe the fixed search procedure, "
            "not ecosystem prevalence."
        ),
        "candidates": combined_candidates,
    }
    V1.write_json(output_dir / "candidate-repositories-v1-v2-union.json", combined)

    v2_hash = V1.sha256_bytes(V1.canonical_json(v2_frozen))
    combined_hash = V1.sha256_bytes(V1.canonical_json(combined))

    with (output_dir / "candidate-repositories-v2.tsv").open("w", encoding="utf-8") as f:
        f.write("repository\tcommit\tsurviving_file_hits\tsignature_ids\n")
        for row in candidates:
            f.write(
                f"{row['repository']}\t{row['commit']}\t{row['surviving_file_hits']}\t"
                f"{','.join(row['signature_ids'])}\n"
            )

    with (output_dir / "candidate-repositories-v1-v2-union.tsv").open("w", encoding="utf-8") as f:
        f.write("repository\tcommit\tsources\tv1_file_hits\tv2_file_hits\n")
        for row in combined_candidates:
            f.write(
                f"{row['repository']}\t{row['commit']}\t{','.join(row['sources'])}\t"
                f"{row['v1_surviving_file_hits']}\t{row['v2_surviving_file_hits']}\n"
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

    soft_target = int(manifest.get("raw_hit_soft_target", 50000))
    overlap = sum(1 for r in combined_candidates if len(r["sources"]) == 2)
    summary = {
        "schema_version": 1,
        "experiment": manifest.get("experiment", "candidate-harvest-v2"),
        "duration_seconds": round(time.time() - started, 3),
        "signatures": len(specs),
        "query_failures": sum(1 for r in query_results if r["error"]),
        "raw_hit_soft_target": soft_target,
        "raw_signature_hit_rows": len(raw_rows),
        "soft_target_reached": len(raw_rows) >= soft_target,
        "deduped_file_hits_before_path_filter": len(
            {(r["repository"], r["commit"], r["path"]) for r in raw_rows}
        ),
        "excluded_obvious_hits": len(excluded_file_hits),
        "excluded_by_reason": dict(sorted(filter_counts.items())),
        "surviving_file_hits_v2": len(surviving_file_hits),
        "surviving_repo_commit_candidates_v2": len(candidates),
        "distinct_surviving_repositories_v2": len({r["repository"] for r in candidates}),
        "frozen_harvest_v1_candidates": len(prior_obj["candidates"]),
        "exact_repo_commit_overlap_v1_v2": overlap,
        "combined_repo_commit_candidates": len(combined_candidates),
        "combined_distinct_repositories": len({r["repository"] for r in combined_candidates}),
        "harvest_v1_canonical_sha256": observed_prior_hash,
        "harvest_v2_canonical_sha256": v2_hash,
        "combined_canonical_sha256": combined_hash,
        "query_stats": query_stats,
        "notes": [
            "Harvest-v1 is consumed from its preserved Actions artifact and verified by canonical SHA-256 before union.",
            "Forks and archived repositories are excluded by Sourcegraph.com default search behavior.",
            "Only Sourcegraph repository names beginning with github.com/ are retained.",
            "The same cheap path filter as Harvest-v1 is reused unchanged.",
            "No V4 semantic classification runs in this stage.",
            "The 50k raw-hit number is a soft planning target, not a quota or prevalence denominator.",
        ],
    }
    V1.write_json(output_dir / "harvest-summary-v2.json", summary)
    (output_dir / "candidate-repositories-v2.sha256").write_text(
        f"{v2_hash}  candidate-repositories-v2.json\n"
        f"{combined_hash}  candidate-repositories-v1-v2-union.json\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "raw_signature_hit_rows": summary["raw_signature_hit_rows"],
        "raw_hit_soft_target": summary["raw_hit_soft_target"],
        "soft_target_reached": summary["soft_target_reached"],
        "surviving_repo_commit_candidates_v2": summary["surviving_repo_commit_candidates_v2"],
        "combined_repo_commit_candidates": summary["combined_repo_commit_candidates"],
        "combined_distinct_repositories": summary["combined_distinct_repositories"],
        "query_failures": summary["query_failures"],
        "combined_canonical_sha256": summary["combined_canonical_sha256"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
