# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

# Run from repository root after materializing study and original datasets.
# Replays frozen methods; refuses mismatching archive; never selects settings.
from pathlib import Path
import sys,json,math,platform
from unittest import mock
sys.path.insert(0,'tools/green_ops')
from analytical_reference import _json_bytes,_sha256
from week8_dataset import load_dataset,frozen_models
from uncertainty import calibrate
import explainability as e
import week8_workflow as w
from ml_dataset import load_dataset as load_old

root=Path('docs/results/week8');data=load_dataset('build/green-ops-week8-data')
old=load_old('build/green-ops-week7/dataset');recipe=Path('tools/green_ops/recipes/week7-regression-v1.json').read_bytes()
models=frozen_models('docs/results/week7-regression-v1/training',recipe,data['recipe'])
ablations=(root/'ablations/ablations.json').read_bytes()
assert w.ablation_files(old,data,models)['ablations.json']==ablations
for name,content in calibrate(data,models,recipe).items():assert content==(root/'calibration'/name).read_bytes()
with mock.patch.object(e,'fit_regressor',side_effect=AssertionError('evaluation refit')):
    files=w.evaluate(data,models,recipe,root/'calibration',ablations)
for name,content in files.items():assert content==(root/'evaluation'/name).read_bytes()
rows=json.loads(files['predictions.json'])['rows'];report=json.loads(files['evaluation.json'])
seen=set()
for row in rows:
    key=(row['run_id'],row['target'],row['panel']);assert key not in seen;seen.add(key)
    q=report['panels'][row['panel']][row['target']]['q']
    assert row['lower']==row['prediction']-q and row['upper']==row['prediction']+q
for panel,targets in report['panels'].items():
    for target,result in targets.items():
        labeled=[r for r in rows if r['panel']==panel and r['target']==target and r['truth'] is not None]
        misses=[r for r in labeled if not r['lower']<=r['truth']<=r['upper']]
        groups={r['group_id'] for r in labeled};failed={r['group_id'] for r in misses}
        assert result['coverage']['row_coverage']==1-len(misses)/len(labeled) or math.isclose(result['coverage']['row_coverage'],1-len(misses)/len(labeled),abs_tol=1e-15)
        assert result['coverage']['family_coverage']==(len(groups)-len(failed))/len(groups)
        assert set(result['coverage']['failed_families'])==failed
        residuals=[r['prediction']-r['truth'] for r in labeled]
        assert math.isclose(result['point_metrics']['rmse'],math.sqrt(sum(v*v for v in residuals)/len(residuals)),rel_tol=1e-12)
        assert len(labeled)==450 and len(groups)==30
receipt=dict(reproduction_version=1,provenance='analytical_simulation',python_version=platform.python_version(),dependencies='stdlib_only',
    dataset_sha256=data['dataset_sha256'],recipe_sha256=data['recipe_sha256'],selection_sha256=data['recipe']['selection_sha256'],
    model_sha256=data['recipe']['model_sha256'],prediction_count=len(rows),unique_prediction_keys=len(seen),
    source_audit_equal=data['audit']==json.loads((root/'dataset-audit.json').read_bytes()),
    ablations_byte_identical=True,calibration_byte_identical=True,evaluation_byte_identical=True,evaluation_fit_calls=0,
    files={name:_sha256(content) for name,content in files.items()},independent_interval_coverage_and_rmse_checks=True)
receipt_bytes=_json_bytes(receipt)
if (root/'reproduction.json').exists():assert (root/'reproduction.json').read_bytes()==receipt_bytes
else:(root/'reproduction.json').write_bytes(receipt_bytes)
print('Verified exact ablation/calibration/evaluation replay and independent interval/coverage/RMSE checks.')
