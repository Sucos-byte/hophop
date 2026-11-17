# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataset_builder import DATASET_FIELDS_V2, build_dataset_row_v2, build_dataset_row_v2_from_files
from feature_contract import extract_features, feature_roles, validate_feature_partition
from tools.green_ops.tests.test_dataset_builder import event_row, run_metadata
from tools.green_ops.tests.test_ppk2_summary_v2 import aligned_window, valid_summary
from converter import CSV_FIELDS


class DatasetV2Tests(unittest.TestCase):
    def setUp(self):
        self.window = aligned_window()
        self.metadata = run_metadata(execution_kind="hardware", measured_power=True)
        self.metadata["run_id"] = "run-001"
        self.rows = [event_row(run_id="run-001", source_kind="hardware", **self.window["end_counters"])]
        self.energy = valid_summary()
        self.delivery = dict(summary_version=1, run_id="run-001", window_id="window-001",
                             sender_id="sender", receiver_id="receiver", offered_packet_ids=["s-1", "s-2", "s-3"],
                             delivered_packet_ids=["s-2", "s-3"], evidence_sha256="b" * 64)

    def build(self, **options):
        return build_dataset_row_v2(self.metadata, self.rows, measurement_window=self.window,
                                    ppk2_summary=self.energy, **options)

    def test_bounded_deltas_and_delivery_are_distinct(self):
        original = copy.deepcopy((self.metadata, self.rows, self.window, self.delivery))
        row = self.build(delivery_summary=self.delivery)
        self.assertEqual(tuple(row), DATASET_FIELDS_V2)
        self.assertEqual(row["rx_operations"], 5)
        self.assertEqual(row["rx_decoded_packets"], 4)
        self.assertEqual(row["delivered_packets"], 2)
        self.assertEqual(row["packet_delivery_ratio"], 2/3)
        self.assertEqual(row["target_energy_per_delivered_packet_uj"], 6250)
        self.assertIsNone(row["ping_rtt_latency_ms"])
        self.assertEqual(original, (self.metadata, self.rows, self.window, self.delivery))

    def test_without_delivery_denominator_energy_per_delivery_is_null(self):
        row = self.build()
        for field in ("offered_packets", "delivered_packets", "packet_delivery_ratio", "target_energy_per_delivered_packet_uj"):
            self.assertIsNone(row[field])
        self.assertEqual(row["delivery_status"], "unavailable")

    def test_zero_deliveries(self):
        self.delivery["delivered_packet_ids"] = []
        self.assertIsNone(self.build(delivery_summary=self.delivery)["target_energy_per_delivered_packet_uj"])

    def test_invalid_observed_counter_or_segment(self):
        for field, value in (("rx_attempts", 9), ("rx_attempts", 16), ("segment_id", 1)):
            with self.subTest(field=field, value=value):
                rows = copy.deepcopy(self.rows)
                rows[0][field] = str(value)
                with self.assertRaises(ValueError):
                    build_dataset_row_v2(self.metadata, rows, measurement_window=self.window, ppk2_summary=self.energy)

    def test_decreasing_observations(self):
        earlier = copy.deepcopy(self.rows[0]); earlier["rx_attempts"] = "14"
        self.rows.append(earlier)
        with self.assertRaisesRegex(ValueError, "decreasing"):
            self.build()

    def test_v1_energy_is_rejected_with_migration_message(self):
        self.energy = {k: v for k, v in self.energy.items() if k in {"summary_version", "run_id", "instrument", "target_mean_power_mw", "target_total_energy_mj"}}
        self.energy["summary_version"] = 1
        with self.assertRaisesRegex(ValueError, "regenerate"):
            self.build()

    def test_synthetic_unmeasured_has_no_targets(self):
        self.metadata = run_metadata(); self.metadata["run_id"] = "run-001"
        self.rows[0]["source_kind"] = "synthetic"
        row = build_dataset_row_v2(self.metadata, self.rows, measurement_window=self.window)
        for target in feature_roles(2)[2]:
            self.assertIsNone(row[target])

    def test_custom_duration_policy_propagates(self):
        self.window["end_us"] = self.window["start_us"] + 7200000000
        self.window["window_duration_ms"] = 7200000
        self.energy["window_duration_ms"] = 7200000
        self.energy["target_total_energy_mj"] = 90000
        self.assertEqual(self.build(max_window_duration_ms=7200000)["window_duration_ms"], 7200000)
        with self.assertRaises(ValueError):
            self.build()

    def test_derived_energy_overflow_is_rejected(self):
        self.energy["target_mean_power_mw"] = 1e307
        self.energy["target_total_energy_mj"] = 1e307
        with self.assertRaisesRegex(ValueError, "overflow"):
            self.build(delivery_summary=self.delivery)

    def test_file_api_round_trip_and_duplicate_json_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in (("metadata", self.metadata), ("window", self.window), ("energy", self.energy)):
                (root / name).write_text(json.dumps(value), encoding="utf-8")
            with (root / "events").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS); writer.writeheader(); writer.writerows(self.rows)
            def load():
                return build_dataset_row_v2_from_files(root / "events", root / "metadata", measurement_window=root / "window", ppk2_summary=root / "energy")
            self.assertEqual(load(), self.build())
            (root / "window").write_text('{"run_id":"a","run_id":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load()

    def test_v2_partition_and_typed_features(self):
        validate_feature_partition(DATASET_FIELDS_V2, schema_version=2)
        row = self.build(delivery_summary=self.delivery)
        row.update(payload_size_bytes=32, interval_ms=1000, tx_power_dbm=0)
        selected = extract_features(row, prediction_mode="post_run", available_fields=frozenset(DATASET_FIELDS_V2))
        self.assertFalse(set(selected) & (feature_roles(2)[0] | feature_roles(2)[2]))
        for field in selected:
            broken = row.copy(); broken[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                extract_features(broken, prediction_mode="post_run", available_fields=frozenset(DATASET_FIELDS_V2))


class DatasetV2CliTests(unittest.TestCase):
    setUp = DatasetV2Tests.setUp
    # Reuse artifact construction and additionally exercise the subprocess boundary.
    def test_cli_v2_hash_and_failure_cleanup(self):
        import hashlib
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, data in (("metadata", self.metadata), ("window", self.window), ("energy", self.energy)):
                (root / name).write_text(json.dumps(data), encoding="utf-8")
            with (root / "events").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS); writer.writeheader(); writer.writerows(self.rows)
            command = [sys.executable, str(Path(__file__).resolve().parents[1] / "green_ops_build_dataset.py"),
                       "--telemetry-csv", str(root / "events"), "--run-metadata", str(root / "metadata"),
                       "--measurement-window", str(root / "window"), "--ppk2-summary", str(root / "energy"),
                       "--dataset-output", str(root / "out.csv"), "--manifest-output", str(root / "out.json")]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse((root / "out.csv").exists())
            result = subprocess.run(command + ["--dataset-version", "2"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((root / "out.json").read_text())
            self.assertEqual(manifest["dataset_sha256"], hashlib.sha256((root / "out.csv").read_bytes()).hexdigest())
            self.assertEqual(set(manifest["input_sha256"]), {"telemetry_csv", "run_metadata", "measurement_window", "ppk2_summary"})
            self.assertIn("ping_rtt_latency_ms", manifest["column_roles"]["targets"])
