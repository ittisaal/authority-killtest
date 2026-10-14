#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).with_name("discover_repository_v3.py")
spec = importlib.util.spec_from_file_location("discover_repository_v3", HERE)
discovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discovery)


def run_case(case):
    try:
        result = discovery.discover(case["repository"], case["commit"])
        return {
            "id": case["id"],
            "repository": case["repository"],
            "commit": case["commit"],
            "status": "ok",
            "scan": result["scan"],
            "candidate_count": result["candidate_count"],
            "candidates": result["candidates"],
        }
    except Exception as exc:
        return {
            "id": case["id"],
            "repository": case["repository"],
            "commit": case["commit"],
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "candidate_count": 0,
            "candidates": [],
        }


def summarize(rows):
    labels = Counter()
    owners = set()
    candidates = 0
    for row in rows:
        owners.add(row["repository"].split("/", 1)[0])
        candidates += row.get("candidate_count", 0)
        for candidate in row.get("candidates", []):
            labels[candidate["label"]] += 1
    return {
        "cases": len(rows),
        "distinct_owners": len(owners),
        "successful_cases": sum(row["status"] == "ok" for row in rows),
        "error_cases": sum(row["status"] != "ok" for row in rows),
        "total_discovered_candidates": candidates,
        "candidate_labels": {k: labels.get(k, 0) for k in ("U", "S", "N")},
        "note": (
            "Raw blind-v3 target-blind outputs. Candidate counts are not prevalence and "
            "are not scored against withheld targets here."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--output", default="-")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    forbidden = {"target_property", "expected_label", "label", "strict_label"}
    for case in manifest["cases"]:
        overlap = forbidden & set(case)
        if overlap:
            raise SystemExit(
                f"blind input leaks scoring fields for {case.get('id')}: {sorted(overlap)}"
            )

    rows = [run_case(case) for case in manifest["cases"]]
    result = {
        "experiment": manifest.get("experiment", "blind-v3"),
        "summary": summarize(rows),
        "cases": rows,
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output == "-":
        print(text)
    else:
        Path(args.output).write_text(text + "\n")


if __name__ == "__main__":
    main()
