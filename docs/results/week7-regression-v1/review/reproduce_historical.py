# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

# Run from a fresh checkout of a2aeb15 with Python 3.11.8, before metric-v2 fixes.
# Creates build/green-ops-week7-review; refuses to overwrite existing output.
from pathlib import Path
import sys,json,hashlib,collections,statistics,math
from unittest import mock
sys.path.insert(0,'tools/green_ops')
from analytical_reference import _json_bytes,_sha256
from ml_dataset import materialize_dataset,load_dataset,publish_files,TARGET_UNITS
import ml_workflow as workflow

root=Path('build/green-ops-week7-review');root.mkdir()
recipe=Path('tools/green_ops/recipes/week7-regression-v1.json')
original=Path('docs/results/week7-regression-v1')
audit=materialize_dataset(recipe,root/'dataset',progress=lambda s:print(s,flush=True))
assert audit==json.loads(Path('docs/results/green-ops-week7-dataset-audit.json').read_text())
dataset=load_dataset(root/'dataset',progress=lambda s:print(s,flush=True))
files=workflow.train_selection(dataset)  # Exact frozen training/CV/validation replay, no new choices/settings.
publish_files(root/'historical-training-replay',files)
assert all(content==(original/'training'/name).read_bytes() for name,content in files.items())
print('Historical replay: dataset audit, all six models, selection and CV/validation report are byte-identical.',flush=True)
with mock.patch.object(workflow,'fit_regressor',side_effect=AssertionError('evaluation fitted a model')):
    evaluated=workflow.locked_evaluation(dataset,original/'training')
assert all(content==(original/'evaluation'/name).read_bytes() for name,content in evaluated.items())
publish_files(root/'historical-evaluation-replay',evaluated)
print('Historical held-out report and all1620 predictions reproduce byte-for-byte; no evaluation fit.',flush=True)
selection=json.loads(files['selection.json']);report=json.loads(files['selection-report.json'])
train=[r for r in dataset['records'] if r['split']=='train']
checks=0
for target,details in report['targets'].items():
    used=[r for r in train if r['row'][target] is not None]
    for role in ('baseline','chosen'):
        model=json.loads(files[f'{target}-{role}.json']);state=model['estimator']
        assert model['training']['train_run_ids']==sorted(r['row']['run_id'] for r in used)
        assert math.isclose(state['intercept'],statistics.fmean(r['row'][target] for r in used),rel_tol=1e-14)
        for j,name in enumerate(model['feature_order']):
            values=[r['row'][name] for r in used]
            assert math.isclose(state['feature_means'][j],statistics.fmean(values),rel_tol=1e-14)
            assert math.isclose(state['feature_scales'][j],statistics.pstdev(values) or 1,rel_tol=1e-14)
            checks+=1
    for candidate in details['candidates'].values():
        for fold in candidate['folds']:
            fit=[r for r in used if r['row']['evaluation_group_id'] in fold['fit_groups']]
            assert len(fit)==fold['fit_sample_count']
            assert _sha256(_json_bytes(sorted(r['row']['run_id'] for r in fit)))==fold['fit_run_ids_sha256']
            assert not set(fold['fit_groups'])&set(fold['assessment_groups'])
            for j,name in enumerate(dataset['recipe']['feature_order']):
                values=[r['row'][name] for r in fit]
                assert math.isclose(fold['feature_means'][j],statistics.fmean(values),rel_tol=1e-14)
                assert math.isclose(fold['feature_scales'][j],statistics.pstdev(values) or 1,rel_tol=1e-14)
                checks+=1
    candidates=details['candidates']
    shortlist=['training_mean']+sorted((n for n in candidates if n!='training_mean'),key=lambda n:(candidates[n]['cv']['rmse'],-candidates[n]['alpha']))[:2]
    expected=min(shortlist,key=lambda n:(candidates[n]['validation']['rmse'],0 if n=='training_mean' else 1,-(candidates[n]['alpha'] or 0)))
    assert details['validation_shortlist']==shortlist and expected==selection['choices'][target]['selected_candidate']
print('Independent statistics/preprocessing and selection-rule checks:',checks,flush=True)
preds=json.loads(evaluated['predictions.json'])['rows'];evaluation=json.loads(evaluated['evaluation.json'])
records={r['row']['run_id']:r for r in dataset['records']}
seen=set();counts=collections.Counter()
for p in preds:
    key=(p['partition'],p['target'],p['model_role'],p['run_id']);assert key not in seen;seen.add(key)
    r=records[p['run_id']]
    assert r['split']=='test' if p['partition']=='test' else r['panel']==p['partition'] and r['split']=='stress'
    assert p['truth']==r['row'][p['target']] and p['group_id']==r['row']['evaluation_group_id']
    assert p['provenance']=='analytical_simulation'
    model=json.loads(files[f"{p['target']}-{p['model_role']}.json"])
    if p['model_role']=='baseline':assert p['prediction']==model['estimator']['intercept']
    counts[key[:3]]+=1
assert len(counts)==18 and set(counts.values())=={90}
for partition,targets in evaluation['partitions'].items():
    for target,scores in targets.items():
        for role in ('baseline','chosen'):
            rows=[p for p in preds if p['partition']==partition and p['target']==target and p['model_role']==role and p['truth'] is not None]
            errors=[p['prediction']-p['truth'] for p in rows]
            assert scores[role]['unit']==TARGET_UNITS[target]
            assert scores[role]['sample_count']==len(rows)==90
            assert math.isclose(scores[role]['mae'],sum(map(abs,errors))/len(errors),rel_tol=1e-14)
            assert math.isclose(scores[role]['rmse'],math.sqrt(sum(e*e for e in errors)/len(errors)),rel_tol=1e-14)
print('Independent source/prediction/metric/count/baseline checks passed.',flush=True)
receipt=dict(review_reproduction_version=1,baseline_commit='a2aeb156634d6ae5a915a5e9eb5c32badd55238e',
    recipe_sha256=dataset['recipe_sha256'],dataset_sha256=dataset['dataset_sha256'],
    selection_sha256=_sha256(files['selection.json']),
    historical_training_files={name:dict(sha256=_sha256(content),byte_identical=True) for name,content in files.items()},
    historical_evaluation_files={name:dict(sha256=_sha256(content),byte_identical=True) for name,content in evaluated.items()},
    preprocessing_statistic_checks=checks,source_replay_count=len(records),unique_prediction_keys=len(seen),
    count_breakdown=[dict(partition=k[0],target=k[1],model_role=k[2],count=v) for k,v in sorted(counts.items())],
    evaluation_fit_calls=0,choices_unchanged=True)
(root/'historical-reproduction.json').write_bytes(_json_bytes(receipt))
