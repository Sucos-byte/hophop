# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import contextlib
import copy
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from analytical_reference import _json_bytes,generate_analytical_artifact
from budget_policy import policy_from_bytes,validate_policy,upper_budget,regression,aggregate
from battery_projection import project_battery,battery_decision
from week8_dataset import recipe_from_bytes,planned_specs
from gate_evidence import FrozenEvidence
import green_ops_gatekeeper as gate
import atomic_outputs

ROOT=Path(__file__).resolve().parents[3]
POLICY=ROOT/'tools/green_ops/policies/green_ops_budget.json'


def battery():
    return dict(capacity_mah=1000,voltage_v=3.6,usable_fraction=.8,conversion_efficiency=.9,year_days=365.25,
        target_years=5,power_basis='load_side_before_conversion',
        workload_profile=dict(kind='run_average',repeat='continuous_same_workload',duty_cycle_included=True))


class ComparisonTests(unittest.TestCase):
    def test_upper_budget_equality_crossing_and_fail(self):
        self.assertEqual(upper_budget([0,10],10)[0],'PASS')
        self.assertEqual(upper_budget([10,11],10)[0],'ABSTAIN')
        self.assertEqual(upper_budget([11,12],10)[0],'FAIL')
        self.assertEqual(upper_budget([10,10],10)[0],'PASS')

    def test_regression_absolute_relative_and_zero_baseline(self):
        self.assertEqual(regression([10,12],[10,10],2)[0],'PASS')
        self.assertEqual(regression([13,14],[10,10],2)[0],'FAIL')
        self.assertEqual(regression([12,13],[10,10],2)[0],'ABSTAIN')
        self.assertEqual(regression([100,110],[100,100],10,relative=True)[0],'PASS')
        self.assertEqual(regression([100,111],[100,100],10,relative=True)[0],'ABSTAIN')
        self.assertEqual(regression([111,112],[100,100],10,relative=True)[0],'FAIL')
        self.assertEqual(regression([0,0],[0,0],0,relative=True)[0],'ABSTAIN')
        self.assertEqual(regression([1,1],[0,0],1)[0],'PASS')
        self.assertEqual(regression([1,1],None,0)[0],'ABSTAIN')
        self.assertEqual(aggregate(['PASS','ABSTAIN','FAIL']),'FAIL');self.assertEqual(aggregate(['FAIL','ERROR']),'ERROR')

    def test_regression_does_not_round_allowed_relative_excess_upward(self):
        excess=math.nextafter(110,math.inf)
        self.assertEqual(regression([excess,excess],[100,100],10,relative=True)[0],'FAIL')

    def test_nonfinite_reversed_and_numeric_overflow(self):
        for interval in ([float('nan'),1],[0,float('inf')],[2,1],[True,1]):
            with self.assertRaises(ValueError):upper_budget(interval,1)
        with self.assertRaises(ValueError):regression([1,1],[1e308,1e308],1e308)
        with self.assertRaises(ValueError):regression([1,1],[1e308,1e308],1e308,relative=True)

    def test_strict_policy_units_unknown_keys_and_json(self):
        original=policy_from_bytes(POLICY.read_bytes())
        self.assertEqual(validate_policy(original),original)
        for key,value in [('budget_version',True),('feature_contract_version',2),('research_only',False),('extra',1),('criteria',{})]:
            bad=copy.deepcopy(original);bad[key]=value
            with self.assertRaises(ValueError):validate_policy(bad)
        for key,value in [('unit','W'),('target',[]),('threshold',float('nan')),('threshold',-1)]:
            bad=copy.deepcopy(original);bad['criteria'][0][key]=value
            with self.assertRaises(ValueError):validate_policy(bad)
        for content in (b'{"a":1,"a":2}',b'{"a":NaN}'):
            with self.assertRaises(ValueError):policy_from_bytes(content)
        bad=copy.deepcopy(original);bad['uncertainty']['minimum_family_coverage']=.8
        with self.assertRaises(ValueError):validate_policy(bad)


class BatteryTests(unittest.TestCase):
    def test_independent_units_efficiency_once_and_year_length(self):
        spec=battery();p=project_battery(spec,dict(point=1,interval=[1,1]))
        # 1Ah * 3.6V * .8 * .9 = 2.592Wh, 2592 hours at 1mW.
        self.assertAlmostEqual(p['load_energy_mwh'],2592)
        self.assertAlmostEqual(p['point_years'],2592/(365.25*24))
        self.assertEqual(p['lifetime_years'],[p['point_years']]*2)
        spec['target_years']=p['point_years'];self.assertEqual(battery_decision(project_battery(spec,dict(point=1,interval=[1,1])))[0],'PASS')
        spec['target_years']=1;self.assertEqual(battery_decision(project_battery(spec,dict(point=1,interval=[1,1])))[0],'FAIL')
        spec['target_years']=.3;self.assertEqual(battery_decision(project_battery(spec,dict(point=1,interval=[.5,2])))[0],'ABSTAIN')

    def test_component_states_average_and_no_double_duty(self):
        spec=battery();spec['workload_profile']=dict(kind='component_states',compatible_states_confirmed=True,complete_cycle=True,compatibility_id='exclusive_same_load_boundary',
            states=[dict(state_id='active',power_mw=10,interval_mw=[8,12],time_fraction=.1),dict(state_id='idle',power_mw=0,interval_mw=[0,0],time_fraction=.9)])
        p=project_battery(spec,None);self.assertEqual(p['mean_power_mw'],1)
        self.assertAlmostEqual(p['lifetime_years'][0],2592/1.2/8766)
        spec['workload_profile']['compatible_states_confirmed']=False
        self.assertFalse(project_battery(spec,None)['available'])
        spec=battery();spec['workload_profile']['duty_cycle']=.1
        with self.assertRaises(ValueError):project_battery(spec,dict(point=10,interval=[10,10]))

    def test_invalid_state_fractions_and_efficiency_boundary(self):
        spec=battery();spec['conversion_efficiency']=1;spec['usable_fraction']=1
        self.assertEqual(project_battery(spec,dict(point=1,interval=[1,1]))['load_energy_mwh'],3600)
        spec['workload_profile']=dict(kind='component_states',compatible_states_confirmed=True,complete_cycle=True,compatibility_id='test',
            states=[dict(state_id='only',power_mw=1,interval_mw=[1,1],time_fraction=.5)])
        with self.assertRaises(ValueError):project_battery(spec,None)
        spec['workload_profile']['states'][0]['time_fraction']=1
        spec['workload_profile']['states'][0]['interval_mw']=[2,3]
        with self.assertRaises(ValueError):project_battery(spec,None)

    def test_missing_zero_negative_and_overflow_battery(self):
        spec=battery();spec['workload_profile']=None;self.assertFalse(project_battery(spec,None)['available'])
        for power in (0,-1):self.assertFalse(project_battery(battery(),dict(point=power,interval=[power,power]))['available'])
        self.assertFalse(project_battery(battery(),dict(point=1,interval=[0,2]))['available'])
        self.assertFalse(project_battery(battery(),dict(point=1,interval=None))['available'])
        for key,value in [('capacity_mah',float('inf')),('conversion_efficiency',1.1),('year_days',0),('usable_fraction',0)]:
            spec=battery();spec[key]=value
            with self.assertRaises(ValueError):project_battery(spec,None)
        spec=battery();spec.update(capacity_mah=1e308,voltage_v=1e308)
        with self.assertRaises(ValueError):project_battery(spec,None)


class GateIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.recipe_path=ROOT/'tools/green_ops/recipes/week8-uncertainty-v1.json';r=recipe_from_bytes(cls.recipe_path.read_bytes())
        specs=planned_specs(r,(ROOT/r['parameters_path']).read_bytes(),json.loads((ROOT/'docs/results/week8/lineage.json').read_bytes()))
        candidates=sorted((s for s in specs if s['split']=='evaluation'),key=lambda s:s['workload']['run_id'])
        first=candidates[0];different=next(s for s in candidates if s['workload']['window_duration_ms']!=first['workload']['window_duration_ms'])
        shift=next(s for s in specs if s['panel']=='airtime-high' and s['workload']['evaluation_group_id']==first['workload']['evaluation_group_id'] and s['workload']['window_duration_ms']==first['workload']['window_duration_ms'] and s['workload']['repetition']==first['workload']['repetition'])
        for name,spec in [('candidate',first),('different',different),('shift',shift)]:
            path=cls.root/name;path.mkdir();run=spec['workload']
            context=dict(available_fields=list(gate.PRE_RUN_FEATURES),planned_window_duration_ms=run['window_duration_ms'],completed_as_planned=True)
            files=generate_analytical_artifact(spec['parameters'],_json_bytes(run),(ROOT/r['assumptions_path']).read_bytes(),prediction_context_bytes=_json_bytes(context))
            for filename,content in files.items():(path/filename).write_bytes(content)
        cls.source=FrozenEvidence(ROOT/'docs/results/week7-regression-v1/training',ROOT/'docs/results/week8/calibration',ROOT/'tools/green_ops/recipes/week7-regression-v1.json',cls.recipe_path,ROOT/'docs/results/week8')
        cls.candidate=cls.source.load(cls.root/'candidate',revision='candidate-code-label')
        cls.policy=policy_from_bytes(POLICY.read_bytes())

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def research(self):
        p=copy.deepcopy(self.policy);p['uncertainty']['allow_unvalidated_research_intervals']=True;return p

    def test_default_abstention_two_part_override_and_determinism(self):
        result=gate.decide(self.policy,self.candidate)
        self.assertEqual(result['status'],'ABSTAIN');self.assertTrue(result['blocks_ci'])
        self.assertIn('observed_family_coverage_inadequate',result['reason_codes'])
        self.assertEqual(gate.decide(self.research(),self.candidate)['status'],'ABSTAIN')
        self.assertEqual(gate.decide(self.policy,self.candidate,allow_research_override=True)['status'],'ABSTAIN')
        passed=gate.decide(self.research(),self.candidate,allow_research_override=True)
        self.assertEqual(passed['status'],'PASS');self.assertTrue(passed['research_override_used'])
        self.assertIn('UNVALIDATED',passed['evidence_label'])
        self.assertEqual(_json_bytes(passed),_json_bytes(gate.decide(self.research(),self.candidate,allow_research_override=True)))
        self.assertIn('model_attribution_not_physical_root_cause',_json_bytes(passed).decode())

    def test_direct_fail_crossing_and_missing_baseline(self):
        for ceiling,status in [(100,'FAIL'),(150,'ABSTAIN'),(200,'PASS')]:
            p=self.research();p['criteria'][0]['threshold']=ceiling
            self.assertEqual(gate.decide(p,self.candidate,allow_research_override=True)['status'],status)
        p=self.research();p['criteria'][0].update(kind='regression_relative',unit='percent',threshold=10)
        self.assertEqual(gate.decide(p,self.candidate,allow_research_override=True)['reason_codes'],['baseline_missing'])

    def test_regression_comparability_and_commit_nonobservability(self):
        p=self.research();p['criteria'][0].update(kind='regression_relative',unit='percent',threshold=25)
        baseline=copy.deepcopy(self.candidate);baseline['revision']='different-commit'
        r=gate.decide(p,self.candidate,baseline,allow_research_override=True)
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['criteria'][0]['point_regression_percent'],0)
        self.assertFalse(r['execution_regression_observable_from_commit_identity'])
        other=self.source.load(self.root/'different')
        self.assertEqual(gate.decide(p,self.candidate,other,allow_research_override=True)['reason_codes'],['incomparable_workload_windows_or_context'])
        p['criteria'][0]['threshold']=0
        self.assertEqual(gate.decide(p,self.candidate,baseline,allow_research_override=True)['status'],'ABSTAIN')

    def test_zero_baseline_and_point_percent_independent_math_fixture(self):
        # Internal pure-engine numerical fixtures, never accepted by file adapter as measured evidence.
        p=self.research();p['criteria'][0].update(kind='regression_relative',unit='percent',threshold=10)
        c=copy.deepcopy(self.candidate);b=copy.deepcopy(c);key='target_mean_power_mw'
        c['predictions'][key].update(point=110,interval=[110,110]);b['predictions'][key].update(point=100,interval=[100,100])
        r=gate.decide(p,c,b,allow_research_override=True);self.assertEqual(r['status'],'PASS');self.assertEqual(r['criteria'][0]['point_regression_percent'],10)
        b['predictions'][key].update(point=0,interval=[0,0])
        r=gate.decide(p,c,b,allow_research_override=True);self.assertEqual(r['status'],'ABSTAIN');self.assertIsNone(r['criteria'][0]['point_regression_percent'])

    def test_provenance_context_shift_and_incompatibility(self):
        p=self.research();other=copy.deepcopy(self.candidate);other['provenance']='measured'
        self.assertEqual(gate.decide(p,other,allow_research_override=True)['reason_codes'],['unsupported_provenance'])
        other=copy.deepcopy(self.candidate);other['prediction_context']['completed_as_planned']=False
        self.assertEqual(gate.decide(p,other,allow_research_override=True)['status'],'ABSTAIN')
        shifted=self.source.load(self.root/'shift',domain='declared_stress')
        self.assertEqual(gate.decide(p,shifted,allow_research_override=True)['reason_codes'],['assumption_shift_not_accepted'])
        p['uncertainty']['allow_assumption_shift']=True
        self.assertEqual(gate.decide(p,shifted,allow_research_override=True)['status'],'PASS')
        for key,value in [('feature_contract_version',2),('model_sha256',{}),('feature_profile','other')]:
            other=copy.deepcopy(self.candidate);other[key]=value
            with self.assertRaises(ValueError):gate.decide(p,other)
        other=copy.deepcopy(self.candidate);other['predictions']['target_mean_power_mw']['unit']='W'
        with self.assertRaises(ValueError):gate.decide(p,other)

    def test_battery_default_abstention_and_research_projection(self):
        p=self.research();p['criteria']=[];p['battery']=battery()
        r=gate.decide(p,self.candidate,allow_research_override=True);self.assertEqual(r['status'],'FAIL')
        self.assertLess(r['battery_projection']['point_years'],1)
        p['battery']['workload_profile']=None
        self.assertEqual(gate.decide(p,self.candidate,allow_research_override=True)['status'],'ABSTAIN')
        p['battery']=battery();p['uncertainty']['allow_unvalidated_research_intervals']=False
        self.assertEqual(gate.decide(p,self.candidate)['status'],'ABSTAIN')

    def cli(self,policy,output,extra=()):
        path=self.root/(output+'.policy.json');path.write_bytes(_json_bytes(policy))
        args=['--policy',str(path),'--candidate',str(self.root/'candidate'),'--output',str(self.root/output),*extra]
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):code=gate.main(args)
        return code,json.loads((self.root/output).read_bytes()) if (self.root/output).exists() else None

    def test_absolute_targets_missing_intervals_and_aggregate_fail_precedence(self):
        p=self.research();p['criteria']=[]
        for i,(target,unit) in enumerate(gate.TARGET_UNITS.items()):
            limit=self.candidate['predictions'][target]['interval'][1]
            p['criteria'].append(dict(id=f'criterion-{i}',kind='absolute_upper',target=target,unit=unit,threshold=limit))
        self.assertEqual(gate.decide(p,self.candidate,allow_research_override=True)['status'],'PASS')
        c=copy.deepcopy(self.candidate);c['predictions']['target_mean_power_mw']['interval']=None
        self.assertEqual(gate.decide(p,c,allow_research_override=True)['status'],'ABSTAIN')
        p['criteria'][1]['threshold']=0
        self.assertEqual(gate.decide(p,c,allow_research_override=True)['status'],'FAIL')

    def test_component_assumptions_cannot_bypass_prediction_context(self):
        p=self.research();p['criteria']=[];p['battery']=battery()
        p['battery']['workload_profile']=dict(kind='component_states',compatible_states_confirmed=True,complete_cycle=True,compatibility_id='exclusive',
            states=[dict(state_id='idle',power_mw=1,interval_mw=[1,1],time_fraction=1)])
        c=copy.deepcopy(self.candidate);c['prediction_context']['completed_as_planned']=False
        self.assertEqual(gate.decide(p,c,allow_research_override=True)['status'],'ABSTAIN')

    def test_reference_tampering_and_model_tampering(self):
        reference=self.root/'bad-reference';(reference/'evaluation').mkdir(parents=True)
        (reference/'evaluation/evaluation.json').write_bytes((ROOT/'docs/results/week8/evaluation/evaluation.json').read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'reference evidence hash'):
            FrozenEvidence(ROOT/'docs/results/week7-regression-v1/training',ROOT/'docs/results/week8/calibration',ROOT/'tools/green_ops/recipes/week7-regression-v1.json',self.recipe_path,reference)
        models=self.root/'bad-models';models.mkdir()
        for source in (ROOT/'docs/results/week7-regression-v1/training').glob('*.json'):(models/source.name).write_bytes(source.read_bytes())
        path=models/'target_mean_power_mw-chosen.json';path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'model hash'):
            FrozenEvidence(models,ROOT/'docs/results/week8/calibration',ROOT/'tools/green_ops/recipes/week7-regression-v1.json',self.recipe_path,ROOT/'docs/results/week8')

    def test_all_exit_codes_structured_errors_and_no_fit(self):
        with mock.patch('ml_pipeline.fit_regressor',side_effect=AssertionError('gate fit')),mock.patch('uncertainty.calibrate',side_effect=AssertionError('gate calibrate')):
            for name,threshold,override,expected in [('pass',200,True,0),('fail',100,True,2),('abstain',200,False,3)]:
                p=self.research() if override else copy.deepcopy(self.policy);p['criteria'][0]['threshold']=threshold
                code,r=self.cli(p,name+'.json',['--allow-research-override'] if override else [])
                self.assertEqual(code,expected);self.assertEqual(r['exit_code'],expected);self.assertEqual(r['blocks_ci'],expected!=0)
        malformed=copy.deepcopy(self.policy);malformed['criteria'][0]['unit']='W'
        code,r=self.cli(malformed,'error.json');self.assertEqual(code,1);self.assertEqual(r['status'],'ERROR')
        self.assertIn('policy',r['artifact_sha256'])

    def test_tampering_collisions_and_atomic_rollback(self):
        path=self.root/'candidate/dataset.csv';saved=path.read_bytes()
        try:
            path.write_bytes(saved.replace(b'148',b'149',1)+b'\n')
            with self.assertRaises(ValueError):self.source.load(self.root/'candidate')
        finally:path.write_bytes(saved)
        code,r=self.cli(self.research(),'existing.json',['--allow-research-override']);self.assertEqual(code,0)
        before=(self.root/'existing.json').read_bytes();code,_=self.cli(self.policy,'existing.json')
        self.assertEqual(code,1);self.assertEqual((self.root/'existing.json').read_bytes(),before)
        with mock.patch.object(atomic_outputs.os,'replace',side_effect=OSError('simulated publish failure')):
            code,r=self.cli(self.policy,'rollback.json')
        self.assertEqual(code,1);self.assertIsNone(r);self.assertFalse((self.root/'rollback.json').exists())
        output=self.root/'candidate/new.json'
        with contextlib.redirect_stderr(io.StringIO()):code=gate.main(['--policy',str(POLICY),'--candidate',str(self.root/'candidate'),'--output',str(output)])
        self.assertEqual(code,1);self.assertFalse(output.exists())
        original=(ROOT/'docs/results/week8/calibration/calibration-set.json').read_bytes()
        altered=self.root/'bad-cal';altered.mkdir();(altered/'calibration-set.json').write_bytes(original+b' ')
        with self.assertRaisesRegex(ValueError,'inventory mismatch'):
            FrozenEvidence(ROOT/'docs/results/week7-regression-v1/training',altered,ROOT/'tools/green_ops/recipes/week7-regression-v1.json',self.recipe_path,ROOT/'docs/results/week8')
