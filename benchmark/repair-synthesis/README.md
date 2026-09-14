# Repair-cut prototype

The analyzer can identify more than one path from bounded authority to an unwanted effective state. A useful repair should therefore cut **all** such paths, not merely suggest a local lint fix.

`repair_cut.py` takes:

- a set of unsafe paths;
- the candidate repair actions capable of cutting each path; and
- an operator-supplied non-negative cost vector for each candidate.

It returns two views:

1. **minimum cardinality** — the fewest configuration changes that cut every path;
2. **Pareto frontier** — repair sets that are not worse in every supplied cost dimension than another feasible set.

This separation matters because the one-change repair is not necessarily the lowest operational-cost repair. For example, centralizing one property may cut two downstream paths with one change, while two narrow downstream changes can preserve legitimate repository automation better.

## Cost semantics

The prototype does **not** invent dollar values or operational measurements. Dimensions are supplied by the operator and are only relative quantities, for example:

- legitimate automation disruption;
- administration scope;
- number of repositories affected;
- number of downstream systems touched.

A paper result should report the frontier and the chosen cost assumptions, not claim that an unmeasured cost vector is objectively optimal.

## Example

`example_two_path.json` models two independent downstream paths fed by the same policy-bearing metadata. Two upstream repairs each cut both paths in one change. A pair of narrow downstream repairs uses two changes but can remain Pareto-optimal because it has lower automation/repository impact.

Run:

```bash
python benchmark/repair-synthesis/repair_cut.py \
  benchmark/repair-synthesis/example_two_path.json
```

The implementation currently enumerates subsets and is intentionally small/transparent for the research benchmark. For large path sets, the same hitting-set objective can be moved to an ILP/MaxSAT solver without changing the semantics.
