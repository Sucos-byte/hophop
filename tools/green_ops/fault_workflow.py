# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Trusted fault-artifact adapter and separate analytical-oracle/model/gate diagnostics."""
from pathlib import Path
import copy
import sys
from analytical_reference import _fields,_json_bytes,_sha256,_integer,_number
from dataset_builder import _json_from_bytes
from ml_dataset import TARGET_UNITS,FreshDirectory,_digest
from ml_pipeline import predict_matrix
from week8_dataset import frozen_models
from explainability import signed_contributions
from feature_contract import PRE_RUN_FEATURES
from green_ops_gatekeeper import decide,EXIT_CODES,Parser
from green_ops_report import escape
from fault_injection import (KINDS,PROVENANCE,ENGINE_ID,make_intent,parent_id,build_artifact,artifact_from_bytes,oracle_violation)

ROOT=Path(__file__).resolve().parents[2]
ASSUMPTIONS=ROOT/'tools/green_ops/faults/assumptions-v1.json'
DEVELOPMENT=ROOT/'tools/green_ops/recipes/week11-development-v1.json'
RESEARCH_POLICY=ROOT/'tools/green_ops/faults/development-policy-v1.json'
GATE_POLICY=ROOT/'tools/green_ops/policies/green_ops_budget.json'


def load_frozen_models():
    original=(ROOT/'tools/green_ops/recipes/week7-regression-v1.json').read_bytes()
    study=_json_from_bytes((ROOT/'tools/green_ops/recipes/week8-uncertainty-v1.json').read_bytes())
    return frozen_models(ROOT/'docs/results/week7-regression-v1/training',original,study)


def permitted_features(intent):
    """No fault/actual-state/outcome/seed data can be read by this interface."""
    return [intent[name] for name in PRE_RUN_FEATURES]


def default_research_policy():
    content=RESEARCH_POLICY.read_bytes();policy=_json_from_bytes(content)
    _fields(policy,{'research_policy_version','policy_id','research_only','analytical_total_energy_increase_budget_percent','comparison','gate_override','positive_detection_definition','production_gate_policy_sha256'},'development oracle policy')
    if type(policy['research_policy_version']) is not int or policy['research_policy_version']!=1 or policy['research_only'] is not True or policy['gate_override'] is not False:raise ValueError('unsupported research policy')
    _number(policy['analytical_total_energy_increase_budget_percent'],'oracle budget percent')
    if policy['production_gate_policy_sha256']!=_sha256(GATE_POLICY.read_bytes()):raise ValueError('frozen production gate policy changed')
    return policy


def resolved_evidence(artifact,models,*,baseline):
    intent=_json_from_bytes(artifact['snapshots']['intended_workload'].encode('utf-8'));execution=artifact['baseline'] if baseline else artifact['execution']
    fault=_json_from_bytes(artifact['snapshots']['fault'].encode('utf-8'));X=permitted_features(intent)
    predictions={};attributions={};complete=execution['status']=='COMPLETE'
    for target,model in models.items():
        point=predict_matrix(model['estimator'],[X])[0]
        predictions[target]=dict(point=point,interval=None,unit=TARGET_UNITS[target],family_coverage=None,
            unavailable_reason='new_fault_engine_scope_without_calibration')
        attributions[target]=dict(unit=TARGET_UNITS[target],method='recomputed_frozen_linear_model_contribution',
            interpretation='model_attribution_not_physical_root_cause',**signed_contributions(model['estimator'],[X])[0])
    workload={name:intent[name] for name in ('payload_size_bytes','interval_ms','tx_power_dbm','window_duration_ms','offered_packets','max_attempts','seed')}
    actual_spec=dict(parameters=artifact['input_sha256']['parameters'],assumptions=artifact['input_sha256']['assumptions'],
                     execution=dict(kind='none',severity=0) if baseline else fault,engine_id=ENGINE_ID)
    workload.update(parameters_sha256=_sha256(_json_bytes(actual_spec)),assumptions_sha256=artifact['input_sha256']['assumptions'],
                    adapter='analytical-fault-v1',feature_profile_id='raw_pre_run_v1')
    context=dict(available_fields=list(PRE_RUN_FEATURES),planned_window_duration_ms=intent['window_duration_ms'],completed_as_planned=complete)
    return dict(evidence_version=1,provenance='analytical_simulation',feature_contract_version=3,feature_profile='raw_pre_run_v1',prediction_mode='pre_run',
        model_sha256={t:_sha256(_json_bytes(m)) for t,m in models.items()},comparable_workload=workload,prediction_context=context,predictions=predictions,
        artifact_sha256=dict(fault_artifact=_sha256(_json_bytes(artifact)),**artifact['input_sha256']),attributions=attributions,
        domain='declared_stress',revision=None,run_id=artifact['lineage']['baseline_id'] if baseline else artifact['lineage']['child_id'])


def mechanism_occurred(artifact):
    r=artifact['execution'];fault=_json_from_bytes(artifact['snapshots']['fault'].encode('utf-8'));kind=fault['kind']
    if r['status']!='COMPLETE':return None
    if kind=='cpu_busy_poll':return r['state_duration_us']['cpu_busy']>0
    if kind=='tx_power_lock':return r['actual_tx_power_dbm']!=r['requested_tx_power_dbm']
    if kind=='bursty_retry_storm':return any(a['forced_failure'] for p in r['packets'] for fragment in p['fragments'] for a in fragment['attempts'])
    if kind=='beacon_hyper_wakeup':return bool(r['beacons'])
    if kind=='payload_fragmentation_bloat':return r['logical_fragments']>r['offered_packets']
    return False


def evaluate_artifact(content):
    artifact=artifact_from_bytes(content);policy=default_research_policy();models=load_frozen_models()
    candidate=resolved_evidence(artifact,models,baseline=False);baseline=resolved_evidence(artifact,models,baseline=True)
    production=_json_from_bytes(GATE_POLICY.read_bytes())
    gate=decide(production,candidate,baseline,allow_research_override=False,policy_sha256=_sha256(GATE_POLICY.read_bytes()))
    intent=_json_from_bytes(artifact['snapshots']['intended_workload'].encode('utf-8'));fault=_json_from_bytes(artifact['snapshots']['fault'].encode('utf-8'))
    before=permitted_features(intent);after=permitted_features(intent)  # Intent is invariant to hidden actual execution.
    b=artifact['baseline'];r=artifact['execution'];limit=policy['analytical_total_energy_increase_budget_percent']
    violation=oracle_violation(b['total_energy_mj'],r['total_energy_mj'],limit)
    configured=fault['kind']!='none' and fault['severity']>0;occurred=mechanism_occurred(artifact)
    inputs_changed=before!=after
    observable=inputs_changed if occurred else None
    changed_predictions=any(candidate['predictions'][t]['point']!=baseline['predictions'][t]['point'] for t in models)
    positive=gate['status']=='FAIL' and violation is True and observable is True
    delta=r['total_energy_mj']-b['total_energy_mj'] if r['total_energy_mj'] is not None else None
    point_checks=[]
    target_fields=dict(target_mean_power_mw='mean_power_mw',target_total_energy_mj='total_energy_mj',target_energy_per_delivered_packet_uj='energy_per_delivered_packet_uj')
    for rule in production['criteria']:
        field=target_fields[rule['target']];bv=b[field];fv=r[field]
        point_checks.append(dict(criterion_id=rule['id'],kind=rule['kind'],unit=rule['unit'],threshold=rule['threshold'],
            baseline_value=bv,fault_value=fv,baseline_violation=(bv>rule['threshold']) if bv is not None and rule['kind']=='absolute_upper' else None,
            fault_violation=(fv>rule['threshold']) if fv is not None and rule['kind']=='absolute_upper' else None,
            scope='analytical_point_diagnostic_only_not_gate_evidence_or_approval'))
    return dict(fault_report_version=1,provenance=PROVENANCE,engine_id=ENGINE_ID,fault=fault,lineage=artifact['lineage'],
        artifact_sha256=_sha256(content),research_policy_sha256=_sha256(RESEARCH_POLICY.read_bytes()),production_gate_policy_sha256=_sha256(GATE_POLICY.read_bytes()),
        analytical=dict(baseline={name:b[name] for name in ('total_energy_mj','mean_power_mw','energy_per_delivered_packet_uj')},
            fault={name:r[name] for name in ('total_energy_mj','mean_power_mw','energy_per_delivered_packet_uj')},fault_status=r['status'],
            energy_delta_mj=delta,budget_increase_percent=limit,budget_violation=violation,frozen_policy_point_checks=point_checks,budget_scope='unvalidated_analytical_execution_oracle_not_gate_override'),
        predictor=dict(feature_order=list(PRE_RUN_FEATURES),baseline_inputs=before,fault_inputs=after,inputs_changed=inputs_changed,
            baseline_predictions={t:v['point'] for t,v in baseline['predictions'].items()},fault_predictions={t:v['point'] for t,v in candidate['predictions'].items()},
            predictions_changed=changed_predictions,prediction_scope='diagnostic_numeric_model_only_new_execution_scope_uncalibrated',
            requested_power_outside_training_profile=intent['tx_power_dbm']!=19,hidden_actual_information_in_X=False),
        gatekeeper=gate,execution_blocked=gate['blocks_ci'],block_semantics='gate_would_block_execution; offline_analytical_simulation_already_performed_no_hardware',
        configured_fault=configured,mechanism_occurred=occurred,observable_in_selected_prediction_context=observable,
        positive_fault_detection=positive,energy_fault_undetected=(occurred is True and violation is True and not positive),
        control_false_alarm=(not configured and gate['status']=='FAIL'),control_blocked_without_positive_detection=(not configured and gate['blocks_ci'] and not positive),
        limitations=['ABSTAIN/ERROR blocking is not fault detection','same intended X and frozen model cannot observe hidden execution faults',
            'all added CPU/lower-TX/wakeup/fragment behavior assumptions explicit, not measured evidence',
            'no calibration intervals transferred to new scope','model contributions are not physical causal proof',
            'fault-artifact-v1 is not a completed reference-v2 bundle; old readers/policies remain unchanged'])


def gate_exit(report):
    gate=report['gatekeeper']
    if gate['status'] not in EXIT_CODES or type(gate['exit_code']) is not int or gate['exit_code']!=EXIT_CODES[gate['status']] or (type(gate['blocks_ci']) is not bool or gate['blocks_ci']!=(gate['status']!='PASS')):raise ValueError('inconsistent gate status propagation')
    return gate['exit_code']


def report_from_bytes(content,artifact_bytes):
    report=_json_from_bytes(content);expected=evaluate_artifact(artifact_bytes)
    if _json_bytes(report)!=_json_bytes(expected):raise ValueError('fault report/model/gate replay mismatch')
    return report


def development_specs(recipe):
    _fields(recipe,{'fault_recipe_version','recipe_id','payload_sizes_bytes','intervals_ms','window_durations_ms','repetitions','master_seed','max_attempts','requested_power_dbm','cases','units','assumptions_sha256','research_policy_sha256','model_parameters_path','model_parameters_sha256','parent_grouping','benchmark_scoring'},'development recipe')
    if type(recipe['fault_recipe_version']) is not int or recipe['fault_recipe_version']!=1 or recipe['benchmark_scoring'] is not False:raise ValueError('only frozen development recipes are supported here')
    _fields(recipe['cases'],KINDS,'fault cases');_fields(recipe['units'],KINDS,'severity units')
    for key in ('repetitions','max_attempts'):_integer(recipe[key],key,minimum=1,maximum=16)
    _integer(recipe['master_seed'],'master_seed',maximum=2**64-1)
    for key in ('payload_sizes_bytes','intervals_ms','window_durations_ms'):
        values=recipe[key]
        if not isinstance(values,list) or not values or values!=sorted(set(values)):raise ValueError('grid axes must be sorted unique')
        for value in values:_integer(value,key,minimum=1,maximum=3600000)
    if any(not isinstance(v,list) or not v or any(type(s) is not int or s<0 for s in v) or v!=sorted(set(v)) for v in recipe['cases'].values()):raise ValueError('invalid fault severity axis')
    _fields(recipe['requested_power_dbm'],{'tx_power_lock','other_faults'},'requested powers')
    for value in recipe['requested_power_dbm'].values():_integer(value,'requested power',minimum=-100,maximum=100)
    for key in ('assumptions_sha256','research_policy_sha256','model_parameters_sha256'):_digest(recipe[key],key)
    specs=[]
    for payload in recipe['payload_sizes_bytes']:
        for interval in recipe['intervals_ms']:
            parent=parent_id(payload,interval)
            for repetition in range(1,recipe['repetitions']+1):
                seed=int(_sha256(f'fault-grid-v1:{recipe["master_seed"]}:{parent}:{repetition}'.encode())[:16],16)
                for window in recipe['window_durations_ms']:
                    for kind,severities in recipe['cases'].items():
                        tx=recipe['requested_power_dbm']['tx_power_lock' if kind=='tx_power_lock' else 'other_faults']
                        for severity in severities:
                            intent=make_intent(payload,interval,window,tx,seed,repetition,max_attempts=recipe['max_attempts'])
                            specs.append((intent,dict(kind=kind,severity=severity)))
    return specs


def write_development(output_path):
    recipe_bytes=DEVELOPMENT.read_bytes();recipe=_json_from_bytes(recipe_bytes);a=ASSUMPTIONS.read_bytes();policy=RESEARCH_POLICY.read_bytes()
    parameters=(ROOT/recipe['model_parameters_path']).read_bytes()
    for actual,expected in [(a,recipe['assumptions_sha256']),(policy,recipe['research_policy_sha256']),(parameters,recipe['model_parameters_sha256'])]:
        if _sha256(actual)!=expected:raise ValueError('development source hash mismatch')
    cases=[];seen=set()
    with FreshDirectory(output_path) as output:
        output.write('recipe.json',recipe_bytes);output.write('research-policy.json',policy)
        for intent,fault in development_specs(recipe):
            artifact=build_artifact(parameters,_json_bytes(intent),a,_json_bytes(fault));data=_json_bytes(artifact)
            report=evaluate_artifact(data);identifier=artifact['lineage']['child_id']
            if identifier in seen:raise ValueError('duplicate development case identity')
            seen.add(identifier);output.write(f'artifacts/{identifier}.json',data);output.write(f'reports/{identifier}.json',_json_bytes(report))
            cases.append(dict(id=identifier,fault=fault,parent_id=artifact['lineage']['parent_id'],status=artifact['execution']['status'],
                baseline_energy_mj=artifact['baseline']['total_energy_mj'],fault_energy_mj=artifact['execution']['total_energy_mj'],
                budget_violation=report['analytical']['budget_violation'],frozen_policy_point_violations=[x['fault_violation'] for x in report['analytical']['frozen_policy_point_checks']],mechanism_occurred=report['mechanism_occurred'],
                inputs_changed=report['predictor']['inputs_changed'],predictions_changed=report['predictor']['predictions_changed'],
                gate_status=report['gatekeeper']['status'],gate_exit=gate_exit(report),execution_blocked=report['execution_blocked'],
                positive_detection=report['positive_fault_detection'],energy_fault_undetected=report['energy_fault_undetected'],
                control_false_alarm=report['control_false_alarm'],control_blocked=report['control_blocked_without_positive_detection'],
                artifact_sha256=_sha256(data),report_sha256=_sha256(_json_bytes(report))))
        summary=dict(development_summary_version=1,provenance=PROVENANCE,recipe_sha256=_sha256(recipe_bytes),case_count=len(cases),
            parent_count=len({c['parent_id'] for c in cases}),cases=cases,benchmark_scored=False,software_harness_success_is_energy_approval=False)
        output.write('summary.json',_json_bytes(summary))
        lines=['# Week11 analytical development diagnostics','', '**ANALYTICAL SIMULATION / RESEARCH ONLY. No physical detection or energy approval.**','',
            'ABSTAIN/ERROR may block; neither is a positive fault detection. Hidden actual states never enter pre-run X.','',
            '| Fault / severity | Actual energy mJ | Baseline mJ | Oracle violation | Gate / exit | Positive detection |',
            '|---|---:|---:|---|---|---|']
        for c in cases:lines.append('| '+' | '.join(escape(v) for v in [f'{c["fault"]["kind"]}/{c["fault"]["severity"]}',c['fault_energy_mj'],c['baseline_energy_mj'],c['budget_violation'],f'{c["gate_status"]}/{c["gate_exit"]}',c['positive_detection']])+' |')
        lines+=['','Gate blocking means would block a candidate; these offline simulations already ran and no physical firmware execution occurred.',
                'All assumptions/source snapshots/lineage and exact gate/model outputs are archived per case. No calibrated intervals or physical causal attributions.','']
        output.write('summary.md','\n'.join(lines).encode())
    return summary


def main(argv=None):
    parser=Parser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('development');p.add_argument('--output-dir',type=Path,required=True)
    p=commands.add_parser('gate');p.add_argument('--artifact',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    try:
        args=parser.parse_args(argv)
        if args.command=='development':
            output=args.output_dir.expanduser().resolve()
            if any(p in output.parents or output==p for p in (ROOT/'tools',ROOT/'docs')):raise ValueError('development output may not alias source directories')
            summary=write_development(output)
            print(f'SOFTWARE HARNESS completed{summary["case_count"]} analytical cases; NOT energy approval.');return 0
        from atomic_outputs import reserve_outputs
        output=args.output.expanduser().resolve()
        if output==args.artifact.resolve() or ROOT/'tools' in output.parents or ROOT/'docs' in output.parents:raise ValueError('output aliases source data')
        with reserve_outputs([output]) as reservation:
            report=evaluate_artifact(args.artifact.read_bytes());reservation.publish({output:_json_bytes(report).decode('utf-8')})
        return gate_exit(report)
    except (OSError,UnicodeError,ValueError,TypeError,OverflowError,ZeroDivisionError) as error:
        print(f'ERROR: {error}',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
