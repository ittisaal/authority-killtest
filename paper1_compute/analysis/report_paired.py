#!/usr/bin/env python3
"""Audit frozen aggregate deltas. No sensor readings or attack code are used."""
import csv, json, random
from pathlib import Path

SOURCE=Path(__file__).with_name('frozen_paired_family_deltas.csv')
EXPECTED={1:0.0,3:0.012205387205387198,5:0.02251683501683502}
B=5003  # Bootstrap replicates, not new physical experiments
SEED=317

def quantile(values,p):
    t=(len(values)-1)*p
    lo=int(t); hi=min(lo+1,len(values)-1)
    return values[lo]*(hi-t)+values[hi]*(t-lo)

def compute(items):
    n=sum(x['n'] for x in items)
    return {'delta_concealment_auc':sum(x['delta_auc_sum'] for x in items)/n,
            'delta_unconcealable_fraction':sum(x['delta_blocked'] for x in items)/n,
            'delta_primary_impact_mass_auc':sum(x['delta_primary_sum'] for x in items)/sum(x['primary_den'] for x in items),
            'delta_robust_impact_mass_auc':sum(x['delta_robust_sum'] for x in items)/sum(x['robust_den'] for x in items)}

def main():
    data={}
    with SOURCE.open(newline='') as f:
        for raw in csv.DictReader(f):
            k=(raw['cluster'],int(raw['budget']))
            if k in data: raise ValueError('duplicate aggregate key')
            data[k]={x:(int(raw[x]) if x in ('n','delta_blocked') else float(raw[x]))
                     for x in ('n','delta_auc_sum','delta_blocked','delta_primary_sum','delta_robust_sum','primary_den','robust_den')}
    clusters=[f'G{i:02d}' for i in range(1,13)]
    if len(data)!=36 or set(data)!={(g,b) for g in clusters for b in (1,3,5)}:
        raise ValueError('expected 12 groups x 3 frozen budgets')
    if any(x['n']!=18 or x['primary_den']<=0 or x['robust_den']<=0 for x in data.values()):
        raise ValueError('invalid group sample size or mass')
    rng=random.Random(SEED)
    output={'status':'FROZEN_POSTHOC_STATISTICAL_AUDIT_NOT_NEW_ATTACK_EVALUATION',
            'group_count':12,'trajectory_count':216,'replicates':B,'seed':SEED,
            'delta_definition':'balanced minus security-path blocking; lower is better except unconcealable fraction',
            'note':'Descriptive family-cluster bootstrap; not a population-level confidence guarantee.',
            'budgets':{}}
    for budget in (1,3,5):
        observations=[data[g,budget] for g in clusters]
        est=compute(observations)
        if abs(est['delta_concealment_auc']-EXPECTED[budget])>1e-6:
            raise ValueError('Frozen AUC did not reproduce at budget '+str(budget))
        boot={k:[] for k in est}
        for _ in range(B):
            sample=[observations[rng.randrange(len(clusters))] for _ in clusters]
            cur=compute(sample)
            for k,v in cur.items(): boot[k].append(v)
        output['budgets'][str(budget)]={k:{'delta':round(v,9),'bootstrap_95pct_interval':[
            round(quantile(sorted(boot[k]),0.025),9),round(quantile(sorted(boot[k]),0.975),9)]}
            for k,v in est.items()}
    Path('audit-results.json').write_text(json.dumps(output,indent=2)+'\n')
    print('PASS: audit of 36 frozen grouped comparisons (12 physical families, 216 trajectories)')
    for b,res in output['budgets'].items():
        print('budget',b,': delta concealment AUC',res['delta_concealment_auc'])

if __name__=='__main__':main()
