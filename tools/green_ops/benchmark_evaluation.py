# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Execute the frozen Week12 protocol; no training, selection or policy overrides."""
import argparse
import gzip
import json
import platform
from pathlib import Path
import statistics
from analytical_reference import _json_bytes, _sha256
from dataset_builder import _json_from_bytes
from analytical_design import configuration_family
from ml_dataset import FreshDirectory
from fault_injection import ENGINE_ID, build_artifact, parent_id
from fault_workflow import (ROOT, ASSUMPTIONS, DEVELOPMENT, RESEARCH_POLICY,
                            GATE_POLICY, development_specs, load_frozen_models,
                            evaluate_artifact, gate_exit)

RECIPE = ROOT/'tools/green_ops/recipes/week12-fault-benchmark-v1.json'
RECEIPT = ROOT/'docs/results/week11/week12-freeze.json'
RECEIPT_SHA = '97a2c8a795eb2508a1ec47b433349070ca047198fced4486632ea8b47ab3a980'


def checked(path, digest):
    content = path.read_bytes()
    if _sha256(content) != digest:
        raise ValueError(f'frozen hash mismatch: {path}')
    return content


def case_id(intent, fault, parameters, assumptions):
    hashes = {k: _sha256(v) for k, v in dict(parameters=parameters,
        intended_workload=_json_bytes(intent), assumptions=assumptions,
        fault=_json_bytes(fault)).items()}
    return 'fc-'+_sha256(_json_bytes(dict(engine_id=ENGINE_ID, inputs=hashes)))[:32]


def verify_frozen():
    freeze = _json_from_bytes(checked(RECEIPT, RECEIPT_SHA))
    raw = checked(RECIPE, freeze['benchmark_recipe_sha256'])
    recipe = _json_from_bytes(raw)
    for name, digest in {**recipe['exclusion_source_sha256'], **freeze['engine_code_sha256']}.items():
        path = (ROOT/name).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('frozen source escapes repository')
        checked(path, digest)
    design = recipe['design']
    parameters = checked(ROOT/design['model_parameters_path'], design['model_parameters_sha256'])
    assumptions = checked(ASSUMPTIONS, design['assumptions_sha256'])
    checked(RESEARCH_POLICY, recipe['research_policy_sha256'])
    checked(GATE_POLICY, freeze['production_gate_policy_sha256'])
    checked(ROOT/'docs/results/week7-regression-v1/training/selection.json', freeze['model_selection_sha256'])
    caldir = ROOT/'docs/results/week8/calibration'
    inventory = _json_from_bytes(checked(caldir/'calibration-set.json', freeze['calibration_inventory_sha256']))
    for name, digest in inventory['files'].items():
        if Path(name).name != name:
            raise ValueError('unsafe calibration name')
        checked(caldir/name, digest)
    week8 = _json_from_bytes(checked(ROOT/'tools/green_ops/recipes/week8-uncertainty-v1.json', recipe['calibration_recipe_sha256']))
    models = load_frozen_models()
    if week8['model_sha256'] != recipe['model_sha256']:
        raise ValueError('model inventory mismatch')
    for target, model in models.items():
        if _sha256(_json_bytes(model)) != recipe['model_sha256'][target]:
            raise ValueError('model canonical hash mismatch')
    if freeze['feature_contract_version'] != 3 or freeze['feature_order'] != ['payload_size_bytes','interval_ms','tx_power_dbm','window_duration_ms']:
        raise ValueError('feature contract mismatch')
    specs = development_specs(design)
    parents = {i['evaluation_group_id'] for i, f in specs}
    exclusions = recipe['excluded_prior_parent_configurations']
    excluded = {parent_id(x['payload_size_bytes'], x['interval_ms']) for x in exclusions}
    if len(excluded) != 109 or any(x['parent_id'] != parent_id(x['payload_size_bytes'], x['interval_ms']) for x in exclusions) or parents & excluded:
        raise ValueError('parent exclusions mismatch')
    # Recheck historical grids and known seeds without reading outcome labels.
    historical = [dict(payload_sizes_bytes=[16,32,64,128,256,512],intervals_ms=[50,100,200,400])]
    for name in ('week7-regression-v1.json','week8-uncertainty-v1.json','week11-development-v1.json'):
        data = _json_from_bytes((ROOT/'tools/green_ops/recipes'/name).read_bytes())
        historical.append(data.get('axes',data))
    if any(parent_id(p,i) not in excluded for a in historical for p in a['payload_sizes_bytes'] for i in a['intervals_ms']):
        raise ValueError('historical grid missing from exclusions')
    prior = set(_json_from_bytes((ROOT/'docs/results/week8/lineage.json').read_bytes())['excluded_seeds'])
    for p in week8['axes']['payload_sizes_bytes']:
        for i in week8['axes']['intervals_ms']:
            family = configuration_family(dict(payload_size_bytes=p,interval_ms=i,tx_power_dbm=19))
            for rep in range(1,6):
                prior.add(int(_sha256(f'analytical-design-v1:{week8["master_seed"]}:{family}:{rep}'.encode())[:16],16))
    prior.update(i['seed'] for i,f in development_specs(_json_from_bytes(DEVELOPMENT.read_bytes())))
    streams = {}
    for intent, fault in specs:
        seed = intent['seed']; group = intent['evaluation_group_id']
        if seed in prior or (seed in streams and streams[seed] != group):
            raise ValueError('seed leakage')
        streams[seed] = group
    ids = sorted(case_id(i,f,parameters,assumptions) for i,f in specs)
    splits = recipe['parent_splits']
    ordered = sorted(parents,key=lambda p:_sha256(f'week12-fault-split-v1:2026112002:{p}'.encode()))
    if splits != dict(validation=sorted(ordered[:8]),locked_evaluation=sorted(ordered[8:])):
        raise ValueError('split membership mismatch')
    counts = {s:sum(i['evaluation_group_id'] in groups for i,f in specs) for s,groups in splits.items()}
    if len(ids)!=1920 or len(set(ids))!=1920 or len(parents)!=16 or len(streams)!=48 or counts!=dict(validation=960,locked_evaluation=960):
        raise ValueError('benchmark dimensions mismatch')
    if ids != recipe['planned_case_ids'] or _sha256(_json_bytes(ids)) != recipe['case_ids_sha256']:
        raise ValueError('case identities mismatch')
    return recipe, specs, parameters, assumptions, dict(preflight_version=1,
        recipe_sha256=_sha256(raw), freeze_receipt_sha256=RECEIPT_SHA,
        case_count=len(ids), parent_count=len(parents), partition_counts=counts,
        random_streams=len(streams), excluded_parent_count=len(excluded),
        prior_parent_overlap=[], prior_known_seed_overlap=[],
        historical_archive_limitation='5334 source paths audited at freeze; transient absolute paths not required for replay; frozen inventory digest retained',
        frozen_dependencies_verified=True)


def summarize(rows):
    n=len(rows); parents=sorted({r['parent'] for r in rows})
    feasible=[r for r in rows if r['feasibility']=='COMPLETE']
    controls=[r for r in rows if not r['configured_fault']]
    violations=[r for r in rows if r['oracle_violation'] is True]
    def rate(num, den, unit='cases'):
        return dict(numerator=num,denominator=den,value=num/den if den else None,
                    denominator_unit=unit,dependence_unit='parent',parent_count=len(parents))
    def effects(values):
        return dict(count=len(values),mean=statistics.mean(values),median=statistics.median(values),minimum=min(values),maximum=max(values)) if values else dict(count=0,mean=None,median=None,minimum=None,maximum=None)
    return dict(case_count=n,parent_count=len(parents),parents=parents,
        feasibility={s:sum(r['feasibility']==s for r in rows) for s in ('COMPLETE','INFEASIBLE','INVALID')},
        statuses={s:sum(r['status']==s for r in rows) for s in ('PASS','FAIL','ABSTAIN','ERROR')},
        oracle_known=sum(r['oracle_violation'] is not None for r in rows),oracle_unknown=sum(r['oracle_violation'] is None for r in rows),
        oracle_violations=len(violations),positive_FAIL_detections=sum(r['positive_detection'] for r in rows),
        violations_without_positive_detection=sum(not r['positive_detection'] for r in violations),
        absolute_200mW_fault_violations=sum(r['absolute_violation'] is True for r in rows),
        control_count=len(controls),control_false_alarms=sum(r['control_false_alarm'] for r in controls),
        control_abstention_blocks=sum(r['status']=='ABSTAIN' and r['blocked'] for r in controls),
        control_error_blocks=sum(r['status']=='ERROR' and r['blocked'] for r in controls),
        inputs_changed=sum(r['inputs_changed'] for r in rows),predictions_changed=sum(r['predictions_changed'] for r in rows),
        observability={str(v):sum(r['observable'] is v for r in rows) for v in (True,False,None)},
        detection_rate=rate(sum(r['positive_detection'] for r in violations),len(violations)),
        control_false_alarm_rate=rate(sum(r['control_false_alarm'] for r in controls),len(controls)),
        control_abstention_rate=rate(sum(r['status']=='ABSTAIN' for r in controls),len(controls)),
        parents_with_violation_rate=rate(len({r['parent'] for r in violations}),len(parents),'parents'),
        effects=dict(paired_energy_mj=effects([r['delta_mj'] for r in feasible]),
            paired_increase_percent=effects([r['increase_percent'] for r in feasible if r['increase_percent'] is not None]),
            paired_power_mw=effects([r['delta_power_mw'] for r in feasible]),
            equal_parent_mean_delta_mj=effects([statistics.mean(r['delta_mj'] for r in feasible if r['parent']==p) for p in parents if any(r['parent']==p for r in feasible)])))


def aggregate(rows):
    return dict(aggregation_version=1,provenance='analytical_simulation',
        units=dict(delta_mj='mJ',delta_power_mw='mW',increase_percent='%'),
        dependence='variants/repetitions share parent; descriptive only, no IID/population inference',
        overall=summarize(rows),by_split={s:summarize([r for r in rows if r['split']==s]) for s in sorted({r['split'] for r in rows})},
        by_fault_severity={f'{s}/{k}/{v}':summarize([r for r in rows if (r['split'],r['kind'],r['severity'])==(s,k,v)]) for s,k,v in sorted({(r['split'],r['kind'],r['severity']) for r in rows})},
        by_parent={p:summarize([r for r in rows if r['parent']==p]) for p in sorted({r['parent'] for r in rows})})


def execute(output, consumption):
    recipe,specs,parameters,assumptions,preflight=verify_frozen()
    output=Path(output);consumption=Path(consumption)
    if output.exists() or consumption.exists() or output.resolve()==consumption.resolve():
        raise ValueError('output/consumption collision')
    # Durable even if output publication rolls back; never relabel exposed data fresh.
    with consumption.open('xb') as stream:
        stream.write(_json_bytes(dict(consumption_version=1,status='BOTH_PARTITIONS_CONSUMED_ON_EXECUTION_START',
            recipe_sha256=preflight['recipe_sha256'],partitions=recipe['parent_splits'],
            tooling_sha256=_sha256(Path(__file__).read_bytes()))))
    rows=[];inventory=[]
    with FreshDirectory(output) as dest:
        dest.write('preflight.json',_json_bytes(preflight))
        for index,(intent,fault) in enumerate(specs):
            cid=case_id(intent,fault,parameters,assumptions);parent=intent['evaluation_group_id']
            split=next(s for s,g in recipe['parent_splits'].items() if parent in g)
            raw=_json_bytes(build_artifact(parameters,_json_bytes(intent),assumptions,_json_bytes(fault)))
            report=evaluate_artifact(raw); code=gate_exit(report)
            if report['lineage']['child_id']!=cid:
                raise ValueError('generated identity differs from freeze')
            a=report['analytical'];p=report['predictor']; b=a['baseline']; f=a['fault']
            rows.append(dict(case_id=cid,parent=parent,split=split,kind=fault['kind'],severity=fault['severity'],
                seed=intent['seed'],window_ms=intent['window_duration_ms'],
                feasibility=a['fault_status'],oracle_violation=a['budget_violation'],
                baseline=b,fault=f,delta_mj=a['energy_delta_mj'],
                increase_percent=100*a['energy_delta_mj']/b['total_energy_mj'] if a['energy_delta_mj'] is not None and b['total_energy_mj'] else None,
                delta_power_mw=f['mean_power_mw']-b['mean_power_mw'] if f['mean_power_mw'] is not None else None,
                absolute_violation=a['frozen_policy_point_checks'][0]['fault_violation'],
                status=report['gatekeeper']['status'],exit_code=code,blocked=report['execution_blocked'],
                configured_fault=report['configured_fault'],mechanism_occurred=report['mechanism_occurred'],
                positive_detection=report['positive_fault_detection'],control_false_alarm=report['control_false_alarm'],
                inputs_changed=p['inputs_changed'],predictions_changed=p['predictions_changed'],
                observable=report['observable_in_selected_prediction_context'],predictor=p,
                artifact_sha256=_sha256(raw),report_sha256=_sha256(_json_bytes(report))))
            files={}
            for name,data in (('artifact',raw),('report',_json_bytes(report))):
                packed=gzip.compress(data,mtime=0);relative=f'cases/{cid}-{name}.json.gz'
                dest.write(relative,packed);files[relative]=dict(raw_sha256=_sha256(data),gzip_sha256=_sha256(packed))
            inventory.append(dict(case_id=cid,files=files))
            if (index+1)%120==0: print(f'executed {index+1}/1920',flush=True)
        rows.sort(key=lambda r:r['case_id']);inventory.sort(key=lambda r:r['case_id'])
        case_bytes=b''.join(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n' for r in rows)
        summary=_json_bytes(aggregate(rows))
        dest.write('cases.jsonl',case_bytes);dest.write('aggregate.json',summary)
        dest.write('manifest.json',_json_bytes(dict(manifest_version=1,python=platform.python_version(),
            preflight_sha256=_sha256(_json_bytes(preflight)),tooling_sha256=_sha256(Path(__file__).read_bytes()),
            cases_sha256=_sha256(case_bytes),aggregate_sha256=_sha256(summary),entries=inventory)))
    return 0  # Completed offline software verification, NOT energy approval.


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path);parser.add_argument('--consumption',type=Path)
    parser.add_argument('--preflight',action='store_true');args=parser.parse_args()
    try:
        if args.preflight: print(_json_bytes(verify_frozen()[-1]).decode());return 0
        if args.output is None or args.consumption is None: parser.error('--output and --consumption required')
        return execute(args.output,args.consumption)
    except (ValueError,OSError) as exc:
        print(f'ERROR: {exc}');return 1

if __name__=='__main__':raise SystemExit(main())
