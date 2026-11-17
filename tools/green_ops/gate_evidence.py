# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Recompute frozen predictions from replay-verified sources, never trust hand-edited predictions."""
from pathlib import Path
from analytical_reference import _json_bytes,_sha256
from analytical_design import load_design_record
from dataset_builder import _json_from_bytes
from feature_contract import PRE_RUN_FEATURES
from ml_pipeline import predict_record,record_features
from week8_dataset import frozen_models,recipe_from_bytes
from uncertainty import calibration_from_bytes,validate_binding,predict_interval
from explainability import signed_contributions

REFERENCE_HASHES={
 'evaluation.json':'74a86bbeb117b6907afc355e016bbc5aefcea1c81de2d8d0ef34e78d2729329c',
 'explanations.json':'26cdd40938c6d1c316020b0af00490f0e40bc7e898e9766d69b1a51d3ee68759'}
CALIBRATION_SET_SHA256='f686446aa1b6e124cc3c60cc01341953c8ffaa05132a6ab002245cf6276fc5b4'


class FrozenEvidence:
    def __init__(self,model_dir,calibration_dir,original_recipe,study_recipe,reference_dir):
        self.original=Path(original_recipe).read_bytes();self.study=Path(study_recipe).read_bytes();self.recipe=recipe_from_bytes(self.study)
        self.models=frozen_models(model_dir,self.original,self.recipe)
        self.hashes=dict(original_recipe=_sha256(self.original),study_recipe=_sha256(self.study),selection=self.recipe['selection_sha256'])
        reference_dir=Path(reference_dir);self.references={}
        for name,digest in REFERENCE_HASHES.items():
            content=(reference_dir/'evaluation'/name).read_bytes()
            if _sha256(content)!=digest:raise ValueError('Week8 reference evidence hash mismatch')
            self.references[name]=_json_from_bytes(content);self.hashes[name]=digest
        directory=Path(calibration_dir);content=(directory/'calibration-set.json').read_bytes()
        if _sha256(content)!=CALIBRATION_SET_SHA256:raise ValueError('frozen calibration inventory mismatch')
        inventory=_json_from_bytes(content);self.hashes['calibration_set']=_sha256(content);self.calibrations={}
        for target,model in self.models.items():
            content=(directory/f'{target}-calibration.json').read_bytes();digest=_sha256(content)
            if digest!=inventory['files'][f'{target}-calibration.json']:raise ValueError('frozen calibration hash mismatch')
            c=calibration_from_bytes(content);validate_binding(c,model,self.study);self.calibrations[target]=c;self.hashes[target+'-calibration']=digest
            self.hashes[target+'-model']=self.recipe['model_sha256'][target]

    def load(self,directory,*,domain='primary',revision=None):
        record=load_design_record(directory);row=record['row'];manifest=record['manifest']
        if manifest['feature_contract_version']!=3:raise ValueError('source feature-contract mismatch')
        context=manifest['prediction_context'];scope=next(iter(self.models.values()))['scope']
        permitted=[scope['primary_parameters_sha256']] if domain=='primary' else scope['stress_parameters_sha256']
        reason=None
        if record['parameter_sha256'] not in permitted or record['assumption_sha256']!=scope['assumptions_sha256']:reason='unsupported_parameter_or_assumption_scope'
        if (context['completed_as_planned'] is not True or context['planned_window_duration_ms']!=row['window_duration_ms']
            or manifest['selected_features']['pre_run']!=list(PRE_RUN_FEATURES)):reason='prediction_context_or_features_unavailable'
        if record['workload']['max_attempts']!=self.recipe['max_attempts'] or row['offered_packets']!=int(row['window_duration_ms'])//row['interval_ms']:reason='unsupported_workload_offer_or_retry_policy'
        predictions={};influences={}
        for target,model in self.models.items():
            point=None;interval=None;unavailable=reason
            if reason is None:
                point=predict_record(model,record,domain=domain,recipe_bytes=self.original)
                try:
                    estimate=predict_interval(model,record,self.calibrations[target],original_recipe_bytes=self.original,study_recipe_bytes=self.study,domain=domain)
                    interval=[estimate['lower'],estimate['upper']]
                except ValueError as error:
                    if str(error) not in ('interval requires a declared fresh evaluation family','interval schedule mismatch','interval schedule seed/run identity mismatch'):raise
                    unavailable='outside_declared_interval_schedule'
                if target=='target_energy_per_delivered_packet_uj' and row[target] is None:unavailable='delivery_target_undefined_for_source'
                contribution=signed_contributions(model['estimator'],[record_features(record)])[0]
                archived=self.references['explanations.json']['results'][target]['contributions']
                match=next((r for r in archived if r['run_id']==row['run_id']),None)
                if domain=='primary' and match is not None:
                    if any(match[k]!=v for k,v in contribution.items()):raise ValueError('archived attribution/model mismatch')
                    method='compatible_archived_week8_signed_model_contribution'
                else:method='recomputed_frozen_linear_model_contribution'
                influences[target]=dict(unit=model['unit'],method=method,interpretation='model_attribution_not_physical_root_cause',**contribution)
            coverage=self.references['evaluation.json']['panels']['primary'][target]['coverage']['family_coverage']
            predictions[target]=dict(point=point,interval=interval,unit=model['unit'],family_coverage=coverage,unavailable_reason=unavailable)
        comparable={k:record['workload'][k] for k in ('payload_size_bytes','interval_ms','tx_power_dbm','window_duration_ms','offered_packets','max_attempts','seed')}
        comparable.update(parameters_sha256=record['parameter_sha256'],assumptions_sha256=record['assumption_sha256'],adapter=row['adapter'],feature_profile_id=row['feature_profile_id'])
        hashes={**self.hashes,'source_manifest':record['manifest_sha256'],'source_dataset':manifest['dataset_sha256'],
            'parameters':record['parameter_sha256'],'assumptions':record['assumption_sha256']}
        return dict(evidence_version=1,provenance=row['measurement_status'],feature_contract_version=3,feature_profile='raw_pre_run_v1',
            prediction_mode='pre_run',model_sha256=self.recipe['model_sha256'],comparable_workload=comparable,prediction_context=context,
            predictions=predictions,artifact_sha256=hashes,attributions=influences,domain=domain,revision=revision,run_id=row['run_id'])
