# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Explicit load-side energy accounting; engineering projection, no battery assurance."""
import math
from budget_policy import validate_battery,checked,bounds

OMISSIONS=['aging','self_discharge','temperature_and_environment','load_dependent_capacity_and_voltage','battery_replacement_and_transients']


def project_battery(spec,run_power):
    validate_battery(spec)
    energy=spec['capacity_mah']*spec['voltage_v']*spec['usable_fraction']*spec['conversion_efficiency']
    hours_per_year=24*spec['year_days'];checked(energy,'usable energy');checked(hours_per_year,'hours per year')
    if energy<=0 or hours_per_year<=0:raise ValueError('battery arithmetic underflow')
    result=dict(available=False,capacity_mah=spec['capacity_mah'],voltage_v=spec['voltage_v'],usable_fraction=spec['usable_fraction'],
        conversion_efficiency=spec['conversion_efficiency'],load_energy_mwh=energy,year_days=spec['year_days'],hours_per_year=hours_per_year,
        target_years=spec['target_years'],workload_profile=spec['workload_profile'],omitted_effects=OMISSIONS,
        assumptions=['constant nominal voltage/capacity','usable fraction excludes conversion loss','efficiency applied once to energy',
                     'load-side power excludes conversion loss','stationary repeating workload','engineering target, no compliance certification'])
    profile=spec['workload_profile']
    if profile is None:return dict(result,reason_code='battery_workload_profile_missing')
    if profile['kind']=='run_average':
        if run_power is None:return dict(result,reason_code='run_average_power_unavailable')
        point=checked(run_power['point'],'run mean power');interval=run_power['interval']
        basis='candidate_run_average_already_duty_averaged'
    else:
        if not profile['compatible_states_confirmed'] or not profile['complete_cycle']:return dict(result,reason_code='component_state_compatibility_unconfirmed')
        states=profile['states'];point=math.fsum(s['power_mw']*s['time_fraction'] for s in states)
        interval=None if any(s['interval_mw'] is None for s in states) else [math.fsum(s['interval_mw'][i]*s['time_fraction'] for s in states) for i in (0,1)]
        basis='declared_compatible_exclusive_state_assumptions_not_calibrated'
    checked(point,'average power');result.update(mean_power_mw=point,power_basis=basis)
    if point<=0:return dict(result,reason_code='nonpositive_power_no_finite_physical_lifetime')
    lifetime=energy/point/hours_per_year;checked(lifetime,'point years');result['point_years']=lifetime
    if interval is None:return dict(result,reason_code='battery_power_interval_missing')
    low,high=bounds(interval)
    if not low<=point<=high:raise ValueError('power point outside interval')
    if low<=0:return dict(result,reason_code='nonpositive_lower_power_unbounded_lifetime')
    years=[energy/high/hours_per_year,energy/low/hours_per_year]
    for value in years:checked(value,'lifetime bound')
    if min(years)<=0:raise ValueError('lifetime numeric underflow')
    return dict(result,available=True,reason_code='battery_projection_available',lifetime_years=years)


def battery_decision(projection):
    if not projection['available']:return 'ABSTAIN',projection['reason_code']
    low,high=projection['lifetime_years'];target=projection['target_years']
    if low>=target:return 'PASS','lifetime_lower_bound_meets_target'
    if high<target:return 'FAIL','lifetime_upper_bound_below_target'
    return 'ABSTAIN','lifetime_range_crosses_target'
