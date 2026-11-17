# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Regression cases found by reviewing Week 5 against its approved plan."""

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataset_builder import DATASET_FIELDS, DATASET_FIELDS_V2
from dataset_table import build_dataset_table, load_dataset_artifact
from feature_contract import PRE_RUN_FEATURES, POST_RUN_FEATURES, extract_features
from green_ops_build_dataset import _dataset_csv, _manifest_v2
from tools.green_ops.tests.test_dataset_table import artifact
from tools.green_ops.tests import test_dataset_v2 as dataset_v2_tests


class PredictionContextReviewTests(unittest.TestCase):
    def configured_row(self):
        row = artifact()["row"]
        row.update(payload_size_bytes=32, interval_ms=1000, tx_power_dbm=0)
        return row

    def test_manifest_does_not_infer_capabilities_from_nonnull_columns(self):
        row = self.configured_row()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"; source.write_text("fixture")
            manifest = json.loads(_manifest_v2(row, {"source": source}, {}))
        self.assertEqual(manifest["available_fields"], [])
        self.assertIsNone(manifest["selected_features"]["pre_run"])

    def test_v2_pre_run_requires_completed_planned_duration_context(self):
        row = self.configured_row()
        with self.assertRaisesRegex(ValueError, "prediction context"):
            extract_features(row, prediction_mode="pre_run", available_fields=frozenset(PRE_RUN_FEATURES))

    def test_explicit_context_rejects_early_termination_and_allows_post_run(self):
        row = self.configured_row()
        context = dict(planned_window_duration_ms=2000.0, completed_as_planned=False)
        with self.assertRaisesRegex(ValueError, "completed|duration"):
            extract_features(row, prediction_mode="pre_run", available_fields=frozenset(PRE_RUN_FEATURES), prediction_context=context)
        context.update(planned_window_duration_ms=1000.0, completed_as_planned=True)
        features = extract_features(row, prediction_mode="pre_run", available_fields=frozenset(PRE_RUN_FEATURES), prediction_context=context)
        self.assertEqual(tuple(features), PRE_RUN_FEATURES)
        self.assertFalse(set(features) & {"seed", "evaluation_group_id", "target_total_energy_mj"})
        context["planned_window_duration_ms"] = 2000.0
        with self.assertRaisesRegex(ValueError, "duration"):
            extract_features(row, prediction_mode="pre_run", available_fields=frozenset(PRE_RUN_FEATURES), prediction_context=context)


class DeliveryReferenceReviewTests(unittest.TestCase):
    def test_measured_delivery_label_requires_delivery_summary_reference(self):
        setup = dataset_v2_tests.DatasetV2Tests(); setup.setUp()
        row = setup.build(delivery_summary=setup.delivery)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"fixture"; path.write_text("simulated evidence")
            manifest = json.loads(_manifest_v2(row, {name: path for name in
                ("ppk2_summary", "measurement_window", "run_metadata", "telemetry_csv")},
                dict(duration_tolerance_ms=1.0, duration_tolerance_fraction=0.001, max_alignment_uncertainty_ms=1.0)))
        a = dict(row=row, manifest=manifest, csv_sha256=manifest["dataset_sha256"], manifest_sha256="a"*64)
        with self.assertRaisesRegex(ValueError, "delivery_summary"):
            build_dataset_table([a], schema_version=2, measurement_status="measured")
        manifest["input_paths"]["delivery_summary"] = "archived-delivery.json"
        manifest["input_sha256"]["delivery_summary"] = "b"*64
        rows, _ = build_dataset_table([a], schema_version=2, measurement_status="measured")
        self.assertEqual(rows[0]["target_energy_per_delivered_packet_uj"], 6250)


class ArtifactSnapshotReviewTests(unittest.TestCase):
    def test_loader_hashes_the_bytes_it_parsed(self):
        a = artifact()
        with tempfile.TemporaryDirectory() as directory:
            source, manifest_path = Path(directory)/"row.csv", Path(directory)/"manifest.json"
            source.write_text(_dataset_csv(a["row"]), encoding="utf-8")
            expected_manifest = json.dumps(a["manifest"]).encode()
            manifest_path.write_bytes(expected_manifest)
            # Replacing the manifest after parsing must not relabel the digest
            # of the already validated snapshot with unrelated later bytes.
            from dataset_table import _validate_manifest
            def replace_after_validation(row, manifest):
                validated = _validate_manifest(row, manifest)
                manifest_path.write_text('{"changed": true}')
                return validated
            with mock.patch("dataset_table._validate_manifest", side_effect=replace_after_validation):
                loaded = load_dataset_artifact(source, manifest_path)
            self.assertEqual(loaded["manifest_sha256"], hashlib.sha256(expected_manifest).hexdigest())


class EvidenceBoundaryReviewTests(unittest.TestCase):
    def test_hardware_rtt_hash_alone_is_not_validated_correlated_evidence(self):
        setup = dataset_v2_tests.DatasetV2Tests(); setup.setUp()
        row = setup.build(); row["ping_rtt_latency_ms"] = 12.0
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"fixture"; path.write_text("simulated evidence")
            manifest = json.loads(_manifest_v2(row, {name: path for name in
                ("ppk2_summary", "measurement_window", "run_metadata", "telemetry_csv", "rtt_evidence")},
                dict(duration_tolerance_ms=1.0, duration_tolerance_fraction=0.001, max_alignment_uncertainty_ms=1.0)))
        a = dict(row=row, manifest=manifest, csv_sha256=manifest["dataset_sha256"], manifest_sha256="a"*64)
        with self.assertRaisesRegex(ValueError, "RTT"):
            build_dataset_table([a], schema_version=2, measurement_status="measured")

    def test_radio_boundaries_include_snapshots_but_not_outside_counters(self):
        setup = dataset_v2_tests.DatasetV2Tests(); setup.setUp()
        # Endpoint snapshots bound the half-open interval's cumulative delta.
        start = copy.deepcopy(setup.rows[0])
        start.update({k: str(v) for k, v in setup.window["start_counters"].items()})
        setup.rows.insert(0, start)
        self.assertEqual(setup.build()["rx_operations"], 5)
        setup.rows[0]["tx_successes"] = "2"  # baseline is 3
        with self.assertRaisesRegex(ValueError, "endpoints"):
            setup.build()

    def test_valid_integer_numeric_targets_survive_csv_roundtrip(self):
        a = artifact(status="analytical_simulation")
        # Finite exact integers are allowed numeric targets. Parsing every
        # numeric column as float must not change the delivery calculation.
        energy = 2**53 + 1
        a["row"].update(target_mean_power_mw=energy, target_total_energy_mj=energy,
                        offered_packets=7, delivered_packets=7, delivery_status="validated",
                        packet_delivery_ratio=1.0, target_energy_per_delivered_packet_uj=energy*1000/7)
        a["manifest"]["input_paths"]["delivery_summary"] = "test-delivery.json"
        a["manifest"]["input_sha256"]["delivery_summary"] = "d"*64
        with tempfile.TemporaryDirectory() as directory:
            source, manifest_path = Path(directory)/"row.csv", Path(directory)/"manifest.json"
            source.write_text(_dataset_csv(a["row"]), encoding="utf-8")
            a["manifest"]["dataset_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(a["manifest"]), encoding="utf-8")
            loaded = load_dataset_artifact(source, manifest_path)
            self.assertEqual(loaded["row"]["target_total_energy_mj"], energy)


class FeaturePartitionReviewTests(unittest.TestCase):
    def test_v2_rejects_overlap_duplicate_and_unclassified_fields(self):
        import feature_contract as contract
        for fields in (DATASET_FIELDS_V2 + ("new_field",), DATASET_FIELDS_V2 + ("run_id",), DATASET_FIELDS_V2[:-1]):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                contract.validate_feature_partition(fields, schema_version=2)
        with mock.patch.object(contract, "TARGET_COLUMNS", contract.TARGET_COLUMNS | {"run_id"}):
            with self.assertRaisesRegex(ValueError, "overlap"):
                contract.validate_feature_partition(DATASET_FIELDS_V2, schema_version=2)

    def test_frozen_v1_header_and_new_v2_order(self):
        expected_v1 = (
            "dataset_version", "run_id", "adapter", "feature_profile_id", "source_kind",
            "execution_kind", "measurement_status", "payload_size_bytes", "interval_ms",
            "tx_power_dbm", "loss_model", "loss_preset", "loss_initial_state",
            "good_to_bad_probability", "bad_to_good_probability", "good_state_loss_probability",
            "bad_state_loss_probability", "seed", "repetition", "segment_count", "rx_attempts",
            "delivered_packets", "sync_beacons", "tx_successes", "packet_delivery_ratio",
            "ping_rtt_latency_ms", "target_mean_power_mw", "target_total_energy_mj",
            "target_energy_per_delivered_packet_uj",
        )
        self.assertEqual(DATASET_FIELDS, expected_v1)
        renames = dict(rx_attempts="rx_operations", delivered_packets="rx_decoded_packets",
                       packet_delivery_ratio="rx_decode_per_operation_ratio")
        self.assertEqual(DATASET_FIELDS_V2, tuple(renames.get(f, f) for f in expected_v1) + (
            "window_duration_ms", "offered_packets", "delivery_status", "evaluation_group_id",
            "analytical_model_id", "delivered_packets", "packet_delivery_ratio"))

    def test_early_terminated_context_retains_post_run_diagnostics(self):
        from feature_contract import describe_prediction_context
        setup = dataset_v2_tests.DatasetV2Tests(); setup.setUp()
        row = setup.build(delivery_summary=setup.delivery)
        row.update(payload_size_bytes=32, interval_ms=1000, tx_power_dbm=0)
        context = dict(available_fields=list(POST_RUN_FEATURES), planned_window_duration_ms=2000.0,
                       completed_as_planned=False)
        original = copy.deepcopy(context)
        available, selected, _ = describe_prediction_context(row, context)
        self.assertIsNone(selected["pre_run"])
        self.assertEqual(selected["post_run"], list(POST_RUN_FEATURES))
        self.assertEqual(context, original)
        for bad in ({**context, "available_fields": ["target_total_energy_mj"]},
                    {**context, "completed_as_planned": 1},
                    {**context, "planned_window_duration_ms": True}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                describe_prediction_context(row, bad)


class DatasetSnapshotReviewTests(unittest.TestCase):
    def test_cli_hashes_the_snapshot_used_to_build_the_row(self):
        import contextlib
        import csv
        import io
        import green_ops_build_dataset as cli
        from converter import CSV_FIELDS
        setup = dataset_v2_tests.DatasetV2Tests(); setup.setUp()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in (("metadata", setup.metadata), ("window", setup.window), ("energy", setup.energy)):
                (root/name).write_text(json.dumps(value), encoding="utf-8")
            metadata_bytes = (root/"metadata").read_bytes()
            from tools.green_ops.tests.test_dataset_builder import experiment_plan
            plan = experiment_plan(execution_kind="hardware")
            plan["experiments"][0]["run_id"] = "run-001"
            (root/"plan").write_text(json.dumps(plan), encoding="utf-8")
            context = dict(available_fields=list(PRE_RUN_FEATURES),
                           planned_window_duration_ms=1000.0, completed_as_planned=True)
            (root/"context").write_text(json.dumps(context), encoding="utf-8")
            with (root/"events").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS); writer.writeheader(); writer.writerows(setup.rows)
            args = ["dataset", "--dataset-version", "2", "--telemetry-csv", str(root/"events"),
                    "--run-metadata", str(root/"metadata"), "--measurement-window", str(root/"window"),
                    "--ppk2-summary", str(root/"energy"), "--dataset-output", str(root/"out.csv"),
                    "--manifest-output", str(root/"out.json"), "--experiment-plan", str(root/"plan"),
                    "--prediction-context", str(root/"context")]
            real_build = cli._build_dataset_row_v2_from_bytes
            def change_file_after_reading(sources, **policies):
                row = real_build(sources, **policies)
                (root/"metadata").write_text('{"changed":true}')
                return row
            with mock.patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()), mock.patch.object(cli, "_build_dataset_row_v2_from_bytes", side_effect=change_file_after_reading):
                self.assertEqual(cli.main(), 0)
            manifest = json.loads((root/"out.json").read_text())
            self.assertEqual(manifest["input_sha256"]["run_metadata"], hashlib.sha256(metadata_bytes).hexdigest())
            self.assertEqual(manifest["selected_features"]["pre_run"], list(PRE_RUN_FEATURES))
            self.assertEqual(manifest["input_sha256"]["prediction_context"],
                             hashlib.sha256((root/"context").read_bytes()).hexdigest())
            # Invalid explicit declarations fail with no final outputs.
            (root/"metadata").write_bytes(metadata_bytes)
            (root/"context").write_text(json.dumps({**context, "completed_as_planned": 1}))
            invalid_args = [arg.replace("out.csv", "invalid.csv").replace("out.json", "invalid.json") for arg in args]
            with mock.patch.object(sys, "argv", invalid_args), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(), 1)
            self.assertFalse((root/"invalid.csv").exists())
            self.assertFalse((root/"invalid.json").exists())


class ManifestPolicyReviewTests(unittest.TestCase):
    def test_invalid_policies_fail_even_for_excluded_unmeasured_sources(self):
        a = artifact()
        for policy in ({"unknown": 0}, dict(duration_tolerance_ms=True,
                       duration_tolerance_fraction=0.001, max_alignment_uncertainty_ms=1.0),
                       dict(duration_tolerance_ms=1.0, duration_tolerance_fraction=1.01,
                            max_alignment_uncertainty_ms=1.0)):
            a["manifest"]["policies"] = policy
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                build_dataset_table([a], schema_version=2, measurement_status="analytical_simulation")


class Ppk2IntegrationReviewTests(unittest.TestCase):
    def test_serial_duration_boundary_and_alignment_rejection_through_builder(self):
        setup = dataset_v2_tests.DatasetV2Tests(); setup.setUp()
        setup.window["alignment"]["method"] = "serial"
        setup.window["alignment"]["uncertainty_ms"] = 1.0
        setup.energy.update(window_duration_ms=1001.0, target_total_energy_mj=12.5125)
        self.assertEqual(setup.build()["target_total_energy_mj"], 12.5125)
        for field, value in (("window_duration_ms", 1001.01),
                             ("alignment_reference_sha256", "e"*64),
                             ("target_total_energy_mj", 15.0)):
            original = setup.energy.copy(); setup.energy[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                setup.build()
            setup.energy = original
        setup.window["alignment"]["uncertainty_ms"] = 1.001
        with self.assertRaisesRegex(ValueError, "uncertainty"):
            setup.build()


class CsvSyntaxReviewTests(unittest.TestCase):
    def test_unterminated_quoted_empty_cell_is_not_a_valid_artifact(self):
        a = artifact()
        with tempfile.TemporaryDirectory() as directory:
            source, manifest_path = Path(directory)/"row.csv", Path(directory)/"manifest.json"
            text = _dataset_csv(a["row"])
            self.assertTrue(text.endswith(",\n"))
            source.write_text(text[:-1] + '"', encoding="utf-8")
            a["manifest"]["dataset_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(a["manifest"]), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_dataset_artifact(source, manifest_path)
