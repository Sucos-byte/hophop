# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Separate immutable ablation fitting, calibration and held-out diagnostics."""
from pathlib import Path
from analytical_reference import _json_bytes,_sha256,_fields
from dataset_builder import _json_from_bytes
from ml_pipeline import record_features,metrics
from uncertainty import calibration_from_bytes,predict_interval,coverage_report,validate_binding
from explainability import (fit_ablations,validate_ablations,evaluate_ablations,signed_contributions,
    permutation_importance,package_explanation,explanation_from_bytes,FEATURES)


def ablation_files(original,dataset,models):
    recipe=dataset['recipe']
    if original['recipe_sha256']!=recipe['original_recipe_sha256']:raise ValueError('ablation original recipe mismatch')
    if any(model['training']['dataset_sha256']!=original['dataset_sha256'] for model in models.values()):raise ValueError('ablation original data mismatch')
    results=validate_ablations(fit_ablations(original,models),models)
    return {'ablations.json':_json_bytes(package_explanation('ablations',results,dataset,models))}


def calibration_inventory(files,dataset,ablations_bytes):
    result=dict(calibration_set_version=1,provenance='analytical_simulation',recipe_sha256=dataset['recipe_sha256'],
        dataset_sha256=dataset['dataset_sha256'],ablation_sha256=_sha256(ablations_bytes),
        files={name:_sha256(content) for name,content in sorted(files.items())})
    return {**files,'calibration-set.json':_json_bytes(result)}


def load_calibrations(path,dataset,models,ablations_bytes):
    path=Path(path);inventory_bytes=(path/'calibration-set.json').read_bytes();inventory=_json_from_bytes(inventory_bytes)
    _fields(inventory,{'calibration_set_version','provenance','recipe_sha256','dataset_sha256','ablation_sha256','files'},'calibration set')
    filenames={f'{t}-calibration.json' for t in models};_fields(inventory['files'],filenames,'calibration files')
    expected=dict(calibration_set_version=1,provenance='analytical_simulation',recipe_sha256=dataset['recipe_sha256'],
        dataset_sha256=dataset['dataset_sha256'],ablation_sha256=_sha256(ablations_bytes))
    if any(_json_bytes(inventory[k])!=_json_bytes(v) for k,v in expected.items()):raise ValueError('calibration set compatibility mismatch')
    result={}
    for target,model in models.items():
        name=f'{target}-calibration.json';content=(path/name).read_bytes()
        if _sha256(content)!=inventory['files'][name]:raise ValueError('calibration file hash mismatch')
        c=calibration_from_bytes(content);validate_binding(c,model,dataset['recipe_bytes'],dataset_sha256=dataset['dataset_sha256']);result[target]=c
    return result,_sha256(inventory_bytes)


def evaluate(dataset,models,original_recipe_bytes,calibration_directory,ablations_bytes):
    """No fit/selection/calibration; all thresholds and estimators already frozen."""
    ablations=explanation_from_bytes(ablations_bytes,dataset,models,kind='ablations')['results']
    calibrations,calibration_sha=load_calibrations(calibration_directory,dataset,models,ablations_bytes)
    records=sorted((r for r in dataset['records'] if r['split']=='evaluation'),key=lambda r:r['row']['run_id'])
    if len(records)!=450:raise ValueError('incomplete evaluation schedule')
    panels={'primary':records}
    for panel in sorted({r['panel'] for r in dataset['records'] if r['split']=='stress'}):
        panels[panel]=sorted((r for r in dataset['records'] if r['split']=='stress' and r['panel']==panel),key=lambda r:r['row']['run_id'])
    report={};saved=[]
    for panel,runs in panels.items():
        report[panel]={}
        for target,model in models.items():
            rows=[]
            for record in runs:
                interval=predict_interval(model,record,calibrations[target],original_recipe_bytes=original_recipe_bytes,
                    study_recipe_bytes=dataset['recipe_bytes'],dataset_sha256=dataset['dataset_sha256'],domain='primary' if panel=='primary' else 'declared_stress')
                row=dict(run_id=record['row']['run_id'],group_id=record['family'],target=target,panel=panel,
                    truth=record['row'][target],**interval);rows.append(row)
            saved+=rows
            labeled=[r for r in rows if r['truth'] is not None]
            report[panel][target]=dict(unit=model['unit'],q=calibrations[target]['q'],coverage=coverage_report(rows,calibrations[target]['q']),
                point_metrics=metrics([r['truth'] for r in labeled],[r['prediction'] for r in labeled]))
    explanations={}
    for target,model in models.items():
        X=[record_features(r) for r in records];contributions=signed_contributions(model['estimator'],X)
        rows=[dict(run_id=r['row']['run_id'],group_id=r['family'],**c) for r,c in zip(records,contributions)]
        mean_absolute={name:sum(abs(row['contributions'][name])/len(rows) for row in rows) for name in FEATURES}
        explanations[target]=dict(unit=model['unit'],permutation=permutation_importance(model['estimator'],records,target,dataset['recipe']),
            contribution_summary=dict(baseline='original_training_means_and_intercept',mean_absolute=mean_absolute,
                top_three=sorted(FEATURES,key=lambda f:(-mean_absolute[f],FEATURES.index(f)))[:3]),contributions=rows)
    artifact=package_explanation('explanations',explanations,dataset,models)
    explanation_bytes=_json_bytes(artifact);explanation_from_bytes(explanation_bytes,dataset,models,kind='explanations')
    result=dict(evaluation_version=1,provenance='analytical_simulation',recipe_sha256=dataset['recipe_sha256'],dataset_sha256=dataset['dataset_sha256'],
        model_sha256=dataset['recipe']['model_sha256'],split_sha256=_sha256(_json_bytes(dataset['recipe']['splits'])),
        feature_contract_version=3,calibration_set_sha256=calibration_sha,ablation_sha256=_sha256(ablations_bytes),
        explanation_sha256=_sha256(explanation_bytes),nominal_coverage=0.95,coverage_unit='all_labeled_rows_in_new_family_same_15_row_schedule',
        panels=report,ablations=evaluate_ablations(ablations,models,records),refit_or_tuning_performed=False,
        limitation='Analytical simulation; exchangeability is unproven for these deterministic configuration grids. No hardware coverage or metric confidence interval.')
    predictions=dict(predictions_version=1,provenance='analytical_simulation',dataset_sha256=dataset['dataset_sha256'],recipe_sha256=dataset['recipe_sha256'],
        calibration_set_sha256=calibration_sha,rows=sorted(saved,key=lambda r:(r['panel'],r['target'],r['run_id'])))
    return {'evaluation.json':_json_bytes(result),'predictions.json':_json_bytes(predictions),'explanations.json':explanation_bytes}
