# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Frozen analytical experiment data and safe, destination-independent outputs."""

import copy
from pathlib import Path

from analytical_reference import (GENERATOR_VERSION,SAMPLER_VERSION,_json_bytes,_sha256,
                                  _integer,_number,_fields,_identifier,generate_analytical_artifact,validate_model)
from analytical_design import plan_workload_grid,load_design_record
from dataset_builder import _json_from_bytes
from feature_contract import PRE_RUN_FEATURES,FEATURE_CONTRACT_VERSION

TARGET_UNITS = {"target_mean_power_mw":"mW","target_total_energy_mj":"mJ",
                "target_energy_per_delivered_packet_uj":"uJ"}
RECIPE_FIELDS = {"recipe_version","experiment_id","dataset_version","feature_contract_version",
    "generator_version","sampler_version","parameters_path","parameters_sha256","assumptions_path",
    "assumptions_sha256","axes","repetitions","master_seed","max_attempts","split_seed","cv_seed",
    "splits","cv_folds","primary_row_count","stress_row_count","stress_variants","feature_profile",
    "prediction_mode","feature_order","targets","ridge_alphas","cv_shortlist","selection_metric",
    "tie_break","refit_on_validation","missing_label_policy","preprocessing","solver"}


class FreshDirectory:
    """Publish into a new directory; roll back only files/directories we created."""
    def __init__(self,path):
        self.path=Path(path).resolve();self.files=[];self.directories=[]
    def __enter__(self):
        self.path.mkdir();self.directories.append(self.path);return self
    def write(self,relative,content):
        relative=Path(relative)
        if relative.is_absolute() or '..' in relative.parts or not relative.parts:
            raise ValueError("output reference must stay inside its new directory")
        if not isinstance(content,bytes):raise ValueError("outputs must be bytes snapshots")
        path=self.path/relative
        missing=[];parent=path.parent
        while not parent.exists():missing.append(parent);parent=parent.parent
        for directory in reversed(missing):directory.mkdir();self.directories.append(directory)
        with path.open('xb') as stream:
            self.files.append(path);stream.write(content)
    def __exit__(self,kind,value,traceback):
        if kind is not None:
            for path in reversed(self.files):path.unlink(missing_ok=True)
            for path in reversed(self.directories):
                try:path.rmdir()
                except OSError:pass
        return False


def publish_files(path,files):
    with FreshDirectory(path) as output:
        for name,content in files.items():output.write(name,content)


def _digest(value,name):
    if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError(f"{name} must be a lowercase SHA-256")


def validate_recipe(data):
    _fields(data,RECIPE_FIELDS,'ML recipe')
    constants=dict(recipe_version=1,dataset_version=2,feature_contract_version=FEATURE_CONTRACT_VERSION,
        generator_version=GENERATOR_VERSION,sampler_version=SAMPLER_VERSION,feature_profile='raw_pre_run_v1',
        prediction_mode='pre_run',feature_order=list(PRE_RUN_FEATURES),targets=list(TARGET_UNITS),
        selection_metric='validation_rmse',tie_break='training_mean_then_larger_alpha',refit_on_validation=False,
        missing_label_policy='exclude_per_target',preprocessing='train_standardize_population_std_constant_scale_1',
        solver='augmented_householder_qr_centered_target_v1')
    for name,value in constants.items():
        if _json_bytes(data[name])!=_json_bytes(value):raise ValueError(f"unsupported recipe {name}")
    _identifier(data['experiment_id'],'experiment_id')
    for name in ('parameters_sha256','assumptions_sha256'):_digest(data[name],name)
    for name in ('parameters_path','assumptions_path'):
        if not isinstance(data[name],str) or not data[name]:raise ValueError(f"invalid {name}")
    for name in ('master_seed','split_seed','cv_seed'):_integer(data[name],name,maximum=2**64-1)
    _integer(data['repetitions'],'repetitions',minimum=1,maximum=10000)
    _integer(data['max_attempts'],'max_attempts',minimum=1,maximum=16)
    _fields(data['axes'],{'payload_sizes_bytes','intervals_ms','window_durations_ms'},'axes')
    for name,levels in data['axes'].items():
        if not isinstance(levels,list) or not levels:raise ValueError(f"invalid {name}")
        for value in levels:_integer(value,name,minimum=1,maximum=3600000)
        if levels!=sorted(set(levels)):raise ValueError(f"{name} must be sorted unique levels")
    _fields(data['splits'],{'train','validation','test'},'splits')
    sets={}
    for split,groups in data['splits'].items():
        if not isinstance(groups,list) or not groups or any(not isinstance(g,str) for g in groups) or groups!=sorted(set(groups)):
            raise ValueError('split membership must be sorted unique nonempty groups')
        sets[split]=set(groups)
    if any(sets[a]&sets[b] for a,b in (('train','validation'),('train','test'),('validation','test'))):
        raise ValueError('family split leakage')
    folds=data['cv_folds']
    if not isinstance(folds,list) or len(folds)<2:raise ValueError('at least two grouped CV folds required')
    assessed=[]
    for fold in folds:
        _fields(fold,{'fit_groups','assessment_groups'},'CV fold')
        for groups in fold.values():
            if not isinstance(groups,list) or not groups or any(not isinstance(g,str) for g in groups) or groups!=sorted(set(groups)):
                raise ValueError('invalid CV membership')
        fit,assessment=set(fold['fit_groups']),set(fold['assessment_groups'])
        if fit&assessment or fit|assessment!=sets['train']:raise ValueError('CV family leakage')
        assessed+=fold['assessment_groups']
    if sorted(assessed)!=sorted(sets['train']):raise ValueError('CV must assess each training family once')
    alphas=data['ridge_alphas']
    if not isinstance(alphas,list) or not alphas:raise ValueError('ridge candidates required')
    for alpha in alphas:_number(alpha,'alpha',positive=True)
    if len(set(alphas))!=len(alphas):raise ValueError('duplicate ridge candidates')
    _integer(data['cv_shortlist'],'cv_shortlist',minimum=1,maximum=len(alphas))
    if not isinstance(data['stress_variants'],list) or not data['stress_variants']:raise ValueError('stress variants required')
    names=set()
    for variant in data['stress_variants']:
        _fields(variant,{'id','tx_per_byte_us'},'stress variant');_identifier(variant['id'],'variant id')
        _integer(variant['tx_per_byte_us'],'tx_per_byte_us',minimum=1)
        if variant['id']=='primary' or variant['id'] in names:raise ValueError('duplicate/reserved panel name')
        names.add(variant['id'])
    for name in ('primary_row_count','stress_row_count'):_integer(data[name],name,minimum=1)
    return copy.deepcopy(data)


def planned_specs(recipe,parameters):
    recipe=validate_recipe(recipe);model=validate_model(_json_from_bytes(parameters))
    if _sha256(parameters)!=recipe['parameters_sha256']:raise ValueError('parameter source hash mismatch')
    options={name:tuple(values) for name,values in recipe['axes'].items()}
    options.update(repetitions=recipe['repetitions'],master_seed=recipe['master_seed'],max_attempts=recipe['max_attempts'])
    primary=plan_workload_grid(model,**options)
    groups={r['evaluation_group_id'] for r in primary}
    if groups!=set().union(*(set(g) for g in recipe['splits'].values())):raise ValueError('recipe families do not match axes')
    expected_order=sorted(groups,key=lambda g:_sha256(f"week7-split-v1:{recipe['split_seed']}:{g}".encode()))
    offset=0
    for split in ('train','validation','test'):
        size=len(recipe['splits'][split])
        if sorted(expected_order[offset:offset+size])!=recipe['splits'][split]:raise ValueError('split seed/membership mismatch')
        offset+=size
    cv_order=sorted(recipe['splits']['train'],key=lambda g:_sha256(f"week7-cv-v1:{recipe['cv_seed']}:{g}".encode()))
    for i,fold in enumerate(recipe['cv_folds']):
        if sorted(cv_order[i::len(recipe['cv_folds'])])!=fold['assessment_groups']:raise ValueError('CV seed/membership mismatch')
    specs=[]
    for panel,param_bytes,runs in [('primary',parameters,primary)]:
        for run in runs:
            split=next(s for s,gs in recipe['splits'].items() if run['evaluation_group_id'] in gs)
            specs.append(dict(panel=panel,split=split,workload=run,parameters=param_bytes))
    for variant in recipe['stress_variants']:
        changed=copy.deepcopy(model);value=variant['tx_per_byte_us'];p=changed['timing_us']['tx_per_byte']
        if not p['min']<=value<=p['max']:raise ValueError('stress setting outside declared assumptions')
        p.update(value=value,basis='assumption',source_id=None)
        changed.update(model_version=model['model_version']+'-'+variant['id'],parameter_version=model['parameter_version']+'-'+variant['id'])
        runs=plan_workload_grid(changed,variant_id=variant['id'],**options)
        for run in runs:
            if run['evaluation_group_id'] in recipe['splits']['test']:
                specs.append(dict(panel=variant['id'],split='stress',workload=run,parameters=_json_bytes(changed)))
    if len(primary)!=recipe['primary_row_count'] or len(specs)-len(primary)!=recipe['stress_row_count']:
        raise ValueError('actual recipe counts mismatch')
    if len({s['workload']['run_id'] for s in specs})!=len(specs):raise ValueError('duplicate planned run')
    return sorted(specs,key=lambda s:s['workload']['run_id'])


def _entry(spec,root):
    run=spec['workload'];relative=f"bundles/{spec['panel']}/{run['run_id']}"
    return dict(run_id=run['run_id'],group_id=run['evaluation_group_id'],panel=spec['panel'],split=spec['split'],path=relative,
        csv_sha256=_sha256((root/relative/'dataset.csv').read_bytes()),
        manifest_sha256=_sha256((root/relative/'manifest.json').read_bytes()))


def materialize_dataset(recipe_path,output_path,*,progress=None):
    recipe_bytes=Path(recipe_path).read_bytes();recipe=validate_recipe(_json_from_bytes(recipe_bytes))
    params=Path(recipe['parameters_path']).read_bytes();assumptions=Path(recipe['assumptions_path']).read_bytes()
    if _sha256(assumptions)!=recipe['assumptions_sha256']:raise ValueError('assumption source hash mismatch')
    specs=planned_specs(recipe,params)
    with FreshDirectory(output_path) as output:
        for name,content in (('recipe.json',recipe_bytes),('parameters.json',params),('assumptions.md',assumptions)):output.write(name,content)
        entries=[]
        for index,spec in enumerate(specs):
            run=spec['workload'];context=dict(available_fields=list(PRE_RUN_FEATURES),planned_window_duration_ms=run['window_duration_ms'],completed_as_planned=True)
            files=generate_analytical_artifact(spec['parameters'],_json_bytes(run),assumptions,prediction_context_bytes=_json_bytes(context))
            relative=f"bundles/{spec['panel']}/{run['run_id']}"
            for name,content in files.items():output.write(f'{relative}/{name}',content)
            entries.append(_entry(spec,output.path))
            if progress is not None and (index+1)%90==0:progress(f'Generated {index+1}/{len(specs)} bundles')
        inventory=dict(inventory_version=1,recipe_sha256=_sha256(recipe_bytes),entries=entries)
        inventory['dataset_sha256']=_sha256(_json_bytes(inventory))
        output.write('inventory.json',_json_bytes(inventory))
        # Full source/replay/plan checks; no fitting or held-out scoring.
        loaded=load_dataset(output.path,progress=progress)
        for name,content in table_files(loaded['records']).items():output.write(name,content)
        output.write('audit.json',_json_bytes(loaded['audit']))
    return loaded['audit']


def load_dataset(directory,*,progress=None):
    root=Path(directory).resolve();recipe_bytes=(root/'recipe.json').read_bytes()
    recipe=validate_recipe(_json_from_bytes(recipe_bytes));parameters=(root/'parameters.json').read_bytes()
    if _sha256((root/'assumptions.md').read_bytes())!=recipe['assumptions_sha256']:raise ValueError('archived assumptions mismatch')
    specs=planned_specs(recipe,parameters);inventory=_json_from_bytes((root/'inventory.json').read_bytes())
    _fields(inventory,{'inventory_version','recipe_sha256','entries','dataset_sha256'},'inventory')
    if type(inventory['inventory_version']) is not int or inventory['inventory_version']!=1:raise ValueError('inventory version mismatch')
    if inventory['recipe_sha256']!=_sha256(recipe_bytes):raise ValueError('recipe digest mismatch')
    expected_digest=_sha256(_json_bytes({k:v for k,v in inventory.items() if k!='dataset_sha256'}))
    if inventory['dataset_sha256']!=expected_digest:raise ValueError('dataset digest mismatch')
    if not isinstance(inventory['entries'],list) or len(inventory['entries'])!=len(specs):raise ValueError('inventory count mismatch')
    records=[];seed_groups={}
    for index,(entry,spec) in enumerate(zip(inventory['entries'],specs)):
        expected=_entry(spec,root)
        if _json_bytes(entry)!=_json_bytes(expected):raise ValueError('inventory/source/split identity mismatch')
        directory=root/entry['path'];record=load_design_record(directory)
        if _json_bytes(record['workload'])!=_json_bytes(spec['workload']):raise ValueError('workload differs from frozen plan')
        if record['parameter_sha256']!=_sha256(spec['parameters']) or record['assumption_sha256']!=recipe['assumptions_sha256']:
            raise ValueError('analytical source scope mismatch')
        if record['manifest']['selected_features']['pre_run']!=list(PRE_RUN_FEATURES):raise ValueError('pre-run capabilities unavailable')
        group=record['row']['evaluation_group_id'];seed=record['row']['seed']
        if seed in seed_groups and seed_groups[seed]!=group:raise ValueError('cross-family seed leakage')
        seed_groups[seed]=group
        record.update(panel=entry['panel'],split=entry['split'],entry=entry);records.append(record)
        if progress is not None and (index+1)%90==0:progress(f'Audited {index+1}/{len(specs)} bundles')
    counts={s:sum(r['split']==s for r in records) for s in ('train','validation','test','stress')}
    audit=dict(audit_version=1,dataset_sha256=expected_digest,recipe_sha256=_sha256(recipe_bytes),
        row_count=len(records),primary_rows=recipe['primary_row_count'],stress_rows=recipe['stress_row_count'],
        partition_counts=counts,group_counts={s:len({r['row']['evaluation_group_id'] for r in records if r['split']==s}) for s in counts},
        provenance='analytical_simulation',all_source_replays_passed=True)
    return dict(recipe=recipe,recipe_sha256=_sha256(recipe_bytes),dataset_sha256=expected_digest,records=records,audit=audit)



def table_files(records):
    """Convenience tables; the source bundle inventory remains authoritative."""
    import csv
    import io
    from dataset_builder import DATASET_FIELDS_V2
    from dataset_table import build_dataset_table
    files={}
    for panel in sorted({r['panel'] for r in records}):
        artifacts=[dict(row=r['row'],manifest=r['manifest'],csv_sha256=r['entry']['csv_sha256'],
                        manifest_sha256=r['entry']['manifest_sha256']) for r in records if r['panel']==panel]
        rows,manifest=build_dataset_table(artifacts,schema_version=2,measurement_status='analytical_simulation')
        stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=DATASET_FIELDS_V2,lineterminator='\n')
        writer.writeheader();writer.writerows(rows);content=stream.getvalue().encode('utf-8')
        manifest['table_sha256']=_sha256(content)
        files[f'{panel}-table.csv']=content;files[f'{panel}-table.json']=_json_bytes(manifest)
    return files
