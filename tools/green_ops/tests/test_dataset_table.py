# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataset_builder import build_dataset_row_v2
from dataset_table import build_dataset_table, load_dataset_artifact, validate_dataset_row
from green_ops_build_dataset import _dataset_csv, _manifest_v2
from tools.green_ops.tests.test_dataset_builder import run_metadata, event_row
from tools.green_ops.tests.test_measurement_window import valid_window


def artifact(run_id="run-001", status="unmeasured"):
    metadata = run_metadata(); metadata["run_id"] = run_id
    window = valid_window(); window["run_id"] = run_id
    row = build_dataset_row_v2(metadata, [event_row(run_id=run_id, **window["end_counters"])], measurement_window=window)
    if status == "analytical_simulation":
        row.update(execution_kind="simulation", measurement_status=status,
                   analytical_model_id="test-model", target_mean_power_mw=2.0,
                   target_total_energy_mj=2.0)
    # Manifest's paths/hashes refer to test evidence only.
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "fixture"
        source.write_text("test data", encoding="utf-8")
        manifest = json.loads(_manifest_v2(row, {"fixture": source}, {}))
    if status == "analytical_simulation":
        manifest["analytical_reference"] = dict(model_id="test-model", version="1",
            configuration_sha256="a"*64, assumptions_document_sha256="b"*64)
        manifest["input_sha256"].update(configuration="a"*64, assumptions_document="b"*64)
        manifest["input_paths"].update(configuration="test-config", assumptions_document="test-assumptions")
    return dict(row=row, manifest=manifest, csv_sha256=manifest["dataset_sha256"], manifest_sha256="c"*64)


class DatasetTableTests(unittest.TestCase):
    def table(self, artifacts, **options):
        return build_dataset_table(artifacts, schema_version=2, measurement_status=options.pop("measurement_status", "unmeasured"), **options)

    def test_two_rows_are_deterministic_and_preserve_nulls_and_groups(self):
        a, b = artifact(), artifact("run-002")
        result = self.table([a, b])
        self.assertEqual(result, self.table([b, a]))
        rows, manifest = result
        self.assertEqual([r["run_id"] for r in rows], ["run-001", "run-002"])
        self.assertEqual(manifest["group_ids"], ["session-001"])
        self.assertEqual(manifest["target_missing_counts"]["target_total_energy_mj"], 2)
        self.assertIsNone(rows[0]["target_total_energy_mj"])

    def test_duplicate_run_is_rejected_before_filtering(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.table([artifact(), artifact()])

    def test_provenance_filter_and_analytical_reference(self):
        a, b = artifact(), artifact("run-002", "analytical_simulation")
        rows, manifest = self.table([a, b], measurement_status="analytical_simulation", required_targets=("target_total_energy_mj",))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["run_id"], "run-002")
        self.assertEqual(manifest["excluded_count"], 1)
        del b["manifest"]["analytical_reference"]
        # Invalid excluded rows fail too.
        with self.assertRaises(ValueError):
            self.table([a, b])

    def test_analytical_reference_hash_mismatch(self):
        a = artifact(status="analytical_simulation")
        a["manifest"]["analytical_reference"]["configuration_sha256"] = "f"*64
        with self.assertRaises(ValueError):
            self.table([a], measurement_status="analytical_simulation")

    def test_missing_targets_error_and_explicit_exclusion(self):
        a, b = artifact(status="analytical_simulation"), artifact("run-002", "analytical_simulation")
        b["row"]["ping_rtt_latency_ms"] = 10.0
        with self.assertRaisesRegex(ValueError, "missing required"):
            self.table([a, b], measurement_status="analytical_simulation", required_targets=("ping_rtt_latency_ms",))
        rows, manifest = self.table([a, b], measurement_status="analytical_simulation", required_targets=("ping_rtt_latency_ms",), missing_target_policy="exclude")
        self.assertEqual(len(rows), 1)
        self.assertIn("missing targets", manifest["exclusions"][0]["reason"])

    def test_invalid_selection_and_types(self):
        for options in (dict(schema_version=1), dict(schema_version=True), dict(required_targets=("seed",)), dict(missing_target_policy="ignore"), dict(measurement_status="all")):
            args = dict(schema_version=2, measurement_status="unmeasured"); args.update(options)
            with self.subTest(options=options), self.assertRaises(ValueError):
                build_dataset_table([artifact()], **args)
        for field, value in (("rx_operations", True), ("window_duration_ms", float("nan")), ("run_id", "bad/id"), ("rx_decode_per_operation_ratio", 1.0), ("target_total_energy_mj", 1)):
            row = artifact()["row"]; row[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_dataset_row(row, schema_version=2)
        with self.assertRaisesRegex(ValueError, "zero rows"):
            self.table([])

    def test_manifest_identity_and_hash_mismatch(self):
        for key, value in (("run_id", "wrong"), ("dataset_version", True), ("dataset_sha256", "a"*64)):
            a = artifact(); a["manifest"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.table([a])

    def test_file_roundtrip_tampering_and_strict_csv(self):
        a = artifact()
        with tempfile.TemporaryDirectory() as directory:
            csv_path, manifest_path = Path(directory)/"row.csv", Path(directory)/"manifest.json"
            csv_path.write_text(_dataset_csv(a["row"]), encoding="utf-8")
            manifest_path.write_text(json.dumps(a["manifest"]), encoding="utf-8")
            loaded = load_dataset_artifact(csv_path, manifest_path)
            self.assertEqual(loaded["row"], a["row"])
            for text in (_dataset_csv(a["row"]).replace("0.8", "NaN"), _dataset_csv(a["row"]).replace("run-001", "run-002"), _dataset_csv(a["row"]) + "extra\n"):
                csv_path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_dataset_artifact(csv_path, manifest_path)
