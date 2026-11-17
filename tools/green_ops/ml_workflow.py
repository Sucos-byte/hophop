# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Separate validation selection from immutable held-out evaluation."""

from pathlib import Path

from analytical_reference import _fields,_json_bytes,_sha256
from dataset_builder import _json_from_bytes
from ml_dataset import TARGET_UNITS,validate_recipe,_digest
from ml_pipeline import (PIPELINE_VERSION,fit_regressor,predict_matrix,prepare_target,metrics,
    evaluate_estimator,package_model,model_to_bytes,model_from_bytes,predict_record)

SELECTION_FIELDS={'selection_version','pipeline_version','stage','provenance','recipe_sha256','dataset_sha256',
                  'split_sha256','choices','model_sha256','selection_report_sha256','locked_test_groups'}


def _partitions(dataset):
    recipe=validate_recipe(dataset['recipe']);parts={s:[] for s in ('train','validation','test','stress')};seen=set()
    for record in dataset['records']:
        split=record.get('split');row=record['row'];group=row['evaluation_group_id']
        if split not in parts:raise ValueError('unknown dataset partition')
        if record['panel']=='primary':
            if split=='stress' or group not in recipe['splits'][split]:raise ValueError('training/held-out group leakage')
        elif split!='stress' or group not in recipe['splits']['test']:raise ValueError('stress family leakage')
        if row['run_id'] in seen:raise ValueError('duplicate experiment run')
        seen.add(row['run_id']);parts[split].append(record)
    for values in parts.values():values.sort(key=lambda r:r['row']['run_id'])
    return parts


def _candidate_name(kind,alpha):return 'training_mean' if kind=='training_mean' else f'ridge_{alpha:g}'


def train_selection(dataset):
    """Train/CV/validation only. No test/stress predictions or metrics here."""
    recipe=validate_recipe(dataset['recipe']);parts=_partitions(dataset)
    if not parts['train'] or not parts['validation']:raise ValueError('train and validation records required')
    files={};choices={};target_reports={}
    candidates=[('training_mean',None)]+[('ridge',alpha) for alpha in recipe['ridge_alphas']]
    for target in recipe['targets']:
        X,y,used,missing=prepare_target(parts['train'],target)
        if not y:raise ValueError(f'{target}: no training labels')
        results={};fitted={}
        for kind,alpha in candidates:
            name=_candidate_name(kind,alpha);fold_reports=[];truth=[];predictions=[]
            for fold in recipe['cv_folds']:
                fit_records=[r for r in parts['train'] if r['row']['evaluation_group_id'] in fold['fit_groups']]
                assessment=[r for r in parts['train'] if r['row']['evaluation_group_id'] in fold['assessment_groups']]
                A,b,fold_used,excluded=prepare_target(fit_records,target)
                V,t,assessment_used,assessment_missing=prepare_target(assessment,target)
                if not b or not t:raise ValueError(f'{target}: insufficient labeled groups in frozen CV fold')
                state=fit_regressor(A,b,kind=kind,alpha=alpha)
                p=predict_matrix(state,V);truth+=t;predictions+=p
                fold_reports.append(dict(fit_groups=fold['fit_groups'],assessment_groups=fold['assessment_groups'],
                    fit_sample_count=len(b),assessment_sample_count=len(t),fit_missing_labels=excluded,
                    assessment_missing_labels=assessment_missing,fit_run_ids_sha256=_sha256(_json_bytes(sorted(r['row']['run_id'] for r in fold_used))),
                    feature_means=state['feature_means'],feature_scales=state['feature_scales'],scores=metrics(t,p)))
            final=fit_regressor(X,y,kind=kind,alpha=alpha)
            val_scores,_=evaluate_estimator(final,parts['validation'],target)
            if val_scores['sample_count']==0:raise ValueError(f'{target}: no validation labels')
            fitted[name]=final
            results[name]=dict(kind=kind,alpha=alpha,cv=metrics(truth,predictions),folds=fold_reports,validation=val_scores)
        ridge_names=sorted((name for name in results if name!='training_mean'),
            key=lambda name:(results[name]['cv']['rmse'],-results[name]['alpha']))[:recipe['cv_shortlist']]
        shortlist=['training_mean']+ridge_names
        chosen=min(shortlist,key=lambda name:(results[name]['validation']['rmse'],0 if name=='training_mean' else 1,
                                               -(results[name]['alpha'] or 0)))
        choice={}
        for role,name in (('baseline','training_mean'),('chosen',chosen)):
            filename=f'{target}-{role}.json'
            files[filename]=model_to_bytes(package_model(fitted[name],target,dataset,parts['train']))
            choice[f'{role}_model']=filename
        choice.update(selected_candidate=chosen,selected_kind=results[chosen]['kind'],selected_alpha=results[chosen]['alpha'])
        choices[target]=choice
        target_reports[target]=dict(unit=TARGET_UNITS[target],training_sample_count=len(used),training_missing_labels=missing,
            candidates=results,validation_shortlist=shortlist,chosen_candidate=chosen,selection_metric='validation_rmse',
            refit_on_validation=False)
    report=dict(selection_report_version=1,provenance='analytical_simulation',recipe_sha256=dataset['recipe_sha256'],
        dataset_sha256=dataset['dataset_sha256'],targets=target_reports,
        policy='frozen grouped CV; top ridge shortlist + baseline; validation RMSE; no test or stress access',
        locked_test_groups=recipe['splits']['test'])
    files['selection-report.json']=_json_bytes(report)
    selection=dict(selection_version=1,pipeline_version=PIPELINE_VERSION,stage='selection_frozen',provenance='analytical_simulation',
        recipe_sha256=dataset['recipe_sha256'],dataset_sha256=dataset['dataset_sha256'],split_sha256=_sha256(_json_bytes(recipe['splits'])),
        choices=choices,model_sha256={name:_sha256(content) for name,content in files.items() if name!='selection-report.json'},
        selection_report_sha256=_sha256(files['selection-report.json']),locked_test_groups=recipe['splits']['test'])
    files['selection.json']=_json_bytes(selection)
    return files


def load_training(directory,dataset):
    directory=Path(directory).resolve();content=(directory/'selection.json').read_bytes();selection=_json_from_bytes(content)
    _fields(selection,SELECTION_FIELDS,'frozen selection')
    for name,value in dict(selection_version=1,pipeline_version=PIPELINE_VERSION,stage='selection_frozen',provenance='analytical_simulation',
        recipe_sha256=dataset['recipe_sha256'],dataset_sha256=dataset['dataset_sha256'],
        split_sha256=_sha256(_json_bytes(dataset['recipe']['splits'])),locked_test_groups=dataset['recipe']['splits']['test']).items():
        if _json_bytes(selection[name])!=_json_bytes(value):raise ValueError(f'incompatible frozen selection {name}')
    _fields(selection['choices'],TARGET_UNITS,'selected targets')
    expected_names={f'{target}-{role}.json' for target in TARGET_UNITS for role in ('baseline','chosen')}
    _fields(selection['model_sha256'],expected_names,'model inventory')
    parts=_partitions(dataset);models={}
    for target,choice in selection['choices'].items():
        _fields(choice,{'baseline_model','chosen_model','selected_candidate','selected_kind','selected_alpha'},'target choice')
        for role in ('baseline','chosen'):
            name=f'{target}-{role}.json'
            if choice[f'{role}_model']!=name:raise ValueError('unsafe model reference')
            model_bytes=(directory/name).read_bytes()
            if _sha256(model_bytes)!=selection['model_sha256'][name]:raise ValueError('frozen model hash mismatch')
            model=model_from_bytes(model_bytes)
            for key in ('recipe_sha256','dataset_sha256','split_sha256'):
                if model['training'][key]!=selection[key]:raise ValueError('model training provenance mismatch')
            if model['target']!=target or model['training']['split_membership']!=dataset['recipe']['splits']:
                raise ValueError('model target/split mismatch')
            _,_,used,_=prepare_target(parts['train'],target)
            if model['training']['train_run_ids']!=sorted(r['row']['run_id'] for r in used):raise ValueError('model training membership mismatch')
            if role=='baseline' and model['estimator']['kind']!='training_mean':raise ValueError('baseline model mismatch')
            if model['estimator']['kind']=='ridge' and model['estimator']['alpha'] not in dataset['recipe']['ridge_alphas']:
                raise ValueError('model alpha is outside frozen recipe')
            if role=='chosen' and (model['estimator']['kind']!=choice['selected_kind'] or model['estimator']['alpha']!=choice['selected_alpha']):
                raise ValueError('choice/model settings mismatch')
            models[name]=model
    report_bytes=(directory/'selection-report.json').read_bytes()
    if _sha256(report_bytes)!=selection['selection_report_sha256']:raise ValueError('selection report hash mismatch')
    report=_json_from_bytes(report_bytes)
    _fields(report,{'selection_report_version','provenance','recipe_sha256','dataset_sha256','targets','policy','locked_test_groups'},'selection report')
    if type(report['selection_report_version']) is not int or report['selection_report_version']!=1 or report['provenance']!='analytical_simulation':raise ValueError('selection report version/provenance mismatch')
    if report['recipe_sha256']!=selection['recipe_sha256'] or report['dataset_sha256']!=selection['dataset_sha256'] or report['locked_test_groups']!=selection['locked_test_groups']:
        raise ValueError('selection report provenance mismatch')
    _fields(report['targets'],TARGET_UNITS,'selection report targets')
    for target,choice in selection['choices'].items():
        target_report=report['targets'][target]
        _fields(target_report,{'unit','training_sample_count','training_missing_labels','candidates','validation_shortlist','chosen_candidate','selection_metric','refit_on_validation'},'selection target report')
        if target_report['chosen_candidate']!=choice['selected_candidate'] or choice['selected_candidate']!=_candidate_name(choice['selected_kind'],choice['selected_alpha']):raise ValueError('choice/report mismatch')
        if target_report['unit']!=TARGET_UNITS[target] or target_report['selection_metric']!='validation_rmse' or target_report['refit_on_validation'] is not False:raise ValueError('selection report policy mismatch')
    return selection,models,_sha256(content)


def locked_evaluation(dataset,training_directory):
    """Score frozen test/stress records. Deliberately never calls fitting APIs."""
    selection,models,selection_digest=load_training(training_directory,dataset);parts=_partitions(dataset)
    partitions={'test':parts['test']}
    for panel in sorted({r['panel'] for r in parts['stress']}):partitions[panel]=[r for r in parts['stress'] if r['panel']==panel]
    if not partitions['test']:raise ValueError('locked test records required')
    report={};saved=[]
    for partition,records in partitions.items():
        results={};domain='primary' if partition=='test' else 'declared_stress'
        for target,choice in selection['choices'].items():
            scores={}
            for role in ('baseline','chosen'):
                model=models[choice[f'{role}_model']]
                summary,predictions=evaluate_estimator(model['estimator'],records,target,scope=model['scope'],domain=domain,recipe=dataset['recipe'])
                scores[role]=summary
                saved += [{**p,'partition':partition,'model_role':role} for p in predictions]
            scores['chosen_minus_baseline']={metric:(scores['chosen'][metric]-scores['baseline'][metric])
                if scores['chosen'][metric] is not None and scores['baseline'][metric] is not None else None for metric in ('mae','rmse','r2')}
            results[target]=scores
        report[partition]=results
    result=dict(evaluation_version=1,provenance='analytical_simulation',pipeline_version=PIPELINE_VERSION,
        recipe_sha256=dataset['recipe_sha256'],dataset_sha256=dataset['dataset_sha256'],selection_sha256=selection_digest,
        model_sha256=selection['model_sha256'],feature_profile=dataset['recipe']['feature_profile'],
        feature_order=dataset['recipe']['feature_order'],split_membership=dataset['recipe']['splits'],
        contracts=dict(dataset_version=dataset['recipe']['dataset_version'],feature_contract_version=dataset['recipe']['feature_contract_version'],recipe_version=1,model_artifact_version=1),
        partitions=report,refit_or_tuning_performed=False,
        limitation='Recovery of analytical generator formulas is not hardware validation; no uncertainty calibration.')
    predictions=dict(predictions_version=1,provenance='analytical_simulation',selection_sha256=selection_digest,
                     rows=sorted(saved,key=lambda p:(p['partition'],p['target'],p['model_role'],p['run_id'])))
    return {'evaluation.json':_json_bytes(result),'predictions.json':_json_bytes(predictions)}
