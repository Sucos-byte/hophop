# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Read-only display adapters for explicit, pinned historical artifact snapshots."""
import hashlib
import math
import os
from pathlib import Path
import re
import stat
from dataset_builder import _json_from_bytes
from green_ops_report import validate_decision

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).with_name('dashboard_assets')
UNITS = {'target_mean_power_mw':'mW','target_total_energy_mj':'mJ',
         'target_energy_per_delivered_packet_uj':'uJ'}
FEATURES = ['payload_size_bytes','interval_ms','tx_power_dbm','window_duration_ms']
EXITS = {'PASS':0,'ERROR':1,'FAIL':2,'ABSTAIN':3}
KINDS = {'none','cpu_busy_poll','tx_power_lock','bursty_retry_storm','beacon_hyper_wakeup','payload_fragmentation_bloat'}


def digest(raw):return hashlib.sha256(raw).hexdigest()


def safe_read(root, relative, limit=12*1024*1024):
    """Walk only explicit catalog paths with no symlinks, including parent dirs."""
    parts=Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(p in ('.','..') for p in parts):
        raise ValueError('unsafe resource path')
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in parts[:-1]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd);fd=child
        file=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        with os.fdopen(file,'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ValueError('resource must be a regular file')
            raw=stream.read(limit+1)
        if len(raw)>limit:raise ValueError('resource exceeds size limit')
        return raw
    finally:os.close(fd)


def require(condition, message):
    if not condition:raise ValueError(message)


def finite(value, nullable=False):
    require((nullable and value is None) or (type(value) in (int,float) and math.isfinite(value)), 'nonfinite or nonnumeric value')


def version(data, field):require(type(data.get(field)) is int and data[field]==1, f'incompatible {field}')


def provenance(data):require(data.get('provenance')=='analytical_simulation','unsupported provenance; not a measured artifact')


def prediction_adapter(evaluation, predictions, study):
    """Different Week7/8 schemas are never conflated or filled with demo values."""
    version(evaluation,'evaluation_version');version(predictions,'predictions_version')
    provenance(evaluation);provenance(predictions)
    require(evaluation['refit_or_tuning_performed'] is False,'unexpected refitting')
    rows=predictions['rows'];require(isinstance(rows,list),'missing prediction rows')
    require(evaluation['recipe_sha256']==predictions.get('recipe_sha256',evaluation['recipe_sha256']),'recipe mismatch')
    if study=='week7':
        require(evaluation['contracts']['feature_contract_version']==3,'feature contract mismatch')
        require(evaluation['feature_order']==FEATURES,'unexpected feature order')
        require(evaluation['selection_sha256']==predictions['selection_sha256'],'selection mismatch')
        panels=evaluation['partitions'];metrics=[]
        for panel,targets in panels.items():
            for target,models in targets.items():
                require(target in UNITS,'unknown target')
                for role,score in models.items():
                    if role=='chosen_minus_baseline':continue
                    require(role in ('baseline','chosen'),'unknown model role')
                    require(score['unit']==UNITS[target],'metric units mismatch')
                    for name in ('mae','rmse','r2'):finite(score[name],nullable=name=='r2')
                    metrics.append(dict(study=study,panel=panel,target=target,model=role,**score))
        for r in rows:
            require(set(r)=={'group_id','model_role','partition','prediction','provenance','run_id','target','truth'},'Week7 row fields mismatch')
        normalized=[dict(r,study=study,panel=r['partition'],model=r['model_role'],unit=UNITS[r['target']],lower=None,upper=None,assumption_shift=r['partition']!='test') for r in rows]
    else:
        require(evaluation['feature_contract_version']==3,'feature contract mismatch')
        require(evaluation['calibration_set_sha256']==predictions['calibration_set_sha256'],'calibration mismatch')
        require(evaluation['dataset_sha256']==predictions['dataset_sha256'],'dataset mismatch')
        metrics=[]
        for panel,targets in evaluation['panels'].items():
            for target,score in targets.items():
                require(target in UNITS and score['unit']==UNITS[target],'metric units mismatch')
                for name in ('mae','rmse','r2'):finite(score['point_metrics'][name],nullable=name=='r2')
                c=score['coverage']
                for name in ('row_coverage','family_coverage','mean_width'):finite(c[name])
                require(0<=c['row_coverage']<=1 and 0<=c['family_coverage']<=1,'invalid coverage')
                metrics.append(dict(study=study,panel=panel,target=target,model='chosen',unit=score['unit'],**score['point_metrics'],coverage=c,nominal_coverage=evaluation['nominal_coverage'],coverage_unit=evaluation['coverage_unit']))
        normalized=[]
        for r in rows:
            require(set(r)=={'assumption_shift','coverage_unit','group_id','lower','nominal_coverage','panel','prediction','provenance','run_id','target','truth','unit','upper'},'Week8 row fields mismatch')
            require(r['unit']==UNITS[r['target']],'prediction units mismatch')
            finite(r['lower']);finite(r['upper']);require(r['lower']<=r['prediction']<=r['upper'],'invalid interval')
            normalized.append(dict(r,study=study,model='chosen'))
    identities=set()
    for r in normalized:
        provenance(r);finite(r['truth'],nullable=True);finite(r['prediction'])
        require(isinstance(r['run_id'],str) and isinstance(r['group_id'],str),'invalid identity')
        require(r['model'] in ('baseline','chosen'),'invalid model role')
        require(r['panel'] in evaluation.get('partitions',evaluation.get('panels',{})),'unknown panel')
        identity=(r['panel'],r['target'],r['model'],r['run_id'])
        require(identity not in identities,'duplicate prediction');identities.add(identity)
        r['error']=r['prediction']-r['truth'] if r['truth'] is not None else None
        r['absolute_error']=abs(r['error']) if r['error'] is not None else None
    for m in metrics:
        subset=[r for r in normalized if (r['panel'],r['target'],r['model'])==(m['panel'],m['target'],m['model'])]
        labeled=[r for r in subset if r['truth'] is not None]
        require(len(labeled)==m['sample_count'],'metric sample count mismatch')
        if 'coverage' in m:
            c=m['coverage'];groups={r['group_id'] for r in labeled}
            covered=lambda r:r['lower']<=r['truth']<=r['upper']
            require(c['labeled_rows']==len(labeled) and c['labeled_families']==len(groups),'coverage denominator mismatch')
            require(math.isclose(c['row_coverage'],sum(covered(r) for r in labeled)/len(labeled)),'row coverage mismatch')
            require(math.isclose(c['family_coverage'],sum(all(covered(r) for r in labeled if r['group_id']==g) for g in groups)/len(groups)),'family coverage mismatch')
    return dict(metrics=metrics,rows=normalized,record_count=len(normalized),unique_runs=len({r['run_id'] for r in normalized}),unique_groups=len({r['group_id'] for r in normalized}),provenance='analytical_simulation')


def fault_adapter(aggregate, rows, manifest, recipe):
    version(aggregate,'aggregation_version');version(manifest,'manifest_version');provenance(aggregate)
    require(aggregate['overall']['case_count']==len(rows),'benchmark count mismatch')
    require(len(rows)==len({r['case_id'] for r in rows}),'duplicate case')
    require(sorted(r['case_id'] for r in rows)==recipe['planned_case_ids'],'frozen case identities mismatch')
    indexed={e['case_id']:e for e in manifest['entries']}
    for r in rows:
        require(r['kind'] in KINDS,'unknown mechanism')
        require(r['parent'] in recipe['parent_splits'][r['split']],'family/split mismatch')
        require(r['status'] in EXITS and r['exit_code']==EXITS[r['status']] and r['blocked']==(r['status']!='PASS'),'status mismatch')
        p=r['predictor'];require(p['feature_order']==FEATURES,'feature profile mismatch')
        require(len(p['baseline_inputs'])==4 and p['baseline_inputs']==p['fault_inputs'],'unexpected intended inputs')
        for v in p['baseline_inputs']:finite(v)
        require(r['window_ms']==p['baseline_inputs'][3],'window mismatch')
        files=indexed[r['case_id']]['files']
        for kind in ('artifact','report'):
            key=f"cases/{r['case_id']}-{kind}.json.gz"
            require(files[key]['raw_sha256']==r[kind+'_sha256'],'manifest reference mismatch')
    allrows=aggregate['overall']
    require(allrows['oracle_violations']==sum(r['oracle_violation'] is True for r in rows),'oracle count mismatch')
    require(allrows['positive_FAIL_detections']==sum(r['positive_detection'] for r in rows),'detection count mismatch')
    for status in EXITS:require(allrows['statuses'][status]==sum(r['status']==status for r in rows),'status count mismatch')
    return dict(aggregate=aggregate,rows=rows,provenance='analytical_simulation')


class ArtifactStore:
    """Snapshot once at startup; restart to inspect changed allowlisted artifacts."""
    def __init__(self, root=ROOT, catalog=None):
        self.root=Path(root)
        self.catalog=catalog if catalog is not None else _json_from_bytes((ASSETS/'catalog.json').read_bytes())
        version(self.catalog,'catalog_version');self.resources=self.catalog['resources']
        self.snapshots={};self.problems={};self.sections={}
        for key,entry in self.resources.items():
            require(re.fullmatch('[a-z0-9-]+',key) is not None,'unsafe resource ID')
            try:
                require(set(entry)=={'path','sha256','kind'},'invalid catalog entry')
                raw=safe_read(self.root,entry['path']);require(digest(raw)==entry['sha256'],'catalog SHA-256 mismatch')
                self.snapshots[key]=raw
            except (OSError,ValueError) as error:self.problems[key]=str(error)
        self.load('overview',self.overview)
        self.load('week7',lambda:self.predictions('week7'))
        self.load('week8',lambda:self.predictions('week8'))
        self.load('faults',self.faults)
        self.load('gates',self.gates)
    def raw(self,key):
        if key not in self.snapshots:raise ValueError(f'{key}: unavailable ({self.problems.get(key,"not allowlisted")})')
        return self.snapshots[key]
    def json(self,key):return _json_from_bytes(self.raw(key))
    def load(self,key,loader):
        try:self.sections[key]=dict(available=True,data=loader())
        except (ValueError,KeyError,TypeError,OverflowError,ZeroDivisionError) as error:
            self.sections[key]=dict(available=False,error=f'Missing or incompatible artifact: {error}')
    def overview(self):
        text=self.raw('project').decode('utf-8')
        evidence=[]
        for line in text.splitlines():
            if line.startswith('| ') and not line.startswith('| Evidence level'):
                cells=[s.strip() for s in line.strip('|').split('|')]
                require(len(cells)==3,'project evidence table changed')
                evidence.append(dict(level=cells[0],delivered=cells[1],limitation=cells[2]))
        require(len(evidence)==4,'project evidence table missing')
        audit=self.raw('audit').decode();require('R16' in audit,'requirements audit unavailable')
        return dict(evidence=evidence,requirements=[line for line in audit.splitlines() if line.startswith('| R')],
            next_backend=self.raw('sprint').decode('utf-8'),provenance='documentation; not experimental measurement')
    def predictions(self,study):
        evaluation=self.json('w7-evaluation' if study=='week7' else 'w8-evaluation')
        predictions=self.json('w7-predictions' if study=='week7' else 'w8-predictions')
        if study=='week7':
            require(digest(self.raw('w7-selection'))==evaluation['selection_sha256'],'selection binding mismatch')
            require(digest(self.raw('w7-recipe'))==evaluation['recipe_sha256'],'recipe binding mismatch')
        else:
            require(digest(self.raw('w8-calibration'))==evaluation['calibration_set_sha256'],'calibration binding mismatch')
            require(digest(self.raw('w8-recipe'))==evaluation['recipe_sha256'],'recipe binding mismatch')
        return prediction_adapter(evaluation,predictions,study)
    def faults(self):
        execution=self.json('w12-execution');version(execution,'execution_version');provenance(execution)
        for key,name in [('w12-aggregate','aggregate.json'),('w12-cases','cases.jsonl'),('w12-manifest','manifest.json')]:
            require(digest(self.raw(key))==execution['outputs_sha256'][name],'execution binding mismatch')
        manifest=self.json('w12-manifest')
        require(digest(self.raw('w12-cases'))==manifest['cases_sha256'],'case manifest mismatch')
        require(digest(self.raw('w12-aggregate'))==manifest['aggregate_sha256'],'aggregate manifest mismatch')
        require(digest(self.raw('w12-recipe'))==execution['recipe_sha256'],'recipe binding mismatch')
        rows=[_json_from_bytes(line) for line in self.raw('w12-cases').splitlines()]
        return fault_adapter(self.json('w12-aggregate'),rows,manifest,self.json('w12-recipe'))
    def gates(self):
        index=self.json('gate-index');reports=[]
        for name,entry in sorted(index['cases'].items()):
            key='gate-'+name.replace('_','-')
            # Catalog IDs use hyphens exclusively; filenames retain their original underscores.
            content=self.raw(key);policy=self.raw('policy-'+name.replace('_','-'))
            require(digest(policy)==entry['policy_sha256'],'gate policy binding mismatch')
            report=validate_decision(content,entry['report_sha256'],policy)
            require(report['status']==entry['status'],'gate index mismatch')
            reports.append(dict(name=name,resource=key,**report))
        return reports
    def summary(self):
        data={}
        for name,section in self.sections.items():
            if not section['available']:data[name]=section;continue
            content=section['data']
            if name in ('week7','week8'):content={k:v for k,v in content.items() if k!='rows'}
            if name=='faults':content={'aggregate':content['aggregate'],'provenance':content['provenance']}
            data[name]=dict(available=True,data=content)
        return dict(snapshot_checkpoint=self.catalog['checkpoint'],sections=data,
            sources={k:dict(**e,available=k in self.snapshots,error=self.problems.get(k)) for k,e in self.resources.items()},
            mode='read_only_saved_artifacts',physical_validation='not_established')
    def page(self,kind,query):
        allowed={'page','limit','split','kind','search'} if kind=='experiments' else {'page','limit','study','panel','target','model','search'}
        require(not set(query)-allowed,'unknown query parameter')
        page=int(query.get('page','1'));limit=int(query.get('limit','20'))
        require(1<=page<=10000 and 1<=limit<=50,'invalid pagination')
        require(all(len(v)<=160 for v in query.values()),'query too long')
        study=query.get('study','week7');section=self.sections['faults' if kind=='experiments' else study] if study in ('week7','week8') else None
        require(section is not None,'unknown study')
        if not section['available']:return dict(available=False,error=section['error'],rows=[],total=0)
        rows=section['data']['rows'];fields=('split','kind') if kind=='experiments' else ('panel','target','model')
        for field in fields:
            value=query.get(field,'')
            if value:rows=[r for r in rows if r[field]==value]
        search=query.get('search','').lower()
        if search:rows=[r for r in rows if search in str(r.get('case_id',r.get('run_id',''))).lower() or search in str(r.get('parent',r.get('group_id',''))).lower()]
        start=(page-1)*limit
        page_rows=[dict(r,seed=str(r['seed'])) if 'seed' in r else r for r in rows[start:start+limit]]
        return dict(available=True,rows=page_rows,total=len(rows),page=page,limit=limit,
                    provenance='analytical_simulation',grouping='related variants/repetitions depend on family/parent')
