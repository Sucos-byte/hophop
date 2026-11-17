# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
import json
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fault_injection as f
from analytical_reference import _json_bytes,simulate_reference

ROOT=Path(__file__).resolve().parents[3]


def model():
    m=json.loads((ROOT/'tools/green_ops/models/nrf9151-dect-reference-v1.json').read_bytes())
    m['sources']={}
    for name,value in [('idle',1),('rx',2),('tx',3)]:m['currents_ma'][name].update(value=value,min=value,max=value,basis='assumption',source_id=None)
    m['conditions']['supply_v']=1
    for name,value in [('prepare',0),('tx_base',1000),('tx_per_byte',0),('rx',1000),('backoff',1000)]:
        m['timing_us'][name].update(value=value,min=value if name=='rx' else 0,max=max(1000,value),basis='assumption',source_id=None)
    m['loss_probability'].update(value=0,min=0,max=1)
    return m


def assumptions():
    a=json.loads((ROOT/'tools/green_ops/faults/assumptions-v1.json').read_bytes())
    a['cpu_increment_ma'].update(value=1,min=0,max=2)
    a['lower_tx_current_ma'].update(value=2,min=1,max=3)
    return a


class FaultAccountingTests(unittest.TestCase):
    def setUp(self):self.m=model();self.a=assumptions();self.intent=f.make_intent(8,100,100,19,0)
    def sim(self,kind='none',severity=0,intent=None):return f.simulate_fault(self.m,intent or self.intent,self.a,dict(kind=kind,severity=severity))

    def test_independent_baseline_and_time_energy_accounting(self):
        r=self.sim();self.assertEqual(r['state_duration_us'],dict(idle=98000,tx=1000,rx=1000,cpu_busy=0))
        # 98ms*1mA +1ms*3mA+1ms*2mA at1V =.103mJ.
        self.assertAlmostEqual(r['total_energy_mj'],.103);self.assertAlmostEqual(r['mean_power_mw'],1.03)
        self.assertAlmostEqual(r['energy_per_delivered_packet_uj'],103)
        old=simulate_reference(self.m,self.intent);self.assertEqual(old['total_energy_mj'],r['total_energy_mj'])
        self.assertEqual(r['delivered_packets'],1);self.assertEqual(r['observation_us'],100000)

    def test_cpu_replaces_free_idle_before_integration_without_double_count(self):
        r=self.sim('cpu_busy_poll',500)
        self.assertEqual(r['state_duration_us']['cpu_busy'],49000);self.assertEqual(r['state_duration_us']['idle'],49000)
        self.assertAlmostEqual(r['total_energy_mj'],.152)
        self.assertEqual(sum(r['state_duration_us'].values()),100000)
        self.assertEqual(r['state_current_ma']['cpu_busy'],2)
        self.assertEqual(r['tx_attempts'],1)

    def test_power_lock_keeps_intended_power_and_changes_actual_tx_current(self):
        intent=f.make_intent(8,100,100,14,0)
        b=self.sim(intent=intent);r=self.sim('tx_power_lock',5,intent)
        self.assertEqual(intent['tx_power_dbm'],14);self.assertEqual(r['requested_tx_power_dbm'],14);self.assertEqual(r['actual_tx_power_dbm'],19)
        self.assertEqual(b['state_duration_us'],r['state_duration_us']);self.assertEqual(b['state_current_ma']['tx'],2);self.assertEqual(r['state_current_ma']['tx'],3)
        self.assertAlmostEqual(r['total_energy_mj']-b['total_energy_mj'],.001)

    def test_seeded_bursty_storm_not_uniform_retry_multiplier(self):
        intent=f.make_intent(8,100,400,19,0)
        r=self.sim('bursty_retry_storm',2,intent)
        self.assertEqual(r['burst_packet_indices'],[0,1]);self.assertEqual(r['tx_attempts'],8)
        self.assertEqual([len(p['fragments'][0]['attempts']) for p in r['packets']],[3,3,1,1])
        self.assertEqual(r['delivered_packets'],4)
        # Extra4 services: TX4ms,RX4ms replace idle plus backoff remains idle.
        self.assertAlmostEqual(r['total_energy_mj']-self.sim(intent=intent)['total_energy_mj'],.012)
        for p in r['packets'][:2]:self.assertEqual([a['forced_failure'] for a in p['fragments'][0]['attempts']],[True,True,False])

    def test_beacons_charge_prepare_listen_without_data_delivery_credit(self):
        r=self.sim('beacon_hyper_wakeup',3)
        self.assertEqual(len(r['beacons']),3);self.assertEqual(r['delivered_packets'],1)
        self.assertEqual(r['rx_operations'],4);self.assertEqual(r['tx_attempts'],1)
        self.assertAlmostEqual(r['total_energy_mj']-.103,.003)
        self.assertTrue(all(not b['logical_data_delivery'] for b in r['beacons']))

    def test_fragment_bloat_has_per_fragment_services_and_logical_denominator(self):
        self.m['timing_us']['tx_per_byte'].update(value=10,min=0,max=10)
        r=self.sim('payload_fragmentation_bloat',1)
        packet=r['packets'][0];self.assertEqual([x['payload_bytes'] for x in packet['fragments']],[4,4])
        self.assertEqual([x['wire_bytes'] for x in packet['fragments']],[12,12]);self.assertEqual(r['tx_attempts'],2)
        self.assertEqual(r['delivered_packets'],1);self.assertEqual(r['logical_fragments'],2)
        self.assertAlmostEqual(r['energy_per_delivered_packet_uj'],r['total_energy_mj']*1000)
        self.assertEqual(r['state_duration_us']['tx'],2240)

    def test_zero_fault_controls_match_full_baseline_ledger(self):
        for kind in f.KINDS:
            baseline=self.sim();r=self.sim(kind,0)
            self.assertEqual(r,baseline,kind)

    def test_null_delivery_labels_and_half_open_acceptance(self):
        self.m['loss_probability']['value']=1
        r=self.sim('payload_fragmentation_bloat',1)
        self.assertEqual(r['delivered_packets'],0);self.assertIsNone(r['energy_per_delivered_packet_uj']);self.assertGreater(r['total_energy_mj'],0)
        self.m['loss_probability']['value']=0
        self.m['timing_us']['tx_base']['value']=99000;self.m['timing_us']['tx_base']['max']=99000
        intent=f.make_intent(8,100,100,19,0,max_attempts=1)
        r=self.sim(intent=intent);self.assertEqual(r['delivered_packets'],0);self.assertEqual(r['state_duration_us']['idle'],0)

    def test_infeasible_slot_rejected_before_any_energy_integration(self):
        from unittest import mock
        with mock.patch.object(f,'integrate_states',side_effect=AssertionError('integrated infeasible schedule')):
            with self.assertRaises(f.InfeasibleSchedule):self.sim('beacon_hyper_wakeup',100)
            r=f.execution_or_infeasible(self.m,self.intent,self.a,dict(kind='beacon_hyper_wakeup',severity=100))
        self.assertEqual(r['status'],'INFEASIBLE');self.assertIsNone(r['total_energy_mj'])

    def test_zero_offers_and_time_remainder(self):
        intent=f.make_intent(8,100,250,19,1,offered_packets=0)
        r=self.sim('cpu_busy_poll',1000,intent)
        self.assertEqual(r['state_duration_us']['cpu_busy'],250000);self.assertIsNone(r['energy_per_delivered_packet_uj'])
        self.assertEqual(r['total_energy_mj'],.5)
        r=self.sim('beacon_hyper_wakeup',1,intent);self.assertEqual(len(r['beacons']),2)
        self.assertEqual(sum(r['state_duration_us'].values()),250000)

    def test_near_boundary_oracle_equality_and_strict_excess(self):
        intent=f.make_intent(8,100,100,19,1,offered_packets=0)
        b=self.sim(intent=intent);r=self.sim('cpu_busy_poll',50,intent)
        self.assertAlmostEqual(r['total_energy_mj'],.105)
        self.assertFalse(f.oracle_violation(b['total_energy_mj'],r['total_energy_mj'],5))
        self.assertTrue(f.oracle_violation(b['total_energy_mj'],self.sim('cpu_busy_poll',51,intent)['total_energy_mj'],5))
        self.assertFalse(f.oracle_violation(100,105,5));self.assertTrue(f.oracle_violation(100,math.nextafter(105,math.inf),5))
        self.assertIsNone(f.oracle_violation(100,None,5))
        self.assertGreater(self.sim('cpu_busy_poll',51,intent)['total_energy_mj'],r['total_energy_mj'])

    def test_invalid_severity_ranges_parent_and_assumptions(self):
        for kind,severity in [('invalid',1),('none',1),('cpu_busy_poll',1001),('tx_power_lock',1),('bursty_retry_storm',-1),('payload_fragmentation_bloat',8),('beacon_hyper_wakeup',True)]:
            with self.assertRaises(ValueError):self.sim(kind,severity)
        bad=copy.deepcopy(self.intent);bad['evaluation_group_id']='fake-group'
        with self.assertRaises(ValueError):self.sim(intent=bad)
        for key,value in [('value',float('inf')),('basis','official_typical')]:
            bad=copy.deepcopy(self.a);bad['cpu_increment_ma'][key]=value
            with self.assertRaises(ValueError):f.simulate_fault(self.m,self.intent,bad,dict(kind='none',severity=0))


class ArtifactTests(unittest.TestCase):
    def artifact(self,kind='cpu_busy_poll',severity=100):
        return f.build_artifact(_json_bytes(model()),_json_bytes(f.make_intent(8,100,100,19,12)),_json_bytes(assumptions()),_json_bytes(dict(kind=kind,severity=severity)))

    def test_replay_determinism_and_sensitivity_ranges(self):
        a=self.artifact();self.assertEqual(a,self.artifact());self.assertEqual(f.artifact_from_bytes(_json_bytes(a)),a)
        self.assertEqual(len(a['sensitivity']),4)
        cpu=[s for s in a['sensitivity'] if s['parameter']=='cpu_increment_ma']
        self.assertLess(cpu[0]['fault_energy_mj'],cpu[1]['fault_energy_mj'])

    def test_lineage_and_power_duration_seed_children_group_together(self):
        a=self.artifact();b=self.artifact('beacon_hyper_wakeup',1)
        self.assertEqual(a['lineage']['parent_id'],b['lineage']['parent_id']);self.assertEqual(a['lineage']['baseline_id'],b['lineage']['baseline_id'])
        self.assertNotEqual(a['lineage']['child_id'],b['lineage']['child_id'])
        self.assertEqual(f.parent_id(8,100),f.make_intent(8,100,200,14,100)['evaluation_group_id'])

    def test_tampered_energy_hash_lineage_and_provenance_rejected(self):
        a=self.artifact()
        for mutate in (lambda r:r['execution'].update(total_energy_mj=999),lambda r:r['input_sha256'].update(fault='0'*64),lambda r:r['lineage'].update(parent_id='fake'),lambda r:r.update(provenance={}),lambda r:r['execution']['segments'][0].update(duration_us=123)):
            bad=copy.deepcopy(a);mutate(bad)
            with self.assertRaises(ValueError):f.artifact_from_bytes(_json_bytes(bad))
        with self.assertRaises(ValueError):f.artifact_from_bytes(b'{"x":1,"x":2}')


class FaultIntegrationTests(unittest.TestCase):
    def setUp(self):
        import fault_workflow as w
        self.w=w
        self.parameters=(ROOT/'tools/green_ops/models/nrf9151-dect-reference-v1.json').read_bytes()
        self.a=(ROOT/'tools/green_ops/faults/assumptions-v1.json').read_bytes()
        self.intent=f.make_intent(96,200,1000,19,123)
    def data(self,kind='cpu_busy_poll',severity=100,intent=None):
        return _json_bytes(f.build_artifact(self.parameters,_json_bytes(intent or self.intent),self.a,_json_bytes(dict(kind=kind,severity=severity))))

    def test_all_mechanisms_hidden_inputs_unchanged_and_gates_block_not_detection(self):
        cases=[('cpu_busy_poll',1000),('tx_power_lock',5),('bursty_retry_storm',3),('beacon_hyper_wakeup',10),('payload_fragmentation_bloat',3)]
        for kind,severity in cases:
            intent=f.make_intent(96,200,1000,14 if kind=='tx_power_lock' else 19,0)
            report=self.w.evaluate_artifact(self.data(kind,severity,intent))
            self.assertTrue(report['mechanism_occurred'],kind)
            self.assertFalse(report['predictor']['inputs_changed']);self.assertFalse(report['predictor']['predictions_changed'])
            self.assertEqual(report['predictor']['feature_order'],['payload_size_bytes','interval_ms','tx_power_dbm','window_duration_ms'])
            self.assertEqual(report['gatekeeper']['status'],'ABSTAIN');self.assertEqual(self.w.gate_exit(report),3)
            self.assertTrue(report['execution_blocked']);self.assertFalse(report['positive_fault_detection'])
            self.assertFalse(report['observable_in_selected_prediction_context'])
            self.assertEqual(report['predictor']['baseline_predictions'],report['predictor']['fault_predictions'])
            check=report['analytical']['frozen_policy_point_checks'][0]
            self.assertEqual(check['threshold'],200);self.assertEqual(check['unit'],'mW')
            self.assertEqual(check['fault_violation'],report['analytical']['fault']['mean_power_mw']>200)

    def test_permitted_interface_rejects_missing_and_ignores_hidden_identity(self):
        intended=copy.deepcopy(self.intent);before=self.w.permitted_features(intended)
        intended.update(fault_identity='storm',actual_tx_power=99,total_energy_mj=999999,seed=999)
        self.assertEqual(before,self.w.permitted_features(intended))
        del intended['payload_size_bytes']
        with self.assertRaises(KeyError):self.w.permitted_features(intended)

    def test_compliant_controls_false_blocks_not_positive_alarms(self):
        r=self.w.evaluate_artifact(self.data('none',0))
        self.assertFalse(r['configured_fault']);self.assertFalse(r['analytical']['budget_violation'])
        self.assertFalse(r['control_false_alarm']);self.assertTrue(r['control_blocked_without_positive_detection'])
        self.assertFalse(r['positive_fault_detection']);self.assertIsNone(r['observable_in_selected_prediction_context'])

    def test_infeasible_artifact_has_null_labels_and_abstains_without_positive(self):
        r=self.w.evaluate_artifact(self.data('beacon_hyper_wakeup',200))
        self.assertEqual(r['analytical']['fault_status'],'INFEASIBLE');self.assertIsNone(r['analytical']['fault']['total_energy_mj'])
        self.assertIsNone(r['analytical']['budget_violation']);self.assertEqual(self.w.gate_exit(r),3);self.assertFalse(r['positive_fault_detection'])

    def test_report_replay_and_exact_status_propagation_all_four_codes(self):
        data=self.data();r=self.w.evaluate_artifact(data)
        self.assertEqual(self.w.report_from_bytes(_json_bytes(r),data),r)
        bad=copy.deepcopy(r);bad['positive_fault_detection']=True
        with self.assertRaises(ValueError):self.w.report_from_bytes(_json_bytes(bad),data)
        for status,code in [('PASS',0),('ERROR',1),('FAIL',2),('ABSTAIN',3)]:
            self.assertEqual(self.w.gate_exit({'gatekeeper':dict(status=status,exit_code=code,blocks_ci=status!='PASS')}),code)
        with self.assertRaises(ValueError):self.w.gate_exit({'gatekeeper':dict(status='ABSTAIN',exit_code=0,blocks_ci=False)})

    def test_cli_exit_collision_and_publication_rollback(self):
        import tempfile,contextlib,io
        from unittest import mock
        import atomic_outputs
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stderr(io.StringIO()):
            root=Path(d);source=root/'artifact.json';source.write_bytes(self.data());out=root/'report.json'
            args=['gate','--artifact',str(source),'--output',str(out)]
            self.assertEqual(self.w.main(args),3);saved=out.read_bytes();self.assertEqual(self.w.main(args),1);self.assertEqual(out.read_bytes(),saved)
            out.unlink()
            with mock.patch.object(atomic_outputs.os,'replace',side_effect=OSError('fault publication failure')):self.assertEqual(self.w.main(args),1)
            self.assertFalse(out.exists())
            source.write_bytes(b'{"bad":NaN}');self.assertEqual(self.w.main(args),1);self.assertFalse(out.exists())

    def test_development_determinism_all_five_cases_and_no_benchmark_scoring(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=self.w.write_development(root/'a');b=self.w.write_development(root/'b')
            self.assertEqual(a,b);self.assertEqual(a['case_count'],40);self.assertEqual(a['parent_count'],1)
            self.assertFalse(a['benchmark_scored'])
            self.assertEqual({c['fault']['kind'] for c in a['cases']},set(f.KINDS))
            self.assertTrue(all(c['gate_exit']==3 and not c['positive_detection'] for c in a['cases']))
            for path in (root/'a').rglob('*'):
                if path.is_file():self.assertEqual(path.read_bytes(),(root/'b'/path.relative_to(root/'a')).read_bytes())
            with self.assertRaises(FileExistsError):self.w.write_development(root/'a')


class BenchmarkPlanningTests(unittest.TestCase):
    def test_frozen_parent_disjoint_counts_and_no_simulation_or_scoring(self):
        from unittest import mock
        import fault_benchmark as b
        with mock.patch.object(f,'simulate_fault',side_effect=AssertionError('benchmark simulated before scoring authorization')):
            recipe=b.prepare_proposal()
        self.assertEqual(recipe['status'],'FROZEN_UNSCORED');self.assertFalse(recipe['benchmark_scored'])
        self.assertEqual(recipe['case_count'],1920);self.assertEqual(recipe['parent_count'],16)
        self.assertEqual(len(recipe['planned_case_ids']),len(set(recipe['planned_case_ids'])))
        train=set(recipe['parent_splits']['validation']);test=set(recipe['parent_splits']['locked_evaluation'])
        old={c['parent_id'] for c in recipe['excluded_prior_parent_configurations']}
        self.assertEqual((len(train),len(test)),(8,8));self.assertFalse(train&test);self.assertFalse((train|test)&old)
        self.assertEqual(recipe['prior_seed_overlap'],[]);self.assertEqual(recipe['distinct_random_streams'],48)

    def test_bad_grid_and_resource_inputs_rejected(self):
        import fault_workflow as w
        recipe=json.loads(w.DEVELOPMENT.read_bytes());recipe['repetitions']=True
        with self.assertRaises(ValueError):w.development_specs(recipe)
        with self.assertRaises(ValueError):f.make_intent(8,0,100,19,1)
        a=assumptions();m=model();intent=f.make_intent(8,1,3600000,19,1,offered_packets=0)
        with self.assertRaisesRegex(ValueError,'resource limit'):f.simulate_fault(m,intent,a,dict(kind='none',severity=0))
        for base in (-1,True,float('nan')):
            with self.assertRaises(ValueError):f.oracle_violation(base,1,5)
