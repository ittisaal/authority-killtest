#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).with_name("discover_repository_tree.py")
spec = importlib.util.spec_from_file_location("discover_repository_tree", HERE)
discovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discovery)


def evaluate_case(case):
    result = discovery.discover(case["repository"], case["commit"])
    target_key = discovery.core.canonical(case["target_property"])
    matched = next((row for row in result["candidates"] if row["canonical"] == target_key), None)
    return {
        "id": case["id"],
        "repository": case["repository"],
        "commit": case["commit"],
        "target_property": case["target_property"],
        "expected_label": case["expected_label"],
        "target_found": matched is not None,
        "predicted_label": matched["label"] if matched else None,
        "classification_match": bool(matched and matched["label"] == case["expected_label"]),
        "candidate_count": result["candidate_count"],
        "scan": result["scan"],
        "matched_candidate": matched,
        "all_candidates": [
            {
                "property": row["property"],
                "label": row["label"],
                "signals": row["discovery_signals"],
            }
            for row in result["candidates"]
        ],
    }


def summarize(rows):
    found = [r for r in rows if r["target_found"]]
    return {
        "cases": len(rows),
        "target_properties_discovered": len(found),
        "target_discovery_recall": len(found) / len(rows) if rows else 0.0,
        "classification_matches_on_discovered_targets": sum(r["classification_match"] for r in found),
        "classification_total_on_discovered_targets": len(found),
        "end_to_end_matches": sum(r["classification_match"] for r in rows),
        "end_to_end_total": len(rows),
        "file_caps_reached": sum(bool(r["scan"]["file_cap_reached"]) for r in rows),
        "tree_truncations": sum(bool(r["scan"]["tree_truncated"]) for r in rows),
        "fetch_errors": sum(r["scan"]["fetch_errors"] for r in rows),
        "note": (
            "The discoverer receives only repository + frozen commit. Target property names and labels are used "
            "afterward for evaluation and are not passed into discovery. File selection is bounded and based only "
            "on repository paths, so this is not ecosystem prevalence or private-organization discovery."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--output", default="-")
    args = ap.parse_args()
    manifest = json.loads(Path(args.manifest).read_text())
    rows = [evaluate_case(case) for case in manifest["cases"]]
    result = {"summary": summarize(rows), "cases": rows}
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output == "-":
        print(text)
    else:
        Path(args.output).write_text(text + "\n")


if __name__ == "__main__":
    main()
