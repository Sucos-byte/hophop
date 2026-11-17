# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0
import copy
import gzip
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import benchmark_evaluation as b
import benchmark_audit as audit
from analytical_reference import _json_bytes
from fault_workflow import development_specs, DEVELOPMENT
from dataset_builder import _json_from_bytes


def row(**kwargs):
    r=dict(parent='p',split='validation',kind='cpu_busy_poll',severity=1,
        feasibility='COMPLETE',configured_fault=True,oracle_violation=True,
        positive_detection=False,absolute_violation=False,status='ABSTAIN',blocked=True,
        control_false_alarm=False,inputs_changed=False,predictions_changed=False,
        observable=False,delta_mj=2.,increase_percent=10.,delta_power_mw=2.)
    r.update(kwargs);return r


class BenchmarkTests(unittest.TestCase):
    def test_preflight_does_not_score(self):
        with patch.object(b,'build_artifact',side_effect=AssertionError('must not simulate')):
            recipe,specs,p,a,receipt=b.verify_frozen()
        self.assertEqual(len(specs),1920)
        self.assertEqual(receipt['parent_count'],16)
        self.assertEqual(receipt['random_streams'],48)
        self.assertEqual(len({b.case_id(i,f,p,a) for i,f in specs}),1920)
        self.assertFalse(set(recipe['parent_splits']['validation']) & set(recipe['parent_splits']['locked_evaluation']))

    def test_tampered_receipt_before_simulation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'receipt';path.write_bytes(b'{}')
            with patch.object(b,'RECEIPT',path),patch.object(b,'build_artifact',side_effect=AssertionError):
                with self.assertRaisesRegex(ValueError,'hash mismatch'):b.verify_frozen()

    def test_dependency_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'file';path.write_bytes(b'changed')
            with self.assertRaises(ValueError):b.checked(path,'0'*64)

    def test_abstention_is_not_detection(self):
        result=b.summarize([row(),row(configured_fault=False,oracle_violation=False,observable=None)])
        self.assertEqual(result['positive_FAIL_detections'],0)
        self.assertEqual(result['violations_without_positive_detection'],1)
        self.assertEqual(result['control_abstention_blocks'],1)
        self.assertEqual(result['control_false_alarms'],0)
        self.assertEqual(result['detection_rate']['denominator'],1)
        self.assertEqual(result['control_abstention_rate']['value'],1)

    def test_statuses_and_null_pairs(self):
        rows=[row(status='PASS',blocked=False),row(status='FAIL',positive_detection=True),
              row(feasibility='INFEASIBLE',oracle_violation=None,delta_mj=None,delta_power_mw=None,increase_percent=None),
              row(status='ERROR',feasibility='INVALID',oracle_violation=None,delta_mj=None,delta_power_mw=None,increase_percent=None)]
        a=b.summarize(rows)
        self.assertEqual(a['statuses'],dict(PASS=1,FAIL=1,ABSTAIN=1,ERROR=1))
        self.assertEqual(a['oracle_unknown'],2)
        self.assertEqual(a['effects']['paired_energy_mj']['count'],2)
        self.assertEqual(a['effects']['paired_energy_mj']['mean'],2)
        self.assertEqual(a['feasibility']['INVALID'],1)

    def test_parent_dependence_and_empty_denominators(self):
        a=b.summarize([row(delta_mj=1),row(delta_mj=1),row(parent='q',delta_mj=7)])
        self.assertEqual(a['effects']['paired_energy_mj']['mean'],3)
        self.assertEqual(a['effects']['equal_parent_mean_delta_mj']['mean'],4)
        self.assertIsNone(a['control_false_alarm_rate']['value'])
        self.assertIsNone(b.summarize([])['detection_rate']['value'])

    def test_aggregate_strata_determinism(self):
        rows=[row(),row(parent='q',split='locked_evaluation',severity=3)]
        a=b.aggregate(rows)
        self.assertEqual(len(a['by_fault_severity']),2)
        self.assertEqual(_json_bytes(a),_json_bytes(b.aggregate(list(reversed(rows)))))

    def test_new_directory_collision_no_consumption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);output=root/'exists';output.mkdir();sentinel=output/'sentinel';sentinel.write_text('keep')
            with self.assertRaisesRegex(ValueError,'collision'):b.execute(output,root/'consumed')
            self.assertFalse((root/'consumed').exists());self.assertEqual(sentinel.read_text(),'keep')

    def test_rollback_keeps_consumption(self):
        recipe,specs,p,a,receipt=b.verify_frozen()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(b,'verify_frozen',return_value=(recipe,specs[:1],p,a,receipt)),patch.object(b,'build_artifact',side_effect=ValueError('bad input')):
                with self.assertRaisesRegex(ValueError,'bad input'):b.execute(root/'out',root/'consumed')
            self.assertFalse((root/'out').exists());self.assertTrue((root/'consumed').exists())

    def test_audit_rejects_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'manifest.json').write_bytes(_json_bytes(dict(cases_sha256='0'*64,aggregate_sha256='0'*64)))
            (root/'cases.jsonl').write_bytes(b'changed');(root/'aggregate.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'output hash mismatch'):audit.audit(root)

    def test_cli_processing_error_exit(self):
        with patch.object(sys,'argv',['benchmark_evaluation','--preflight']),patch.object(b,'verify_frozen',side_effect=ValueError('frozen mismatch')):
            self.assertEqual(b.main(),1)

    def test_small_development_execution_not_benchmark_scoring(self):
        recipe,_,p,a,receipt=b.verify_frozen()
        specs=development_specs(_json_from_bytes(DEVELOPMENT.read_bytes()))[:2]
        recipe=copy.deepcopy(recipe);recipe['parent_splits']={'validation':[specs[0][0]['evaluation_group_id']]}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(b,'verify_frozen',return_value=(recipe,specs,p,a,receipt)):
                self.assertEqual(b.execute(root/'a',root/'ca'),0)
                self.assertEqual(b.execute(root/'b',root/'cb'),0)
            af={str(p.relative_to(root/'a')):p.read_bytes() for p in (root/'a').rglob('*') if p.is_file()}
            bf={str(p.relative_to(root/'b')):p.read_bytes() for p in (root/'b').rglob('*') if p.is_file()}
            self.assertEqual(af,bf)
            self.assertEqual(len(af['cases.jsonl'].splitlines()),2)
            manifest=_json_from_bytes(af['manifest.json'])
            for entry in manifest['entries']:
                for name,digest in entry['files'].items():
                    self.assertEqual(b._sha256(gzip.decompress(af[name])),digest['raw_sha256'])
            self.assertEqual(_json_from_bytes(af['aggregate.json'])['overall']['statuses']['ABSTAIN'],2)

if __name__=='__main__':unittest.main()
