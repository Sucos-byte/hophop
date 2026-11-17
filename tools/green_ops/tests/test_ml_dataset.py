# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ml_dataset as data
from analytical_reference import _json_bytes,_sha256
from analytical_design import plan_workload_grid

ROOT=Path(__file__).resolve().parents[1]
RECIPE=ROOT/'recipes/week7-regression-v1.json'


def small_recipe():
    recipe=json.loads(RECIPE.read_text())
    for name in ('parameters_path','assumptions_path'):recipe[name]=str(Path(recipe[name]).resolve())
    recipe['axes']=dict(payload_sizes_bytes=[32,128,512],intervals_ms=[50,200],window_durations_ms=[1000])
    recipe.update(experiment_id='toy-pipeline-tests',repetitions=1,primary_row_count=6,stress_row_count=2)
    model=json.loads(Path(recipe['parameters_path']).read_text())
    runs=plan_workload_grid(model,**{k:tuple(v) for k,v in recipe['axes'].items()},repetitions=1,master_seed=recipe['master_seed'])
    gs=sorted({r['evaluation_group_id'] for r in runs},key=lambda g:_sha256(f"week7-split-v1:{recipe['split_seed']}:{g}".encode()))
    recipe['splits']={s:sorted(g) for s,g in [('train',gs[:4]),('validation',gs[4:5]),('test',gs[5:])]}
    ordered=sorted(gs[:4],key=lambda g:_sha256(f"week7-cv-v1:{recipe['cv_seed']}:{g}".encode()))
    recipe['cv_folds']=[dict(fit_groups=sorted(g for j,g in enumerate(ordered) if j%2!=i),assessment_groups=sorted(ordered[i::2])) for i in range(2)]
    return recipe


class DatasetFreezeTests(unittest.TestCase):
    def test_real_recipe_counts_membership_and_folds_are_frozen(self):
        recipe=data.validate_recipe(json.loads(RECIPE.read_text()))
        specs=data.planned_specs(recipe,Path(recipe['parameters_path']).read_bytes())
        self.assertEqual(len(specs),720)
        self.assertEqual(sum(s['panel']=='primary' for s in specs),540)
        self.assertEqual([len(recipe['splits'][s]) for s in ('train','validation','test')],[24,6,6])
        for spec in specs:
            if spec['panel']!='primary':self.assertIn(spec['workload']['evaluation_group_id'],recipe['splits']['test'])
        self.assertEqual(len({s['workload']['run_id'] for s in specs}),720)

    def test_recipe_rejects_group_leakage_target_features_and_wrong_types(self):
        for field in ('split','fold','feature','refit','alpha'):
            recipe=small_recipe()
            if field=='split':recipe['splits']['test']=recipe['splits']['train'][:1]
            elif field=='fold':recipe['cv_folds'][0]['assessment_groups']=recipe['splits']['test']
            elif field=='feature':recipe['feature_order'][0]='target_total_energy_mj'
            elif field=='refit':recipe['refit_on_validation']=0
            else:recipe['ridge_alphas']=[True]
            with self.subTest(field=field),self.assertRaises(ValueError):data.validate_recipe(recipe)

    def test_materialization_determinism_source_replay_and_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);recipe=root/'recipe.json';recipe.write_bytes(_json_bytes(small_recipe()))
            a=data.materialize_dataset(recipe,root/'a');b=data.materialize_dataset(recipe,root/'b')
            self.assertEqual(a,b)
            self.assertEqual(a['partition_counts'],dict(train=4,validation=1,test=1,stress=2))
            self.assertEqual((root/'a/inventory.json').read_bytes(),(root/'b/inventory.json').read_bytes())
            self.assertEqual(len(data.load_dataset(root/'a')['records']),8)
            with self.assertRaises(FileExistsError):data.materialize_dataset(recipe,root/'a')

    def test_source_tampering_and_rehashed_split_changes_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);recipe=root/'recipe.json';recipe.write_bytes(_json_bytes(small_recipe()))
            data.materialize_dataset(recipe,root/'out')
            inventory=json.loads((root/'out/inventory.json').read_text())
            inventory['entries'][0]['split']='train' if inventory['entries'][0]['split']!='train' else 'test'
            inventory['dataset_sha256']=_sha256(_json_bytes({k:v for k,v in inventory.items() if k!='dataset_sha256'}))
            (root/'out/inventory.json').write_bytes(_json_bytes(inventory))
            with self.assertRaisesRegex(ValueError,'identity mismatch'):data.load_dataset(root/'out')

    def test_fresh_output_rollback_does_not_touch_existing_or_external_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);keep=root/'keep';keep.write_text('KEEP')
            with self.assertRaises(ValueError):
                with data.FreshDirectory(root/'new') as output:
                    output.write('sub/file',b'owned');output.write('../keep',b'bad')
            self.assertFalse((root/'new').exists());self.assertEqual(keep.read_text(),'KEEP')
            with self.assertRaises(FileExistsError):
                with data.FreshDirectory(root) as output:output.write('keep',b'bad')
