# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from converter import CSV_FIELDS
from dataset_builder import DATASET_FIELDS, aggregate_telemetry, build_dataset_row


def event_row(*, segment_id=0, event="rx_data", run_id="demo-001",
              source_kind="synthetic", **values):
    row = dict.fromkeys(CSV_FIELDS, "")
    row.update({
        "run_id": run_id,
        "source_kind": source_kind,
        "source_line": "1",
        "segment_id": str(segment_id),
        "event": event,
    })
    row.update({key: str(value) for key, value in values.items()})
    return row


class TelemetryAggregationTests(unittest.TestCase):
    def test_one_segment_uses_counter_maxima(self):
        result = aggregate_telemetry([
            event_row(rx_attempts=3, rx_data_packets=2),
            event_row(rx_attempts=5, rx_data_packets=4),
            event_row(event="sync_beacon", sync_beacons=2),
            event_row(event="tx_success", tx_successes=3),
        ])
        self.assertEqual(result, {
            "run_id": "demo-001",
            "source_kind": "synthetic",
            "segment_count": 1,
            "rx_attempts": 5,
            "delivered_packets": 4,
            "sync_beacons": 2,
            "tx_successes": 3,
            "packet_delivery_ratio": 0.8,
            "ping_rtt_latency_ms": None,
        })

    def test_segment_resets_are_aggregated_independently(self):
        result = aggregate_telemetry([
            event_row(segment_id=0, rx_attempts=5, rx_data_packets=4),
            event_row(segment_id=1, rx_attempts=2, rx_data_packets=1),
        ])
        self.assertEqual(result["segment_count"], 2)
        self.assertEqual(result["rx_attempts"], 7)
        self.assertEqual(result["delivered_packets"], 5)
        self.assertEqual(result["packet_delivery_ratio"], 5 / 7)

    def test_sparse_interleaved_events_keep_counters_separate(self):
        result = aggregate_telemetry([
            event_row(rx_attempts=1, rx_data_packets=1),
            event_row(event="tx_success", tx_successes=99),
            event_row(event="sync_beacon", sync_beacons=4),
            event_row(rx_attempts=2, rx_data_packets=2),
        ])
        self.assertEqual(result["delivered_packets"], 2)
        self.assertEqual(result["tx_successes"], 99)
        self.assertEqual(result["sync_beacons"], 4)

    def test_segment_order_and_last_row_do_not_change_maxima(self):
        result = aggregate_telemetry([
            event_row(segment_id=1, rx_attempts=2, rx_data_packets=1),
            event_row(segment_id=0, rx_attempts=5, rx_data_packets=4),
            event_row(segment_id=0, rx_attempts=5, rx_data_packets=4),
            event_row(segment_id=1, rx_attempts=1, rx_data_packets=1),
        ])
        self.assertEqual(result["rx_attempts"], 7)
        self.assertEqual(result["delivered_packets"], 5)

    def test_zero_attempts_produce_no_delivery_ratio(self):
        result = aggregate_telemetry([
            event_row(event="sync_beacon", sync_beacons=1),
            event_row(event="tx_success", tx_successes=1),
        ])
        self.assertEqual(result["rx_attempts"], 0)
        self.assertEqual(result["delivered_packets"], 0)
        self.assertIsNone(result["packet_delivery_ratio"])

    def test_empty_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            aggregate_telemetry([])

    def test_mixed_or_invalid_provenance_is_rejected(self):
        cases = [
            [event_row(), event_row(run_id="demo-002")],
            [event_row(), event_row(source_kind="hardware")],
            [event_row(run_id="=formula")],
            [event_row(source_kind="simulation")],
        ]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                aggregate_telemetry(rows)

    def test_invalid_segment_and_counter_values_are_rejected(self):
        cases = [
            event_row(segment_id=-1),
            event_row(segment_id="bad"),
            event_row(rx_attempts=-1, rx_data_packets=0),
            event_row(rx_attempts="1.0", rx_data_packets=0),
            event_row(rx_attempts=True, rx_data_packets=0),
            event_row(event="unknown"),
        ]
        for row in cases:
            with self.subTest(row=row), self.assertRaises(ValueError):
                aggregate_telemetry([row])

    def test_delivery_cannot_exceed_receive_attempts_in_any_segment(self):
        with self.assertRaisesRegex(ValueError, "delivered"):
            aggregate_telemetry([
                event_row(segment_id=0, rx_attempts=1, rx_data_packets=2),
                event_row(segment_id=1, rx_attempts=10, rx_data_packets=0),
            ])

    def test_row_fields_must_match_converter_schema(self):
        missing = event_row()
        del missing["source_line"]
        extra = event_row()
        extra["unknown"] = "value"
        for row in (missing, extra, None):
            with self.subTest(row=row), self.assertRaises(ValueError):
                aggregate_telemetry([row])


def run_metadata(*, execution_kind="synthetic", measured_power=False):
    hardware = execution_kind == "hardware"
    return {
        "metadata_version": 1,
        "run_id": "demo-001",
        "adapter_id": "hophop",
        "feature_profile_id": "hophop-nrf9151-v1",
        "execution_kind": execution_kind,
        "firmware_revision": "a" * 40 if hardware else None,
        "firmware_dirty": False if hardware else None,
        "device_id": "board-01" if hardware else None,
        "target_provenance": {
            "target_power_draw_mw": "measured" if measured_power else "missing",
            "target_ping_rtt_latency_ms": "missing",
        },
    }


def telemetry(*, source_kind="synthetic", delivered=4, attempts=5):
    return {
        "run_id": "demo-001",
        "source_kind": source_kind,
        "segment_count": 2,
        "rx_attempts": attempts,
        "delivered_packets": delivered,
        "sync_beacons": 3,
        "tx_successes": 6,
        "packet_delivery_ratio": delivered / attempts if attempts else None,
        "ping_rtt_latency_ms": None,
    }


def experiment(*, execution_kind="synthetic"):
    return {
        "run_id": "demo-001",
        "adapter_id": "hophop",
        "feature_profile_id": "hophop-nrf9151-v1",
        "execution_kind": execution_kind,
        "state": "planned",
        "requested_settings": {
            "payload_size_bytes": 64,
            "interval_ms": 100,
            "tx_power_dbm": 0,
            "loss_scenario": {
                "model": "gilbert_elliott",
                "preset": "moderate",
                "initial_state": "good",
                "good_to_bad_probability": 0.05,
                "bad_to_good_probability": 0.25,
                "good_state_loss_probability": 0.01,
                "bad_state_loss_probability": 0.70,
            },
            "seed": 42,
            "repetition": 2,
        },
    }


def ppk2():
    return {
        "summary_version": 1,
        "run_id": "demo-001",
        "instrument": "nordic-ppk2",
        "target_mean_power_mw": 12.5,
        "target_total_energy_mj": 250.0,
    }


class DatasetRowTests(unittest.TestCase):
    def test_unmeasured_row_keeps_energy_targets_empty(self):
        result = build_dataset_row(run_metadata(), telemetry())
        self.assertEqual(set(result), set(DATASET_FIELDS))
        self.assertEqual(result["dataset_version"], 1)
        self.assertEqual(result["run_id"], "demo-001")
        self.assertEqual(result["adapter"], "hophop")
        self.assertEqual(result["feature_profile_id"], "hophop-nrf9151-v1")
        self.assertEqual(result["source_kind"], "synthetic")
        self.assertEqual(result["execution_kind"], "synthetic")
        self.assertEqual(result["measurement_status"], "unmeasured")
        self.assertEqual(result["delivered_packets"], 4)
        self.assertEqual(result["packet_delivery_ratio"], 0.8)
        self.assertIsNone(result["ping_rtt_latency_ms"])
        for field in (
            "target_mean_power_mw",
            "target_total_energy_mj",
            "target_energy_per_delivered_packet_uj",
        ):
            self.assertIsNone(result[field])

    def test_absent_experiment_keeps_planned_features_empty(self):
        result = build_dataset_row(run_metadata(), telemetry())
        for field in (
            "payload_size_bytes", "interval_ms", "tx_power_dbm", "loss_model",
            "loss_preset", "loss_initial_state", "good_to_bad_probability",
            "bad_to_good_probability", "good_state_loss_probability",
            "bad_state_loss_probability", "seed", "repetition",
        ):
            self.assertIsNone(result[field])

    def test_planned_experiment_settings_become_features(self):
        result = build_dataset_row(
            run_metadata(), telemetry(), experiment=experiment()
        )
        self.assertEqual(result["payload_size_bytes"], 64)
        self.assertEqual(result["interval_ms"], 100)
        self.assertEqual(result["tx_power_dbm"], 0)
        self.assertEqual(result["loss_model"], "gilbert_elliott")
        self.assertEqual(result["loss_preset"], "moderate")
        self.assertEqual(result["loss_initial_state"], "good")
        self.assertEqual(result["good_to_bad_probability"], 0.05)
        self.assertEqual(result["bad_to_good_probability"], 0.25)
        self.assertEqual(result["good_state_loss_probability"], 0.01)
        self.assertEqual(result["bad_state_loss_probability"], 0.70)
        self.assertEqual(result["seed"], 42)
        self.assertEqual(result["repetition"], 2)

    def test_measured_hardware_row_computes_energy_per_delivery(self):
        result = build_dataset_row(
            run_metadata(execution_kind="hardware", measured_power=True),
            telemetry(source_kind="hardware"),
            ppk2_summary=ppk2(),
        )
        self.assertEqual(result["measurement_status"], "measured")
        self.assertEqual(result["target_mean_power_mw"], 12.5)
        self.assertEqual(result["target_total_energy_mj"], 250.0)
        self.assertEqual(result["target_energy_per_delivered_packet_uj"], 62_500.0)

    def test_zero_deliveries_keep_per_packet_energy_empty(self):
        result = build_dataset_row(
            run_metadata(execution_kind="hardware", measured_power=True),
            telemetry(source_kind="hardware", delivered=0),
            ppk2_summary=ppk2(),
        )
        self.assertEqual(result["target_total_energy_mj"], 250.0)
        self.assertIsNone(result["target_energy_per_delivered_packet_uj"])

    def test_ppk2_requires_hardware_measurement_provenance(self):
        cases = [
            (run_metadata(), telemetry()),
            (run_metadata(execution_kind="hardware"), telemetry(source_kind="hardware")),
            (run_metadata(execution_kind="hardware", measured_power=True), telemetry()),
        ]
        for metadata, aggregated in cases:
            with self.subTest(metadata=metadata, telemetry=aggregated), self.assertRaises(ValueError):
                build_dataset_row(metadata, aggregated, ppk2_summary=ppk2())

    def test_measured_power_provenance_requires_ppk2_artifact(self):
        with self.assertRaisesRegex(ValueError, "PPK2"):
            build_dataset_row(
                run_metadata(execution_kind="hardware", measured_power=True),
                telemetry(source_kind="hardware"),
            )

    def test_all_run_id_values_must_match(self):
        bad_telemetry = telemetry()
        bad_telemetry["run_id"] = "other-run"
        bad_ppk2 = ppk2()
        bad_ppk2["run_id"] = "other-run"
        bad_experiment = experiment()
        bad_experiment["run_id"] = "other-run"
        for changes in (
            {"telemetry": bad_telemetry},
            {"ppk2_summary": bad_ppk2},
            {"experiment": bad_experiment},
        ):
            arguments = {"telemetry": telemetry(), **changes}
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                build_dataset_row(run_metadata(), **arguments)

    def test_experiment_identity_and_state_must_match_metadata(self):
        for field, value in (
            ("adapter_id", "platform-b"),
            ("feature_profile_id", "profile-b"),
            ("execution_kind", "simulation"),
            ("state", "measured"),
        ):
            planned = experiment()
            planned[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_dataset_row(
                    run_metadata(), telemetry(), experiment=planned
                )

    def test_malformed_telemetry_and_experiment_are_rejected(self):
        bad_ratio = telemetry()
        bad_ratio["packet_delivery_ratio"] = 0.1
        bad_scenario = experiment()
        bad_scenario["requested_settings"]["loss_scenario"][
            "bad_state_loss_probability"
        ] = 0.0
        for aggregated, planned in (
            (bad_ratio, None),
            (telemetry(), bad_scenario),
            (telemetry(), {}),
        ):
            with self.subTest(telemetry=aggregated, experiment=planned), self.assertRaises(ValueError):
                build_dataset_row(
                    run_metadata(), aggregated, experiment=planned
                )


if __name__ == "__main__":
    unittest.main()
