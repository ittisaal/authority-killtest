#!/usr/bin/env python3
"""Reproduce summary statistics for the frozen scale manual audit.

This script intentionally reports metrics only for the selected manual-audit
sample. It does not estimate ecosystem prevalence or full-harvest accuracy.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "scale-manual-eval-v1-results.csv"

LABELS = ("U", "S", "N")


def safe_div(num: int, den: int):
    return None if den == 0 else num / den


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    manual = Counter(row["manual_strict_label"] for row in rows)
    auto = Counter(row["auto_case_label"] for row in rows)
    ustar = sum(row["narrative_u_star"].strip().lower() == "true" for row in rows)

    matrix = defaultdict(lambda: Counter())
    for row in rows:
        matrix[row["manual_strict_label"]][row["auto_case_label"]] += 1

    agreement = sum(
        matrix[label][label]
        for label in LABELS
    )

    per_label = {}
    for label in LABELS:
        tp = matrix[label][label]
        predicted = auto[label]
        actual = manual[label]
        per_label[label] = {
            "precision": safe_div(tp, predicted),
            "recall": safe_div(tp, actual),
            "tp": tp,
            "predicted": predicted,
            "actual": actual,
        }

    false_u = sum(
        1
        for row in rows
        if row["auto_case_label"] == "U" and row["manual_strict_label"] != "U"
    )
    false_s = sum(
        1
        for row in rows
        if row["auto_case_label"] == "S" and row["manual_strict_label"] != "S"
    )

    output = {
        "scope": "selected 50-case manual audit only; not ecosystem prevalence or full-harvest accuracy",
        "cases": len(rows),
        "manual_counts": {label: manual[label] for label in LABELS},
        "automatic_counts": {label: auto[label] for label in LABELS},
        "narrative_u_star_count": ustar,
        "confusion_matrix_manual_rows_auto_columns": {
            manual_label: {
                auto_label: matrix[manual_label][auto_label]
                for auto_label in LABELS
            }
            for manual_label in LABELS
        },
        "agreement": {
            "count": agreement,
            "rate": safe_div(agreement, len(rows)),
        },
        "false_u_count": false_u,
        "false_s_count": false_s,
        "per_label": per_label,
    }

    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
