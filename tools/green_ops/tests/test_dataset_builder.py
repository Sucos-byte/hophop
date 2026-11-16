# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from converter import CSV_FIELDS
from dataset_builder import aggregate_telemetry


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


if __name__ == "__main__":
    unittest.main()
