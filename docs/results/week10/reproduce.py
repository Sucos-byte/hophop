# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Render eight frozen Week9 decisions plus fresh default ABSTAIN; local files only."""
from pathlib import Path
import json
import platform
import sys
import tempfile
sys.path.insert(0,'tools/green_ops')
from analytical_reference import _json_bytes,_sha256
from ml_dataset import FreshDirectory
from green_ops_report import generate
from green_ops_gate_report import main as gate_report

CASES={'pass_upper','fail_upper','abstain_crossing','default_coverage_abstain','error_wrong_units',
       'battery_five_years_fail','battery_missing_workload_abstain','same_features_regression'}


def run(destination):
    fixtures=Path('docs/results/week9');inventory_bytes=(fixtures/'demo-summary.json').read_bytes();summary=json.loads(inventory_bytes)
    if set(summary['cases'])!=CASES:raise ValueError('unsupported source decision inventory')
    evidence={};statuses=set()
    with FreshDirectory(destination) as output:
        for name,case in sorted(summary['cases'].items()):
            decision=(fixtures/'reports'/f'{name}.json').read_bytes();policy=(fixtures/'policies'/f'{name}.json').read_bytes()
            markdown=generate(decision,case['report_sha256'],policy).encode('utf-8');r=json.loads(decision)
            if f"**{r['status']} —" not in markdown.decode('utf-8'):raise ValueError('rendered status missing')
            statuses.add(r['status']);output.write(f'{name}.md',markdown)
            evidence[name]=dict(source_decision_sha256=_sha256(decision),policy_sha256=_sha256(policy),markdown_sha256=_sha256(markdown),
                decision_exit=r['exit_code'],renderer_exit=0,blocks_candidate_ci=r['blocks_ci'])
        if statuses!={'PASS','FAIL','ABSTAIN','ERROR'}:raise ValueError('not all statuses demonstrated')
        with tempfile.TemporaryDirectory(prefix='green-ops-week10-demo-') as directory:
            temp=Path(directory);decision=temp/'default.json';markdown=temp/'default.md'
            code=gate_report(['--policy','tools/green_ops/policies/green_ops_budget.json','--candidate',str(fixtures/'source'),
                '--output',str(decision),'--markdown-output',str(markdown)])
            r=json.loads(decision.read_bytes())
            if code!=3 or r['research_override_requested'] or r['research_override_used']:raise ValueError('default no-override ABSTAIN changed')
            output.write('fresh-default-decision.json',decision.read_bytes());output.write('fresh-default-report.md',markdown.read_bytes())
        receipt=dict(report_demo_version=1,scope='local_rendering_and_software_verification_not_candidate_approval',
            provenance='analytical_simulation',python_version=platform.python_version(),dependencies='stdlib_only',
            source_inventory_sha256=_sha256(inventory_bytes),cases=evidence,default_wrapper_exit=3,default_override=False,
            fresh_default_decision_sha256=_sha256((output.path/'fresh-default-decision.json').read_bytes()),
            fresh_default_markdown_sha256=_sha256((output.path/'fresh-default-report.md').read_bytes()),
            implementation_sha256={name:_sha256((Path('tools/green_ops')/name).read_bytes()) for name in ('green_ops_report.py','green_ops_gate_report.py','green_ops_ci_smoke.py')},
            no_github_actions_execution_or_posting=True)
        output.write('reproduction.json',_json_bytes(receipt))
    print('All four statuses rendered in eight local examples; fresh default wrapper remains ABSTAIN3.')


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python3 docs/results/week10/reproduce.py NEW_OUTPUT_DIRECTORY')
    run(sys.argv[1])
