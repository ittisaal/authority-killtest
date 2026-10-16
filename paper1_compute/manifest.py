"""Frozen study workload manifest builder. This does not execute experiments."""
import argparse, hashlib, itertools, json, random
from pathlib import Path

TEP = [f"XMEAS({i})" for i in range(1,23)]
HAI = ["P1_FT01","P1_FT02","P1_FT03","P1_LIT01","P1_PIT01",
       "P1_PIT02","P1_TIT01","P1_TIT02","P1_TIT03","P2_24Vdc",
       "P2_SIT01","P2_VIBTR01","P2_VIBTR02","P2_VIBTR03",
       "P2_VIBTR04","P2_VT01","P3_FIT01","P3_LIT01","P3_PIT01"]
HAI_HELDOUT = ["A03","A06","A10","A14","A19","A22","A26","A33","A42","A45","A50","A55"]
HAI_SEEDS = [283,293,307,311,313]
TEP_SEEDS = [269,271,277]
TEP_FROZEN_PROTOCOL_SHA256 = '9f0118d17ad66e7a2c9f8aa0980affc5a41a3d2f9e5a624abfa9890d13f6b263'
# The 72 IDs below were checked one-by-one against the 2026-08-21 frozen Step44A2 V2 protocol.
# This is a scheduling snapshot only. Executors MUST re-check the frozen protocol hash.
TEP_CONFIG_IDS = [f'XMV{i}_{direction}__severity_{severity}'
                  for i in range(1,13) for direction in ('minus','plus')
                  for severity in ('low','medium','high')]
assert len(TEP_CONFIG_IDS) == len(set(TEP_CONFIG_IDS)) == 72
TEP_FAMILIES = [f"XMV{i}_{d}" for i in range(1,13) for d in ["minus","plus"]]
V2 = {3:("XMEAS(4)","XMEAS(9)","XMEAS(18)"),
      5:("XMEAS(1)","XMEAS(9)","XMEAS(10)","XMEAS(18)","XMEAS(21)")}
ORIGINAL_B5 = ("XMEAS(4)","XMEAS(21)","XMEAS(20)","XMEAS(18)","XMEAS(13)")
FAMILIES = ["tep_b1","tep_bounded_b3","tep_bounded_b5","hai_b1","hai_b2",
            "hai_frozen_random","tep_stronger_attacker","tep_cross_detector"]

def row(family,**kw):
    x=dict(family=family,**kw)
    x["job_id"]=hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()[:24]
    return x

def make(family):
    if family=="tep_b1":
        return [row(family,protected_sensors=[ch],budget=1) for ch in TEP]
    if family in ("tep_bounded_b3","tep_bounded_b5"):
        b=3 if family.endswith("b3") else 5
        seen={tuple(sorted(V2[b]))}
        if b==5: seen.add(tuple(sorted(ORIGINAL_B5)))
        rng=random.Random(317 if b==3 else 331)
        while len(seen)<(90+(1 if b==3 else 2)):
            seen.add(tuple(sorted(rng.sample(TEP,b))))
        return [row(family,protected_sensors=list(s),budget=b,
                    provisional_candidate_pool=True) for s in sorted(seen)]
    if family in ("hai_b1","hai_b2"):
        b=1 if family=="hai_b1" else 2
        return [row(family,protected_sensors=list(s),budget=b) for s in itertools.combinations(HAI,b)]
    if family=="hai_frozen_random":
        # Rankings must be loaded from the pre-reserved manifest; never reconstructed from seeds.
        return [row(family,ranking_seed=seed,budget=b,attack_id=attack,
                    requires_frozen_ranking=True)
                for seed in HAI_SEEDS for b in [1,2,3,5] for attack in HAI_HELDOUT]
    if family in ("tep_stronger_attacker","tep_cross_detector"):
        return [row(family,simulator_seed=seed,attack_config_id=config_id,
                    frozen_protocol_sha256=TEP_FROZEN_PROTOCOL_SHA256,
                    requires_frozen_trajectory=True)
                for seed in TEP_SEEDS for config_id in TEP_CONFIG_IDS]
    raise ValueError(family)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--family",choices=FAMILIES)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--shards",type=int,default=1)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--verify-dir",type=Path)
    a=p.parse_args()
    if a.shards<1 or not 0<=a.shard<a.shards: p.error("Invalid shard/shards")
    if a.verify_dir:
        files=list(a.verify_dir.glob("*.json"))
        if not files: raise RuntimeError("No shard manifests found")
        jobs={}
        for f in files:
            obj=json.loads(f.read_text())
            if obj["mode"]!="MANIFEST_ONLY_NOT_SCIENTIFIC_RESULTS":
                raise RuntimeError(f"Invalid mode: {f}")
            for j in obj["jobs"]:
                if j["job_id"] in jobs: raise RuntimeError(f"Duplicate {j['job_id']}")
                jobs[j["job_id"]]=j
        for fam in FAMILIES:
            expected={j["job_id"] for j in make(fam)}
            found={k for k,v in jobs.items() if v["family"]==fam}
            if expected!=found:
                raise RuntimeError(f"Incomplete {fam}: {len(expected)} expected, {len(found)} found")
        result={"mode":"MANIFEST_ONLY_NOT_SCIENTIFIC_RESULTS","verified":True,
                "families":len(FAMILIES),"total_jobs":len(jobs),
                "counts":{f:len(make(f)) for f in FAMILIES}}
    else:
        jobs=make(a.family)
        result={"mode":"MANIFEST_ONLY_NOT_SCIENTIFIC_RESULTS","family":a.family,
                "shard":a.shard,"shards":a.shards,"total_family_jobs":len(jobs),
                "jobs":[j for i,j in enumerate(jobs) if i%a.shards==a.shard]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="jobs"},sort_keys=True))

if __name__=="__main__": main()
