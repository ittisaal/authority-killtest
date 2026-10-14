#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


def validate(model: dict) -> tuple[list[dict], dict[str, dict], list[str]]:
    paths = model.get('paths') or []
    repairs = model.get('repairs') or []
    if not paths:
        raise ValueError('at least one unsafe path is required')
    if not repairs:
        raise ValueError('at least one repair candidate is required')
    by_id = {}
    dimensions: list[str] | None = None
    for r in repairs:
        rid = r['id']
        if rid in by_id:
            raise ValueError(f'duplicate repair id: {rid}')
        cost = r.get('cost') or {}
        dims = sorted(cost)
        if dimensions is None:
            dimensions = dims
        elif dims != dimensions:
            raise ValueError('all repair candidates must use the same cost dimensions')
        if any(not isinstance(v, (int, float)) or v < 0 for v in cost.values()):
            raise ValueError(f'costs must be non-negative numbers: {rid}')
        by_id[rid] = r
    known = set(by_id)
    for p in paths:
        cuts = p.get('cuts') or []
        if not cuts:
            raise ValueError(f"path {p.get('id')} has no repair cuts")
        missing = set(cuts) - known
        if missing:
            raise ValueError(f"path {p.get('id')} references unknown repairs: {sorted(missing)}")
    return paths, by_id, dimensions or []


def hits_all(candidate: frozenset[str], paths: list[dict]) -> bool:
    return all(candidate.intersection(p['cuts']) for p in paths)


def total_cost(candidate: frozenset[str], repairs: dict[str, dict], dimensions: list[str]) -> dict[str, float]:
    return {d: sum(float(repairs[r]['cost'][d]) for r in candidate) for d in dimensions}


def dominates(a: dict[str, float], b: dict[str, float]) -> bool:
    """True when a is no worse in every dimension and strictly better in at least one."""
    keys = a.keys()
    return all(a[k] <= b[k] for k in keys) and any(a[k] < b[k] for k in keys)


def solve(model: dict) -> dict:
    paths, repairs, dimensions = validate(model)
    ids = sorted(repairs)
    feasible = []
    for size in range(1, len(ids) + 1):
        for combo in itertools.combinations(ids, size):
            chosen = frozenset(combo)
            if not hits_all(chosen, paths):
                continue
            cost = total_cost(chosen, repairs, dimensions)
            feasible.append({
                'repairs': list(combo),
                'repair_count': size,
                'cost': cost,
                'cuts_paths': sorted(p['id'] for p in paths if chosen.intersection(p['cuts'])),
            })
    if not feasible:
        raise ValueError('no repair set cuts every unsafe path')

    min_count = min(x['repair_count'] for x in feasible)
    minimum_cardinality = [x for x in feasible if x['repair_count'] == min_count]

    pareto = []
    for item in feasible:
        if not any(
            other is not item and dominates(other['cost'], item['cost'])
            for other in feasible
        ):
            pareto.append(item)

    key = lambda x: (x['repair_count'], tuple(x['cost'][d] for d in dimensions), tuple(x['repairs']))
    minimum_cardinality.sort(key=key)
    pareto.sort(key=key)

    return {
        'path_count': len(paths),
        'repair_candidate_count': len(repairs),
        'cost_dimensions': dimensions,
        'minimum_cardinality': minimum_cardinality,
        'pareto_frontier': pareto,
        'note': 'Costs are operator-supplied relative quantities. Pareto results expose trade-offs; they are not empirical operational measurements unless the input costs were measured independently.'
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model')
    ap.add_argument('--output', default='-')
    args = ap.parse_args()
    model = json.loads(Path(args.model).read_text())
    result = solve(model)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output == '-':
        print(text)
    else:
        Path(args.output).write_text(text + '\n')


if __name__ == '__main__':
    main()
