# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Independent ledger arithmetic/hash audit and exact two-run comparison."""
import argparse
from fractions import Fraction
import gzip
import json
import math
from pathlib import Path
from analytical_reference import _json_bytes, _sha256
from dataset_builder import _json_from_bytes
from benchmark_evaluation import verify_frozen, aggregate


def audit(directory):
    directory=Path(directory)
    recipe, specs, _, _, preflight=verify_frozen()
    manifest=_json_from_bytes((directory/'manifest.json').read_bytes())
    cases=(directory/'cases.jsonl').read_bytes();summary=(directory/'aggregate.json').read_bytes()
    if _sha256(cases)!=manifest['cases_sha256'] or _sha256(summary)!=manifest['aggregate_sha256']:
        raise ValueError('output hash mismatch')
    if (directory/'preflight.json').read_bytes()!=_json_bytes(preflight):raise ValueError('preflight changed')
    rows=[json.loads(line) for line in cases.splitlines()]
    if len(rows)!=1920 or sorted(r['case_id'] for r in rows)!=recipe['planned_case_ids']:
        raise ValueError('case identity/count mismatch')
    if _json_bytes(aggregate(rows))!=summary:raise ValueError('aggregate mismatch')
    indexed={r['case_id']:r for r in rows};completed=0;infeasible=0
    if sorted(e['case_id'] for e in manifest['entries'])!=recipe['planned_case_ids']:raise ValueError('manifest identities mismatch')
    for entry in manifest['entries']:
        objects={}
        for name, hashes in entry['files'].items():
            path=directory/name
            if not path.resolve().is_relative_to(directory.resolve()):raise ValueError('unsafe artifact path')
            compressed=path.read_bytes();raw=gzip.decompress(compressed)
            if _sha256(compressed)!=hashes['gzip_sha256'] or _sha256(raw)!=hashes['raw_sha256']:raise ValueError('artifact hash mismatch')
            kind='artifact' if name.endswith('-artifact.json.gz') else 'report'
            objects[kind]=_json_from_bytes(raw)
            if _sha256(raw)!=indexed[entry['case_id']][kind+'_sha256']:raise ValueError('case/artifact hash mismatch')
        artifact=objects['artifact'];report=objects['report'];row=indexed[entry['case_id']]
        if artifact['lineage']['child_id']!=row['case_id'] or artifact['lineage']['parent_id']!=row['parent']:raise ValueError('lineage mismatch')
        parameters=_json_from_bytes(artifact['snapshots']['parameters'].encode())
        voltage=Fraction(parameters['conditions']['supply_v'])
        for name in ('baseline','execution'):
            execution=artifact[name]
            if execution['status']=='INFEASIBLE':
                if execution['total_energy_mj'] is not None:raise ValueError('infeasible label not null')
                infeasible+=1;continue
            durations=execution['state_duration_us'];currents=execution['state_current_ma']
            if sum(durations.values())!=execution['observation_us']:raise ValueError('time mismatch')
            end=0;ledger={state:0 for state in durations}
            for segment in execution['segments']:
                if segment['start_us']!=end:raise ValueError('segment overlap/gap')
                ledger[segment['state']]+=segment['duration_us'];end+=segment['duration_us']
            if ledger!=durations or end!=execution['observation_us']:raise ValueError('ledger mismatch')
            # Independent rational arithmetic; does not call engine's energy integrator.
            energy=float(sum(voltage*Fraction(currents[s])*d for s,d in durations.items())/1000000)
            if not math.isclose(energy,execution['total_energy_mj'],rel_tol=1e-12,abs_tol=1e-12):raise ValueError('independent energy mismatch')
            if not math.isclose(energy*1000000/end,execution['mean_power_mw'],rel_tol=1e-12):raise ValueError('power units mismatch')
            completed+=1
        if report['gatekeeper']['status']!=row['status'] or report['positive_fault_detection']!=row['positive_detection']:raise ValueError('report outcome mismatch')
        baseline=artifact['baseline']['total_energy_mj'];fault=artifact['execution']['total_energy_mj']
        truth=None if fault is None or baseline==0 else Fraction(fault)>Fraction(baseline)*Fraction(105,100)
        if truth is not row['oracle_violation']:raise ValueError('independent oracle mismatch')
    return dict(case_count=len(rows),completed_ledgers_audited=completed,infeasible_ledgers=infeasible,
                case_hash=manifest['cases_sha256'],aggregate_hash=manifest['aggregate_sha256'])


def compare(first, second):
    a=audit(first);b=audit(second)
    def hashes(root):return {str(p.relative_to(root)):_sha256(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
    ah=hashes(Path(first));bh=hashes(Path(second))
    if ah!=bh or a!=b:raise ValueError('independent runs differ')
    return dict(reproduction_version=1,provenance='analytical_simulation',all_files_identical=True,
                compared_files=len(ah),audit=a,inventory_sha256=_sha256(_json_bytes(ah)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('first',type=Path);parser.add_argument('second',type=Path)
    args=parser.parse_args();print(_json_bytes(compare(args.first,args.second)).decode())
