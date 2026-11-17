# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analytical_design import plan_workload_grid, configuration_family, load_design_record, audit_reference_dataset
from analytical_reference import generate_analytical_artifact, _json_bytes
from feature_contract import PRE_RUN_FEATURES
from tools.green_ops.tests.test_analytical_reference import model, workload, assumed_value

CONTEXT = _json_bytes(dict(available_fields=list(PRE_RUN_FEATURES),planned_window_duration_ms=1000,completed_as_planned=True))


def save_bundle(root, run, data=None, assumptions=b"Uncalibrated analytical assumptions"):
    root.mkdir()
    context = json.loads(CONTEXT);context["planned_window_duration_ms"]=run["window_duration_ms"]
    files = generate_analytical_artifact(_json_bytes(model() if data is None else data),_json_bytes(run),assumptions,
                                         prediction_context_bytes=_json_bytes(context))
    for name,content in files.items():(root/name).write_bytes(content)
    return root


class AnalyticalGridTests(unittest.TestCase):
    def plan(self, **options):
        defaults=dict(payload_sizes_bytes=(32,128),intervals_ms=(50,200),window_durations_ms=(1000,2000),
                      repetitions=2,master_seed=123)
        defaults.update(options)
        return plan_workload_grid(model(),**defaults)

    def test_grid_has_multiple_configurations_and_full_predeclared_workloads(self):
        runs=self.plan()
        self.assertEqual(len(runs),16)
        self.assertEqual(len({run["evaluation_group_id"] for run in runs}),4)
        self.assertEqual(len({run["run_id"] for run in runs}),16)
        for run in runs:
            self.assertEqual(run["offered_packets"],run["window_duration_ms"]//run["interval_ms"])
            self.assertEqual(run["evaluation_group_id"],configuration_family(run))
        self.assertEqual(runs,self.plan(payload_sizes_bytes=(128,32),intervals_ms=(200,50),window_durations_ms=(2000,1000)))

    def test_repetitions_duration_and_parameter_variants_share_family_not_run_id(self):
        original=self.plan();variant=self.plan(variant_id="timing-high")
        def keyed(runs):return {(r["evaluation_group_id"],r["repetition"],r["window_duration_ms"]):r for r in runs}
        for key,run in keyed(original).items():
            other=keyed(variant)[key]
            self.assertEqual(run["seed"],other["seed"])
            self.assertNotEqual(run["run_id"],other["run_id"])
        seed_groups={}
        for run in original:
            seed_groups.setdefault(run["seed"],set()).add(run["evaluation_group_id"])
        self.assertTrue(all(len(groups)==1 for groups in seed_groups.values()))

    def test_invalid_duplicate_and_oversubscribed_grid_levels_fail(self):
        for changes in (dict(payload_sizes_bytes=(True,)),dict(payload_sizes_bytes=(32,32)),
                        dict(intervals_ms=(1,)),dict(repetitions=0),dict(master_seed=True),dict(variant_id="bad/id")):
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.plan(**changes)


class AnalyticalDesignAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)

    def test_ready_primary_panel_has_grouped_repetitions_and_nonconstant_targets(self):
        runs=plan_workload_grid(model(),payload_sizes_bytes=(32,128,512),intervals_ms=(50,200),
            window_durations_ms=(1000,),repetitions=2,master_seed=123)
        paths=[save_bundle(self.root/str(i),run) for i,run in enumerate(runs)]
        report=audit_reference_dataset(paths)
        self.assertEqual(report["row_count"],12)
        self.assertEqual(report["group_count"],6)
        self.assertTrue(report["ready_for_grouped_software_pilot"])
        self.assertEqual(report["feature_distinct_counts"]["payload_size_bytes"],3)
        self.assertEqual(report["feature_distinct_counts"]["tx_power_dbm"],1)
        self.assertEqual(report,audit_reference_dataset(list(reversed(paths))))
        self.assertEqual(report["target_ranges"]["ping_rtt_latency_ms"]["missing_count"],12)

    def test_identical_traffic_families_cannot_escape_groups_by_repetition_or_model_changes(self):
        a=save_bundle(self.root/"a",workload(evaluation_group_id="group-a",offered_packets=10))
        data=model();assumed_value(data["timing_us"]["tx_base"],1500)
        b=save_bundle(self.root/"b",workload(run_id="other",evaluation_group_id="group-b",seed=7,repetition=2,offered_packets=10),data)
        with self.assertRaisesRegex(ValueError,"split across groups"):audit_reference_dataset([a,b])

    def test_shared_seed_across_distinct_groups_is_rejected(self):
        a=save_bundle(self.root/"a",workload(evaluation_group_id="group-a",offered_packets=10))
        b=save_bundle(self.root/"b",workload(run_id="other",evaluation_group_id="group-b",payload_size_bytes=128,offered_packets=10))
        with self.assertRaisesRegex(ValueError,"shared sampler seed"):audit_reference_dataset([a,b])

    def test_duplicate_realization_is_not_an_independent_repetition(self):
        a=save_bundle(self.root/"a",workload())
        b=save_bundle(self.root/"b",workload(run_id="renamed",repetition=2))
        with self.assertRaisesRegex(ValueError,"duplicate analytical realization"):audit_reference_dataset([a,b])

    def test_hidden_offers_retry_limits_and_parameter_variants_block_primary_readiness(self):
        a=save_bundle(self.root/"a",workload(offered_packets=10))
        data=model();assumed_value(data["currents_ma"]["tx"],250)
        b=save_bundle(self.root/"b",workload(run_id="stress",seed=7,max_attempts=2),data)
        report=audit_reference_dataset([a,b],minimum_groups=2)
        self.assertFalse(report["ready_for_grouped_software_pilot"])
        self.assertEqual(len(report["primary_scope_issues"]),3)
        self.assertEqual(report["group_count"],1)  # model variants remain in the same family

    def test_archive_tampering_fails_even_though_csv_and_manifest_still_match(self):
        path=save_bundle(self.root/"a",workload())
        (path/"parameters.json").write_text('{}')
        with self.assertRaisesRegex(ValueError,"source hash mismatch"):load_design_record(path)

    def test_coherent_hashes_do_not_hide_a_row_from_another_workload(self):
        path=save_bundle(self.root/"a",workload())
        # Update archived configuration/workload hashes together, leaving the
        # row/evidence from the original run. The source join/replay must fail.
        run=json.loads((path/"workload.json").read_text());run["offered_packets"]=3
        changed=_json_bytes(run);(path/"workload.json").write_bytes(changed)
        config=json.loads((path/"configuration.json").read_text());config.update(workload=run,workload_sha256=hashlib.sha256(changed).hexdigest())
        config_bytes=_json_bytes(config);(path/"configuration.json").write_bytes(config_bytes)
        manifest=json.loads((path/"manifest.json").read_text())
        manifest["input_sha256"].update(workload=hashlib.sha256(changed).hexdigest(),configuration=hashlib.sha256(config_bytes).hexdigest())
        manifest["analytical_reference"]["configuration_sha256"]=hashlib.sha256(config_bytes).hexdigest()
        (path/"manifest.json").write_bytes(_json_bytes(manifest))
        with self.assertRaisesRegex(ValueError,"source workload|replay"):load_design_record(path)

    def test_sources_cannot_escape_bundle_and_small_demo_is_not_training_evidence(self):
        path=save_bundle(self.root/"a",workload())
        report=audit_reference_dataset([path])
        self.assertFalse(report["ready_for_grouped_software_pilot"])
        manifest=json.loads((path/"manifest.json").read_text());manifest["input_paths"]["parameters"]="../outside.json"
        (path/"manifest.json").write_bytes(_json_bytes(manifest))
        with self.assertRaisesRegex(ValueError,"escapes"):load_design_record(path)

    def test_old_generator_patch_bundle_remains_auditable(self):
        path=save_bundle(self.root/"legacy",workload())
        config=json.loads((path/"configuration.json").read_text());config["generator_version"]="1.0.0"
        config_bytes=_json_bytes(config);(path/"configuration.json").write_bytes(config_bytes)
        report=json.loads((path/"state-accounting.json").read_text());report["generator_version"]="1.0.0"
        report_bytes=_json_bytes(report);(path/"state-accounting.json").write_bytes(report_bytes)
        manifest=json.loads((path/"manifest.json").read_text())
        manifest["input_sha256"].update(configuration=hashlib.sha256(config_bytes).hexdigest(),
                                         state_accounting=hashlib.sha256(report_bytes).hexdigest())
        manifest["analytical_reference"]["configuration_sha256"]=hashlib.sha256(config_bytes).hexdigest()
        (path/"manifest.json").write_bytes(_json_bytes(manifest))
        self.assertEqual(load_design_record(path)["row"]["run_id"],"analytical-001")

    def test_replayed_counts_cannot_be_forged_by_updating_source_hashes(self):
        path=save_bundle(self.root/"forged",workload())
        report=json.loads((path/"state-accounting.json").read_text());report["rx_operations"]+=1
        content=_json_bytes(report);(path/"state-accounting.json").write_bytes(content)
        manifest=json.loads((path/"manifest.json").read_text())
        manifest["input_sha256"]["state_accounting"]=hashlib.sha256(content).hexdigest()
        (path/"manifest.json").write_bytes(_json_bytes(manifest))
        with self.assertRaisesRegex(ValueError,"replay"):load_design_record(path)

    def test_same_pre_run_inputs_do_not_explain_arbitrary_offer_counts(self):
        from feature_contract import extract_features
        a=save_bundle(self.root/"partial",workload(offered_packets=1))
        b=save_bundle(self.root/"full",workload(run_id="full",seed=7,offered_packets=10))
        records=[load_design_record(path) for path in (a,b)]
        features=[extract_features(r["row"],prediction_mode="pre_run",available_fields=frozenset(PRE_RUN_FEATURES),
            prediction_context=dict(planned_window_duration_ms=1000,completed_as_planned=True)) for r in records]
        self.assertEqual(features[0],features[1])
        self.assertNotEqual(records[0]["row"]["target_total_energy_mj"],records[1]["row"]["target_total_energy_mj"])
        report=audit_reference_dataset([a,b],minimum_groups=2)
        self.assertTrue(any("offered count" in reason for reason in report["primary_scope_issues"]))
