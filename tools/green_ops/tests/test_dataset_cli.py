# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atomic_outputs
import green_ops_build_dataset as cli

SCRIPT = Path(__file__).resolve().parents[1] / "green_ops_build_dataset.py"


class AtomicOutputTests(unittest.TestCase):
    def test_refuses_existing_destination_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first = directory / "dataset.csv"
            second = directory / "manifest.json"
            second.write_text("KEEP", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                atomic_outputs.publish_outputs({first: "csv\n", second: "{}\n"})

            self.assertFalse(first.exists())
            self.assertEqual(second.read_text(encoding="utf-8"), "KEEP")

    def test_rejects_same_or_resolved_colliding_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            nested = directory / "nested"
            nested.mkdir()
            path = directory / "dataset.csv"
            alias = nested / ".." / "dataset.csv"

            with self.assertRaises(ValueError):
                atomic_outputs.reserve_outputs([path, alias])

    def test_rolls_back_first_output_if_second_publish_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first = directory / "dataset.csv"
            second = directory / "manifest.json"
            real_replace = atomic_outputs.os.replace

            def fail_second(source, destination):
                if Path(destination) == second:
                    raise OSError("simulated second publication failure")
                real_replace(source, destination)

            with mock.patch.object(
                atomic_outputs.os, "replace", side_effect=fail_second
            ):
                with self.assertRaisesRegex(OSError, "simulated"):
                    atomic_outputs.publish_outputs({first: "csv\n", second: "{}\n"})

            self.assertFalse(first.exists())
            self.assertFalse(second.exists())
            self.assertEqual(list(directory.iterdir()), [])

    def test_publishes_newline_terminated_text_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first = directory / "dataset.csv"
            second = directory / "manifest.json"
            atomic_outputs.publish_outputs({first: "csv", second: "{}"})
            self.assertEqual(first.read_text(encoding="utf-8"), "csv\n")
            self.assertEqual(second.read_text(encoding="utf-8"), "{}\n")


class DatasetCliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            text=True,
            capture_output=True,
        )

    def write_inputs(self, directory, *, energy=False, kind="synthetic"):
        directory = Path(directory)
        telemetry = directory / "events.csv"
        metadata = directory / "run.json"
        experiment_plan = directory / "plan.json"
        ppk2 = directory / "ppk2.json"
        with telemetry.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow([
                "run_id", "source_kind", "source_line", "segment_id", "event",
                "rx_attempts", "rx_data_packets", "sync_beacons", "tx_successes",
                "local_rx_ticks", "scheduled_tx_ticks",
            ])
            writer.writerow([
                "demo-001", kind, 1, 0, "rx_data", 5, 4, "", "", 10, "",
            ])
        hardware = kind == "hardware"
        provenance = "measured" if energy else "missing"
        metadata.write_text(json.dumps({
            "metadata_version": 1,
            "run_id": "demo-001",
            "adapter_id": "hophop",
            "feature_profile_id": "hophop-nrf9151-v1",
            "execution_kind": kind,
            "firmware_revision": "a" * 40 if hardware else None,
            "firmware_dirty": False if hardware else None,
            "device_id": "board-01" if hardware else None,
            "target_provenance": {
                "target_power_draw_mw": provenance,
                "target_ping_rtt_latency_ms": "missing",
            },
        }), encoding="utf-8")
        if energy:
            ppk2.write_text(json.dumps({
                "summary_version": 1,
                "run_id": "demo-001",
                "instrument": "nordic-ppk2",
                "target_mean_power_mw": 12.5,
                "target_total_energy_mj": 250.0,
            }), encoding="utf-8")
        return telemetry, metadata, ppk2

    def test_unmeasured_input_leaves_target_columns_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            telemetry, metadata, _ = self.write_inputs(directory)
            output = directory / "dataset.csv"
            manifest = directory / "manifest.json"
            result = self.run_cli(
                "--telemetry-csv", str(telemetry),
                "--run-metadata", str(metadata),
                "--dataset-output", str(output),
                "--manifest-output", str(manifest),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(encoding="utf-8", newline="") as stream:
                row = next(csv.DictReader(stream))
            summary = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(row["measurement_status"], "unmeasured")
            self.assertEqual(row["target_mean_power_mw"], "")
            self.assertEqual(row["target_total_energy_mj"], "")
            self.assertEqual(row["target_energy_per_delivered_packet_uj"], "")
            self.assertEqual(summary["measurement_status"], "unmeasured")
            self.assertEqual(summary["dataset_rows"], 1)

    def test_measured_input_computes_energy_targets_and_manifest_digests(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            telemetry, metadata, ppk2 = self.write_inputs(
                directory, energy=True, kind="hardware"
            )
            output = directory / "dataset.csv"
            manifest_path = directory / "manifest.json"
            result = self.run_cli(
                "--telemetry-csv", str(telemetry),
                "--run-metadata", str(metadata),
                "--ppk2-summary", str(ppk2),
                "--dataset-output", str(output),
                "--manifest-output", str(manifest_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(encoding="utf-8", newline="") as stream:
                row = next(csv.DictReader(stream))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(row["target_mean_power_mw"], "12.5")
            self.assertEqual(row["target_total_energy_mj"], "250.0")
            self.assertEqual(row["target_energy_per_delivered_packet_uj"], "62500.0")
            self.assertEqual(manifest["measurement_status"], "measured")
            self.assertEqual(manifest["execution_kind"], "hardware")
            self.assertIn("ppk2_summary", manifest["input_sha256"])

    def test_rejects_input_failure_without_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            telemetry, metadata, _ = self.write_inputs(directory)
            telemetry.write_bytes(b"\xff")
            output = directory / "dataset.csv"
            manifest = directory / "manifest.json"
            result = self.run_cli(
                "--telemetry-csv", str(telemetry),
                "--run-metadata", str(metadata),
                "--dataset-output", str(output),
                "--manifest-output", str(manifest),
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())

    def test_refuses_overwrite_and_output_collisions(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            telemetry, metadata, _ = self.write_inputs(directory)
            output = directory / "dataset.csv"
            manifest = directory / "manifest.json"
            output.write_text("KEEP", encoding="utf-8")
            result = self.run_cli(
                "--telemetry-csv", str(telemetry),
                "--run-metadata", str(metadata),
                "--dataset-output", str(output),
                "--manifest-output", str(manifest),
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(output.read_text(encoding="utf-8"), "KEEP")
            self.assertFalse(manifest.exists())

            collision = self.run_cli(
                "--telemetry-csv", str(telemetry),
                "--run-metadata", str(metadata),
                "--dataset-output", str(telemetry),
                "--manifest-output", str(telemetry),
            )
            self.assertEqual(collision.returncode, 1)

    def test_repeated_runs_at_distinct_paths_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            telemetry, metadata, _ = self.write_inputs(directory)
            contents = []
            for index in range(2):
                output = directory / f"dataset-{index}.csv"
                manifest = directory / f"manifest-{index}.json"
                result = self.run_cli(
                    "--telemetry-csv", str(telemetry),
                    "--run-metadata", str(metadata),
                    "--dataset-output", str(output),
                    "--manifest-output", str(manifest),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                contents.append((output.read_text(encoding="utf-8"),
                                 manifest.read_text(encoding="utf-8")))
            self.assertEqual(contents[0], contents[1])


if __name__ == "__main__":
    unittest.main()
