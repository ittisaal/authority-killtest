#!/usr/bin/env python3
import json
import sys
from collections import Counter
from pathlib import Path


def classify(case):
    f = case["facts"]
    actor = f.get("actor_can_modify")
    relation = f.get("consumer_relation")
    delta = f.get("marginal_protection_delta")
    reachable = f.get("security_reducing_state_reachable")
    guard = f.get("independent_guard_blocks")
    complete = f.get("evidence_complete", False)

    if actor is False:
        return "safe", "repository-scoped actor lacks mutation authority"
    if actor is None:
        return "unknown", "mutation authority is not established"
    if relation == "confirmed_no_policy_edge":
        return "safe", "no relevant consumer edge is present in the evaluated configuration"
    if relation == "unknown":
        return "unknown", "downstream consumer relation is incomplete"
    if guard is True:
        return "safe", "an independent guard prevents a marginal protection delta"
    if delta is False and complete:
        return "safe", "consumption produces no marginal protection/privilege delta"
    if reachable is False and complete:
        return "safe", "security-reducing state is unreachable by the actor"
    if not complete or delta is None or reachable is None:
        return "unknown", "evidence is insufficient to establish the full composed effect"
    if actor is True and relation == "policy_edge" and delta is True and reachable is True and guard is False:
        return "unsafe", "actor-authorized mutation reaches a new effective protection/privilege state"
    return "unknown", "composition is not fully resolved"


def baseline_editable(case):
    return case["facts"].get("actor_can_modify") is True


def baseline_editable_consumed(case):
    return (case["facts"].get("actor_can_modify") is True and
            case["facts"].get("consumer_relation") in {"policy_edge", "integrity_marker"})


def confusion(cases, predicate):
    out = Counter()
    for c in cases:
        gold = c["expected_label"]
        if gold == "unknown":
            continue
        pred = predicate(c)
        if gold == "unsafe" and pred:
            out["TP"] += 1
        elif gold == "unsafe" and not pred:
            out["FN"] += 1
        elif gold == "safe" and pred:
            out["FP"] += 1
        elif gold == "safe" and not pred:
            out["TN"] += 1
    return {k: out[k] for k in ("TP", "FP", "TN", "FN")}


def main(path):
    data = json.loads(Path(path).read_text())
    rows = []
    for c in data["cases"]:
        label, why = classify(c)
        rows.append({
            "id": c["id"],
            "repository": c["repository"],
            "commit": c["commit"],
            "expected": c["expected_label"],
            "analyzer": label,
            "match": label == c["expected_label"],
            "reason": why,
            "witness_length": 1 if label == "unsafe" else None,
            "repair_candidates": [
                "centralize property write authority",
                "make the consumer ignore repository-controlled state for the protection decision"
            ] if label == "unsafe" else []
        })

    summary = {
        "corpus_size": len(rows),
        "gold_counts": dict(Counter(r["expected"] for r in rows)),
        "analyzer_counts": dict(Counter(r["analyzer"] for r in rows)),
        "semantic_regression_matches": sum(r["match"] for r in rows),
        "semantic_regression_total": len(rows),
        "known_binary_subset": sum(r["expected"] != "unknown" for r in rows),
        "analyzer_known_binary_confusion": confusion(data["cases"], lambda c: classify(c)[0] == "unsafe"),
        "baseline_editable_only_confusion": confusion(data["cases"], baseline_editable),
        "baseline_editable_and_consumed_confusion": confusion(data["cases"], baseline_editable_consumed),
        "unknowns_forced_to_binary": 0
    }
    result = {"summary": summary, "cases": rows}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: evaluate_corpus.py corpus.json")
    main(sys.argv[1])
