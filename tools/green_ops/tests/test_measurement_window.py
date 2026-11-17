# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from measurement_window import (
    compute_counter_deltas,
    validate_measurement_window,
)


def valid_window():
    return {
        "window_version": 1,
        "run_id": "run-001",
        "window_id": "window-001",
        "clock_id": "device-monotonic",
        "start_us": 1000000,
        "end_us": 2000000,
        "window_duration_ms": 1000.0,
        "segment_id": 0,
        "observed_segment_ids": [0],
        "start_counters": {
            "rx_attempts": 10,
            "rx_data_packets": 8,
            "sync_beacons": 2,
            "tx_successes": 3,
        },
        "end_counters": {
            "rx_attempts": 15,
            "rx_data_packets": 12,
            "sync_beacons": 3,
            "tx_successes": 5,
        },
        "alignment": {
            "method": "synthetic_fixture",
            "reference_artifact_sha256": "a" * 64,
            "start_marker_id": "start-001",
            "end_marker_id": "end-001",
            "uncertainty_ms": 0.5,
        },
        "evaluation_group_id": "session-001",
    }


class MeasurementWindowTests(unittest.TestCase):
    def validate(self, window, **options):
        return validate_measurement_window(
            window, expected_run_id="run-001", **options
        )

    def test_valid_window_returns_independent_copy(self):
        window = valid_window()
        original = copy.deepcopy(window)
        result = self.validate(window)
        self.assertEqual(result, window)
        self.assertEqual(window, original)
        result["start_counters"]["rx_attempts"] = 999
        self.assertEqual(window, original)

    def test_subtracts_nonzero_baselines(self):
        self.assertEqual(compute_counter_deltas(valid_window()), {
            "rx_attempts": 5,
            "rx_data_packets": 4,
            "sync_beacons": 1,
            "tx_successes": 2,
        })

    def test_fractional_millisecond_duration_is_valid(self):
        window = valid_window()
        window["end_us"] = window["start_us"] + 1500
        window["window_duration_ms"] = 1.5
        self.validate(window)

    def test_rejects_wrong_identity_unknown_or_missing_fields(self):
        windows = []
        wrong_id = valid_window()
        wrong_id["run_id"] = "other-run"
        windows.append(wrong_id)
        extra = valid_window()
        extra["unknown"] = 1
        windows.append(extra)
        missing = valid_window()
        del missing["clock_id"]
        windows.append(missing)
        for window in windows:
            with self.subTest(window=window):
                with self.assertRaises(ValueError):
                    self.validate(window)

    def test_rejects_invalid_timestamps_and_durations(self):
        cases = (
            ("start_us", True),
            ("start_us", -1),
            ("end_us", 1000000),
            ("end_us", 999999),
            ("end_us", 2000000.5),
            ("window_duration_ms", True),
            ("window_duration_ms", 0),
            ("window_duration_ms", float("nan")),
            ("window_duration_ms", float("inf")),
            ("window_duration_ms", "1000"),
            ("window_duration_ms", 999),
        )
        for field, value in cases:
            window = valid_window()
            window[field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    self.validate(window)

    def test_duration_bound_is_configurable_and_strict(self):
        self.validate(valid_window(), max_window_duration_ms=1000)
        for maximum in (999, 0, -1, True, float("inf"), float("nan")):
            with self.subTest(maximum=maximum):
                with self.assertRaises(ValueError):
                    self.validate(
                        valid_window(), max_window_duration_ms=maximum
                    )

    def test_rejects_counter_reset_saturation_and_invalid_types(self):
        for endpoint in ("start_counters", "end_counters"):
            for value in (-1, True, 1.5, "10", 2**32 - 1, 2**32):
                window = valid_window()
                window[endpoint]["rx_attempts"] = value
                with self.subTest(endpoint=endpoint, value=value):
                    with self.assertRaises(ValueError):
                        self.validate(window)

        window = valid_window()
        window["end_counters"]["rx_attempts"] = 9
        with self.assertRaises(ValueError):
            self.validate(window)
        with self.assertRaises(ValueError):
            compute_counter_deltas(window)

    def test_rejects_discontinuous_or_invalid_segments(self):
        for segments in ([], [0, 1], [1], [True], [0, 0]):
            window = valid_window()
            window["observed_segment_ids"] = segments
            with self.subTest(segments=segments):
                with self.assertRaises(ValueError):
                    self.validate(window)

    def test_rejects_invalid_alignment(self):
        cases = (
            ("method", "unknown"),
            ("reference_artifact_sha256", "not-a-hash"),
            ("start_marker_id", ""),
            ("end_marker_id", "start-001"),
            ("uncertainty_ms", -1),
            ("uncertainty_ms", True),
            ("uncertainty_ms", float("nan")),
        )
        for field, value in cases:
            window = valid_window()
            window["alignment"][field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    self.validate(window)


if __name__ == "__main__":
    unittest.main()
