# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ml_workflow as workflow
import green_ops_ml as cli
from ml_dataset import materialize_dataset,load_dataset,publish_files
from ml_pipeline import model_from_bytes,TARGET_UNITS
from analytical_reference import _json_bytes
from tools.green_ops.tests.test_ml_dataset import small_recipe


class ForbiddenHeldoutLabels(dict):
    def __getitem__(self,key):
        if key in TARGET_UNITS:raise AssertionError('selection accessed locked labels')
        return super().__getitem__(key)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name);self.recipe=self.root/'recipe.json';self.recipe.write_bytes(_json_bytes(small_recipe()))
        self.data_root=self.root/'data';materialize_dataset(self.recipe,self.data_root);self.dataset=load_dataset(self.data_root)

    def test_selection_never_reads_test_or_stress_labels_and_is_deterministic(self):
        guarded=copy.deepcopy(self.dataset)
        for record in guarded['records']:
            if record['split'] in ('test','stress'):record['row']=ForbiddenHeldoutLabels(record['row'])
        files=workflow.train_selection(guarded)
        reverse=copy.deepcopy(self.dataset);reverse['records'].reverse()
        self.assertEqual(files,workflow.train_selection(reverse))
        self.assertNotIn('evaluation.json',files)
        report=json.loads(files['selection-report.json'])
        for target,details in report['targets'].items():
            model=model_from_bytes(files[f'{target}-chosen.json'])
            train=[r for r in self.dataset['records'] if r['split']=='train']
            self.assertEqual(model['training']['train_run_ids'],sorted(r['row']['run_id'] for r in train))
            for j,name in enumerate(model['feature_order']):
                self.assertAlmostEqual(model['estimator']['feature_means'][j],sum(r['row'][name] for r in train)/len(train))
            for candidate in details['candidates'].values():
                for frozen,fold in zip(self.dataset['recipe']['cv_folds'],candidate['folds']):
                    fits=[r for r in train if r['row']['evaluation_group_id'] in frozen['fit_groups']]
                    self.assertFalse(set(fold['fit_groups'])&set(fold['assessment_groups']))
                    for j,name in enumerate(model['feature_order']):
                        self.assertAlmostEqual(fold['feature_means'][j],sum(r['row'][name] for r in fits)/len(fits))

    def test_locked_evaluation_never_refits_and_keeps_artifacts_unchanged(self):
        training=self.root/'training';files=workflow.train_selection(self.dataset);publish_files(training,files)
        before={p.name:p.read_bytes() for p in training.iterdir()}
        with mock.patch.object(workflow,'fit_regressor',side_effect=AssertionError('locked evaluation refit')):
            first=workflow.locked_evaluation(self.dataset,training)
            self.assertEqual(first,workflow.locked_evaluation(self.dataset,training))
        self.assertEqual(before,{p.name:p.read_bytes() for p in training.iterdir()})
        report=json.loads(first['evaluation.json']);predictions=json.loads(first['predictions.json'])
        self.assertFalse(report['refit_or_tuning_performed'])
        self.assertEqual(len(predictions['rows']),18)
        for scores in report['partitions']['test'].values():
            self.assertEqual(scores['chosen']['sample_count'],1)
            self.assertIsNone(scores['chosen']['r2'])

    def test_split_leakage_and_tampered_frozen_models_fail(self):
        bad=copy.deepcopy(self.dataset)
        record=next(r for r in bad['records'] if r['split']=='test');record['split']='train'
        with self.assertRaisesRegex(ValueError,'leakage'):workflow.train_selection(bad)
        files=workflow.train_selection(self.dataset);training=self.root/'training';publish_files(training,files)
        name=next(name for name in files if name.endswith('-chosen.json'))
        model=json.loads((training/name).read_text());model['estimator']['intercept']+=1
        (training/name).write_bytes(_json_bytes(model))
        with self.assertRaisesRegex(ValueError,'hash mismatch'):workflow.locked_evaluation(self.dataset,training)

    def run_cli(self,*args):return subprocess.run([sys.executable,str(Path(cli.__file__)),*map(str,args)],capture_output=True,text=True)

    def test_cli_train_evaluate_predict_and_output_safety(self):
        training=self.root/'training';evaluation=self.root/'evaluation'
        result=self.run_cli('train','--dataset',self.data_root,'--output-dir',training)
        self.assertEqual(result.returncode,0,result.stderr)
        result=self.run_cli('evaluate','--dataset',self.data_root,'--training',training,'--output-dir',evaluation)
        self.assertEqual(result.returncode,0,result.stderr)
        record=next(r for r in self.dataset['records'] if r['split']=='test')
        artifact_dir=self.data_root/record['entry']['path'];output=self.root/'prediction.json'
        target='target_total_energy_mj'
        result=self.run_cli('predict','--model',training/f'{target}-chosen.json','--artifact-dir',artifact_dir,'--output',output)
        self.assertEqual(result.returncode,0,result.stderr)
        prediction=json.loads(output.read_text());self.assertEqual(prediction['unit'],'mJ')
        rows=json.loads((evaluation/'predictions.json').read_text())['rows']
        expected=next(p['prediction'] for p in rows if p['partition']=='test' and p['target']==target and p['model_role']=='chosen')
        self.assertEqual(prediction['value'],expected)
        original=output.read_bytes()
        self.assertEqual(self.run_cli('predict','--model',training/f'{target}-chosen.json','--artifact-dir',artifact_dir,'--output',output).returncode,1)
        self.assertEqual(original,output.read_bytes())
        self.assertEqual(self.run_cli('train','--dataset',self.data_root,'--output-dir',training).returncode,1)
        self.assertEqual(self.run_cli('bad-command').returncode,1)

    def test_publication_failure_rolls_back_and_preserves_source_snapshots(self):
        original=(self.data_root/'inventory.json').read_bytes();real_write=cli.publish_files
        def failing_publish(path,files):
            from ml_dataset import FreshDirectory
            with FreshDirectory(path) as output:
                output.write('owned.json',b'{}');raise OSError('simulated output failure')
        out=self.root/'fail'
        with mock.patch.object(cli,'publish_files',side_effect=failing_publish),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(['train','--dataset',str(self.data_root),'--output-dir',str(out)]),1)
        self.assertFalse(out.exists());self.assertEqual(original,(self.data_root/'inventory.json').read_bytes())
