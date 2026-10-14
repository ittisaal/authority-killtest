#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE=Path(__file__).with_name('discover_repository_v4.py')
spec=importlib.util.spec_from_file_location('discover_repository_v4_dev', HERE)
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)

manifest=json.loads(Path(__file__).with_name('blind-v3-input.json').read_text())
gold=json.loads(Path(__file__).with_name('blind-v3-adjudication.json').read_text())
gold_by={c['id']:c for c in gold['cases']}


def run_case(case):
    try:
        result=v4.discover(case['repository'], case['commit'])
        target=gold_by[case['id']]['target_property']
        key=v4.core.canonical(target)
        found=next((c for c in result['candidates'] if c['canonical']==key), None)
        return {
            'id':case['id'],'repository':case['repository'],'target_property':target,
            'target_found':found is not None,'predicted':found['label'] if found else None,
            'strict_label':gold_by[case['id']]['strict_label'],
            'correct':bool(found and found['label']==gold_by[case['id']]['strict_label']),
            'candidate_count':result['candidate_count'],'status':'ok'}
    except Exception as exc:
        return {'id':case['id'],'repository':case['repository'],'status':'error','error':f'{type(exc).__name__}: {exc}','target_found':False,'correct':False}

rows=[]
with ThreadPoolExecutor(max_workers=4) as pool:
    futures={pool.submit(run_case, case):case['id'] for case in manifest['cases']}
    for future in as_completed(futures):
        row=future.result()
        rows.append(row)
        print(row, flush=True)
rows.sort(key=lambda r:r['id'])
summary={
    'cases':len(rows),
    'errors':sum(r['status']!='ok' for r in rows),
    'targets_found':sum(r.get('target_found',False) for r in rows),
    'semantic_correct':sum(r.get('correct',False) for r in rows),
    'false_U':sum(r.get('predicted')=='U' and r.get('strict_label')!='U' for r in rows),
    'false_S':sum(r.get('predicted')=='S' and r.get('strict_label')!='S' for r in rows),
}
out={'experiment':'v4-on-v3-development','summary':summary,'cases':rows}
Path('benchmark/discovery/v4-v3-dev-results.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
