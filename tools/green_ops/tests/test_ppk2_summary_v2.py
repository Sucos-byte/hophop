# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ppk2_summary as ppk2
from tools.green_ops.tests.test_measurement_window import valid_window


def aligned_window():
    window = valid_window()
    window["alignment"]["method"] = "gpio"
    return window


def valid_summary():
    return {
        "summary_version": 2,
        "run_id": "run-001",
        "instrument": "nordic-ppk2",
        "target_mean_power_mw": 12.5,
        "target_total_energy_mj": 12.5,
        "window_id": "window-001",
        "window_duration_ms": 1000.0,
        "voltage_v": 3.3,
        "raw_capture_sha256": "c" * 64,
        "alignment_reference_sha256": "a" * 64,
    }


class Ppk2SummaryV2Tests(unittest.TestCase):
    def validate(self, summary, window=None, **options):
        return ppk2.validate_ppk2_summary_v2(
            summary,
            expected_run_id="run-001",
            window=aligned_window() if window is None else window,
            **options,
        )

    def test_valid_summary_returns_copy_without_mutation(self):
        summary = valid_summary()
        window = aligned_window()
        originals = copy.deepcopy((summary, window))
        result = self.validate(summary, window)
        self.assertEqual(result, summary)
        self.assertIsNot(result, summary)
        self.assertEqual((summary, window), originals)

    def test_requires_matching_identity_and_alignment_reference(self):
        for field, value in (
            ("run_id", "other"),
            ("window_id", "other"),
            ("alignment_reference_sha256", "b" * 64),
            ("raw_capture_sha256", "invalid"),
            ("instrument", "other"),
            ("summary_version", 1),
        ):
            summary = valid_summary()
            summary[field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    self.validate(summary)

    def test_duration_tolerance_is_configurable(self):
        summary = valid_summary()
        summary["window_duration_ms"] = 1000.5
        summary["target_total_energy_mj"] = 12.50625
        self.validate(
            summary,
            duration_tolerance_ms=0.5,
            duration_tolerance_fraction=0.0,
        )
        with self.assertRaises(ValueError):
            self.validate(
                summary,
                duration_tolerance_ms=0.49,
                duration_tolerance_fraction=0.0,
            )

    def test_rejects_inconsistent_energy_power_and_duration(self):
        summary = valid_summary()
        summary["target_total_energy_mj"] = 25.0
        with self.assertRaises(ValueError):
            self.validate(summary)

    def test_rejects_nonpositive_nonfinite_and_boolean_values(self):
        for field in (
            "target_mean_power_mw", "target_total_energy_mj",
            "window_duration_ms", "voltage_v",
        ):
            for value in (0, -1, True, float("nan"), float("inf"), "3.3"):
                summary = valid_summary()
                summary[field] = value
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        self.validate(summary)

    def test_rejects_synthetic_or_excessively_uncertain_alignment(self):
        window = valid_window()
        with self.assertRaises(ValueError):
            self.validate(valid_summary(), window)

        window = aligned_window()
        self.validate(
            valid_summary(), window, max_alignment_uncertainty_ms=0.5
        )
        with self.assertRaises(ValueError):
            self.validate(
                valid_summary(), window, max_alignment_uncertainty_ms=0.49
            )

    def test_revalidates_window_continuity(self):
        window = aligned_window()
        window["observed_segment_ids"] = [0, 1]
        with self.assertRaises(ValueError):
            self.validate(valid_summary(), window)

    def test_rejects_invalid_policy_tolerances(self):
        options = (
            {"duration_tolerance_ms": -1},
            {"duration_tolerance_ms": True},
            {"duration_tolerance_fraction": 1.1},
            {"duration_tolerance_fraction": float("nan")},
            {"max_alignment_uncertainty_ms": float("inf")},
            {"max_alignment_uncertainty_ms": -1},
        )
        for policy in options:
            with self.subTest(policy=policy):
                with self.assertRaises(ValueError):
                    self.validate(valid_summary(), **policy)

    def test_requires_exact_summary_schema(self):
        summary = valid_summary()
        summary["unknown"] = 1
        with self.assertRaises(ValueError):
            self.validate(summary)
        del summary["unknown"]
        del summary["voltage_v"]
        with self.assertRaises(ValueError):
            self.validate(summary)


if __name__ == "__main__":
    unittest.main()
