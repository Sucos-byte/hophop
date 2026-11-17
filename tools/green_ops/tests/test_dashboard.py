# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0
import copy
from contextlib import closing
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dashboard_artifacts as a
import dashboard


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.store=a.ArtifactStore()
    def test_real_artifacts_bind_and_negative_result_preserved(self):
        s=self.store
        self.assertTrue(all(v['available'] for v in s.sections.values()))
        f=s.sections['faults']['data']['aggregate']['overall']
        self.assertEqual(f['case_count'],1920)
        self.assertEqual(f['positive_FAIL_detections'],0)
        self.assertEqual(f['statuses']['ABSTAIN'],1920)
        self.assertEqual(f['control_abstention_blocks'],576)
        self.assertEqual(f['oracle_violations'],552)
        self.assertEqual(f['inputs_changed'],0)
    def test_prediction_records_not_runs_or_groups(self):
        d=self.store.sections['week7']['data']
        self.assertEqual((d['record_count'],d['unique_runs'],d['unique_groups']),(1620,270,6))
        d=self.store.sections['week8']['data']
        self.assertEqual((d['record_count'],d['unique_runs'],d['unique_groups']),(4050,1350,30))
        primary=[m for m in d['metrics'] if m['panel']=='primary' and m['target']=='target_mean_power_mw'][0]
        self.assertEqual(primary['coverage']['family_coverage'],28/30)
        self.assertNotEqual(primary['coverage']['row_coverage'],primary['coverage']['family_coverage'])
    def test_signed_errors_units_missing_intervals_and_baseline(self):
        d=self.store.sections['week7']['data'];r=d['rows'][0]
        self.assertEqual(r['error'],r['prediction']-r['truth'])
        self.assertIsNone(r['lower']);self.assertEqual(r['unit'],'uJ')
        self.assertEqual({r['model'] for r in d['rows']},{'baseline','chosen'})
    def test_missing_labels_remain_missing_not_zero(self):
        e=copy.deepcopy(self.store.json('w7-evaluation'));p=copy.deepcopy(self.store.json('w7-predictions'))
        row=p['rows'][0];row['truth']=None
        score=e['partitions'][row['partition']][row['target']][row['model_role']]
        score['sample_count']-=1
        result=a.prediction_adapter(e,p,'week7')['rows'][0]
        self.assertIsNone(result['truth']);self.assertIsNone(result['error'])
        self.assertIsNone(result['absolute_error'])

    def test_unsupported_schema_provenance_nonfinite_duplicate(self):
        evaluation=self.store.json('w7-evaluation');predictions=self.store.json('w7-predictions')
        for field,value in [('evaluation_version',2),('provenance','measured')]:
            bad=copy.deepcopy(evaluation);bad[field]=value
            with self.assertRaises(ValueError):a.prediction_adapter(bad,predictions,'week7')
        for value in (float('nan'),float('inf'),'42',True):
            bad=copy.deepcopy(predictions);bad['rows'][0]['prediction']=value
            with self.assertRaises(ValueError):a.prediction_adapter(evaluation,bad,'week7')
        bad=copy.deepcopy(predictions);bad['rows'].append(bad['rows'][0])
        with self.assertRaisesRegex(ValueError,'duplicate'):a.prediction_adapter(evaluation,bad,'week7')
    def test_coverage_and_missing_fields_rejected(self):
        e=copy.deepcopy(self.store.json('w8-evaluation'));p=self.store.json('w8-predictions')
        e['panels']['primary']['target_mean_power_mw']['coverage']['family_coverage']=1
        with self.assertRaisesRegex(ValueError,'family coverage mismatch'):a.prediction_adapter(e,p,'week8')
        del e['feature_contract_version']
        with self.assertRaises(KeyError):a.prediction_adapter(e,p,'week8')
    def test_hash_failure_and_missing_have_no_metrics_fallback(self):
        catalog=copy.deepcopy(self.store.catalog);catalog['resources']['w7-predictions']['sha256']='0'*64
        s=a.ArtifactStore(catalog=catalog)
        self.assertFalse(s.sections['week7']['available']);self.assertIn('SHA-256',s.sections['week7']['error'])
        self.assertTrue(s.sections['faults']['available'])
        with tempfile.TemporaryDirectory() as tmp:
            s=a.ArtifactStore(root=tmp)
            self.assertFalse(any(v['available'] for v in s.sections.values()))
            self.assertNotIn('data',s.summary()['sections']['faults'])
    def test_saved_gate_statuses_and_overrides(self):
        reports=self.store.sections['gates']['data']
        self.assertEqual({r['status'] for r in reports},set(a.EXITS))
        for r in reports:
            self.assertEqual(r['exit_code'],a.EXITS[r['status']]);self.assertFalse(r['hardware_assurance'])
        default=next(r for r in reports if r['name']=='default_coverage_abstain')
        self.assertEqual(default['status'],'ABSTAIN');self.assertFalse(default['research_override_used'])
        passed=next(r for r in reports if r['status']=='PASS')
        self.assertTrue(passed['research_override_used'])
    def test_pagination_filters_and_seed_precision(self):
        page=self.store.page('experiments',{'page':'1','limit':'3','split':'locked_evaluation','kind':'cpu_busy_poll'})
        self.assertEqual(len(page['rows']),3);self.assertEqual(page['total'],192)
        self.assertIsInstance(page['rows'][0]['seed'],str)
        nextpage=self.store.page('experiments',{'page':'2','limit':'3','split':'locked_evaluation','kind':'cpu_busy_poll'})
        self.assertNotEqual(page['rows'][0]['case_id'],nextpage['rows'][0]['case_id'])
        for q in ({'limit':'51'},{'page':'0'},{'path':'/etc/passwd'},{'study':'nope'},{'search':'x'*161}):
            with self.assertRaises(ValueError):self.store.page('predictions',q)
    def test_safe_read_rejects_paths_symlinks_and_oversized_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'ok').write_text('hello');(root/'link').symlink_to(root/'ok')
            for path in ('../ok','/etc/passwd','link'):
                with self.assertRaises((OSError,ValueError)):a.safe_read(root,path)
            (root/'real').mkdir();(root/'alias').symlink_to(root/'real',target_is_directory=True)
            (root/'real'/'data').write_text('hidden')
            with self.assertRaises(OSError):a.safe_read(root,'alias/data')
            with self.assertRaises(ValueError):a.safe_read(root,'ok',limit=2)
            os.mkfifo(root/'pipe')
            with self.assertRaises(ValueError):a.safe_read(root,'pipe')


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store=a.ArtifactStore();cls.server=dashboard.make_server(0,cls.store)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self,path,method='GET',headers=None):
        with closing(HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)) as connection:
            connection.request(method,path,headers=headers or {});response=connection.getresponse()
            return response.status,dict(response.getheaders()),response.read()
    def test_loopback_only_static_security_headers_offline_assets(self):
        self.assertEqual(self.server.server_address[0],'127.0.0.1')
        code,headers,body=self.request('/')
        self.assertEqual(code,200);self.assertIn("default-src 'none'",headers['Content-Security-Policy'])
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
        self.assertIn(b'ANALYTICAL SIMULATION',body);self.assertIn('Measured evidence: not established',' '.join(body.decode().split()))
        self.assertNotIn(b'https://',body)
        code,_,js=self.request('/app.js');self.assertEqual(code,200)
        self.assertNotIn(b'innerHTML',js);self.assertIn(b'textContent',js)
        self.assertIn(b'Not percentage accuracy',js);self.assertIn(b'blanket abstention',js)
    def test_no_arbitrary_repository_paths_or_execution(self):
        for path in ('/.git/config','/docs/plans/green-ops-progress.md','/../README.md','/%2e%2e/etc/passwd','/resource/../../etc/passwd','//example.com/path','/api/train','/api/gate','/catalog.json','/resource/missing'):
            with self.subTest(path=path):self.assertIn(self.request(path)[0],(400,404))
        for method in ('POST','PUT','PATCH','DELETE'):
            self.assertEqual(self.request('/api/summary',method)[0],405)
    def test_rebinding_cross_origin_and_bad_queries(self):
        self.assertEqual(self.request('/api/summary',headers={'Host':'evil.example'})[0],403)
        self.assertEqual(self.request('/api/summary',headers={'Origin':'https://evil.example'})[0],403)
        for path in ('/api/predictions?limit=0','/api/predictions?study=nope','/api/experiments?page=1&page=2','/api/experiments?limit=100000','/api/experiments?path=x'):
            self.assertEqual(self.request(path)[0],400)
    def test_text_resources_inert_and_summary_valid(self):
        code,headers,body=self.request('/resource/gate-pass-upper')
        self.assertEqual(code,200);self.assertEqual(headers['Content-Type'],'text/plain; charset=utf-8')
        code,headers,body=self.request('/api/summary');data=json.loads(body)
        self.assertEqual(data['mode'],'read_only_saved_artifacts')
        self.assertEqual(data['physical_validation'],'not_established')
        self.assertNotIn('rows',data['sections']['faults']['data'])
    def test_hostile_artifact_text_remains_inert_json(self):
        original=self.store.sections['overview']['data']['evidence'][0]['delivered']
        try:
            self.store.sections['overview']['data']['evidence'][0]['delivered']='<img src=x onerror=alert(1)>'
            code,headers,body=self.request('/api/summary')
            self.assertEqual(code,200);self.assertTrue(headers['Content-Type'].startswith('application/json'))
            self.assertIn('<img',json.loads(body)['sections']['overview']['data']['evidence'][0]['delivered'])
        finally:self.store.sections['overview']['data']['evidence'][0]['delivered']=original

if __name__=='__main__':unittest.main()
