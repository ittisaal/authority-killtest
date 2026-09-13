#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, re, urllib.request
from collections import Counter
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

UA = 'authority-provenance-evidence-extractor/1.1'


def raw_url(url: str) -> str:
    m = re.fullmatch(r'https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)', url)
    if not m:
        return url
    owner, repo, ref, path = m.groups()
    return f'https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}'


def fetch(url: str) -> str:
    req = urllib.request.Request(raw_url(url), headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', errors='replace')


def parts(name: str):
    return [x.strip() for x in name.split('+') if x.strip()]


def variants(name: str):
    snake = re.sub(r'[^A-Za-z0-9]+', '_', name)
    camel = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    vals = {name, name.lower(), name.upper(), snake, snake.lower(), snake.upper(), camel.upper()}
    return sorted((v for v in vals if v), key=len, reverse=True)


def windows(text: str, names, radius=800):
    low = text.lower()
    out = []
    for name in names:
        needle = name.lower()
        pos = 0
        while True:
            i = low.find(needle, pos)
            if i < 0:
                break
            out.append(text[max(0, i-radius):min(len(text), i+len(needle)+radius)])
            pos = i + max(1, len(needle))
    return out


def extension(url: str) -> str:
    path = urlparse(url).path.lower()
    return Path(path).suffix


def authority(prop: str, docs):
    """Return repository-level write authority only when the frozen evidence states it concretely.

    We intentionally do not treat conditional prose (e.g. "repo admins can set it IF the
    schema is repo-editable") as proof of the deployed schema.
    """
    signals, urls = set(), set()
    for p in parts(prop):
        pv = variants(p)
        for url, text in docs:
            # Structured object / IaC declaration: property and authority must be local.
            for w in windows(text, pv, 900):
                s = w.lower()
                if re.search(r'values_editable_by["\']?\s*[=:]\s*["\']?org_and_repo_actors', s):
                    signals.add(True); urls.add(url)
                if re.search(r'values_editable_by["\']?\s*[=:]\s*["\']?org_actors', s):
                    signals.add(False); urls.add(url)
                # Explicit fixed-authority prose is also useful when it names the selector itself.
                if ('org-only' in s or 'org owners only' in s or 'org-owners-only' in s) and ('property' in s or 'selector' in s):
                    signals.add(False); urls.add(url)

            # CLI schema creation: require the schema endpoint for THIS property.
            for v in pv:
                schema_pat = re.compile(r'/properties/schema/' + re.escape(v) + r'\b', re.I)
                for m in schema_pat.finditer(text):
                    w = text[max(0, m.start()-300):min(len(text), m.end()+1300)].lower()
                    if re.search(r'values_editable_by\s*=\s*["\']?org_and_repo_actors', w):
                        signals.add(True); urls.add(url)
                    if re.search(r'values_editable_by\s*=\s*["\']?org_actors', w):
                        signals.add(False); urls.add(url)

            # Helper-call schema creation, common in shell/Python bootstrap code.
            for line in text.splitlines():
                low = line.lower()
                if 'create_property' not in low:
                    continue
                if not any(v.lower() in low for v in pv):
                    continue
                if 'org_and_repo_actors' in low:
                    signals.add(True); urls.add(url)
                elif re.search(r'\borg_actors\b', low):
                    signals.add(False); urls.add(url)

    if signals == {True}: return True, sorted(urls)
    if signals == {False}: return False, sorted(urls)
    return None, sorted(urls)


def consumer(prop: str, docs):
    urls = set(); integrity = False
    schema = ('values_editable_by', 'allowed_values', '/properties/schema/', 'property_name', 'create_property')
    use = ('skip', 'bypass', 'disable', 'require', 'ruleset', 'workflow', 'automerge', 'auto-merge',
           'gate', 'condition', 'select', 'reads the property', 'uses the property', 'stamp', 'rollout')
    for p in parts(prop):
        for url, text in docs:
            for w in windows(text, variants(p), 900):
                s = w.lower()
                schemaish = any(x in s for x in schema)
                strong = any(x in s for x in use)
                if strong and (not schemaish or any(x in s for x in ('skip','bypass','automerge','auto-merge','required checks','ruleset','workflow'))):
                    urls.add(url)
                if ('version' in s or 'stamp' in s or 'claim' in s) and ('verified' in s or 'rollout' in s or 'sync' in s):
                    integrity = True
    if not urls: return 'unknown', []
    return ('integrity_marker' if integrity else 'policy_edge'), sorted(urls)


REDUCE = re.compile(r'(skip(?:ping|s|ped)?|bypass(?:ed|es|ing)?|disable(?:d|s|ing)?|exclude(?:d|s|ing)?|without (?:running|performing|requiring)?|no[- ]scan|do not (?:run|require|check)).{0,180}(scan|check|review|verification|signature|protection|ruleset|gate)', re.I|re.S)
REDUCE_R = re.compile(r'(scan|check|review|verification|signature|protection|ruleset|gate).{0,180}(skip(?:ping|s|ped)?|bypass(?:ed|es|ing)?|disable(?:d|s|ing)?|exclude(?:d|s|ing)?)', re.I|re.S)
GUARDS = [
    r'required_approving_review_count\s*[:=]\s*[1-9]',
    r'require_last_push_approval\s*[:=]\s*true',
    r'all required checks (?:are )?green',
    r'required checks .* approval',
    r'approval .* required checks',
    r'review/ci protection',
    r'required status check',
]
CODEISH = {'.py', '.sh', '.bash', '.yml', '.yaml', '.json', '.tf', '.hcl', '.js', '.ts', '.rb', '.go'}


def callable_links(prop: str, docs):
    """Find function names called near a target property and return matching definitions.

    This provides a small, generic cross-file link: `property -> function call` in one file can
    be joined to the function body in another evidence file without knowing any case names.
    """
    called = set()
    for p in parts(prop):
        for _, text in docs:
            for w in windows(text, variants(p), 750):
                for name in re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', w):
                    if name not in {'if', 'for', 'while', 'print', 'get', 'set'}:
                        called.add(name)
    bodies = []
    for url, text in docs:
        for name in called:
            pat = re.compile(r'(?m)^def\s+' + re.escape(name) + r'\s*\([^\n]*\):')
            for m in pat.finditer(text):
                nxt = re.search(r'(?m)^def\s+[A-Za-z_][A-Za-z0-9_]*\s*\(', text[m.end():])
                end = m.end() + (nxt.start() if nxt else min(7000, len(text)-m.end()))
                bodies.append((url, text[m.start():end]))
    return bodies


def semantics(prop: str, docs):
    red, guard = set(), set()
    for p in parts(prop):
        pv = variants(p)
        for url, text in docs:
            # Prose gets a tight local window to avoid borrowing unrelated policy language.
            radius = 700 if extension(url) in {'.md', '.rst', '.txt'} else 1500
            for w in windows(text, pv, radius):
                if REDUCE.search(w) or REDUCE_R.search(w): red.add(url)
                if any(re.search(g, w, re.I|re.S) for g in GUARDS): guard.add(url)

    # Follow a property-associated function call into its definition for code/config evidence.
    for url, body in callable_links(prop, docs):
        if extension(url) in CODEISH and (REDUCE.search(body) or REDUCE_R.search(body)):
            red.add(url)
        if any(re.search(g, body, re.I|re.S) for g in GUARDS):
            guard.add(url)

    reduction: Optional[bool] = True if red else None
    fixed: Optional[bool] = True if guard else (False if red else None)
    return reduction, fixed, sorted(red | guard)


def explicit_no_edge(prop: str, docs):
    hits = []
    for url, text in docs:
        low = text.lower()
        if 'github_organization_ruleset' not in low or 'github_organization_custom_propert' not in low:
            continue
        if not all(re.search(r'property_name\s*=\s*["\']'+re.escape(p)+r'["\']', text, re.I) for p in parts(prop)):
            continue
        if 'repository_name' not in low:
            continue
        if any(x in low for x in ('repository_property','custom_property_condition','repository_custom_property')):
            continue
        hits.append(url)
    return bool(hits), hits


def classify(actor, relation, reduction, guard, no_edge):
    if actor is False: return 'safe', 'repository-level write authority is absent'
    if actor is None: return 'unknown', 'repository-level write authority is not established'
    if no_edge: return 'safe', 'the evaluated IaC selects the ruleset by another repository criterion'
    if guard is True: return 'safe', 'an independent required review/check condition remains'
    if relation == 'unknown': return 'unknown', 'no concrete consuming policy edge is established'
    if reduction is True and guard is False:
        return 'unsafe', 'raw consumer logic exposes a protection-reducing state reachable by the repository writer'
    return 'unknown', 'the raw evidence does not establish the full composed effect'


def extract(case):
    docs, errors = [], []
    for url in case.get('evidence', []):
        try: docs.append((url, fetch(url)))
        except Exception as e: errors.append({'url': url, 'error': f'{type(e).__name__}: {e}'})
    a, aev = authority(case['property'], docs)
    rel, cev = consumer(case['property'], docs)
    red, grd, sev = semantics(case['property'], docs)
    noedge, nev = explicit_no_edge(case['property'], docs)
    label, why = classify(a, rel, red, grd, noedge)
    return {
        'id': case['id'], 'repository': case['repository'], 'commit': case['commit'], 'property': case['property'],
        'fetched_files': len(docs), 'fetch_errors': errors,
        'extracted': {
            'actor_can_modify': a,
            'consumer_relation': 'confirmed_no_policy_edge' if noedge else rel,
            'protection_reducing_state_observed': red,
            'independent_guard_observed': grd,
        },
        'evidence_files': {'authority': aev, 'consumer': cev, 'semantics': sev, 'no_edge': nev},
        'label': label, 'reason': why,
    }


def score(rows, cases):
    gold = {c['id']: c['expected_label'] for c in cases}
    c = Counter(); known = [r for r in rows if gold[r['id']] != 'unknown']
    for r in known:
        g, p = gold[r['id']], r['label']
        if g == 'unsafe' and p == 'unsafe': c['TP'] += 1
        elif g == 'unsafe': c['FN'] += 1
        elif g == 'safe' and p == 'unsafe': c['FP'] += 1
        else: c['TN'] += 1
    unknown = [r for r in rows if gold[r['id']] == 'unknown']
    return {
        'cases': len(rows),
        'raw_evidence_label_matches': sum(r['label'] == gold[r['id']] for r in rows),
        'raw_evidence_label_total': len(rows),
        'known_binary_subset': len(known),
        'known_binary_confusion': {k: c[k] for k in ('TP','FP','TN','FN')},
        'gold_unknown_cases': len(unknown),
        'gold_unknowns_forced_to_binary': sum(r['label'] != 'unknown' for r in unknown),
        'predicted_counts': dict(Counter(r['label'] for r in rows)),
        'note': 'Frozen-evidence extraction regression, not ecosystem accuracy. Relevant evidence URLs and property names were selected during corpus construction; arbitrary-repository discovery is not evaluated here.'
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('corpus'); ap.add_argument('--output', default='-'); args = ap.parse_args()
    data = json.loads(Path(args.corpus).read_text())
    rows = [extract(c) for c in data['cases']]
    result = {'summary': score(rows, data['cases']), 'cases': rows}
    out = json.dumps(result, indent=2, sort_keys=True)
    if args.output == '-': print(out)
    else: Path(args.output).write_text(out+'\n')

if __name__ == '__main__': main()
