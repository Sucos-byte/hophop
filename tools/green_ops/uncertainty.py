# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Family-max split calibration: prediction intervals, never metric confidence intervals."""
import math
import copy
from analytical_reference import _fields,_integer,_json_bytes,_sha256
from dataset_builder import _json_from_bytes
from ml_dataset import _digest,TARGET_UNITS
from ml_pipeline import finite,predict_record
from week8_dataset import recipe_from_bytes,DATASET_SHA256

CAL_FIELDS={'calibration_version','provenance','target','unit','model_sha256','dataset_sha256','recipe_sha256',
 'original_recipe_sha256','feature_contract_version','feature_order','split_sha256','lineage_sha256','method',
 'calibration_groups','family_scores','missing_label_run_ids','excluded_families','rank','q','coverage_numerator','coverage_denominator'}


def finite_sample_quantile(scores,numerator=19,denominator=20):
    if type(numerator) is not int or type(denominator) is not int or not 0<numerator<denominator:raise ValueError('invalid coverage fraction')
    if not isinstance(scores,list):raise ValueError('scores must be a list')
    for value in scores:
        finite(value,'nonconformity score')
        if value<0:raise ValueError('negative nonconformity score')
    n=len(scores);rank=((n+1)*numerator+denominator-1)//denominator
    if not n or rank>n:raise ValueError('insufficient calibration families for finite quantile')
    return rank,sorted(scores)[rank-1]


def score_families(rows):
    """Rows contain explicit group/truth/prediction; null truth never becomes zero."""
    families={};missing=[];seen=set()
    for row in rows:
        if row['run_id'] in seen:raise ValueError('duplicate calibration run')
        seen.add(row['run_id']);finite(row['prediction'],'prediction')
        values=families.setdefault(row['group_id'],[])
        if row['truth'] is None:missing.append(row['run_id']);continue
        finite(row['truth'],'truth');score=abs(row['truth']-row['prediction']);finite(score,'residual');values.append(score)
    return {g:max(v) for g,v in sorted(families.items()) if v},sorted(missing),sorted(g for g,v in families.items() if not v)


def calibration_from_bytes(content):
    return validate_calibration(_json_from_bytes(content))


def validate_calibration(artifact):
    _fields(artifact,CAL_FIELDS,'calibration')
    for key,value in dict(calibration_version=1,provenance='analytical_simulation',feature_contract_version=3,
        method='family_max_absolute_residual',coverage_numerator=19,coverage_denominator=20).items():
        if _json_bytes(artifact[key])!=_json_bytes(value):raise ValueError(f'unsupported calibration {key}')
    from feature_contract import PRE_RUN_FEATURES
    if artifact['feature_order']!=list(PRE_RUN_FEATURES):raise ValueError('calibration feature order mismatch')
    if artifact['target'] not in TARGET_UNITS or artifact['unit']!=TARGET_UNITS[artifact['target']]:raise ValueError('calibration target/unit mismatch')
    for key in ('model_sha256','dataset_sha256','recipe_sha256','original_recipe_sha256','split_sha256','lineage_sha256'):_digest(artifact[key],key)
    for key in ('calibration_groups','missing_label_run_ids','excluded_families'):
        v=artifact[key]
        if not isinstance(v,list) or any(not isinstance(s,str) or not s for s in v) or v!=sorted(set(v)):raise ValueError(f'invalid {key}')
    scores=artifact['family_scores']
    if not isinstance(scores,dict) or sorted(scores)!=sorted(set(artifact['calibration_groups'])-set(artifact['excluded_families'])):raise ValueError('family score membership mismatch')
    if not set(artifact['excluded_families'])<=set(artifact['calibration_groups']):raise ValueError('invalid excluded families')
    rank,q=finite_sample_quantile(list(scores.values()))
    if type(artifact['rank']) is not int or artifact['rank']!=rank:raise ValueError('quantile rank mismatch')
    finite(artifact['q'],'q')
    if artifact['q']!=q:raise ValueError('quantile value mismatch')
    return copy.deepcopy(artifact)


def calibrate(dataset,models,original_recipe_bytes):
    """Only calibration record labels are accessed; selection/training is impossible here."""
    recipe=dataset['recipe'];records=[r for r in dataset['records'] if r['split']=='calibration' and r['panel']=='primary']
    if len(records)!=450 or {r['family'] for r in records}!=set(recipe['splits']['calibration']):raise ValueError('incomplete calibration schedule')
    files={}
    for target,model in models.items():
        rows=[dict(run_id=r['row']['run_id'],group_id=r['family'],truth=r['row'][target],
                   prediction=predict_record(model,r,recipe_bytes=original_recipe_bytes)) for r in records]
        scores,missing,excluded=score_families(rows);rank,q=finite_sample_quantile(list(scores.values()))
        artifact=dict(calibration_version=1,provenance='analytical_simulation',target=target,unit=TARGET_UNITS[target],
            model_sha256=recipe['model_sha256'][target],dataset_sha256=dataset['dataset_sha256'],recipe_sha256=dataset['recipe_sha256'],
            original_recipe_sha256=recipe['original_recipe_sha256'],feature_contract_version=3,feature_order=recipe['feature_order'],
            split_sha256=_sha256(_json_bytes(recipe['splits'])),lineage_sha256=recipe['lineage_sha256'],method='family_max_absolute_residual',
            calibration_groups=recipe['splits']['calibration'],family_scores=scores,missing_label_run_ids=missing,excluded_families=excluded,
            rank=rank,q=q,coverage_numerator=19,coverage_denominator=20)
        files[f'{target}-calibration.json']=_json_bytes(validate_calibration(artifact))
    return files


def validate_binding(calibration,model,study_recipe_bytes,*,dataset_sha256=None):
    c=validate_calibration(calibration);r=recipe_from_bytes(study_recipe_bytes);target=model['target']
    expected=dict(target=target,model_sha256=_sha256(_json_bytes(model)),recipe_sha256=_sha256(study_recipe_bytes),
        original_recipe_sha256=model['training']['recipe_sha256'],split_sha256=_sha256(_json_bytes(r['splits'])),
        lineage_sha256=r['lineage_sha256'],calibration_groups=r['splits']['calibration'])
    if dataset_sha256 is not None and dataset_sha256!=DATASET_SHA256:raise ValueError('unsupported calibration dataset')
    expected['dataset_sha256']=DATASET_SHA256
    for key,value in expected.items():
        if c[key]!=value:raise ValueError(f'calibration compatibility mismatch: {key}')
    if c['model_sha256']!=r['model_sha256'][target]:raise ValueError('model not frozen in study')
    return c,r


def interval_bounds(prediction,q):
    finite(prediction,'prediction');finite(q,'q')
    if q<0:raise ValueError('negative interval width')
    lower=prediction-q;upper=prediction+q
    finite(lower,'lower bound');finite(upper,'upper bound')
    return lower,upper


def predict_interval(model,record,calibration,*,original_recipe_bytes,study_recipe_bytes,dataset_sha256=None,domain='primary'):
    c,r=validate_binding(calibration,model,study_recipe_bytes,dataset_sha256=dataset_sha256)
    from analytical_design import configuration_family
    group=configuration_family(record['workload'])
    if group not in r['splits']['evaluation']:raise ValueError('interval requires a declared fresh evaluation family')
    run=record['workload']
    if (run['window_duration_ms'] not in r['axes']['window_durations_ms'] or run['repetition'] not in range(1,r['repetitions']+1)
            or record['row']['evaluation_group_id']!=group):raise ValueError('interval schedule mismatch')
    expected_seed=int.from_bytes(bytes.fromhex(_sha256(f"analytical-design-v1:{r['master_seed']}:{group}:{run['repetition']}".encode()))[:8],'big')
    variants=['nominal'] if domain=='primary' else [v['id'] for v in r['stress_variants']]
    expected_ids={'ar-'+_sha256(_json_bytes(dict(family=group,repetition=run['repetition'],duration_ms=run['window_duration_ms'],
        variant_id=v,master_seed=r['master_seed'],max_attempts=r['max_attempts'])))[:32] for v in variants}
    if run['seed']!=expected_seed or run['run_id'] not in expected_ids:raise ValueError('interval schedule seed/run identity mismatch')
    prediction=predict_record(model,record,recipe_bytes=original_recipe_bytes,domain=domain)
    lower,upper=interval_bounds(prediction,c['q'])
    return dict(prediction=prediction,lower=lower,upper=upper,unit=c['unit'],nominal_coverage=0.95,
        coverage_unit='all_labeled_rows_in_new_family_same_15_row_schedule',assumption_shift=domain!='primary',
        provenance='analytical_simulation')


def coverage_report(rows,q):
    interval_bounds(0,q);families={};missing=[];widths=[]
    for row in rows:
        lower,upper=interval_bounds(row['prediction'],q);widths.append(upper-lower)
        group=families.setdefault(row['group_id'],dict(labeled_rows=0,failed_run_ids=[]))
        if row['truth'] is None:missing.append(row['run_id']);continue
        finite(row['truth'],'truth');group['labeled_rows']+=1
        if not lower<=row['truth']<=upper:group['failed_run_ids'].append(row['run_id'])
    labeled=sum(v['labeled_rows'] for v in families.values());failed=sum(len(v['failed_run_ids']) for v in families.values())
    used=[v for v in families.values() if v['labeled_rows']]
    for value in families.values():
        value['failed_run_ids'].sort();value['covered']=not value['failed_run_ids'] if value['labeled_rows'] else None
    return dict(row_count=len(rows),labeled_rows=labeled,missing_label_run_ids=sorted(missing),row_coverage=(labeled-failed)/labeled if labeled else None,
        family_count=len(families),labeled_families=len(used),family_coverage=sum(v['covered'] for v in used)/len(used) if used else None,
        mean_width=math.fsum(v/len(widths) for v in widths) if widths else None,
        failed_families=sorted(g for g,v in families.items() if v['covered'] is False),per_family=dict(sorted(families.items())))
