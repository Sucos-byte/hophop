# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from analytical_reference import _json_bytes,_sha256
from analytical_design import configuration_family
from ml_pipeline import fit_regressor,predict_matrix
import ml_dataset as original
import week8_dataset as study
import uncertainty as u
import explainability as e
import week8_workflow as workflow
import green_ops_ml as prediction_cli

ROOT=Path(__file__).resolve().parents[3]
RECIPE=ROOT/'tools/green_ops/recipes/week8-uncertainty-v1.json'
LINEAGE=ROOT/'docs/results/week8/lineage.json'
ORIGINAL_RECIPE=ROOT/'tools/green_ops/recipes/week7-regression-v1.json'
MODELS=ROOT/'docs/results/week7-regression-v1/training'


class QuantileTests(unittest.TestCase):
    def test_exact_rank_and_insufficient_calibration(self):
        self.assertEqual(u.finite_sample_quantile(list(range(30))),(30,29))
        self.assertEqual(u.finite_sample_quantile(list(range(19))),(19,18))
        self.assertEqual(u.finite_sample_quantile(list(range(39))),(38,37))
        for scores in ([],[0]*18,[float('nan')]*30,[-1]*30):
            with self.assertRaises(ValueError):u.finite_sample_quantile(scores)
        for a,b in ((True,20),(20,20),(0,20),(19,0)):
            with self.assertRaises(ValueError):u.finite_sample_quantile([1]*30,a,b)

    def test_group_max_not_row_quantile_and_missing_labels(self):
        rows=[dict(run_id=f'{g}-{i}',group_id=g,truth=i,prediction=0) for g in ('a','b') for i in range(15)]
        rows.append(dict(run_id='missing',group_id='c',truth=None,prediction=99))
        scores,missing,excluded=u.score_families(rows)
        self.assertEqual(scores,{'a':14,'b':14});self.assertEqual(missing,['missing']);self.assertEqual(excluded,['c'])
        with self.assertRaises(ValueError):u.score_families(rows+rows[:1])

    def test_interval_inclusive_boundary_and_family_failure(self):
        rows=[dict(run_id='a1',group_id='a',truth=2,prediction=0),dict(run_id='a2',group_id='a',truth=3,prediction=0),
              dict(run_id='b1',group_id='b',truth=0,prediction=0),dict(run_id='c1',group_id='c',truth=None,prediction=0)]
        result=u.coverage_report(rows,2)
        self.assertEqual(result['row_coverage'],2/3);self.assertEqual(result['family_coverage'],0.5)
        self.assertEqual(result['mean_width'],4);self.assertEqual(result['failed_families'],['a'])
        self.assertIsNone(result['per_family']['c']['covered'])
        self.assertEqual(u.interval_bounds(-1,2),(-3,1))
        with self.assertRaises(ValueError):u.interval_bounds(1,-1)
        with self.assertRaises(ValueError):u.interval_bounds(1e308,1e308)

    def test_contributions_independent_expected_and_constant_features(self):
        model=fit_regressor([[1,0,19,1000],[2,0,19,1000],[3,0,19,1000]],[5,7,9],alpha=3)
        rows=e.signed_contributions(model,[[1,0,19,1000],[3,0,19,1000]])
        for row,expected in zip(rows,[-1,1]):
            self.assertAlmostEqual(row['contributions']['payload_size_bytes'],expected)
            self.assertEqual(row['baseline'],7)
            self.assertAlmostEqual(row['baseline']+math.fsum(row['contributions'].values()),row['prediction'])
            self.assertEqual(row['contributions']['tx_power_dbm'],0)
        self.assertEqual(rows,e.signed_contributions(model,[[1,0,19,1000],[3,0,19,1000]]))


class StudyIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.oldroot=cls.root/'old';original.materialize_dataset(ORIGINAL_RECIPE,cls.oldroot)
        cls.old=original.load_dataset(cls.oldroot)
        cls.data_root=cls.root/'study';study.materialize(RECIPE,LINEAGE,cls.data_root)
        cls.data=study.load_dataset(cls.data_root);cls.recipe=cls.data['recipe']
        cls.original_bytes=ORIGINAL_RECIPE.read_bytes()
        cls.models=study.frozen_models(MODELS,cls.original_bytes,cls.recipe)
        cls.ablation_bytes=workflow.ablation_files(cls.old,cls.data,cls.models)['ablations.json']
        cls.cal_files=workflow.calibration_inventory(u.calibrate(cls.data,cls.models,cls.original_bytes),cls.data,cls.ablation_bytes)
        cls.cal_root=cls.root/'cal';original.publish_files(cls.cal_root,cls.cal_files)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_counts_semantic_disjointness_seeds_and_v2_tables(self):
        self.assertEqual(self.data['audit']['counts'],dict(calibration=450,evaluation=450,stress=900))
        oldgroups={r['family'] for r in self.old['records']};newgroups={r['family'] for r in self.data['records']}
        self.assertEqual(len(newgroups),60);self.assertFalse(oldgroups&newgroups)
        self.assertFalse({r['workload']['seed'] for r in self.old['records']}&{r['workload']['seed'] for r in self.data['records']})
        for panel in ('primary','airtime-low','airtime-high'):
            content=(self.data_root/f'{panel}-table.csv').read_bytes();manifest=json.loads((self.data_root/f'{panel}-table.json').read_bytes())
            self.assertEqual(manifest['table_sha256'],_sha256(content))
        self.assertEqual(self.recipe['splits'],study.recipe_from_bytes(RECIPE.read_bytes())['splits'])

    def test_recipe_lineage_and_duplicate_plan_rejected(self):
        with self.assertRaises(ValueError):study.recipe_from_bytes(_json_bytes({**self.recipe,'primary_rows':901}))
        with self.assertRaises(ValueError):study.lineage_from_bytes(b'{}',self.recipe)
        lineage=json.loads(LINEAGE.read_bytes());lineage['excluded_families']+=self.recipe['splits']['calibration'][:1]
        with self.assertRaisesRegex(ValueError,'family leakage'):study.planned_specs(self.recipe,(self.data_root/'parameters.json').read_bytes(),lineage)

    def test_source_tampering_and_output_overwrite_rejected(self):
        path=self.data_root/'inventory.json';content=path.read_bytes()
        try:
            parsed=json.loads(content);parsed['entries'][0]['group_id']='wrong'
            path.write_bytes(_json_bytes(parsed))
            with self.assertRaisesRegex(ValueError,'inventory mismatch'):study.load_dataset(self.data_root)
        finally:path.write_bytes(content)
        with self.assertRaises(FileExistsError):study.materialize(RECIPE,LINEAGE,self.data_root)
        self.assertEqual(path.read_bytes(),content)

    def test_no_label_families_and_invalid_calibration_membership(self):
        target=next(iter(self.models));c=u.calibration_from_bytes(self.cal_files[f'{target}-calibration.json'])
        c['excluded_families']=c['calibration_groups'][:12]
        for group in c['excluded_families']:del c['family_scores'][group]
        with self.assertRaisesRegex(ValueError,'insufficient'):u.validate_calibration(c)
        record=next(r for r in self.data['records'] if r['split']=='calibration')
        c=u.calibration_from_bytes(self.cal_files[f'{target}-calibration.json'])
        with self.assertRaisesRegex(ValueError,'fresh evaluation family'):
            u.predict_interval(self.models[target],record,c,original_recipe_bytes=self.original_bytes,study_recipe_bytes=self.data['recipe_bytes'])

    def test_calibration_does_not_read_evaluation_labels_or_fit(self):
        class LockedLabels(dict):
            def __getitem__(self,key):
                if key in original.TARGET_UNITS:raise AssertionError('locked label access')
                return super().__getitem__(key)
        data=copy.deepcopy(self.data)
        for record in data['records']:
            if record['split']!='calibration':record['row']=LockedLabels(record['row'])
        with mock.patch.object(e,'fit_regressor',side_effect=AssertionError('calibration fit')):
            self.assertEqual(u.calibrate(data,self.models,self.original_bytes),{k:v for k,v in self.cal_files.items() if k!='calibration-set.json'})

    def test_ablations_only_original_training_labels_and_frozen_alpha(self):
        class LockedLabels(dict):
            def __getitem__(self,key):
                if key in original.TARGET_UNITS:raise AssertionError('held-out ablation label access')
                return super().__getitem__(key)
        data=copy.deepcopy(self.old)
        for record in data['records']:
            if record['split']!='train':record['row']=LockedLabels(record['row'])
        self.assertEqual(workflow.ablation_files(data,self.data,self.models)['ablations.json'],self.ablation_bytes)
        parsed=e.explanation_from_bytes(self.ablation_bytes,self.data,self.models,kind='ablations')
        for target,features in parsed['results'].items():
            for j,name in enumerate(e.FEATURES):
                state=features[name]['estimator'];self.assertEqual(state['coefficients'][j],0)
                self.assertEqual(state['alpha'],self.models[target]['estimator']['alpha'])

    def test_calibration_roundtrip_and_compatibility(self):
        target=next(iter(self.models));content=self.cal_files[f'{target}-calibration.json'];artifact=u.calibration_from_bytes(content)
        self.assertEqual(artifact['rank'],30);self.assertEqual(len(artifact['family_scores']),30)
        self.assertEqual(_json_bytes(artifact),content)
        for key,value in [('q',artifact['q']+1),('rank',29),('calibration_version',True),('extra',0)]:
            bad=copy.deepcopy(artifact);bad[key]=value
            with self.assertRaises(ValueError):u.calibration_from_bytes(_json_bytes(bad))
        for key in ('dataset_sha256','model_sha256','recipe_sha256','split_sha256','lineage_sha256'):
            bad=copy.deepcopy(artifact);bad[key]='0'*64
            with self.assertRaises(ValueError):u.validate_binding(bad,self.models[target],self.data['recipe_bytes'],dataset_sha256=self.data['dataset_sha256'])
            with self.assertRaises(ValueError):u.validate_binding(bad,self.models[target],self.data['recipe_bytes'])
        with self.assertRaises(ValueError):u.calibration_from_bytes(b'{"q":1,"q":2}')
        record=copy.deepcopy(next(r for r in self.data['records'] if r['split']=='evaluation'))
        record['workload']['seed']+=1
        with self.assertRaisesRegex(ValueError,'seed/run identity'):
            u.predict_interval(self.models[target],record,artifact,original_recipe_bytes=self.original_bytes,study_recipe_bytes=self.data['recipe_bytes'])


    def test_permutation_blocks_and_invalid_combinations(self):
        records=[r for r in self.data['records'] if r['split']=='evaluation']
        indices=[0,1];settings=self.recipe['explainability']
        first=e.permuted_features(records,indices,seed=settings['seed'],repeat=0,axes=self.recipe['axes'])
        self.assertEqual(first,e.permuted_features(records,indices,seed=settings['seed'],repeat=0,axes=self.recipe['axes']))
        for duration in self.recipe['axes']['window_durations_ms']:
            rows=[(r,x) for r,x in zip(records,first) if r['workload']['window_duration_ms']==duration]
            for group in self.recipe['splits']['evaluation']:
                self.assertEqual(len({tuple(x[:2]) for r,x in rows if r['family']==group}),1)
        with self.assertRaises(ValueError):e.permuted_features(records[:-1],indices,seed=1,repeat=0,axes=self.recipe['axes'])
        with self.assertRaises(ValueError):e.permuted_features(records,[3],seed=1,repeat=0,axes={**self.recipe['axes'],'payload_sizes_bytes':[]})

    def test_evaluation_determinism_no_fit_or_recalibration_and_serialization(self):
        with mock.patch.object(e,'fit_regressor',side_effect=AssertionError('evaluation fit')),mock.patch.object(u,'calibrate',side_effect=AssertionError('recalibration')):
            first=workflow.evaluate(self.data,self.models,self.original_bytes,self.cal_root,self.ablation_bytes)
            self.assertEqual(first,workflow.evaluate(self.data,self.models,self.original_bytes,self.cal_root,self.ablation_bytes))
        report=json.loads(first['evaluation.json']);predictions=json.loads(first['predictions.json'])
        self.assertEqual(len(predictions['rows']),4050);self.assertFalse(report['refit_or_tuning_performed'])
        artifact=e.explanation_from_bytes(first['explanations.json'],self.data,self.models,kind='explanations')
        for target,result in artifact['results'].items():
            self.assertEqual(result['permutation']['features']['tx_power_dbm']['mean'],0)
        bad=json.loads(first['explanations.json']);target=next(iter(bad['results']));bad['results'][target]['contributions'][0]['prediction']+=1
        with self.assertRaises(ValueError):e.explanation_from_bytes(_json_bytes(bad),self.data,self.models,kind='explanations')
        bad=json.loads(self.ablation_bytes);bad['model_sha256'][target]='0'*64
        with self.assertRaises(ValueError):e.explanation_from_bytes(_json_bytes(bad),self.data,self.models,kind='ablations')

    def test_prediction_cli_default_and_optional_interval_output_safety(self):
        target=next(iter(self.models));record=next(r for r in self.data['records'] if r['split']=='evaluation');output=self.root/'prediction.json'
        args=['predict','--model',str(MODELS/f'{target}-chosen.json'),'--recipe',str(ORIGINAL_RECIPE),'--artifact-dir',str(self.data_root/record['entry']['path']),'--output',str(output)]
        self.assertEqual(prediction_cli.main(args),0);default=json.loads(output.read_bytes());self.assertEqual(default['prediction_version'],1)
        output.unlink();args+=['--calibration',str(self.cal_root/f'{target}-calibration.json'),'--study-recipe',str(RECIPE)]
        self.assertEqual(prediction_cli.main(args),0);interval=json.loads(output.read_bytes())
        self.assertEqual(interval['prediction_version'],2);self.assertEqual(interval['value'],default['value'])
        self.assertLessEqual(interval['interval']['lower'],interval['value']);saved=output.read_bytes()
        self.assertEqual(prediction_cli.main(args),1);self.assertEqual(output.read_bytes(),saved)
        output.unlink();self.assertEqual(prediction_cli.main(args[:-2]),1);self.assertFalse(output.exists())
        spoof=self.root/'spoof-calibration.json'
        parsed=json.loads(self.cal_files[f'{target}-calibration.json']);parsed['dataset_sha256']='0'*64;spoof.write_bytes(_json_bytes(parsed))
        args[args.index('--calibration')+1]=str(spoof)
        self.assertEqual(prediction_cli.main(args),1);self.assertFalse(output.exists())
