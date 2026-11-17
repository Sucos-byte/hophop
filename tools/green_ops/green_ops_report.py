# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Validate/hash-bound Week9 decisions and render local Markdown; never post comments."""
import html
import json
import math
from pathlib import Path
import sys
import unicodedata
from analytical_reference import _fields,_json_bytes,_sha256,_number
from dataset_builder import _json_from_bytes
from budget_policy import (EXIT_CODES,policy_from_bytes,aggregate,checked,bounds,upper_budget,regression,nonempty)
from battery_projection import battery_decision
from ml_dataset import TARGET_UNITS,_digest
from feature_contract import PRE_RUN_FEATURES
from atomic_outputs import reserve_outputs
from green_ops_gatekeeper import Parser
from gate_evidence import REFERENCE_HASHES,CALIBRATION_SET_SHA256
from week8_dataset import RECIPE_SHA256

COMMON={'decision_report_version','status','exit_code','blocks_ci','reason_codes','research_only','hardware_assurance',
        'criteria','provenance','artifact_sha256','uncertainty_policy','assumptions','limitations','candidate_revision','baseline_revision'}
NORMAL=COMMON|{'policy_id','policy_sha256','research_override_requested','research_override_used','evidence_label','battery_projection',
 'feature_contract_version','feature_profile','model_sha256','comparison_scope','validated_95_percent_coverage','resolved_workload',
 'prediction_context','prediction_domain','coverage_reference','execution_regression_observable_from_commit_identity','attributions'}
ERROR=COMMON|{'detail'}
PREDICTION={'point','interval','unit','family_coverage','unavailable_reason'}


def strings(value,name):
    if not isinstance(value,list) or any(not isinstance(x,str) or not x for x in value):raise ValueError(f'invalid {name}')


def hash_tree(value,*,allow_none=False):
    if isinstance(value,dict):
        if not value:raise ValueError('empty artifact hash inventory')
        for key,item in value.items():nonempty(key,'hash label');hash_tree(item,allow_none=allow_none)
    elif value is None and allow_none:return
    else:_digest(value,'artifact digest')


def prediction(value,target):
    if value is None:return
    _fields(value,PREDICTION,'criterion prediction')
    if value['unit']!=TARGET_UNITS[target]:raise ValueError('prediction unit mismatch')
    if value['point'] is not None:checked(value['point'],'prediction point')
    if value['interval'] is not None:
        low,high=bounds(value['interval'])
        if value['point'] is None or not low<=value['point']<=high:raise ValueError('point/range mismatch')
    if value['family_coverage'] is not None:
        _number(value['family_coverage'],'family coverage')
        if value['family_coverage']>1:raise ValueError('invalid family coverage')
    if value['unavailable_reason'] is not None:nonempty(value['unavailable_reason'],'unavailable reason')


def validate_attributions(value,criteria):
    if value is None:return
    _fields(value,{'candidate','baseline'},'attribution roles')
    for role,targets in value.items():
        if targets is None:continue
        if not isinstance(targets,dict) or not set(targets)<=set(TARGET_UNITS):raise ValueError('invalid attribution targets')
        for target,a in targets.items():
            _fields(a,{'unit','method','interpretation','baseline','prediction','contributions','top_three'},'attribution')
            if a['unit']!=TARGET_UNITS[target] or a['interpretation']!='model_attribution_not_physical_root_cause':raise ValueError('incompatible attribution unit/interpretation')
            nonempty(a['method'],'attribution method');_fields(a['contributions'],PRE_RUN_FEATURES,'contribution features')
            for x in [a['baseline'],a['prediction'],*a['contributions'].values()]:checked(x,'contribution value')
            if not math.isclose(a['baseline']+math.fsum(a['contributions'].values()),a['prediction'],rel_tol=1e-12,abs_tol=1e-9):raise ValueError('contribution accounting mismatch')
            expected=sorted(PRE_RUN_FEATURES,key=lambda f:(-abs(a['contributions'][f]),list(PRE_RUN_FEATURES).index(f)))[:3]
            if a['top_three']!=expected:raise ValueError('top-three contribution mismatch')
            for c in criteria:
                if c['kind']!='battery_minimum_years' and c['target']==target and c[role] is not None and c[role]['point'] is not None:
                    if a['prediction']!=c[role]['point']:raise ValueError('attribution/prediction mismatch')


def _validate_decision(content,expected_sha256,policy_bytes):
    """Digest must be supplied by a trusted producer; hashes are not authentication."""
    _digest(expected_sha256,'expected decision SHA256')
    if len(content)>4*1024*1024:raise ValueError('decision exceeds report size limit')
    if _sha256(content)!=expected_sha256:raise ValueError('decision hash mismatch')
    r=_json_from_bytes(content);_json_bytes(r)
    if not isinstance(r,dict) or not isinstance(r.get('status'),str) or r['status'] not in EXIT_CODES:raise ValueError('unsupported decision status')
    _fields(r,ERROR if r['status']=='ERROR' else NORMAL,'decision report')
    if type(r['decision_report_version']) is not int or r['decision_report_version']!=1:raise ValueError('unsupported decision version')
    if type(r['exit_code']) is not int or r['exit_code']!=EXIT_CODES[r['status']] or type(r['blocks_ci']) is not bool or r['blocks_ci']!=(r['status']!='PASS'):raise ValueError('decision status/exit/block mismatch')
    if r['research_only'] is not True or r['hardware_assurance'] is not False:raise ValueError('report must remain research-only')
    for key in ('reason_codes','assumptions','limitations'):strings(r[key],key)
    if not r['reason_codes'] or r['reason_codes']!=sorted(set(r['reason_codes'])):raise ValueError('reason codes must be sorted unique')
    for key in ('candidate_revision','baseline_revision'):
        if r[key] is not None:nonempty(r[key],key)
    if r['status']=='ERROR':
        nonempty(r['detail'],'error detail')
        if r['criteria']!=[] or r['provenance']!='not_established' or r['uncertainty_policy'] is not None:raise ValueError('invalid ERROR decision shape')
        _fields(r['artifact_sha256'],{'policy'},'error hash inventory')
        digest=r['artifact_sha256']['policy']
        if digest is not None and digest!=_sha256(policy_bytes):raise ValueError('ERROR policy hash mismatch')
        return r
    policy=policy_from_bytes(policy_bytes)
    if r['policy_sha256']!=_sha256(policy_bytes) or r['policy_id']!=policy['policy_id']:raise ValueError('policy binding mismatch')
    if (r['feature_contract_version']!=policy['feature_contract_version'] or type(r['feature_contract_version']) is not int
        or r['feature_profile']!=policy['feature_profile'] or r['model_sha256']!=policy['scope']['model_sha256']):raise ValueError('model/feature policy mismatch')
    if r['uncertainty_policy']!=policy['uncertainty']:raise ValueError('uncertainty policy mismatch')
    for key in ('research_override_requested','research_override_used'):
        if type(r[key]) is not bool:raise ValueError('invalid override flag')
    if r['research_override_used'] and not (r['research_override_requested'] and policy['uncertainty']['allow_unvalidated_research_intervals']):raise ValueError('override lacks explicit two-part opt-in')
    if (r['validated_95_percent_coverage'] is not False or r['execution_regression_observable_from_commit_identity'] is not False
        or r['comparison_scope']!='configuration_estimates_only'):raise ValueError('unsupported assurance/observability claim')
    if r['provenance'] not in ('analytical_simulation','measured','unmeasured'):raise ValueError('invalid provenance')
    for key in ('evidence_label','coverage_reference'):nonempty(r[key],key)
    _fields(r['artifact_sha256'],{'candidate','baseline'},'artifact roles')
    source_fields={'original_recipe','study_recipe','selection','evaluation.json','explanations.json','calibration_set','source_manifest','source_dataset','parameters','assumptions'}|{t+suffix for t in TARGET_UNITS for suffix in ('-model','-calibration')}
    for role in ('candidate','baseline'):
        inventory=r['artifact_sha256'][role]
        if inventory is None and role=='baseline':continue
        _fields(inventory,source_fields,'source hash inventory');hash_tree(inventory)
        if any(inventory[t+'-model']!=digest for t,digest in r['model_sha256'].items()):raise ValueError('referenced model identity mismatch')
        if any(inventory[name]!=digest for name,digest in REFERENCE_HASHES.items()) or inventory['calibration_set']!=CALIBRATION_SET_SHA256 or inventory['study_recipe']!=RECIPE_SHA256:raise ValueError('frozen evidence reference mismatch')
    for key in ('resolved_workload','prediction_context','prediction_domain'):_fields(r[key],{'candidate','baseline'},key)
    for role in ('candidate','baseline'):
        w=r['resolved_workload'][role];c=r['prediction_context'][role];d=r['prediction_domain'][role]
        if w is None:
            if role=='candidate' or c is not None or d is not None:raise ValueError('missing/inconsistent workload context')
            continue
        _fields(w,{'payload_size_bytes','interval_ms','tx_power_dbm','window_duration_ms','offered_packets','max_attempts','seed','parameters_sha256','assumptions_sha256','adapter','feature_profile_id'},'workload')
        for name in ('payload_size_bytes','interval_ms','window_duration_ms','max_attempts'):_number(w[name],name,positive=True)
        for name in ('offered_packets','seed'):_number(w[name],name)
        checked(w['tx_power_dbm'],'TX power')
        for name in ('parameters_sha256','assumptions_sha256'):_digest(w[name],name)
        for name in ('adapter','feature_profile_id'):nonempty(w[name],name)
        _fields(c,{'available_fields','planned_window_duration_ms','completed_as_planned'},'prediction context')
        strings(c['available_fields'],'available fields')
        if c['completed_as_planned'] is not None and type(c['completed_as_planned']) is not bool:raise ValueError('invalid completion')
        if c['planned_window_duration_ms'] is not None:_number(c['planned_window_duration_ms'],'planned duration',positive=True)
        if d not in ('primary','declared_stress'):raise ValueError('invalid prediction domain')
    if not isinstance(r['criteria'],list) or not r['criteria'] or any(not isinstance(c,dict) for c in r['criteria']):raise ValueError('decision criteria required')
    expected={c['id']:c for c in policy['criteria']}
    if policy['battery'] is not None:expected['battery']=dict(id='battery',kind='battery_minimum_years',target='target_mean_power_mw',unit='years',threshold=policy['battery']['target_years'])
    if [c.get('id') for c in r['criteria']]!=list(expected):raise ValueError('policy/decision criterion membership mismatch')
    for c in r['criteria']:
        rule=expected[c['id']];base={'id','kind','target','unit','threshold','candidate','baseline','status','reason_code','comparison_method'}
        if c['kind']!='battery_minimum_years':base.add('evidence_acceptance')
        extras=set(c)-base
        if extras and (c['kind'] not in ('regression_absolute','regression_relative') or extras!={'point_delta','point_delta_unit','point_regression_percent'}):raise ValueError('unknown criterion fields')
        _fields(c,base|extras,'criterion')
        if any(_json_bytes(c[k])!=_json_bytes(rule[k]) for k in ('id','kind','target','unit','threshold')):raise ValueError('criterion policy/units mismatch')
        if c['status'] not in ('PASS','FAIL','ABSTAIN'):raise ValueError('invalid criterion status')
        for key in ('reason_code','comparison_method'):nonempty(c[key],key)
        if c['kind']=='battery_minimum_years':
            if c['candidate'] is not None:bounds(c['candidate'],'lifetime range')
            if c['baseline'] is not None:raise ValueError('unexpected battery baseline')
        else:
            prediction(c['candidate'],c['target']);prediction(c['baseline'],c['target'])
            if c['candidate'] is None:raise ValueError('missing candidate prediction')
            nonempty(c['evidence_acceptance'],'evidence acceptance')
            if extras:
                checked(c['point_delta'],'point delta')
                if c['point_delta_unit']!=TARGET_UNITS[c['target']]:raise ValueError('point delta unit mismatch')
                if c['point_regression_percent'] is not None:checked(c['point_regression_percent'],'point percent')
            if c['status'] in ('PASS','FAIL'):
                p=c['candidate']
                if p['point'] is None or p['interval'] is None or p['unavailable_reason']:raise ValueError('decision lacks applicable interval')
                if p['family_coverage'] is None or p['family_coverage']<.95:
                    if not r['research_override_used']:raise ValueError('decision bypassed inadequate coverage')
                if r['prediction_domain']['candidate']=='declared_stress' and not (policy['uncertainty']['allow_assumption_shift'] and r['research_override_used']):raise ValueError('decision bypassed assumption shift')
                status=upper_budget(p['interval'],c['threshold'])[0] if c['kind']=='absolute_upper' else regression(p['interval'],c['baseline']['interval'] if c['baseline'] is not None else None,c['threshold'],relative=c['kind']=='regression_relative')[0]
                if status!=c['status']:raise ValueError('numeric criterion decision mismatch')
    if aggregate([c['status'] for c in r['criteria']])!=r['status'] or sorted({c['reason_code'] for c in r['criteria']})!=r['reason_codes']:raise ValueError('aggregate decision mismatch')
    projection=r['battery_projection']
    if policy['battery'] is None:
        if projection is not None:raise ValueError('unexpected battery projection')
    else:
        if not isinstance(projection,dict) or type(projection.get('available')) is not bool:raise ValueError('invalid battery projection')
        base={'available','capacity_mah','voltage_v','usable_fraction','conversion_efficiency','load_energy_mwh','year_days','hours_per_year','target_years','workload_profile','omitted_effects','assumptions','reason_code'}
        optional={'mean_power_mw','power_basis','point_years','lifetime_years'}
        if not base<=set(projection) or set(projection)-base-optional:raise ValueError('battery projection fields mismatch')
        spec=policy['battery']
        for k in ('capacity_mah','voltage_v','usable_fraction','conversion_efficiency','year_days','target_years','workload_profile'):
            if projection[k]!=spec[k]:raise ValueError('battery/policy assumption mismatch')
        if projection['load_energy_mwh']!=spec['capacity_mah']*spec['voltage_v']*spec['usable_fraction']*spec['conversion_efficiency'] or projection['hours_per_year']!=24*spec['year_days']:raise ValueError('battery units/loss accounting mismatch')
        for k in ('load_energy_mwh','hours_per_year','mean_power_mw','point_years'):
            if k in projection:checked(projection[k],k)
        strings(projection['assumptions'],'battery assumptions');strings(projection['omitted_effects'],'battery omissions')
        bc=next(c for c in r['criteria'] if c['id']=='battery')
        if projection['available']:
            low,high=bounds(projection['lifetime_years'])
            if low<=0 or bc['candidate']!=projection['lifetime_years']:raise ValueError('battery lifetime mismatch')
            if bc['status'] in ('PASS','FAIL') and battery_decision(projection)[0]!=bc['status']:raise ValueError('battery decision mismatch')
    validate_attributions(r['attributions'],r['criteria'])
    return r


def validate_decision(content,expected_sha256,policy_bytes):
    try:return _validate_decision(content,expected_sha256,policy_bytes)
    except (TypeError,KeyError,AttributeError,OverflowError,RecursionError) as error:
        raise ValueError(f'malformed decision: {error}') from error


def escape(value):
    """One inert table cell: no raw HTML, active Markdown, links or hidden controls."""
    if value is None:return 'Not provided'
    if not isinstance(value,str):value=json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False)
    out=[]
    for char in value:
        if unicodedata.category(char) in ('Cc','Cf'):out.append(' ' if char in '\r\n\t' else f'U+{ord(char):04X}')
        elif char in '&<>"\'':out.append(html.escape(char,quote=True))
        elif char in ':@':out.append(f'&#{ord(char)};')
        elif char in '\\`*_{}[]()#+-.!|~':out.append('\\'+char)
        else:out.append(char)
    return ''.join(out)


def table(rows):return ['| Field | Value |','|---|---|']+[f'| {escape(k)} | {escape(v)} |' for k,v in rows]


def leaves(value,prefix=''):
    if isinstance(value,dict):
        for k in sorted(value):yield from leaves(value[k],f'{prefix}.{k}' if prefix else k)
    else:yield prefix,value


def render(r,decision_sha256):
    lines=['# Green Ops engineering-policy report','',f"**{r['status']} — exit {r['exit_code']}; {'BLOCKS' if r['blocks_ci'] else 'scoped research result only'}.**",'',
      '**RESEARCH ONLY. No hardware assurance or legal-compliance certification.**','',
      '**ANALYTICAL SIMULATION; unvalidated evidence**' if r['provenance']=='analytical_simulation' else '**Evidence provenance not established for physical assurance.**','']
    if r.get('research_override_used'):lines+=['**EXPLICIT UNVALIDATED RESEARCH OVERRIDE — no validated 95% coverage.**','']
    lines+=table([('Reason codes',r['reason_codes']),('Provenance',r['provenance']),('Decision SHA256',decision_sha256),
        ('Candidate identity label',r['candidate_revision']),('Baseline identity label',r['baseline_revision'])])+['']
    if r['status']=='ERROR':
        lines+=['## Processing error','']+table([('Detail',r['detail']),('Policy digest',r['artifact_sha256']['policy']),('Explanations','Not provided; evidence was not established.')])+['']
    else:
        lines+=['## Policy, model and comparable context','']+table([('Policy',r['policy_id']),('Policy SHA256',r['policy_sha256']),
            ('Evidence label',r['evidence_label']),('Override requested / used',[r['research_override_requested'],r['research_override_used']]),
            ('Feature contract/profile',[r['feature_contract_version'],r['feature_profile']]),('Comparison scope',r['comparison_scope'])])+['']
        for label,key in [('Model identities','model_sha256'),('Workload and windows','resolved_workload'),('Prediction context','prediction_context'),('Domains','prediction_domain')]:
            lines+=['### '+label,'']+table(list(leaves(r[key])))+['']
        lines+=['## Required criteria','']
        for c in r['criteria']:
            lines+=table(list(leaves(c)))+['']
        lines+=['## Battery assumptions and projection','']
        lines+=table(list(leaves(r['battery_projection']))) if r['battery_projection'] is not None else ['No battery criterion/projection provided.']
        lines+=['','Five years is a configurable engineering-policy target, not a certification. Run-average duty is not applied twice.','',
                '## Top-three compatible model attributions','',
                'Signed influence relative to the model training baseline, in target units. Model influence is not proven physical root cause.','']
        for role in ('candidate','baseline'):
            attrs=(r['attributions'] or {}).get(role)
            lines+=['### '+role.title(),'']
            if not attrs:lines+=['Missing explanations: no compatible attributions provided.',''];continue
            for target,a in sorted(attrs.items()):
                lines+=table([('Target',target),('Unit',a['unit']),('Method',a['method']),('Training baseline',a['baseline']),('Prediction',a['prediction'])]+
                    [(feature,a['contributions'][feature]) for feature in a['top_three']])+['']
        lines+=['## Evidence and artifact references','']+table(list(leaves(r['artifact_sha256'])))+['']
        lines+=['## Uncertainty and coverage','']+table(list(leaves(r['uncertainty_policy']))+[('Coverage reference',r['coverage_reference'])])+['',
            'Observed nominal family coverage: power 28/30, total energy 28/30, per-delivery 26/30; below nominal 95%. Assumption shifts have no calibrated coverage guarantee.',
            'Marginal interval comparisons are not calibrated difference or joint confidence intervals.','']
    lines+=['## Assumptions and limitations','']+table([('Assumptions',r['assumptions']),('Limitations',r['limitations'])])+['',
      'Identical permitted features yield identical fixed-model predictions regardless of commit identity. Configuration estimates are not execution telemetry.','',
      'Rendered locally. No GitHub comment, upload, publication or deployment performed.','']
    return '\n'.join(lines)


def generate(content,expected_sha256,policy_bytes):return render(validate_decision(content,expected_sha256,policy_bytes),expected_sha256)


def main(argv=None):
    parser=Parser(description=__doc__);parser.add_argument('--decision',type=Path,required=True);parser.add_argument('--decision-sha256',required=True)
    parser.add_argument('--policy',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    try:
        args=parser.parse_args(argv);output=args.output.expanduser().resolve()
        if output in (args.decision.resolve(),args.policy.resolve()):raise ValueError('report output aliases input')
        with reserve_outputs([output]) as reservation:
            markdown=generate(args.decision.read_bytes(),args.decision_sha256,args.policy.read_bytes())
            reservation.publish({output:markdown})
        print('Markdown generated locally; rendering success is not candidate approval.');return 0
    except (OSError,UnicodeError,ValueError,TypeError,KeyError,OverflowError) as error:
        print(f'ERROR: {error}',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
