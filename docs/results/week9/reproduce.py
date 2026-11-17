# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Run from repository root with a NEW output directory argument; no fitting or tuning."""
from pathlib import Path
import copy
import json
import platform
import sys
sys.path.insert(0,'tools/green_ops')
from analytical_reference import _json_bytes,_sha256,generate_analytical_artifact
from week8_dataset import recipe_from_bytes,planned_specs
from ml_dataset import FreshDirectory
from green_ops_gatekeeper import main


def run(destination):
    recipe=recipe_from_bytes(Path('tools/green_ops/recipes/week8-uncertainty-v1.json').read_bytes())
    specs=planned_specs(recipe,Path(recipe['parameters_path']).read_bytes(),json.loads(Path('docs/results/week8/lineage.json').read_bytes()))
    spec=min((s for s in specs if s['split']=='evaluation'),key=lambda s:s['workload']['run_id'])
    run=spec['workload'];context=dict(available_fields=recipe['feature_order'],planned_window_duration_ms=run['window_duration_ms'],completed_as_planned=True)
    source=generate_analytical_artifact(spec['parameters'],_json_bytes(run),Path(recipe['assumptions_path']).read_bytes(),prediction_context_bytes=_json_bytes(context))
    default=json.loads(Path('tools/green_ops/policies/green_ops_budget.json').read_bytes())
    research=copy.deepcopy(default);research['uncertainty']['allow_unvalidated_research_intervals']=True
    cases=[]
    for name,limit,expected in [('pass_upper',200,0),('fail_upper',100,2),('abstain_crossing',150,3)]:
        policy=copy.deepcopy(research);policy['criteria'][0]['threshold']=limit;cases.append((name,policy,True,False,expected))
    cases.append(('default_coverage_abstain',default,False,False,3))
    policy=copy.deepcopy(default);policy['criteria'][0]['unit']='W';cases.append(('error_wrong_units',policy,False,False,1))
    battery=dict(capacity_mah=1000,voltage_v=3.6,usable_fraction=.8,conversion_efficiency=.9,year_days=365.25,
        target_years=5,power_basis='load_side_before_conversion',workload_profile=dict(kind='run_average',repeat='continuous_same_workload',duty_cycle_included=True))
    policy=copy.deepcopy(research);policy['criteria']=[];policy['battery']=battery
    cases.append(('battery_five_years_fail',policy,True,False,2))
    policy=copy.deepcopy(policy);policy['battery']['workload_profile']=None
    cases.append(('battery_missing_workload_abstain',policy,True,False,3))
    policy=copy.deepcopy(research);policy['criteria'][0].update(kind='regression_relative',unit='percent',threshold=25)
    cases.append(('same_features_regression',policy,True,True,0))
    with FreshDirectory(destination) as output:
        for name,content in source.items():output.write('source/'+name,content)
        output.write('reports/.keep',b'');results={}
        for name,policy,override,baseline,expected in cases:
            policy=copy.deepcopy(policy);policy['policy_id']='RESEARCH-FIXTURE-'+name
            output.write('policies/'+name+'.json',_json_bytes(policy))
            report=output.path/'reports'/f'{name}.json'
            args=['--policy',str(output.path/'policies'/f'{name}.json'),'--candidate',str(output.path/'source'),'--output',str(report),
                  '--candidate-revision','research-candidate-label-not-an-observable-feature']
            if override:args.append('--allow-research-override')
            if baseline:args+=['--baseline',str(output.path/'source'),'--baseline-revision','research-baseline-label-not-an-observable-feature']
            code=main(args)
            if report.exists():output.files.append(report)
            if code!=expected:raise ValueError(f'{name}: expected exit{expected}, got{code}')
            data=report.read_bytes();decoded=json.loads(data)
            results[name]=dict(exit_code=code,status=decoded['status'],reason_codes=decoded['reason_codes'],report_sha256=_sha256(data),
                policy_sha256=_sha256(_json_bytes(policy)),research_override_requested=override)
        for name in ('pass_upper','same_features_regression'):
            report=json.loads((output.path/'reports'/f'{name}.json').read_bytes())
            assert report['research_override_used'] and 'NO VALIDATED 95%' in report['evidence_label']
        summary=dict(demo_version=1,provenance='analytical_simulation',research_only=True,source_selection='lexicographically first nominal Week8 evaluation run; no outcome selection',
            run_id=run['run_id'],workload=run,model_sha256=recipe['model_sha256'],selection_sha256=recipe['selection_sha256'],
            source_manifest_sha256=_sha256(source['manifest.json']),cases=results,python_version=platform.python_version(),dependencies='stdlib_only',
            implementation_sha256={name:_sha256((Path('tools/green_ops')/name).read_bytes()) for name in ('green_ops_gatekeeper.py','budget_policy.py','battery_projection.py','gate_evidence.py')},
            limitations=['fixtures exercise explicit research policy semantics, not validated budgets','no model/calibration modification or fitting','no hardware/compliance assurance','configuration estimates cannot observe commit-only code changes'])
        output.write('demo-summary.json',_json_bytes(summary))
    print('Verified all8 research demonstration exits; source/model/calibration unchanged.')


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python3 docs/results/week9/reproduce.py NEW_OUTPUT_DIRECTORY')
    run(sys.argv[1])
