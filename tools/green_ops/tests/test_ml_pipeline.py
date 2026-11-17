# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ml_pipeline as ml
from ml_dataset import materialize_dataset,load_dataset
from analytical_reference import _json_bytes
from tools.green_ops.tests.test_ml_dataset import small_recipe
from tools.green_ops.tests.test_analytical_design import save_bundle
from tools.green_ops.tests.test_analytical_reference import workload
from analytical_design import load_design_record


class NumericalRegressionTests(unittest.TestCase):
    def test_independent_one_column_ridge_solution_and_mean_baseline(self):
        X=[[x,0,19,1000] for x in (1,2,3)];y=[5,7,9]
        model=ml.fit_regressor(X,y,alpha=3)
        self.assertAlmostEqual(model['coefficients'][0]/model['feature_scales'][0],1)
        self.assertEqual(model['intercept'],7)
        for prediction,expected in zip(ml.predict_matrix(model,X),[6,7,8]):self.assertAlmostEqual(prediction,expected)
        baseline=ml.fit_regressor(X,y,kind='training_mean')
        self.assertEqual(ml.predict_matrix(baseline,X),[7,7,7])

    def test_rank_deficient_and_constant_features_are_stable(self):
        X=[[x,2*x,19,1000] for x in (1,2,3)];y=[4,7,10]
        model=ml.fit_regressor(X,y,alpha=3)
        for actual,expected in zip(ml.predict_matrix(model,X),[5,7,9]):self.assertAlmostEqual(actual,expected)
        self.assertAlmostEqual(model['coefficients'][0],model['coefficients'][1])
        constant=ml.fit_regressor([[1,1,19,1000]]*3,[2,4,6],alpha=0.01)
        self.assertEqual(constant['constant_features'],[0,1,2,3])
        fractional=ml.fit_regressor([[0.1,1,19,1000]]*7,list(range(7)),alpha=1)
        self.assertEqual(fractional['constant_features'],[0,1,2,3])
        self.assertEqual(constant['coefficients'],[0,0,0,0])
        self.assertEqual(ml.predict_matrix(constant,[[1,1,19,1000]]),[4])

    def test_preprocessing_is_train_only_and_predictions_do_not_mutate_model(self):
        model=ml.fit_regressor([[1,10,19,1000],[3,20,19,1000]],[2,4],alpha=1)
        self.assertEqual(model['feature_means'],[2,15,19,1000])
        for actual,expected in zip(model['feature_scales'],[1,5,1,1]):self.assertAlmostEqual(actual,expected)
        original=copy.deepcopy(model)
        ml.predict_matrix(model,[[1000,1000000,19,1000]])
        self.assertEqual(model,original)

    def test_determinism_no_prediction_clipping_and_invalid_numbers(self):
        X=[[1,1,19,1000],[2,2,19,2000]];y=[0,1]
        a=ml.fit_regressor(X,y,alpha=0.01)
        self.assertEqual(a,ml.fit_regressor(X,y,alpha=0.01))
        self.assertLess(ml.predict_matrix(a,[[-100,-100,19,-100]])[0],0)
        for value in (True,None,'1',float('nan'),float('inf')):
            bad=copy.deepcopy(X);bad[0][0]=value
            with self.subTest(value=value),self.assertRaises(ValueError):ml.fit_regressor(bad,y)
        for alpha in (0,-1,True,float('nan')):
            with self.subTest(alpha=alpha),self.assertRaises(ValueError):ml.fit_regressor(X,y,alpha=alpha)
        with self.assertRaises(ValueError):ml.fit_regressor([],[])

    def test_metric_oracles_and_undefined_r2(self):
        score=ml.metrics([1,2,3],[2,2,2])
        self.assertAlmostEqual(score['mae'],2/3);self.assertAlmostEqual(score['rmse'],math.sqrt(2/3));self.assertAlmostEqual(score['r2'],0)
        for truth,predictions,reason in (([],[],'no_labels'),([2],[2],'fewer_than_two_labels'),([2,2],[2,2],'constant_truth')):
            result=ml.metrics(truth,predictions);self.assertIsNone(result['r2']);self.assertEqual(result['r2_undefined_reason'],reason)
        with self.assertRaises(ValueError):ml.metrics([1],[float('inf')])


class ModelArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name);self.recipe=self.root/'recipe.json';self.recipe.write_bytes(_json_bytes(small_recipe()))
        materialize_dataset(self.recipe,self.root/'data');self.dataset=load_dataset(self.root/'data')
        self.train=[r for r in self.dataset['records'] if r['split']=='train'];self.target='target_total_energy_mj'
        X,y,_,_=ml.prepare_target(self.train,self.target)
        self.artifact=ml.package_model(ml.fit_regressor(X,y),self.target,self.dataset,self.train)

    def test_strict_roundtrip_prediction_and_compatibility(self):
        encoded=ml.model_to_bytes(self.artifact)
        loaded=ml.model_from_bytes(encoded)
        self.assertEqual(ml.predict_record(loaded,self.train[0]),ml.predict_record(self.artifact,self.train[0]))
        for name,value in (('feature_contract_version',99),('feature_order',['target_total_energy_mj']),('target','ping_rtt_latency_ms'),('extra',1)):
            bad=copy.deepcopy(self.artifact);bad[name]=value
            with self.subTest(name=name),self.assertRaises(ValueError):ml.model_to_bytes(bad)
        with self.assertRaises(ValueError):ml.model_from_bytes(b'{"a":1,"a":2}')
        with self.assertRaises(ValueError):ml.model_from_bytes(b'{"bad":NaN}')

    def test_missing_label_is_excluded_and_invalid_x_cannot_hide_behind_it(self):
        zero=save_bundle(self.root/'zero',workload(run_id='zero',offered_packets=0))
        missing=load_design_record(zero)
        X,y,used,excluded=ml.prepare_target([self.train[0],missing],'target_energy_per_delivered_packet_uj')
        self.assertEqual(len(X),1);self.assertEqual(len(y),1);self.assertEqual(excluded,['zero'])
        model=ml.fit_regressor(X,y,kind='training_mean')
        report,predictions=ml.evaluate_estimator(model,[self.train[0],missing],'target_energy_per_delivered_packet_uj')
        self.assertEqual(report['missing_label_count'],1);self.assertEqual(report['sample_count'],1)
        self.assertIsNone(predictions[1]['truth'])
        self.assertEqual(report['per_family'][missing['row']['evaluation_group_id']]['r2_undefined_reason'],'no_labels')
        bad=copy.deepcopy(missing);bad['row']['payload_size_bytes']=None
        with self.assertRaises(ValueError):ml.prepare_target([bad],'target_energy_per_delivered_packet_uj')

    def test_scope_and_availability_block_wrong_prediction_domain(self):
        stress=next(r for r in self.dataset['records'] if r['split']=='stress')
        with self.assertRaises(ValueError):ml.predict_record(self.artifact,stress)
        self.assertTrue(math.isfinite(ml.predict_record(self.artifact,stress,domain='declared_stress')))
        bad=copy.deepcopy(self.train[0]);bad['manifest']['available_fields']=[]
        with self.assertRaises(ValueError):ml.predict_record(self.artifact,bad)
        bad=copy.deepcopy(self.artifact);bad['training']['train_group_ids']=bad['training']['split_membership']['test']
        with self.assertRaises(ValueError):ml.model_to_bytes(bad)

    def test_targets_ids_and_outcomes_never_enter_features(self):
        record=copy.deepcopy(self.train[0])
        features=ml.record_features(record)
        self.assertEqual(len(features),4)
        self.assertEqual(features,[record['row'][name] for name in self.artifact['feature_order']])
        self.assertFalse(set(self.artifact['feature_order'])&{'seed','run_id','rx_operations','target_total_energy_mj'})
