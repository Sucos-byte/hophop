# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Deterministic stdlib regression, train-only preprocessing and strict prediction."""

import copy
import math
import platform

from analytical_reference import _fields,_integer,_number,_json_bytes,_sha256
from dataset_builder import _json_from_bytes
from dataset_table import validate_dataset_row,_validate_manifest
from feature_contract import PRE_RUN_FEATURES,FEATURE_CONTRACT_VERSION,extract_features
from ml_dataset import TARGET_UNITS,_digest,validate_recipe

PIPELINE_VERSION=1
SOLVER='augmented_householder_qr_centered_target_v1'
ESTIMATOR_FIELDS={'kind','alpha','solver','feature_means','feature_scales','constant_features','intercept','coefficients','training_sample_count'}
MODEL_FIELDS={'model_artifact_version','pipeline_version','dataset_version','feature_contract_version',
    'feature_profile','prediction_mode','feature_order','target','unit','provenance','estimator','scope','training'}
SCOPE_FIELDS={'source_kind','execution_kind','measurement_status','adapter','feature_profile_id','analytical_model_id',
              'primary_parameters_sha256','stress_parameters_sha256','assumptions_sha256'}
TRAINING_FIELDS={'recipe_sha256','dataset_sha256','split_sha256','experiment_id','split_membership',
    'train_run_ids','train_group_ids','seeds','fit_partition','python_version','dependencies','preprocessing','objective'}


def finite(value,name):
    _number(value,name,minimum=-math.inf)
    return value


def _vector(values,name,length=4):
    if not isinstance(values,list) or len(values)!=length:raise ValueError(f'{name} must have {length} numeric values')
    for value in values:finite(value,name)
    return values


def _matrix(X):
    if not isinstance(X,list):raise ValueError('X must be a list of feature rows')
    for row in X:_vector(row,'X row')


def validate_estimator(state):
    _fields(state,ESTIMATOR_FIELDS,'estimator')
    if state['kind'] not in ('training_mean','ridge'):raise ValueError('unsupported estimator kind')
    if state['kind']=='ridge':
        _number(state['alpha'],'alpha',positive=True)
        if state['solver']!=SOLVER:raise ValueError('unsupported solver')
    elif state['alpha'] is not None or state['solver']!='training_mean_v1':raise ValueError('invalid mean baseline settings')
    for name in ('feature_means','feature_scales','coefficients'):_vector(state[name],name)
    if any(s<=0 for s in state['feature_scales']):raise ValueError('scales must be positive')
    _integer(state['training_sample_count'],'training_sample_count',minimum=1)
    finite(state['intercept'],'intercept')
    indices=state['constant_features']
    if not isinstance(indices,list) or any(type(i) is not int or not 0<=i<4 for i in indices) or indices!=sorted(set(indices)):
        raise ValueError('invalid constant feature indices')
    for index in indices:
        if state['feature_scales'][index]!=1 or state['coefficients'][index]!=0:raise ValueError('constant features must have scale1/coefficient0')
    if state['kind']=='training_mean' and any(state['coefficients']):raise ValueError('mean baseline coefficients must be zero')
    return copy.deepcopy(state)


def _qr_solve(A,b):
    """Householder QR least squares; augmented ridge rows guarantee full rank."""
    A=[row[:] for row in A];b=b[:];m=len(A);p=4
    for k in range(p):
        norm=math.hypot(*(A[i][k] for i in range(k,m)))
        if not math.isfinite(norm) or norm==0:raise ValueError('QR rank/numeric failure')
        diagonal=-math.copysign(norm,A[k][k]);v=[A[i][k] for i in range(k,m)];v[0]-=diagonal
        length=math.hypot(*v)
        v=[value/length for value in v]
        for j in range(k,p):
            dot=2*math.fsum(v[i-k]*A[i][j] for i in range(k,m))
            for i in range(k,m):A[i][j]-=dot*v[i-k]
        dot=2*math.fsum(v[i-k]*b[i] for i in range(k,m))
        for i in range(k,m):b[i]-=dot*v[i-k]
        A[k][k]=diagonal
        for i in range(k+1,m):A[i][k]=0.0
    coefficients=[0.0]*p
    for i in reversed(range(p)):
        coefficients[i]=(b[i]-math.fsum(A[i][j]*coefficients[j] for j in range(i+1,p)))/A[i][i]
        finite(coefficients[i],'QR coefficient')
    return coefficients


def fit_regressor(X,y,*,kind='ridge',alpha=1.0):
    _matrix(X)
    if not X or not isinstance(y,list) or len(y)!=len(X):raise ValueError('nonempty aligned X/y required')
    for value in y:finite(value,'training label')
    if kind not in ('training_mean','ridge'):raise ValueError('unsupported estimator kind')
    if kind=='ridge':_number(alpha,'alpha',positive=True)
    n=len(X);means=[math.fsum(row[j]/n for row in X) for j in range(4)]
    scales=[];constant=[]
    for j in range(4):
        if all(row[j]==X[0][j] for row in X):
            means[j]=X[0][j];scales.append(1.0);constant.append(j);continue
        scale=math.hypot(*((row[j]-means[j])/math.sqrt(n) for row in X))
        finite(scale,'training scale')
        if scale==0:raise ValueError('nonconstant feature variance underflow')
        scales.append(scale)
    intercept=math.fsum(value/n for value in y);finite(intercept,'training mean')
    coefficients=[0.0]*4
    try:
        if kind=='ridge':
            A=[[(row[j]-means[j])/scales[j] for j in range(4)] for row in X]
            b=[value-intercept for value in y]
            for i in range(4):A.append([math.sqrt(alpha) if j==i else 0.0 for j in range(4)]);b.append(0.0)
            for row in A:
                for value in row:finite(value,'standardized X')
            for value in b:finite(value,'centered target')
            coefficients=_qr_solve(A,b)
            for index in constant:coefficients[index]=0.0
    except (OverflowError,ZeroDivisionError) as error:raise ValueError('regression numeric overflow') from error
    return validate_estimator(dict(kind=kind,alpha=alpha if kind=='ridge' else None,
        solver=SOLVER if kind=='ridge' else 'training_mean_v1',feature_means=means,feature_scales=scales,
        constant_features=constant,intercept=intercept,coefficients=coefficients,training_sample_count=n))


def predict_matrix(estimator,X):
    estimator=validate_estimator(estimator);_matrix(X);predictions=[]
    try:
        for row in X:
            prediction=estimator['intercept']+math.fsum(estimator['coefficients'][j]*(row[j]-estimator['feature_means'][j])/estimator['feature_scales'][j] for j in range(4))
            finite(prediction,'prediction');predictions.append(prediction)
    except (OverflowError,ZeroDivisionError) as error:raise ValueError('prediction numeric overflow') from error
    return predictions


def metrics(truth,predictions):
    if not isinstance(truth,list) or not isinstance(predictions,list) or len(truth)!=len(predictions):raise ValueError('metrics need aligned vectors')
    for value in truth+predictions:finite(value,'metric input')
    n=len(truth)
    if not n:return dict(sample_count=0,mae=None,rmse=None,r2=None,r2_undefined_reason='no_labels')
    try:
        errors=[prediction-value for prediction,value in zip(predictions,truth)]
        for error in errors:finite(error,'prediction residual')
        mae=math.fsum(abs(error)/n for error in errors)
        rmse=math.hypot(*(error/math.sqrt(n) for error in errors))
        reason=None;r2=None
        if n<2:reason='fewer_than_two_labels'
        elif all(value==truth[0] for value in truth):reason='constant_truth'
        else:
            mean=math.fsum(value/n for value in truth)
            spread=math.hypot(*((value-mean)/math.sqrt(n) for value in truth))
            if spread==0:reason='constant_truth'
            else:r2=1-(rmse/spread)**2;finite(r2,'R2')
        finite(mae,'MAE');finite(rmse,'RMSE')
    except OverflowError as error:raise ValueError('metric numeric overflow') from error
    return dict(sample_count=n,mae=mae,rmse=rmse,r2=r2,r2_undefined_reason=reason)


def record_features(record,*,scope=None,domain='primary'):
    if not isinstance(record,dict) or 'row' not in record or 'manifest' not in record:raise ValueError('validated analytical record required')
    row=validate_dataset_row(record['row'],schema_version=2);manifest=_validate_manifest(row,record['manifest'])
    if (row['source_kind'],row['execution_kind'],row['measurement_status'])!=('synthetic','simulation','analytical_simulation'):
        raise ValueError('regression scope is analytical_simulation only')
    if manifest['selected_features']['pre_run']!=list(PRE_RUN_FEATURES):raise ValueError('pre-run capabilities unavailable')
    if scope is not None:
        for name in ('source_kind','execution_kind','measurement_status','adapter','feature_profile_id','analytical_model_id'):
            if row[name]!=scope[name]:raise ValueError(f'incompatible prediction {name}')
        allowed=[scope['primary_parameters_sha256']] if domain=='primary' else scope['stress_parameters_sha256'] if domain=='declared_stress' else []
        if record.get('parameter_sha256') not in allowed or record.get('assumption_sha256')!=scope['assumptions_sha256']:
            raise ValueError('prediction parameter/assumption scope mismatch')
    context={name:manifest['prediction_context'][name] for name in ('planned_window_duration_ms','completed_as_planned')}
    values=extract_features(row,prediction_mode='pre_run',available_fields=frozenset(manifest['available_fields']),prediction_context=context)
    return [values[name] for name in PRE_RUN_FEATURES]


def prepare_target(records,target):
    if not isinstance(target,str) or target not in TARGET_UNITS:raise ValueError('unsupported energy target')
    X=[];y=[];used=[];missing=[];seen=set()
    for record in records:
        features=record_features(record)  # Invalid X cannot hide behind a missing label.
        row=record['row']
        if row['run_id'] in seen:raise ValueError('duplicate training/evaluation run')
        seen.add(row['run_id']);value=row[target]
        if value is None:missing.append(row['run_id']);continue
        finite(value,target);X.append(features);y.append(value);used.append(record)
    return X,y,used,sorted(missing)


def evaluate_estimator(estimator,records,target,*,scope=None,domain='primary'):
    predictions=[];truth=[];scores=[];families={};missing=[]
    for record in records:
        features=record_features(record,scope=scope,domain=domain)
        prediction=predict_matrix(estimator,[features])[0];row=record['row'];value=row[target]
        predictions.append(dict(run_id=row['run_id'],group_id=row['evaluation_group_id'],target=target,
                                truth=value,prediction=prediction,provenance='analytical_simulation'))
        pair=families.setdefault(row['evaluation_group_id'],([],[]))
        if value is None:missing.append(row['run_id']);continue
        finite(value,target);truth.append(value);scores.append(prediction)
        pair[0].append(value);pair[1].append(prediction)
    summary=metrics(truth,scores)
    summary.update(total_rows=len(records),labeled_group_count=sum(bool(pair[0]) for pair in families.values()),
        total_group_count=len({r['row']['evaluation_group_id'] for r in records}),missing_label_count=len(missing),
        missing_label_run_ids=sorted(missing),negative_prediction_count=sum(p['prediction']<0 for p in predictions),
        unit=TARGET_UNITS[target],per_family={g:metrics(*pair) for g,pair in sorted(families.items())})
    return summary,predictions


def validate_model_artifact(artifact):
    _fields(artifact,MODEL_FIELDS,'model artifact')
    fixed=dict(model_artifact_version=1,pipeline_version=PIPELINE_VERSION,dataset_version=2,
        feature_contract_version=FEATURE_CONTRACT_VERSION,feature_profile='raw_pre_run_v1',prediction_mode='pre_run',
        feature_order=list(PRE_RUN_FEATURES),provenance='analytical_simulation')
    for name,value in fixed.items():
        if _json_bytes(artifact[name])!=_json_bytes(value):raise ValueError(f'incompatible model {name}')
    if not isinstance(artifact['target'],str) or artifact['target'] not in TARGET_UNITS or artifact['unit']!=TARGET_UNITS[artifact['target']]:raise ValueError('target/unit mismatch')
    validate_estimator(artifact['estimator']);scope=artifact['scope'];training=artifact['training']
    _fields(scope,SCOPE_FIELDS,'model scope');_fields(training,TRAINING_FIELDS,'model training metadata')
    if (scope['source_kind'],scope['execution_kind'],scope['measurement_status'])!=('synthetic','simulation','analytical_simulation'):raise ValueError('invalid model provenance')
    for name in ('adapter','feature_profile_id','analytical_model_id'):
        if not isinstance(scope[name],str) or not scope[name]:raise ValueError('invalid scope identifier')
    for name in ('primary_parameters_sha256','assumptions_sha256'):_digest(scope[name],name)
    if not isinstance(scope['stress_parameters_sha256'],list) or any(not isinstance(v,str) for v in scope['stress_parameters_sha256']) or scope['stress_parameters_sha256']!=sorted(set(scope['stress_parameters_sha256'])):raise ValueError('invalid stress scope')
    for value in scope['stress_parameters_sha256']:_digest(value,'stress hash')
    if scope['primary_parameters_sha256'] in scope['stress_parameters_sha256']:raise ValueError('primary scope cannot masquerade as stress')
    for name in ('recipe_sha256','dataset_sha256','split_sha256'):_digest(training[name],name)
    _fields(training['split_membership'],{'train','validation','test'},'model split metadata')
    memberships={}
    for split,groups in training['split_membership'].items():
        if not isinstance(groups,list) or any(not isinstance(g,str) for g in groups) or groups!=sorted(set(groups)):raise ValueError('invalid split groups')
        memberships[split]=set(groups)
    if any(memberships[a]&memberships[b] for a,b in (('train','validation'),('train','test'),('validation','test'))):raise ValueError('model split leakage')
    if _sha256(_json_bytes(training['split_membership']))!=training['split_sha256']:raise ValueError('split metadata hash mismatch')
    for name in ('train_run_ids','train_group_ids'):
        values=training[name]
        if not isinstance(values,list) or not values or any(not isinstance(v,str) for v in values) or values!=sorted(set(values)):raise ValueError(f'invalid {name}')
    if not set(training['train_group_ids'])<=memberships['train']:raise ValueError('model fit includes held-out groups')
    if len(training['train_run_ids'])!=artifact['estimator']['training_sample_count']:raise ValueError('model training count mismatch')
    _fields(training['seeds'],{'master_seed','split_seed','cv_seed'},'seeds')
    for name,value in training['seeds'].items():_integer(value,name,maximum=2**64-1)
    if training['fit_partition']!='train' or training['dependencies']!={'runtime':'stdlib','optional':{}}:raise ValueError('unsupported model runtime/fit partition')
    if not isinstance(training['python_version'],str) or not isinstance(training['experiment_id'],str):raise ValueError('invalid runtime/experiment metadata')
    if training['preprocessing']!='train_standardize_population_std_constant_scale_1' or training['objective']!='sum_squared_residuals_plus_alpha_beta_squared_intercept_unpenalized':raise ValueError('unsupported model training policy')
    return copy.deepcopy(artifact)


def package_model(estimator,target,dataset,training_records):
    recipe=validate_recipe(dataset['recipe']);scope_record=next(r for r in training_records)
    _,_,used,_=prepare_target(training_records,target)
    artifact=dict(model_artifact_version=1,pipeline_version=PIPELINE_VERSION,dataset_version=2,
        feature_contract_version=FEATURE_CONTRACT_VERSION,feature_profile=recipe['feature_profile'],prediction_mode='pre_run',
        feature_order=list(PRE_RUN_FEATURES),target=target,unit=TARGET_UNITS[target],provenance='analytical_simulation',estimator=estimator,
        scope={**{name:scope_record['row'][name] for name in ('source_kind','execution_kind','measurement_status','adapter','feature_profile_id','analytical_model_id')},
               'primary_parameters_sha256':recipe['parameters_sha256'],
               'stress_parameters_sha256':sorted({r['parameter_sha256'] for r in dataset['records'] if r['split']=='stress'}),
               'assumptions_sha256':recipe['assumptions_sha256']},
        training=dict(recipe_sha256=dataset['recipe_sha256'],dataset_sha256=dataset['dataset_sha256'],
            split_sha256=_sha256(_json_bytes(recipe['splits'])),experiment_id=recipe['experiment_id'],split_membership=recipe['splits'],
            train_run_ids=sorted(r['row']['run_id'] for r in used),train_group_ids=sorted({r['row']['evaluation_group_id'] for r in used}),
            seeds={k:recipe[k] for k in ('master_seed','split_seed','cv_seed')},fit_partition='train',python_version=platform.python_version(),
            dependencies={'runtime':'stdlib','optional':{}},preprocessing=recipe['preprocessing'],
            objective='sum_squared_residuals_plus_alpha_beta_squared_intercept_unpenalized'))
    return validate_model_artifact(artifact)


def model_to_bytes(artifact):return _json_bytes(validate_model_artifact(artifact))
def model_from_bytes(content):return validate_model_artifact(_json_from_bytes(content))

def predict_record(artifact,record,*,domain='primary'):
    artifact=validate_model_artifact(artifact)
    X=record_features(record,scope=artifact['scope'],domain=domain)
    return predict_matrix(artifact['estimator'],[X])[0]
