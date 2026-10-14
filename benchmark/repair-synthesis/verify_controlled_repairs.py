#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

CUT_PATH = Path(__file__).with_name("repair_cut.py")
spec = importlib.util.spec_from_file_location("repair_cut_for_verify", CUT_PATH)
repair_cut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair_cut)


def path_status(model: dict, chosen: set[str]) -> dict[str, bool]:
    """True means the originally demonstrated unsafe path remains reachable."""
    out = {}
    for path in model["paths"]:
        out[path["id"]] = not bool(chosen.intersection(path["cuts"]))
    return out


def verify(model: dict) -> dict:
    solver = repair_cut.solve(model)
    baseline = path_status(model, set())
    if not all(baseline.values()):
        raise AssertionError("all controlled U paths must be reachable before repair")

    single_repairs = []
    for repair in model["repairs"]:
        chosen = {repair["id"]}
        status = path_status(model, chosen)
        expected_cuts = sorted(p["id"] for p in model["paths"] if repair["id"] in p["cuts"])
        observed_cuts = sorted(pid for pid, reachable in status.items() if not reachable)
        if expected_cuts != observed_cuts:
            raise AssertionError(f"cut mismatch for {repair['id']}")
        single_repairs.append({
            "repair": repair["id"],
            "cuts": observed_cuts,
            "remaining_reachable": sorted(pid for pid, reachable in status.items() if reachable),
            "evidence": repair.get("evidence"),
        })

    min_sets = []
    for item in solver["minimum_cardinality"]:
        status = path_status(model, set(item["repairs"]))
        if any(status.values()):
            raise AssertionError(f"solver repair set does not cut all paths: {item['repairs']}")
        min_sets.append(item)

    empirical = {
        "U3_fixed_guard": {
            "repair": "R-u3-fixed-org-only-floor",
            "controlled_counterexample": "S2-fixed-guard",
            "status": "empirically-demonstrated"
        },
        "U3_safe_domain": {
            "repair": "R-u3-safe-value-domain",
            "controlled_counterexample": "S3-value-domain-block",
            "status": "empirically-demonstrated"
        },
        "U4_org_only_boundary": {
            "repair": "R-u4-profile-org-only",
            "public_counterexample": "mitodl/ol-infrastructure tier",
            "status": "independently-observed-boundary-not-live-post-repair-rerun"
        }
    }

    return {
        "baseline_reachable_paths": sorted(pid for pid, reachable in baseline.items() if reachable),
        "single_repair_checks": single_repairs,
        "minimum_cardinality_sets": min_sets,
        "pareto_frontier": solver["pareto_frontier"],
        "empirical_links": empirical,
        "claim_boundary": (
            "The cut verification is executable reachability over the frozen controlled path model. "
            "Only S2 and S3 are live controlled post-condition demonstrations in this bundle; external GCP/JFrog "
            "and organization-admin mutations are not claimed as live repair reruns."
        )
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--output", default="-")
    args = ap.parse_args()
    model = json.loads(Path(args.model).read_text())
    result = verify(model)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        print(text, end="")
    else:
        Path(args.output).write_text(text)


if __name__ == "__main__":
    main()
