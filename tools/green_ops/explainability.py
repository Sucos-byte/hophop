# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Frozen-model sensitivity diagnostics; no physical causality or model selection."""
import math
from analytical_reference import _fields,_json_bytes,_sha256
from dataset_builder import _json_from_bytes
from feature_contract import PRE_RUN_FEATURES
from ml_dataset import _digest,TARGET_UNITS
from ml_pipeline import (validate_estimator,finite,predict_matrix,record_features,prepare_target,
                         fit_regressor,metrics)

FEATURES=list(PRE_RUN_FEATURES)


def signed_contributions(estimator,X):
    estimator=validate_estimator(estimator);predictions=predict_matrix(estimator,X);rows=[]
    for x,prediction in zip(X,predictions):
        contributions=[estimator['coefficients'][j]*(x[j]-estimator['feature_means'][j])/estimator['feature_scales'][j] for j in range(4)]
        for c in contributions:finite(c,'contribution')
        top=sorted(range(4),key=lambda j:(-abs(contributions[j]),j))[:3]
        rows.append(dict(baseline=estimator['intercept'],prediction=prediction,contributions=dict(zip(FEATURES,contributions)),
                         top_three=[FEATURES[j] for j in top]))
    return rows


def _masked(X,drop):return [[0.0 if j==drop else v for j,v in enumerate(row)] for row in X]


def fit_ablations(original_dataset,models):
    """Read only original training labels; fixed selected alpha, no selection."""
    records=sorted((r for r in original_dataset['records'] if r['split']=='train'),key=lambda r:r['row']['run_id'])
    result={}
    for target,model in models.items():
        X,y,used,missing=prepare_target(records,target)
        result[target]={}
        for j,name in enumerate(FEATURES):
            state=fit_regressor(_masked(X,j),y,kind=model['estimator']['kind'],alpha=model['estimator']['alpha'])
            result[target][name]=dict(dropped_feature=name,estimator=state,fit_run_ids=sorted(r['row']['run_id'] for r in used),
                missing_label_run_ids=missing)
    return result


def validate_ablations(result,models):
    _fields(result,TARGET_UNITS,'ablation targets')
    for target,features in result.items():
        _fields(features,FEATURES,'ablation features')
        for j,name in enumerate(FEATURES):
            item=features[name];_fields(item,{'dropped_feature','estimator','fit_run_ids','missing_label_run_ids'},'ablation')
            state=validate_estimator(item['estimator']);original=models[target]
            if (item['dropped_feature']!=name or state['kind']!=original['estimator']['kind'] or state['alpha']!=original['estimator']['alpha']
                or item['fit_run_ids']!=original['training']['train_run_ids'] or state['training_sample_count']!=len(item['fit_run_ids'])
                or j not in state['constant_features'] or state['feature_means'][j]!=0):raise ValueError('ablation training/settings mismatch')
            if item['missing_label_run_ids']!=sorted(set(item['missing_label_run_ids'])):raise ValueError('invalid ablation missing labels')
    return result


def evaluate_ablations(ablations,models,records):
    validate_ablations(ablations,models);result={}
    for target in models:
        X,y,_,missing=prepare_target(records,target)
        reference=metrics(y,predict_matrix(models[target]['estimator'],X))
        comparisons={}
        for j,name in enumerate(FEATURES):
            score=metrics(y,predict_matrix(ablations[target][name]['estimator'],_masked(X,j)))
            comparisons[name]=dict(scores=score,rmse_minus_frozen=score['rmse']-reference['rmse'] if y else None)
        result[target]=dict(unit=TARGET_UNITS[target],frozen=reference,missing_label_run_ids=missing,ablations=comparisons)
    return result


def permuted_features(records,indices,*,seed,repeat,axes):
    """Whole repetition blocks shuffled among families separately per duration."""
    if not isinstance(indices,list) or not indices or any(type(j) is not int or j not in range(4) for j in indices):raise ValueError('invalid feature indices')
    if type(seed) is not int or type(repeat) is not int or seed<0 or repeat<0:raise ValueError('invalid permutation seed/repeat')
    slots={};X=[]
    for i,record in enumerate(records):
        run=record['workload'];key=(record['family'],run['window_duration_ms'],run['repetition'])
        if key in slots:raise ValueError('duplicate permutation slot')
        slots[key]=i;X.append(record_features(record))
    groups=sorted({k[0] for k in slots});durations=sorted({k[1] for k in slots});repetitions=sorted({k[2] for k in slots})
    if len(slots)!=len(groups)*len(durations)*len(repetitions):raise ValueError('incomplete permutation blocks')
    permuted=[row[:] for row in X]
    for duration in durations:
        donors=sorted(groups,key=lambda g:_sha256(f'week8-permute-v1:{seed}:{repeat}:{indices}:{duration}:{g}'.encode()))
        for recipient,donor in zip(groups,donors):
            for repetition in repetitions:
                i=slots[recipient,duration,repetition];source=X[slots[donor,duration,repetition]]
                for j in indices:permuted[i][j]=source[j]
    for row in permuted:
        if (row[0] not in axes['payload_sizes_bytes'] or row[1] not in axes['intervals_ms'] or row[2]!=19
                or row[3] not in axes['window_durations_ms'] or row[3]//row[1]<1):raise ValueError('invalid counterfactual combination')
    return permuted


def permutation_importance(estimator,records,target,recipe):
    """Use all records as donor blocks, score only available target labels."""
    settings=recipe['explainability'];X=[record_features(r) for r in records]
    used=[i for i,r in enumerate(records) if r['row'][target] is not None]
    y=[records[i]['row'][target] for i in used]
    original_predictions=predict_matrix(estimator,X)
    baseline=metrics(y,[original_predictions[i] for i in used])['rmse']
    if baseline is None:raise ValueError('no permutation assessment labels')
    tests=[([j],name) for j,name in enumerate(FEATURES)]+[([0,1],'joint_payload_interval')]
    result={}
    for indices,name in tests:
        changes=[]
        for repeat in range(settings['repetitions']):
            P=permuted_features(records,indices,seed=settings['seed'],repeat=repeat,axes=recipe['axes'])
            predictions=predict_matrix(estimator,P)
            changes.append(metrics(y,[predictions[i] for i in used])['rmse']-baseline)
        mean=math.fsum(changes)/len(changes)
        result[name]=dict(rmse_increases=changes,mean=mean,sd=math.hypot(*((x-mean)/math.sqrt(len(changes)) for x in changes)),
                          minimum=min(changes),maximum=max(changes))
    ordered=sorted(FEATURES,key=lambda name:(-result[name]['mean'],FEATURES.index(name)))
    ranks={name:[] for name in FEATURES}
    for repeat in range(settings['repetitions']):
        order=sorted(FEATURES,key=lambda name:(-result[name]['rmse_increases'][repeat],FEATURES.index(name)))
        for rank,name in enumerate(order,1):ranks[name].append(rank)
    return dict(unit=TARGET_UNITS[target],baseline_rmse=baseline,labeled_rows=len(y),family_count=len({r['family'] for r in records}),
                top_three=ordered[:3],rank_by_repeat=ranks,features=result,method=settings['permutation'])


ARTIFACT_FIELDS={'explanation_version','kind','provenance','model_sha256','dataset_sha256','recipe_sha256','split_sha256',
 'feature_contract_version','feature_order','lineage_sha256','original_recipe_sha256','original_dataset_sha256','method','results'}


def package_explanation(kind,results,dataset,models):
    recipe=dataset['recipe']
    return dict(explanation_version=1,kind=kind,provenance='analytical_simulation',model_sha256=recipe['model_sha256'],
        dataset_sha256=dataset['dataset_sha256'],recipe_sha256=dataset['recipe_sha256'],split_sha256=_sha256(_json_bytes(recipe['splits'])),
        feature_contract_version=3,feature_order=FEATURES,lineage_sha256=recipe['lineage_sha256'],
        original_recipe_sha256=recipe['original_recipe_sha256'],original_dataset_sha256=next(iter(models.values()))['training']['dataset_sha256'],
        method=recipe['ablations'] if kind=='ablations' else recipe['explainability'],results=results)


def explanation_from_bytes(content,dataset,models,*,kind):
    artifact=_json_from_bytes(content);_fields(artifact,ARTIFACT_FIELDS,'explanation artifact')
    expected=package_explanation(kind,artifact['results'],dataset,models)
    if _json_bytes({k:v for k,v in artifact.items() if k!='results'})!=_json_bytes({k:v for k,v in expected.items() if k!='results'}):raise ValueError('explanation compatibility mismatch')
    if kind=='ablations':validate_ablations(artifact['results'],models)
    elif kind=='explanations':
        _fields(artifact['results'],TARGET_UNITS,'explanation targets')
        for target,result in artifact['results'].items():
            _fields(result,{'unit','permutation','contribution_summary','contributions'},'target explanation')
            if result['unit']!=TARGET_UNITS[target]:raise ValueError('explanation unit mismatch')
            permutation=result['permutation']
            _fields(permutation,{'unit','baseline_rmse','labeled_rows','family_count','top_three','rank_by_repeat','features','method'},'permutation result')
            if permutation['unit']!=TARGET_UNITS[target] or permutation['method']!=dataset['recipe']['explainability']['permutation']:raise ValueError('permutation method/unit mismatch')
            tests=FEATURES+['joint_payload_interval'];_fields(permutation['features'],tests,'permutation features')
            repeats=dataset['recipe']['explainability']['repetitions']
            for name,values in permutation['features'].items():
                _fields(values,{'rmse_increases','mean','sd','minimum','maximum'},'permutation stability')
                changes=values['rmse_increases']
                if not isinstance(changes,list) or len(changes)!=repeats:raise ValueError('permutation repeat mismatch')
                for value in changes:finite(value,'permutation increase')
                mean=math.fsum(changes)/len(changes)
                expected=dict(mean=mean,sd=math.hypot(*((x-mean)/math.sqrt(len(changes)) for x in changes)),minimum=min(changes),maximum=max(changes))
                if any(values[k]!=v for k,v in expected.items()):raise ValueError('permutation stability accounting mismatch')
            order=sorted(FEATURES,key=lambda f:(-permutation['features'][f]['mean'],FEATURES.index(f)))
            if permutation['top_three']!=order[:3]:raise ValueError('permutation ranking mismatch')
            expected_ranks={f:[] for f in FEATURES}
            for repeat in range(repeats):
                ranked=sorted(FEATURES,key=lambda f:(-permutation['features'][f]['rmse_increases'][repeat],FEATURES.index(f)))
                for rank,name in enumerate(ranked,1):expected_ranks[name].append(rank)
            if permutation['rank_by_repeat']!=expected_ranks:raise ValueError('permutation rank stability mismatch')
            expected_records={r['row']['run_id']:r for r in dataset['records'] if r['split']=='evaluation'}
            if sorted(row['run_id'] for row in result['contributions'])!=sorted(expected_records):raise ValueError('contribution run membership mismatch')
            summary=result['contribution_summary']
            _fields(summary,{'baseline','mean_absolute','top_three'},'contribution summary')
            absolute={name:sum(abs(row['contributions'][name])/len(result['contributions']) for row in result['contributions']) for name in FEATURES}
            if (summary['baseline']!='original_training_means_and_intercept' or summary['mean_absolute']!=absolute
                or summary['top_three']!=sorted(FEATURES,key=lambda f:(-absolute[f],FEATURES.index(f)))[:3]):raise ValueError('contribution summary mismatch')
            for row in result['contributions']:
                _fields(row,{'run_id','group_id','baseline','prediction','contributions','top_three'},'contribution row')
                _fields(row['contributions'],FEATURES,'signed contributions')
                record=expected_records[row['run_id']]
                expected_row=signed_contributions(models[target]['estimator'],[record_features(record)])[0]
                if row['group_id']!=record['family'] or any(row[k]!=v for k,v in expected_row.items()):raise ValueError('contribution model/source mismatch')
                if not math.isclose(row['baseline']+math.fsum(row['contributions'].values()),row['prediction'],rel_tol=1e-12,abs_tol=1e-9):raise ValueError('contribution accounting mismatch')
                if row['top_three']!=sorted(FEATURES,key=lambda f:(-abs(row['contributions'][f]),FEATURES.index(f)))[:3]:raise ValueError('top influence mismatch')
    else:raise ValueError('unsupported explanation kind')
    _json_bytes(artifact)  # recursively rejects nonfinite values
    return artifact
