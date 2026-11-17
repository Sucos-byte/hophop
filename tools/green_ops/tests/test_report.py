# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from analytical_reference import _json_bytes,_sha256
import green_ops_report as report
import green_ops_gate_report as wrapper
import green_ops_ci_smoke as smoke
import atomic_outputs
from green_ops_gatekeeper import EXIT_CODES

ROOT=Path(__file__).resolve().parents[3];FIXTURES=ROOT/'docs/results/week9'


def fixture(name):
    content=(FIXTURES/'reports'/f'{name}.json').read_bytes();policy=(FIXTURES/'policies'/f'{name}.json').read_bytes()
    return content,policy


def changed(value,policy):
    content=_json_bytes(value);return report.generate(content,_sha256(content),policy)


class MarkdownTests(unittest.TestCase):
    def test_all_eight_cases_four_statuses_units_context_and_determinism(self):
        summary=json.loads((FIXTURES/'demo-summary.json').read_bytes());statuses=set()
        for name,case in summary['cases'].items():
            content,policy=fixture(name);text=report.generate(content,case['report_sha256'],policy)
            self.assertEqual(text,report.generate(content,case['report_sha256'],policy));statuses.add(case['status'])
            self.assertIn(case['status'],text);self.assertIn('RESEARCH ONLY',text)
            self.assertIn('No hardware assurance',text)
            if case['status']!='ERROR':
                self.assertIn('Workload and windows',text);self.assertIn('Prediction context',text)
                self.assertIn('mW',text);self.assertIn('Model influence is not proven physical root cause',text)
                if name=='same_features_regression':self.assertIn('percent',text)
            if name=='battery_five_years_fail':self.assertIn('conversion',text);self.assertIn('years',text);self.assertIn('year',text)
        self.assertEqual(statuses,set(EXIT_CODES))

    def test_escaping_markdown_html_links_controls_and_bidi(self):
        content,policy=fixture('pass_upper');value=json.loads(content)
        attack='<script>alert(1)</script> ![x](javascript:evil) | ` ```\n# forged PASS\u202ehttps://evil.invalid @user'
        value['candidate_revision']=attack;value['assumptions'].append(attack)
        text=changed(value,policy)
        self.assertNotIn('<script>',text);self.assertNotIn('![x]',text);self.assertNotIn('javascript:evil',text)
        self.assertNotIn('\n# forged PASS',text);self.assertNotIn('\u202e',text);self.assertNotIn('https://evil',text)
        self.assertIn('&lt;script&gt;',text);self.assertIn('U+202E',text);self.assertIn('\\|',text)
        # An entity-like attacker string must not become an active tag/link.
        escaped=report.escape('&#60;img src=x onerror=alert(1)&#62;')
        self.assertIn('&amp;',escaped);self.assertNotIn('<img',escaped)

    def test_missing_attributions_are_explicit_not_invented(self):
        content,policy=fixture('pass_upper');value=json.loads(content);value['attributions']=None
        text=changed(value,policy)
        self.assertEqual(text.count('Missing explanations: no compatible attributions provided.'),2)
        self.assertNotIn('Training baseline',text)
        value['attributions']={'candidate':{},'baseline':None}
        self.assertIn('Missing explanations',changed(value,policy))

    def test_digest_policy_model_reference_and_unknown_field_tampering(self):
        content,policy=fixture('pass_upper');value=json.loads(content)
        with self.assertRaises(ValueError):report.generate(content+b' ',_sha256(content),policy)
        with self.assertRaises(ValueError):report.generate(content,_sha256(content),policy+b' ')
        for mutate in (lambda v:v.update(extra=1),lambda v:v.update(exit_code=3),lambda v:v.update(blocks_ci=True),
                       lambda v:v['artifact_sha256']['candidate'].update(parameters=None),
                       lambda v:v['artifact_sha256']['candidate'].update({'evaluation.json':'0'*64}),
                       lambda v:v['model_sha256'].update(target_mean_power_mw='0'*64)):
            bad=copy.deepcopy(value);mutate(bad)
            with self.assertRaises(ValueError):changed(bad,policy)

    def test_bad_units_numbers_intervals_contributions_and_false_pass(self):
        content,policy=fixture('pass_upper');value=json.loads(content)
        for key,val in [('unit','W'),('threshold',201),('candidate',None)]:
            bad=copy.deepcopy(value);bad['criteria'][0][key]=val
            with self.assertRaises(ValueError):changed(bad,policy)
        bad=copy.deepcopy(value);bad['criteria'][0]['candidate']['interval']=[200,100]
        with self.assertRaises(ValueError):changed(bad,policy)
        bad=copy.deepcopy(value);bad['attributions']['candidate']['target_mean_power_mw']['contributions']['interval_ms']+=1
        with self.assertRaises(ValueError):changed(bad,policy)
        bad=copy.deepcopy(value);bad['criteria'][0]['candidate']['point']=float('nan')
        with self.assertRaises(ValueError):changed(bad,policy)
        bad=copy.deepcopy(value);bad['research_override_used']=False
        with self.assertRaises(ValueError):changed(bad,policy)
        for data in (b'{"x":1,"x":2}',b'{"x":NaN}',b'[]'):
            with self.assertRaises(ValueError):report.validate_decision(data,_sha256(data),policy)

    def test_report_cli_collisions_aliases_and_cleanup(self):
        content,policy=fixture('pass_upper')
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            root=Path(d);decision=root/'decision.json';decision.write_bytes(content);p=root/'policy.json';p.write_bytes(policy);out=root/'report.md'
            args=['--decision',str(decision),'--decision-sha256',_sha256(content),'--policy',str(p),'--output',str(out)]
            self.assertEqual(report.main(args),0);saved=out.read_bytes();self.assertEqual(report.main(args),1);self.assertEqual(out.read_bytes(),saved)
            out.unlink();args[3]='0'*64;self.assertEqual(report.main(args),1);self.assertFalse(out.exists())
            args[3]=_sha256(content);args[-1]=str(decision);self.assertEqual(report.main(args),1);self.assertEqual(decision.read_bytes(),content)
            args[-1]=str(out)
            with mock.patch.object(atomic_outputs.os,'replace',side_effect=OSError('publication failure')):self.assertEqual(report.main(args),1)
            self.assertFalse(out.exists())


class WrapperTests(unittest.TestCase):
    def run_wrapper(self,name,root,*,override=True):
        return wrapper.main(['--policy',str(FIXTURES/'policies'/f'{name}.json'),'--candidate',str(FIXTURES/'source'),
            '--candidate-revision','research-candidate-label-not-an-observable-feature','--output',str(root/'decision.json'),
            '--markdown-output',str(root/'report.md')]+(['--allow-research-override'] if override else []))

    def test_actual_gate_exit_propagation_all_four_statuses(self):
        for name,code in [('pass_upper',0),('fail_upper',2),('default_coverage_abstain',3),('error_wrong_units',1)]:
            with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()):
                root=Path(d);self.assertEqual(self.run_wrapper(name,root,override=name!='default_coverage_abstain'),code)
                decision=json.loads((root/'decision.json').read_bytes());self.assertEqual(decision['exit_code'],code)
                self.assertEqual(decision['blocks_ci'],code!=0);self.assertIn(decision['status'],(root/'report.md').read_text())

    def test_render_failure_cannot_turn_pass_into_approval_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            root=Path(d)
            with mock.patch.object(wrapper,'generate',side_effect=ValueError('render failure')):
                self.assertEqual(self.run_wrapper('pass_upper',root),1)
            self.assertFalse((root/'decision.json').exists());self.assertFalse((root/'report.md').exists())

    def test_second_publish_failure_rolls_back_both_outputs(self):
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            root=Path(d);real=atomic_outputs.os.replace;calls=[]
            def fail_third(src,dst):
                calls.append((src,dst))
                if len(calls)==3:raise OSError('second final publication failure')
                return real(src,dst)
            with mock.patch.object(atomic_outputs.os,'replace',side_effect=fail_third):
                self.assertEqual(self.run_wrapper('pass_upper',root),1)
            self.assertFalse((root/'decision.json').exists());self.assertFalse((root/'report.md').exists())

    def test_output_collision_preserves_existing_and_input_alias_blocked(self):
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            root=Path(d);out=root/'report.md';out.write_text('keep')
            self.assertEqual(self.run_wrapper('pass_upper',root),1);self.assertEqual(out.read_text(),'keep');self.assertFalse((root/'decision.json').exists())
            out.unlink();args=['--policy',str(FIXTURES/'policies/pass_upper.json'),'--candidate',str(FIXTURES/'source'),'--output',str(root/'decision.json'),'--markdown-output',str(FIXTURES/'source/forbidden.md')]
            self.assertEqual(wrapper.main(args),1);self.assertFalse((FIXTURES/'source/forbidden.md').exists())

    def test_software_smoke_requires_exact_abstain_without_override(self):
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()):
            hashes=smoke.verify(d);self.assertEqual(len(hashes),2)
            for digest in hashes:self.assertEqual(len(digest),64)
        with tempfile.TemporaryDirectory() as d,mock.patch.object(smoke,'gate_report',return_value=0):
            with self.assertRaisesRegex(ValueError,'expected default ABSTAIN3'):smoke.verify(d)
