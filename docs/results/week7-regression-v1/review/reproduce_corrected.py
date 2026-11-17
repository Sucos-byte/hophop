# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Run from repository root; uses replay-validated dataset, never tunes on held-out data.
Materialize a fresh dataset with green_ops_ml.py materialize if none exists; pass its
path as argv[1]. Output is exclusive, argv[2] (default build/.../corrected).
"""
from pathlib import Path
import sys,json,math
from unittest import mock
sys.path.insert(0,'tools/green_ops')
from ml_dataset import load_dataset,publish_files
from analytical_reference import _json_bytes,_sha256
import ml_workflow as workflow

source=Path('docs/results/week7-regression-v1')
data=load_dataset(Path(sys.argv[1]) if len(sys.argv)>1 else Path('build/green-ops-week7-review/dataset'))
output=Path(sys.argv[2]) if len(sys.argv)>2 else Path('build/green-ops-week7-review/corrected')
# Replay the predeclared training-only recipe solely to audit the original choice.
# No new candidates; never replace selection.json or deploy replayed models.
replay=workflow.train_selection(data)
for name,content in replay.items():
    if name not in ('selection.json','selection-report.json'):
        assert content==(source/'training'/name).read_bytes(),name
assert json.loads(replay['selection.json'])['choices']==json.loads((source/'training/selection.json').read_bytes())['choices']
with mock.patch.object(workflow,'fit_regressor',side_effect=AssertionError('evaluation refit')):
    files=workflow.locked_evaluation(data,source/'training')
assert files['predictions.json']==(source/'evaluation/predictions.json').read_bytes()
old=json.loads((source/'evaluation/evaluation.json').read_bytes());new=json.loads(files['evaluation.json'])
changes=[]
def compare(a,b,path=''):
    if isinstance(a,dict):
        for key in a:compare(a[key],b[key],path+'/'+key)
    elif a!=b:
        assert path.endswith(('/r2','/r2_undefined_reason')),path
        changes.append(dict(path=path,old=a,replacement=b))
compare(old['partitions'],new['partitions'])
# Independent centered-offset expected R2, ordinary finite energy-scale inputs.
rows=json.loads(files['predictions.json'])['rows']
for partition,targets in new['partitions'].items():
    for target,scores in targets.items():
        for role in ('baseline','chosen'):
            selected=[r for r in rows if (r['partition'],r['target'],r['model_role'])==(partition,target,role) and r['truth'] is not None]
            for group,score in [(None,scores[role])]+list(scores[role]['per_family'].items()):
                samples=[r for r in selected if group is None or r['group_id']==group]
                t=[r['truth'] for r in samples];p=[r['prediction'] for r in samples]
                offsets=[v-t[0] for v in t];center=math.fsum(offsets)/len(t)
                sst=math.fsum((v-center)**2 for v in offsets)
                expected=None if len(t)<2 or sst==0 else 1-math.fsum((x-y)**2 for x,y in zip(t,p))/sst
                assert (expected is None and score['r2'] is None) or math.isclose(expected,score['r2'],rel_tol=1e-12,abs_tol=1e-12)
receipt=dict(review_correction_version=1,metrics_version=2,provenance='analytical_simulation',
    dataset_sha256=data['dataset_sha256'],recipe_sha256=data['recipe_sha256'],
    original_selection_sha256=_sha256((source/'training/selection.json').read_bytes()),
    unchanged_predictions_sha256=_sha256(files['predictions.json']),model_bytes_unchanged=True,choices_unchanged=True,
    mae_rmse_unchanged=True,evaluation_fit_calls=0,r2_changes=changes,
    files={name:_sha256(content) for name,content in files.items()})
# Predictions are identical: reference their historical hash rather than duplicate.
publish_files(output,{'evaluation.json':files['evaluation.json'],
    'selection-report-metrics-v2.json':replay['selection-report.json'],'correction-receipt.json':_json_bytes(receipt)})
print(f'Verified unchanged models/choices/predictions/MAE/RMSE; {len(changes)} R2 fields replaced.')
