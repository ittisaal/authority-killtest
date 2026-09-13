#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def classify(observation: dict) -> str:
    actor = observation.get("actor_can_modify")
    relation = observation.get("consumer_relation")
    reduction = observation.get("protection_reducing_state_observed")
    guard = observation.get("independent_guard_observed")
    delta = observation.get("marginal_delta_observed")

    if actor is False:
        return "S"
    if actor is None:
        return "N"
    if relation == "confirmed_no_policy_edge":
        return "S"
    if guard is True:
        return "S"
    if relation in (None, "unknown"):
        return "N"
    if reduction is False:
        return "S"
    if delta is False:
        return "S"
    if reduction is True and guard is False and delta is True:
        return "U"
    return "N"


def evaluate(data: dict) -> dict:
    rows = []
    for case in data["cases"]:
        predicted = classify(case["observation"])
        rows.append(
            {
                "id": case["id"],
                "semantic_truth": case["semantic_truth"],
                "expected_observation": case["expected_observation"],
                "predicted_observation": predicted,
                "evidence_complete": case["evidence_complete"],
            }
        )

    complete = [r for r in rows if r["evidence_complete"]]
    incomplete = [r for r in rows if not r["evidence_complete"]]
    return {
        "summary": {
            "cases": len(rows),
            "predicted_counts": dict(Counter(r["predicted_observation"] for r in rows)),
            "observation_matches": sum(
                r["predicted_observation"] == r["expected_observation"] for r in rows
            ),
            "observation_total": len(rows),
            "complete_evidence_cases": len(complete),
            "complete_evidence_truth_matches": sum(
                r["predicted_observation"] == r["semantic_truth"] for r in complete
            ),
            "incomplete_evidence_cases": len(incomplete),
            "incomplete_cases_returning_N": sum(
                r["predicted_observation"] == "N" for r in incomplete
            ),
            "note": "U/S are semantic outcomes. N is an evidence-state outcome and is not treated as a third ground-truth system class."
        },
        "cases": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cases")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    data = json.loads(Path(args.cases).read_text())
    result = evaluate(data)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        print(text, end="")
    else:
        Path(args.output).write_text(text)


if __name__ == "__main__":
    main()
