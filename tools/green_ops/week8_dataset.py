# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Replay-validated frozen Week8 study; separate from Week7 training recipes."""
import copy
from pathlib import Path
from analytical_reference import _json_bytes,_sha256,generate_analytical_artifact,validate_model
from analytical_design import plan_workload_grid,load_design_record,configuration_family
from dataset_builder import _json_from_bytes
from feature_contract import PRE_RUN_FEATURES
from ml_dataset import FreshDirectory,table_files,_entry
from ml_pipeline import model_from_bytes,validate_model_recipe

RECIPE_PATH=Path('tools/green_ops/recipes/week8-uncertainty-v1.json')
# Exact supported release inventory, established by two independent generations.
DATASET_SHA256='d4a3c8a0ecbaf774274aa33ccd334bdf991180863212a14e5cae47e8b163545e'
RECIPE_SHA256='547c93bf038eb9a064571f3d1d46f28fb071e1f76106673ec537e597d3cb20fa'


def recipe_from_bytes(content):
    recipe=_json_from_bytes(content)
    if _sha256(content)!=RECIPE_SHA256:raise ValueError('unsupported or modified Week8 frozen recipe')
    return recipe


def lineage_from_bytes(content,recipe):
    lineage=_json_from_bytes(content)
    if _sha256(content)!=recipe['lineage_sha256']:raise ValueError('lineage hash mismatch')
    return lineage


def planned_specs(recipe,parameters,lineage):
    if _sha256(parameters)!=recipe['parameters_sha256']:raise ValueError('parameter hash mismatch')
    model=validate_model(_json_from_bytes(parameters));options={k:tuple(v) for k,v in recipe['axes'].items()}
    options.update(repetitions=recipe['repetitions'],master_seed=recipe['master_seed'],max_attempts=recipe['max_attempts'])
    primary=plan_workload_grid(model,**options)
    groups={configuration_family(r) for r in primary}
    if groups&set(lineage['excluded_families']):raise ValueError('previous family leakage')
    if {r['seed'] for r in primary}&set(lineage['excluded_seeds']):raise ValueError('previous seed leakage')
    ranked=sorted(groups,key=lambda g:_sha256(f"week8-proposal:{recipe['split_seed']}:{g}".encode()))
    if (len(groups)!=60 or len(primary)!=900 or sorted(ranked[:30])!=recipe['splits']['calibration']
            or sorted(ranked[30:])!=recipe['splits']['evaluation']):raise ValueError('frozen counts or group split mismatch')
    specs=[dict(panel='primary',split='calibration' if r['evaluation_group_id'] in ranked[:30] else 'evaluation',workload=r,parameters=parameters) for r in primary]
    for variant in recipe['stress_variants']:
        changed=copy.deepcopy(model);p=changed['timing_us']['tx_per_byte'];p.update(value=variant['tx_per_byte_us'],basis='assumption',source_id=None)
        changed.update(model_version=model['model_version']+'-'+variant['id'],parameter_version=model['parameter_version']+'-'+variant['id'])
        content=_json_bytes(changed)
        runs=plan_workload_grid(changed,variant_id=variant['id'],**options)
        specs.extend(dict(panel=variant['id'],split='stress',workload=r,parameters=content) for r in runs if r['evaluation_group_id'] in recipe['splits']['evaluation'])
    if len(specs)!=1800 or len({s['workload']['run_id'] for s in specs})!=1800:raise ValueError('study run counts/uniqueness mismatch')
    return sorted(specs,key=lambda s:s['workload']['run_id'])


def materialize(recipe_path,lineage_path,output_path,progress=None):
    content=Path(recipe_path).read_bytes();recipe=recipe_from_bytes(content)
    lineage_bytes=Path(lineage_path).read_bytes();lineage=lineage_from_bytes(lineage_bytes,recipe)
    parameters=Path(recipe['parameters_path']).read_bytes();assumptions=Path(recipe['assumptions_path']).read_bytes()
    if _sha256(assumptions)!=recipe['assumptions_sha256']:raise ValueError('assumption hash mismatch')
    specs=planned_specs(recipe,parameters,lineage)
    with FreshDirectory(output_path) as output:
        for name,data in [('recipe.json',content),('lineage.json',lineage_bytes),('parameters.json',parameters),('assumptions.md',assumptions)]:output.write(name,data)
        entries=[]
        for index,spec in enumerate(specs):
            run=spec['workload'];context=dict(available_fields=list(PRE_RUN_FEATURES),planned_window_duration_ms=run['window_duration_ms'],completed_as_planned=True)
            files=generate_analytical_artifact(spec['parameters'],_json_bytes(run),assumptions,prediction_context_bytes=_json_bytes(context))
            for name,data in files.items():output.write(f"bundles/{spec['panel']}/{run['run_id']}/{name}",data)
            entries.append(_entry(spec,output.path))
            if progress and (index+1)%300==0:progress(f'Generated {index+1}/1800')
        inventory=dict(study_inventory_version=1,recipe_sha256=_sha256(content),lineage_sha256=recipe['lineage_sha256'],entries=entries)
        inventory['dataset_sha256']=_sha256(_json_bytes(inventory));output.write('inventory.json',_json_bytes(inventory))
        loaded=load_dataset(output.path,progress=progress)
        for name,data in table_files(loaded['records']).items():output.write(name,data)
        output.write('audit.json',_json_bytes(loaded['audit']))
    return loaded['audit']


def load_dataset(path,progress=None):
    root=Path(path);content=(root/'recipe.json').read_bytes();recipe=recipe_from_bytes(content)
    lineage=lineage_from_bytes((root/'lineage.json').read_bytes(),recipe)
    if _sha256((root/'assumptions.md').read_bytes())!=recipe['assumptions_sha256']:raise ValueError('archived assumption mismatch')
    specs=planned_specs(recipe,(root/'parameters.json').read_bytes(),lineage)
    inventory=_json_from_bytes((root/'inventory.json').read_bytes())
    expected=dict(study_inventory_version=1,recipe_sha256=_sha256(content),lineage_sha256=recipe['lineage_sha256'],entries=[_entry(s,root) for s in specs])
    digest=_sha256(_json_bytes(expected));expected['dataset_sha256']=digest
    if digest!=DATASET_SHA256:raise ValueError('unsupported study dataset digest')
    if _json_bytes(inventory)!=_json_bytes(expected):raise ValueError('study inventory mismatch')
    records=[]
    for index,(entry,spec) in enumerate(zip(inventory['entries'],specs)):
        record=load_design_record(root/entry['path'])
        if (_json_bytes(record['workload'])!=_json_bytes(spec['workload']) or record['parameter_sha256']!=_sha256(spec['parameters'])
                or record['assumption_sha256']!=recipe['assumptions_sha256']):raise ValueError('study source/plan mismatch')
        record.update(panel=spec['panel'],split=spec['split'],entry=entry);records.append(record)
        if progress and (index+1)%300==0:progress(f'Audited {index+1}/1800')
    audit=dict(study_audit_version=1,provenance='analytical_simulation',dataset_sha256=digest,recipe_sha256=_sha256(content),lineage_sha256=recipe['lineage_sha256'],
        row_count=1800,counts={s:sum(r['split']==s for r in records) for s in ('calibration','evaluation','stress')},
        group_counts={s:len({r['family'] for r in records if r['split']==s}) for s in ('calibration','evaluation','stress')},
        prior_family_overlap=[],all_source_replays_passed=True)
    return dict(recipe=recipe,recipe_bytes=content,recipe_sha256=_sha256(content),dataset_sha256=digest,records=records,audit=audit)


def frozen_models(directory,original_recipe_bytes,recipe):
    directory=Path(directory)
    if _sha256(original_recipe_bytes)!=recipe['original_recipe_sha256']:raise ValueError('original recipe mismatch')
    if _sha256((directory/'selection.json').read_bytes())!=recipe['selection_sha256']:raise ValueError('original selection mismatch')
    models={}
    for target,digest in recipe['model_sha256'].items():
        content=(directory/f'{target}-chosen.json').read_bytes()
        if _sha256(content)!=digest:raise ValueError('frozen model hash mismatch')
        model=model_from_bytes(content);validate_model_recipe(model,_json_from_bytes(original_recipe_bytes));models[target]=model
    return models
