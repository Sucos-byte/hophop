# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Strict research budget policy v1 and deterministic interval comparisons."""
import copy
import math
from fractions import Fraction
from analytical_reference import _fields,_number
from dataset_builder import _json_from_bytes
from ml_dataset import TARGET_UNITS,_digest

EXIT_CODES={'PASS':0,'ERROR':1,'FAIL':2,'ABSTAIN':3}


def checked(value,name):return _number(value,name,minimum=-math.inf)


def boolean(value,name):
    if type(value) is not bool:raise ValueError(f'{name} must be boolean')


def nonempty(value,name):
    if not isinstance(value,str) or not value.strip():raise ValueError(f'{name} must be a nonempty string')


def bounds(value,name='interval'):
    if not isinstance(value,list) or len(value)!=2:raise ValueError(f'{name} needs two endpoints')
    for x in value:checked(x,name)
    if value[0]>value[1]:raise ValueError('reversed interval')
    return value


def validate_battery(spec):
    _fields(spec,{'capacity_mah','voltage_v','usable_fraction','conversion_efficiency','year_days','target_years','power_basis','workload_profile'},'battery')
    for key in ('capacity_mah','voltage_v','year_days','target_years'):_number(spec[key],key,positive=True)
    for key in ('usable_fraction','conversion_efficiency'):
        _number(spec[key],key,positive=True)
        if spec[key]>1:raise ValueError(f'{key} exceeds one')
    if spec['power_basis']!='load_side_before_conversion':raise ValueError('battery powers must be load-side before conversion')
    profile=spec['workload_profile']
    if profile is None:return
    if not isinstance(profile,dict):raise ValueError('invalid battery workload profile')
    if profile.get('kind')=='run_average':
        _fields(profile,{'kind','repeat','duty_cycle_included'},'run-average profile')
        if profile['repeat']!='continuous_same_workload' or profile['duty_cycle_included'] is not True:raise ValueError('run-average profile must already include duty cycle')
    elif profile.get('kind')=='component_states':
        _fields(profile,{'kind','compatible_states_confirmed','compatibility_id','complete_cycle','states'},'state profile')
        for key in ('compatible_states_confirmed','complete_cycle'):boolean(profile[key],key)
        nonempty(profile['compatibility_id'],'compatibility_id')
        if not isinstance(profile['states'],list) or not profile['states']:raise ValueError('states required')
        names=set()
        for state in profile['states']:
            _fields(state,{'state_id','power_mw','interval_mw','time_fraction'},'component state')
            nonempty(state['state_id'],'state_id')
            if state['state_id'] in names:raise ValueError('duplicate component state')
            names.add(state['state_id']);_number(state['power_mw'],'state power');_number(state['time_fraction'],'time_fraction')
            if state['time_fraction']>1:raise ValueError('invalid time fraction')
            if state['interval_mw'] is not None:
                low,high=bounds(state['interval_mw'])
                if not 0<=low<=state['power_mw']<=high:raise ValueError('state power outside physical interval')
        if not math.isclose(math.fsum(s['time_fraction'] for s in profile['states']),1,rel_tol=0,abs_tol=1e-12):raise ValueError('state fractions must sum one')
    else:raise ValueError('unsupported workload profile kind')


def validate_policy(policy):
    _fields(policy,{'budget_version','policy_id','research_only','feature_contract_version','feature_profile','scope','uncertainty','criteria','battery'},'budget policy')
    if type(policy['budget_version']) is not int or policy['budget_version']!=1:raise ValueError('unsupported budget version')
    if policy['research_only'] is not True:raise ValueError('only research-only policies supported')
    if type(policy['feature_contract_version']) is not int or policy['feature_contract_version']!=3 or policy['feature_profile']!='raw_pre_run_v1':raise ValueError('incompatible policy feature contract/profile')
    nonempty(policy['policy_id'],'policy_id')
    scope=policy['scope'];_fields(scope,{'provenance','prediction_mode','model_sha256'},'scope')
    if scope['provenance'] not in ('analytical_simulation','measured'):raise ValueError('unknown requested provenance')
    if scope['prediction_mode']!='pre_run':raise ValueError('unsupported prediction mode')
    _fields(scope['model_sha256'],TARGET_UNITS,'policy model identity')
    for digest in scope['model_sha256'].values():_digest(digest,'model hash')
    u=policy['uncertainty'];_fields(u,{'minimum_family_coverage','allow_unvalidated_research_intervals','allow_assumption_shift'},'uncertainty')
    if type(u['minimum_family_coverage']) not in (int,float) or u['minimum_family_coverage']!=.95:raise ValueError('v1 requires nominal 95% evidence; use explicit research override instead of lowering evidence requirement')
    for key in ('allow_unvalidated_research_intervals','allow_assumption_shift'):boolean(u[key],key)
    criteria=policy['criteria']
    if not isinstance(criteria,list):raise ValueError('criteria must be a list')
    ids=set()
    for item in criteria:
        _fields(item,{'id','kind','target','unit','threshold'},'criterion');nonempty(item['id'],'criterion id')
        if item['id'] in ids or item['id']=='battery':raise ValueError('duplicate/reserved criterion id')
        ids.add(item['id'])
        if not isinstance(item['target'],str) or item['target'] not in TARGET_UNITS:raise ValueError('unsupported criterion target')
        if item['kind'] not in ('absolute_upper','regression_absolute','regression_relative'):raise ValueError('unsupported budget criterion')
        expected='percent' if item['kind']=='regression_relative' else TARGET_UNITS[item['target']]
        if item['unit']!=expected:raise ValueError('criterion unit mismatch')
        _number(item['threshold'],'threshold')
    if policy['battery'] is not None:validate_battery(policy['battery'])
    if not criteria and policy['battery'] is None:raise ValueError('at least one required criterion is necessary')
    return copy.deepcopy(policy)


def policy_from_bytes(content):return validate_policy(_json_from_bytes(content))


def upper_budget(interval,threshold):
    low,high=bounds(interval);checked(threshold,'threshold')
    if high<=threshold:return 'PASS','upper_bound_within_budget'
    if low>threshold:return 'FAIL','lower_bound_exceeds_budget'
    return 'ABSTAIN','interval_crosses_budget'


def regression(candidate,baseline,threshold,*,relative=False):
    c=bounds(candidate);checked(threshold,'regression threshold')
    if baseline is None:return 'ABSTAIN','baseline_missing'
    b=bounds(baseline)
    if relative and b[0]<=0:return 'ABSTAIN','baseline_not_strictly_positive'
    # Compare exact rational values of decoded numerics: avoid rounding an
    # allowance upwards (e.g.100*1.1) and accidentally accepting an excess.
    factor=1+Fraction(threshold)/100 if relative else None
    lower=Fraction(b[0])*factor if relative else Fraction(b[0])+Fraction(threshold)
    upper=Fraction(b[1])*factor if relative else Fraction(b[1])+Fraction(threshold)
    try:
        checked(float(lower),'allowed lower');checked(float(upper),'allowed upper')
    except OverflowError as error:raise ValueError('regression allowance overflow') from error
    if Fraction(c[1])<=lower:return 'PASS','candidate_upper_within_baseline_lower_allowance'
    if Fraction(c[0])>upper:return 'FAIL','candidate_lower_exceeds_baseline_upper_allowance'
    return 'ABSTAIN','marginal_ranges_inconclusive_not_a_difference_ci'


def aggregate(statuses):
    for status in ('ERROR','FAIL','ABSTAIN','PASS'):
        if status in statuses:return status
    raise ValueError('no decision criteria')
