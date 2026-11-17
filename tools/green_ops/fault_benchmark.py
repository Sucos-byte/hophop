# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Plan/freeze parent-disjoint Week12 cases WITHOUT simulating or scoring them."""
from pathlib import Path
from analytical_reference import _json_bytes,_sha256,_fields
from analytical_design import configuration_family
from dataset_builder import _json_from_bytes
from fault_injection import parent_id,ENGINE_ID
from fault_workflow import ROOT,DEVELOPMENT,ASSUMPTIONS,RESEARCH_POLICY,development_specs


def prepare_proposal():
    design=_json_from_bytes(DEVELOPMENT.read_bytes());design.update(recipe_id='week12-frozen-unscored-v1',payload_sizes_bytes=[40,72,112,144],
        intervals_ms=[65,110,220,360],window_durations_ms=[1000,5000],repetitions=3,master_seed=2026112001)
    previous=set();source_hashes={}
    # Week6's committed review declares its grid; Week7/8 are machine recipes.
    historical=[dict(payload_sizes_bytes=[16,32,64,128,256,512],intervals_ms=[50,100,200,400])]
    review=ROOT/'docs/plans/green-ops-week6-review.md';source_hashes[str(review.relative_to(ROOT))]=_sha256(review.read_bytes())
    for name in ('week7-regression-v1.json','week8-uncertainty-v1.json','week11-development-v1.json'):
        path=ROOT/'tools/green_ops/recipes'/name;content=path.read_bytes();data=_json_from_bytes(content)
        historical.append(data.get('axes',data));source_hashes[str(path.relative_to(ROOT))]=_sha256(content)
    for axes in historical:
        for p in axes['payload_sizes_bytes']:
            for i in axes['intervals_ms']:previous.add((p,i))
    # Additional archived sources available locally are read for keys, never targets.
    archived=[];observed_seeds=set()
    for base in (ROOT/'docs/results',ROOT/'build',Path('/tmp')):
        paths=base.rglob('workload.json') if base!=Path('/tmp') else (p for r in sorted(base.glob('green-ops*')) if r.is_dir() for p in r.rglob('workload.json'))
        for path in paths:
            data=_json_from_bytes(path.read_bytes())
            if {'payload_size_bytes','interval_ms'}<=set(data):
                previous.add((data['payload_size_bytes'],data['interval_ms']))
                archived.append(dict(path=str(path),sha256=_sha256(path.read_bytes())))
                if type(data.get('seed')) is int:observed_seeds.add(data['seed'])
    configs=[dict(payload_size_bytes=p,interval_ms=i,parent_id=parent_id(p,i)) for p,i in sorted(previous)]
    planned=development_specs(design);parents=sorted({i['evaluation_group_id'] for i,f in planned})
    if set(parents)&{c['parent_id'] for c in configs}:raise ValueError('Week12 parent intersects historical/development data')
    order=sorted(parents,key=lambda p:_sha256(f'week12-fault-split-v1:2026112002:{p}'.encode()))
    membership=dict(validation=sorted(order[:8]),locked_evaluation=sorted(order[8:]))
    # Freeze counts/identities from source bytes; never call the energy generator.
    parameters=(ROOT/design['model_parameters_path']).read_bytes();assumptions=ASSUMPTIONS.read_bytes()
    ids=[];seeds={}
    for intended,fault in planned:
        hashes={k:_sha256(v) for k,v in dict(parameters=parameters,intended_workload=_json_bytes(intended),assumptions=assumptions,fault=_json_bytes(fault)).items()}
        ids.append('fc-'+_sha256(_json_bytes(dict(engine_id=ENGINE_ID,inputs=hashes)))[:32])
        group=intended['evaluation_group_id'];seed=intended['seed']
        if seed in seeds and seeds[seed]!=group:raise ValueError('cross-parent seed collision')
        seeds[seed]=group
    if len(ids)!=1920 or len(set(ids))!=1920 or len(parents)!=16 or len(seeds)!=48:raise ValueError('planned Week12 counts mismatch')
    lineage=_json_from_bytes((ROOT/'docs/results/week8/lineage.json').read_bytes());prior_seeds=set(lineage['excluded_seeds'])|observed_seeds
    week8=_json_from_bytes((ROOT/'tools/green_ops/recipes/week8-uncertainty-v1.json').read_bytes())
    for p in week8['axes']['payload_sizes_bytes']:
        for i in week8['axes']['intervals_ms']:
            family=configuration_family(dict(payload_size_bytes=p,interval_ms=i,tx_power_dbm=19))
            for rep in range(1,6):prior_seeds.add(int(_sha256(f'analytical-design-v1:{week8["master_seed"]}:{family}:{rep}'.encode())[:16],16))
    for intended,_ in development_specs(_json_from_bytes(DEVELOPMENT.read_bytes())):prior_seeds.add(intended['seed'])
    if set(seeds)&prior_seeds:raise ValueError('Week12 seed reuses prior/development stream')
    for name in ('fault_injection.py','fault_workflow.py','fault_benchmark.py'):
        path=ROOT/'tools/green_ops'/name;source_hashes[str(path.relative_to(ROOT))]=_sha256(path.read_bytes())
    default=_json_from_bytes((ROOT/'tools/green_ops/recipes/week8-uncertainty-v1.json').read_bytes())
    return dict(benchmark_recipe_version=1,status='FROZEN_UNSCORED',benchmark_scored=False,provenance='analytical_simulation',
        design=design,parent_splits=membership,split_seed=2026112002,parent_definition='payload+interval, coarsened across requestedTX/duration/repetition/fault/severity',
        excluded_prior_parent_configurations=configs,exclusion_source_sha256=source_hashes,archived_workload_source_count=len(archived),archived_workload_inventory_sha256=_sha256(_json_bytes(sorted(archived,key=lambda x:x['path']))),case_count=1920,parent_count=16,
        partition_counts=dict(validation=960,locked_evaluation=960),planned_case_ids=sorted(ids),case_ids_sha256=_sha256(_json_bytes(sorted(ids))),
        distinct_random_streams=48,prior_parent_overlap=[],prior_seed_overlap=[],model_sha256=default['model_sha256'],
        calibration_recipe_sha256=_sha256((ROOT/'tools/green_ops/recipes/week8-uncertainty-v1.json').read_bytes()),
        research_policy_sha256=_sha256(RESEARCH_POLICY.read_bytes()),
        scoring_protocol='Week12 only; freeze harness/model/policies before final labels. Keep all related parent variants together. ABSTAIN/ERROR blocking is not positive fault detection. Report undetected faults, control false alarms and control abstention blocks separately; never optimize on locked outcomes.',
        limitations=['same analytical law, not physical independence or validated coverage','validation/evaluation are benchmark roles, not new calibration permission','zero-severity controls share baseline evidence, not independent observations'])
