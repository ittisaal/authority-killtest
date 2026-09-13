#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import extract_evidence as extraction


def decide(actor, relation, reduction, guard, no_edge):
    if actor is False:
        return 'safe', 'repository-level write authority is absent'
    if actor is None:
        return 'unknown', 'repository-level write authority is not established'
    if no_edge:
        return 'safe', 'the evaluated configuration selects the rule by another repository criterion'
    if guard is True:
        return 'safe', 'an independent required review/check condition remains'
    if relation == 'unknown':
        return 'unknown', 'no concrete consuming policy edge is established'
    if relation == 'integrity_marker':
        return 'unknown', 'editable integrity state is observed, but a concrete privilege/protection consumer is not established'
    if relation == 'policy_edge' and reduction is True and guard is False:
        return 'unsafe', 'a protection-reducing state is reachable by the repository writer'
    return 'unknown', 'the extracted evidence does not establish the full composed effect'


def evaluate_case(case):
    row = extraction.extract(case)
    x = row['extracted']
    label, reason = decide(
        x['actor_can_modify'],
        x['consumer_relation'],
        x['protection_reducing_state_observed'],
        x['independent_guard_observed'],
        x['consumer_relation'] == 'confirmed_no_policy_edge',
    )
    row['label'] = label
    row['reason'] = reason
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('corpus')
    ap.add_argument('--output', default='-')
    args = ap.parse_args()
    data = json.loads(Path(args.corpus).read_text())
    rows = [evaluate_case(c) for c in data['cases']]
    result = {'summary': extraction.score(rows, data['cases']), 'cases': rows}
    out = json.dumps(result, indent=2, sort_keys=True)
    if args.output == '-':
        print(out)
    else:
        Path(args.output).write_text(out + '\n')


if __name__ == '__main__':
    main()
