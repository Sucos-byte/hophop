# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Five state/workload faults before energy integration; analytical_simulation only."""
import copy
from fractions import Fraction
import math
from pathlib import Path
from analytical_reference import (_fields,_number,_integer,_json_bytes,_sha256,validate_model,
                                  validate_workload,integrate_states,_lost)
from analytical_design import configuration_family
from dataset_builder import _json_from_bytes

ENGINE_ID='exclusive-fault-accounting-v1'
KINDS=('none','cpu_busy_poll','tx_power_lock','bursty_retry_storm','beacon_hyper_wakeup','payload_fragmentation_bloat')
PROVENANCE=dict(source_kind='synthetic',execution_kind='simulation',measurement_status='analytical_simulation')
ASSUMPTION_FIELDS={'assumption_version','assumption_id','cpu_increment_ma','lower_tx_current_ma','lower_tx_dbm','upper_tx_dbm',
                   'fragment_header_bytes','burst_period_packets','burst_length_packets','notes'}
ARTIFACT_FIELDS={'fault_artifact_version','engine_id','provenance','snapshots','input_sha256','lineage','baseline','execution','sensitivity'}


class InfeasibleSchedule(ValueError):
    """A valid fault cannot complete its service inside the reserved slot."""


def parent_id(payload,interval):
    _integer(payload,'payload',minimum=1,maximum=65535);_integer(interval,'interval',minimum=1,maximum=3600000)
    return 'fp-'+_sha256(_json_bytes(dict(payload_size_bytes=payload,interval_ms=interval)))[:32]


def make_intent(payload,interval,window,tx_power_dbm,seed,repetition=1,*,max_attempts=3,offered_packets=None):
    _integer(window,'window',minimum=1,maximum=3600000);_integer(interval,'interval',minimum=1,maximum=3600000)
    if offered_packets is None:offered_packets=window//interval
    identity=dict(payload_size_bytes=payload,interval_ms=interval,window_duration_ms=window,tx_power_dbm=tx_power_dbm,
                  seed=seed,repetition=repetition,max_attempts=max_attempts,offered_packets=offered_packets)
    return dict(workload_version=1,run_id='fi-'+_sha256(_json_bytes(identity))[:32],evaluation_group_id=parent_id(payload,interval),**identity)


def validate_assumptions(a,model):
    _fields(a,ASSUMPTION_FIELDS,'fault assumptions')
    if type(a['assumption_version']) is not int or a['assumption_version']!=1 or a['assumption_id']!='fault-assumptions-v1':raise ValueError('unsupported fault assumptions')
    for key in ('cpu_increment_ma','lower_tx_current_ma'):
        p=a[key];_fields(p,{'value','min','max','unit','basis'},key)
        for name in ('value','min','max'):_number(p[name],key+'.'+name)
        if p['unit']!='mA' or p['basis']!='assumption' or not p['min']<=p['value']<=p['max']:raise ValueError('invalid assumption range/unit')
    _integer(a['lower_tx_dbm'],'lower_tx_dbm',minimum=-100,maximum=100);_integer(a['upper_tx_dbm'],'upper_tx_dbm',minimum=-100,maximum=100)
    if not a['lower_tx_dbm']<a['upper_tx_dbm'] or a['upper_tx_dbm']!=model['conditions']['tx_power_dbm']:raise ValueError('fault TX scope mismatch')
    if a['lower_tx_current_ma']['max']>model['currents_ma']['tx']['value']:raise ValueError('lower-power assumption exceeds reference TX current')
    _integer(a['fragment_header_bytes'],'fragment_header_bytes',maximum=256)
    _integer(a['burst_period_packets'],'burst_period_packets',minimum=1,maximum=10000)
    _integer(a['burst_length_packets'],'burst_length_packets',minimum=1,maximum=a['burst_period_packets'])
    if not isinstance(a['notes'],list) or any(not isinstance(s,str) or not s for s in a['notes']):raise ValueError('assumption notes required')
    return copy.deepcopy(a)


def validate_intent(intent,model,a):
    proxy=copy.deepcopy(intent);proxy['tx_power_dbm']=model['conditions']['tx_power_dbm']
    validate_workload(proxy,model=model)
    _integer(intent['tx_power_dbm'],'requested TX',minimum=a['lower_tx_dbm'],maximum=a['upper_tx_dbm'])
    if intent!=make_intent(intent['payload_size_bytes'],intent['interval_ms'],intent['window_duration_ms'],intent['tx_power_dbm'],intent['seed'],intent['repetition'],max_attempts=intent['max_attempts'],offered_packets=intent['offered_packets']):raise ValueError('intended run/parent identity mismatch')
    return copy.deepcopy(intent)


def validate_fault(fault,intent,a):
    _fields(fault,{'kind','severity'},'fault')
    if not isinstance(fault['kind'],str) or fault['kind'] not in KINDS:raise ValueError('unknown fault mechanism')
    limits=dict(none=0,cpu_busy_poll=1000,tx_power_lock=a['upper_tx_dbm']-intent['tx_power_dbm'],bursty_retry_storm=64,
                beacon_hyper_wakeup=1000,payload_fragmentation_bloat=min(255,intent['payload_size_bytes']-1))
    _integer(fault['severity'],'fault severity',maximum=limits[fault['kind']])
    return copy.deepcopy(fault)


def tx_current(model,a,power):
    if power==a['upper_tx_dbm']:return model['currents_ma']['tx']['value']
    low=a['lower_tx_current_ma']['value'];high=model['currents_ma']['tx']['value']
    return low+(high-low)*(power-a['lower_tx_dbm'])/(a['upper_tx_dbm']-a['lower_tx_dbm'])


def simulate_fault(model,intent,assumptions,fault):
    model=validate_model(model);a=validate_assumptions(assumptions,model);run=validate_intent(intent,model,a);fault=validate_fault(fault,run,a)
    kind=fault['kind'];severity=fault['severity'];t={k:p['value'] for k,p in model['timing_us'].items()}
    fragments=1+severity if kind=='payload_fragmentation_bloat' else 1
    extra=severity if kind=='bursty_retry_storm' else 0
    wakes=severity if kind=='beacon_hyper_wakeup' else 0
    power=run['tx_power_dbm']+(severity if kind=='tx_power_lock' else 0)
    horizon=run['window_duration_ms']*1000;slot_us=run['interval_ms']*1000;slots=horizon//slot_us
    if slots>100000:raise ValueError('fault slot enumeration exceeds100000 resource limit')
    if slots*wakes+run['offered_packets']*fragments*(run['max_attempts']+extra)>100000:raise ValueError('fault exceeds100000-service resource limit')
    currents=dict(idle=model['currents_ma']['idle']['value'],tx=tx_current(model,a,power),rx=model['currents_ma']['rx']['value'],
                  cpu_busy=model['currents_ma']['idle']['value']+a['cpu_increment_ma']['value'])
    for value in currents.values():_number(value,'state current')
    segments=[];packets=[];cursor=0;attempts=0;beacons=[];burst_packets=[]
    def add(state,duration,phase,deadline,packet=None,fragment=None,attempt=None):
        nonlocal cursor
        _integer(duration,'segment duration')
        if cursor+duration>deadline:raise InfeasibleSchedule(f'{phase} service exceeds reserved slot at{cursor}+{duration}>{deadline}us')
        if duration:
            segments.append(dict(state=state,phase=phase,start_us=cursor,duration_us=duration,packet_index=packet,fragment_index=fragment,attempt_index=attempt))
            cursor+=duration
    for slot in range(slots):
        deadline=(slot+1)*slot_us
        for wake in range(wakes):
            start=cursor;add('idle',t['prepare'],'beacon_prepare',deadline);add('rx',t['rx'],'beacon_listen',deadline)
            beacons.append(dict(slot=slot,index=wake,start_us=start,end_us=cursor,logical_data_delivery=False))
        if slot<run['offered_packets']:
            packet=slot;fragment_reports=[]
            in_burst=extra>0 and (packet+run['seed']%a['burst_period_packets'])%a['burst_period_packets']<a['burst_length_packets']
            forced=extra if in_burst else 0
            if in_burst:burst_packets.append(packet)
            quotient,remainder=divmod(run['payload_size_bytes'],fragments)
            for fragment in range(fragments):
                payload=quotient+(fragment<remainder);header=a['fragment_header_bytes'] if fragments>1 else 0;wire_bytes=payload+header
                tx_us=t['tx_base']+t['tx_per_byte']*wire_bytes
                history=[];delivered=False
                seed=run['seed'] if fragment==0 else int(_sha256(f'fault-fragment-v1:{run["seed"]}:{fragment}'.encode())[:16],16)
                for attempt in range(run['max_attempts']+forced):
                    start=cursor
                    add('idle',t['prepare'],'prepare',deadline,packet,fragment,attempt)
                    add('tx',tx_us,'transmit',deadline,packet,fragment,attempt)
                    add('rx',t['rx'],'ack_wait',deadline,packet,fragment,attempt);attempts+=1
                    forced_loss=attempt<forced
                    lost=forced_loss or _lost(seed,packet,attempt-forced,model['loss_probability']['value'])
                    history.append(dict(attempt_index=attempt,start_us=start,ack_end_us=cursor,forced_failure=forced_loss,lost=lost))
                    delivered=not lost and cursor<horizon
                    if not lost:break
                    if attempt+1<run['max_attempts']+forced:add('idle',t['backoff'],'retry_backoff',deadline,packet,fragment,attempt)
                fragment_reports.append(dict(fragment_index=fragment,payload_bytes=payload,header_bytes=header,wire_bytes=wire_bytes,
                    delivered=delivered,attempts=history))
            delivered=all(f['delivered'] for f in fragment_reports)
            packets.append(dict(packet_id=_sha256(f'{run["run_id"]}:{packet}'.encode()),packet_index=packet,offered_us=packet*slot_us,
                fragments=fragment_reports,delivered=delivered,accepted_us=cursor if delivered else None))
        add('idle',deadline-cursor,'free_idle',deadline)
    add('idle',horizon-cursor,'window_remainder',horizon)
    # CPU replacement precedes integration; no extra current overlaps a radio state.
    if kind=='cpu_busy_poll' and severity:
        replaced=[]
        for s in segments:
            if s['state']=='idle' and s['phase'] in ('free_idle','window_remainder'):
                busy=s['duration_us']*severity//1000;remaining=s['duration_us']-busy
                if remaining:replaced.append({**s,'duration_us':remaining})
                if busy:replaced.append({**s,'state':'cpu_busy','phase':'busy_poll','start_us':s['start_us']+remaining,'duration_us':busy})
            else:replaced.append(s)
        segments=replaced
    durations=dict.fromkeys(currents,0);end=0
    for s in segments:
        if s['start_us']!=end:raise ValueError('noncontiguous fault state ledger')
        durations[s['state']]+=s['duration_us'];end+=s['duration_us']
    if end!=horizon or sum(durations.values())!=horizon:raise ValueError('fault observation-time conservation failure')
    # Targets are derived ONLY from the completed actual state ledger here.
    energy=integrate_states(durations,currents,voltage_v=model['conditions']['supply_v'])
    delivered=sum(p['delivered'] for p in packets)
    epd=energy['total_energy_mj']*1000/delivered if delivered else None
    if epd is not None:_number(epd,'energy per logical delivered packet')
    return dict(status='COMPLETE',provenance=PROVENANCE,observation_us=horizon,state_duration_us=durations,state_current_ma=currents,
        segments=segments,packets=packets,beacons=beacons,offered_packets=len(packets),delivered_packets=delivered,
        tx_attempts=attempts,rx_operations=attempts+len(beacons),logical_fragments=sum(len(p['fragments']) for p in packets),
        burst_packet_indices=burst_packets,actual_tx_power_dbm=power,requested_tx_power_dbm=run['tx_power_dbm'],
        actual_attempt_cap_on_burst=run['max_attempts']+extra,fragment_count=fragments,extra_wakeups_per_slot=wakes,
        energy_per_delivered_packet_uj=epd,ping_rtt_latency_ms=None,**energy)


def execution_or_infeasible(model,intent,a,fault):
    try:return simulate_fault(model,intent,a,fault)
    except InfeasibleSchedule as error:
        return dict(status='INFEASIBLE',provenance=PROVENANCE,reason_code='reserved_slot_exceeded',detail=str(error),
            total_energy_mj=None,mean_power_mw=None,energy_per_delivered_packet_uj=None)


def build_artifact(parameters_bytes,intent_bytes,assumptions_bytes,fault_bytes,*,include_sensitivity=True):
    if type(include_sensitivity) is not bool:raise ValueError('sensitivity flag must be boolean')
    sources=dict(parameters=parameters_bytes,intended_workload=intent_bytes,assumptions=assumptions_bytes,fault=fault_bytes)
    if any(not isinstance(v,bytes) for v in sources.values()):raise ValueError('immutable source snapshots required')
    model=validate_model(_json_from_bytes(parameters_bytes));a=validate_assumptions(_json_from_bytes(assumptions_bytes),model)
    intent=validate_intent(_json_from_bytes(intent_bytes),model,a);fault=validate_fault(_json_from_bytes(fault_bytes),intent,a)
    baseline=simulate_fault(model,intent,a,dict(kind='none',severity=0));execution=execution_or_infeasible(model,intent,a,fault)
    hashes={name:_sha256(data) for name,data in sources.items()}
    baseline_id='fb-'+_sha256(_json_bytes({k:v for k,v in hashes.items() if k!='fault'}))[:32]
    lineage=dict(parent_id=parent_id(intent['payload_size_bytes'],intent['interval_ms']),family_id=configuration_family(intent),
        evaluation_group_id=intent['evaluation_group_id'],baseline_id=baseline_id,child_id='fc-'+_sha256(_json_bytes(dict(engine_id=ENGINE_ID,inputs=hashes)))[:32],
        intended_run_id=intent['run_id'],seed=intent['seed'],repetition=intent['repetition'])
    sensitivity=[]
    if include_sensitivity:
        for parameter in ('cpu_increment_ma','lower_tx_current_ma'):
            for bound in ('min','max'):
                varied=copy.deepcopy(a);varied[parameter]['value']=varied[parameter][bound]
                b=simulate_fault(model,intent,varied,dict(kind='none',severity=0));f=execution_or_infeasible(model,intent,varied,fault)
                sensitivity.append(dict(parameter=parameter,bound=bound,value=varied[parameter]['value'],unit='mA',basis='assumption',
                    baseline_energy_mj=b['total_energy_mj'],fault_energy_mj=f['total_energy_mj'],status=f['status']))
    return dict(fault_artifact_version=1,engine_id=ENGINE_ID,provenance=PROVENANCE,
        snapshots={name:data.decode('utf-8') for name,data in sources.items()},input_sha256=hashes,lineage=lineage,
        baseline=baseline,execution=execution,sensitivity=sensitivity)


def artifact_from_bytes(content):
    artifact=_json_from_bytes(content);_fields(artifact,ARTIFACT_FIELDS,'fault artifact')
    if type(artifact['fault_artifact_version']) is not int or artifact['fault_artifact_version']!=1 or artifact['engine_id']!=ENGINE_ID or artifact['provenance']!=PROVENANCE:raise ValueError('incompatible fault artifact contract/provenance')
    _fields(artifact['snapshots'],{'parameters','intended_workload','assumptions','fault'},'source snapshots')
    if any(not isinstance(v,str) for v in artifact['snapshots'].values()):raise ValueError('source snapshots must be UTF8 text')
    sensitivity=artifact['sensitivity']
    if not isinstance(sensitivity,list) or len(sensitivity) not in (0,4):raise ValueError('invalid sensitivity coverage')
    replay=build_artifact(*(artifact['snapshots'][k].encode() for k in ('parameters','intended_workload','assumptions','fault')),include_sensitivity=bool(sensitivity))
    if _json_bytes(artifact)!=_json_bytes(replay):raise ValueError('fault artifact source/hash/state/lineage replay mismatch')
    return artifact


def oracle_violation(baseline,fault,limit_percent):
    _number(limit_percent,'research energy budget percent')
    _number(baseline,'baseline energy')
    if fault is not None:_number(fault,'fault energy')
    if baseline==0 or fault is None:return None
    return Fraction(fault)>Fraction(baseline)*(1+Fraction(limit_percent)/100)
