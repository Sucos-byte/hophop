# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Research-only energy budget gate. PASS=0 ERROR=1 FAIL=2 ABSTAIN=3; no hardware assurance."""
import argparse
import copy
from pathlib import Path
import sys
from analytical_reference import _fields,_json_bytes,_sha256,_number
from ml_dataset import TARGET_UNITS,_digest
from feature_contract import PRE_RUN_FEATURES
from budget_policy import (EXIT_CODES,validate_policy,policy_from_bytes,checked,bounds,nonempty,
                           upper_budget,regression,aggregate)
from battery_projection import project_battery,battery_decision
from gate_evidence import FrozenEvidence
from atomic_outputs import reserve_outputs

REPO=Path(__file__).resolve().parents[2]
EVIDENCE_FIELDS={'evidence_version','provenance','feature_contract_version','feature_profile','prediction_mode','model_sha256',
 'comparable_workload','prediction_context','predictions','artifact_sha256','attributions','domain','revision','run_id'}
LIMITATIONS=['research_only_no_hardware_assurance','observed_family_coverage_below_nominal_95_percent',
 'marginal_ranges_are_not_calibrated_difference_or_joint_confidence_intervals',
 'identical_permitted_features_fixed_model_identical_predictions_regardless_of_commit',
 'configuration_estimate_not_actual_execution_telemetry','consumed_week8_data_not_reused_for_tuning',
 'assumption_shift_has_no_calibrated_coverage_guarantee','model_attribution_not_physical_causation']


def validate_evidence(value,policy):
    _fields(value,EVIDENCE_FIELDS,'resolved evidence')
    if type(value['evidence_version']) is not int or value['evidence_version']!=1:raise ValueError('evidence version mismatch')
    if (type(value['feature_contract_version']) is not int or value['feature_contract_version']!=policy['feature_contract_version']
        or value['feature_profile']!=policy['feature_profile'] or value['prediction_mode']!='pre_run'):raise ValueError('incompatible evidence feature contract/context')
    if value['provenance'] not in ('analytical_simulation','measured','unmeasured'):raise ValueError('unknown provenance')
    if value['domain'] not in ('primary','declared_stress'):raise ValueError('invalid prediction domain')
    if value['model_sha256']!=policy['scope']['model_sha256']:raise ValueError('policy/model identity mismatch')
    if value['revision'] is not None:nonempty(value['revision'],'revision label')
    nonempty(value['run_id'],'run id')
    workload=value['comparable_workload'];context=value['prediction_context']
    _fields(workload,{'payload_size_bytes','interval_ms','tx_power_dbm','window_duration_ms','offered_packets','max_attempts','seed','parameters_sha256','assumptions_sha256','adapter','feature_profile_id'},'comparable workload')
    for name in ('payload_size_bytes','interval_ms','window_duration_ms','max_attempts'):_number(workload[name],name,positive=True)
    for name in ('offered_packets','seed'):_number(workload[name],name)
    checked(workload['tx_power_dbm'],'TX power')
    for name in ('parameters_sha256','assumptions_sha256'):_digest(workload[name],name)
    for name in ('adapter','feature_profile_id'):nonempty(workload[name],name)
    _fields(context,{'available_fields','completed_as_planned','planned_window_duration_ms'},'prediction context')
    if context['completed_as_planned'] is not None and type(context['completed_as_planned']) is not bool:raise ValueError('invalid completion flag')
    if context['planned_window_duration_ms'] is not None:_number(context['planned_window_duration_ms'],'planned duration',positive=True)
    if not isinstance(context['available_fields'],list) or any(not isinstance(v,str) for v in context['available_fields']):raise ValueError('invalid feature availability')
    if not isinstance(value['artifact_sha256'],dict) or not value['artifact_sha256']:raise ValueError('artifact hashes required')
    for key,digest in value['artifact_sha256'].items():nonempty(key,'hash name');_digest(digest,'artifact hash')
    _fields(value['predictions'],TARGET_UNITS,'predictions')
    for target,prediction in value['predictions'].items():
        _fields(prediction,{'point','interval','unit','family_coverage','unavailable_reason'},'resolved prediction')
        if prediction['unit']!=TARGET_UNITS[target]:raise ValueError('prediction unit mismatch')
        if prediction['unavailable_reason'] is not None:nonempty(prediction['unavailable_reason'],'unavailable reason')
        if prediction['point'] is not None:checked(prediction['point'],'prediction point')
        if prediction['interval'] is not None:
            low,high=bounds(prediction['interval'])
            if prediction['point'] is None or not low<=prediction['point']<=high:raise ValueError('prediction point/range mismatch')
        if prediction['family_coverage'] is not None:
            _number(prediction['family_coverage'],'family coverage')
            if prediction['family_coverage']>1:raise ValueError('family coverage exceeds one')
    _json_bytes(value)
    return value


def accepted(policy,evidence,target,override):
    if evidence['provenance']!='analytical_simulation' or evidence['provenance']!=policy['scope']['provenance']:return False,'unsupported_provenance',False
    context=evidence['prediction_context']
    if (context['completed_as_planned'] is not True or context['planned_window_duration_ms']!=evidence['comparable_workload']['window_duration_ms']
        or not set(PRE_RUN_FEATURES)<=set(context['available_fields'])):return False,'prediction_context_unavailable',False
    p=evidence['predictions'][target]
    if p['unavailable_reason']:return False,p['unavailable_reason'],False
    if p['point'] is None or p['interval'] is None:return False,'prediction_interval_missing',False
    if p['point']<0:return False,'negative_model_prediction_not_physical_energy',False
    u=policy['uncertainty'];explicit=override and u['allow_unvalidated_research_intervals']
    if evidence['domain']=='declared_stress':
        if not (u['allow_assumption_shift'] and explicit):return False,'assumption_shift_not_accepted',False
        return True,'explicit_unvalidated_research_shift_override',True
    if p['family_coverage'] is None or p['family_coverage']<u['minimum_family_coverage']:
        if not explicit:return False,'observed_family_coverage_inadequate',False
        return True,'explicit_unvalidated_research_coverage_override',True
    return True,'scoped_interval_evidence_accepted',False


def decide(policy,candidate,baseline=None,*,allow_research_override=False,policy_sha256=None):
    """Pure policy engine over evidence already resolved by FrozenEvidence, not a JSON evidence loader."""
    policy=validate_policy(policy)
    if type(allow_research_override) is not bool:raise ValueError('override must be boolean')
    validate_evidence(candidate,policy)
    if baseline is not None:validate_evidence(baseline,policy)
    criteria=[];used=False
    for rule in policy['criteria']:
        target=rule['target'];c=candidate['predictions'][target];b=baseline['predictions'][target] if baseline is not None else None
        ok,reason,overridden=accepted(policy,candidate,target,allow_research_override);used|=overridden
        entry=dict(id=rule['id'],kind=rule['kind'],target=target,unit=rule['unit'],threshold=rule['threshold'],
                   candidate=copy.deepcopy(c),baseline=copy.deepcopy(b),evidence_acceptance=reason,
                   comparison_method='upper_bound' if rule['kind']=='absolute_upper' else 'logical_marginal_range_comparison_not_a_difference_ci')
        status='ABSTAIN'
        if ok and rule['kind']=='absolute_upper':status,reason=upper_budget(c['interval'],rule['threshold'])
        elif ok:
            if baseline is None:reason='baseline_missing'
            elif (candidate['provenance']!=baseline['provenance'] or candidate['comparable_workload']!=baseline['comparable_workload']
                  or candidate['prediction_context']!=baseline['prediction_context'] or candidate['domain']!=baseline['domain']):reason='incomparable_workload_windows_or_context'
            else:
                bok,reason,boverride=accepted(policy,baseline,target,allow_research_override);used|=boverride
                if bok:
                    relative=rule['kind']=='regression_relative';status,reason=regression(c['interval'],b['interval'],rule['threshold'],relative=relative)
                    delta=c['point']-b['point'];checked(delta,'point regression delta');entry['point_delta']=delta;entry['point_delta_unit']=TARGET_UNITS[target]
                    if b['point']>0:
                        percent=(delta/b['point'])*100;checked(percent,'point regression percent');entry['point_regression_percent']=percent
                    else:entry['point_regression_percent']=None
        entry.update(status=status,reason_code=reason);criteria.append(entry)
    projection=None
    if policy['battery'] is not None:
        target='target_mean_power_mw';c=candidate['predictions'][target]
        projection=project_battery(policy['battery'],c if c['point'] is not None else None)
        ok,reason,overridden=accepted(policy,candidate,target,allow_research_override);used|=overridden
        profile=policy['battery']['workload_profile']
        if profile is not None and profile['kind']=='component_states':
            explicit=allow_research_override and policy['uncertainty']['allow_unvalidated_research_intervals']
            if ok:
                ok=explicit
                reason='explicit_unvalidated_component_state_assumptions' if ok else 'component_states_have_no_calibrated_coverage'
            used|=ok
        if not projection['available']:ok=False;reason=projection['reason_code']
        status,reason=battery_decision(projection) if ok else ('ABSTAIN',reason)
        criteria.append(dict(id='battery',kind='battery_minimum_years',target=target,unit='years',threshold=policy['battery']['target_years'],
            candidate=projection.get('lifetime_years'),baseline=None,status=status,reason_code=reason,
            comparison_method='inverse_power_bounds_engineering_projection_not_confidence_interval'))
    status=aggregate([r['status'] for r in criteria])
    return dict(decision_report_version=1,status=status,exit_code=EXIT_CODES[status],blocks_ci=status!='PASS',reason_codes=sorted({r['reason_code'] for r in criteria}),
        policy_id=policy['policy_id'],policy_sha256=policy_sha256 or _sha256(_json_bytes(policy)),research_only=True,
        research_override_requested=allow_research_override,research_override_used=used,
        evidence_label='UNVALIDATED RESEARCH-ONLY OVERRIDE; NO VALIDATED 95% COVERAGE OR HARDWARE ASSURANCE' if used else 'RESEARCH ONLY; NO HARDWARE ASSURANCE',
        uncertainty_policy=policy['uncertainty'],criteria=criteria,battery_projection=projection,
        provenance=candidate['provenance'],feature_contract_version=3,feature_profile=policy['feature_profile'],model_sha256=candidate['model_sha256'],
        artifact_sha256=dict(candidate=candidate['artifact_sha256'],baseline=baseline['artifact_sha256'] if baseline else None),
        candidate_revision=candidate['revision'],baseline_revision=baseline['revision'] if baseline else None,
        execution_regression_observable_from_commit_identity=False,
        attributions=dict(candidate=candidate['attributions'],baseline=baseline['attributions'] if baseline else None),
        assumptions=['frozen analytical generator and prediction profile','intervals retain observed family coverage failures',
          'comparable full-slot workloads and windows for regression','no joint or difference confidence guarantee'],limitations=LIMITATIONS)


class Parser(argparse.ArgumentParser):
    def error(self,message):raise ValueError(message)


def main(argv=None):
    parser=Parser(description=__doc__)
    parser.add_argument('--policy',type=Path,required=True);parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--baseline',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--model-dir',type=Path,default=REPO/'docs/results/week7-regression-v1/training')
    parser.add_argument('--calibration-dir',type=Path,default=REPO/'docs/results/week8/calibration')
    parser.add_argument('--original-recipe',type=Path,default=REPO/'tools/green_ops/recipes/week7-regression-v1.json')
    parser.add_argument('--study-recipe',type=Path,default=REPO/'tools/green_ops/recipes/week8-uncertainty-v1.json')
    parser.add_argument('--reference-dir',type=Path,default=REPO/'docs/results/week8')
    parser.add_argument('--domain',choices=('primary','declared_stress'),default='primary')
    parser.add_argument('--baseline-domain',choices=('primary','declared_stress'),default='primary')
    parser.add_argument('--candidate-revision');parser.add_argument('--baseline-revision')
    parser.add_argument('--allow-research-override',action='store_true')
    try:
        args=parser.parse_args(argv);output=args.output.expanduser().resolve()
        inputs=[v.expanduser().resolve() for k,v in vars(args).items() if isinstance(v,Path) and k!='output']
        if any(output==p or p in output.parents for p in inputs):raise ValueError('decision output aliases or lies within input sources')
        with reserve_outputs([output]) as reservation:
            content=None
            try:
                content=args.policy.read_bytes();policy=policy_from_bytes(content)
                source=FrozenEvidence(args.model_dir,args.calibration_dir,args.original_recipe,args.study_recipe,args.reference_dir)
                candidate=source.load(args.candidate,domain=args.domain,revision=args.candidate_revision)
                baseline=source.load(args.baseline,domain=args.baseline_domain,revision=args.baseline_revision) if args.baseline else None
                result=decide(policy,candidate,baseline,allow_research_override=args.allow_research_override,policy_sha256=_sha256(content))
            except (OSError,UnicodeError,ValueError,OverflowError,ZeroDivisionError) as error:
                result=dict(decision_report_version=1,status='ERROR',exit_code=1,blocks_ci=True,research_only=True,
                    reason_codes=['malformed_incompatible_or_processing_error'],detail=str(error),hardware_assurance=False,criteria=[],
                    provenance='not_established',artifact_sha256={'policy':_sha256(content) if content is not None else None},uncertainty_policy=None,
                    assumptions=[],limitations=LIMITATIONS,candidate_revision=args.candidate_revision,baseline_revision=args.baseline_revision)
            reservation.publish({output:_json_bytes(result).decode('utf-8')})
        print(f"{result['status']}: research-only gate; exit {result['exit_code']}")
        return result['exit_code']
    except (OSError,UnicodeError,ValueError,OverflowError,ZeroDivisionError) as error:
        print(f'ERROR: {error}',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
