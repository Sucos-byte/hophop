# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ppk2_summary as ppk2
from tools.green_ops.tests.test_ppk2_summary_v2 import (
    aligned_window,
    valid_summary,
)


class Ppk2V2BoundaryTests(unittest.TestCase):
    def validate(self, summary, window=None, **policy):
        return ppk2.validate_ppk2_summary_v2(
            summary,
            expected_run_id="run-001",
            window=aligned_window() if window is None else window,
            **policy,
        )

    def test_relative_duration_tolerance(self):
        summary = valid_summary()
        summary["window_duration_ms"] = 1001.0
        summary["target_total_energy_mj"] = 12.5125
        self.validate(
            summary,
            duration_tolerance_ms=0.0,
            duration_tolerance_fraction=0.001,
        )
        summary["window_duration_ms"] = 1001.01
        summary["target_total_energy_mj"] = 12.512625
        with self.assertRaises(ValueError):
            self.validate(
                summary,
                duration_tolerance_ms=0.0,
                duration_tolerance_fraction=0.001,
            )

    def test_absolute_energy_tolerance_boundary(self):
        summary = valid_summary()
        summary["target_total_energy_mj"] = 12.625
        self.validate(
            summary,
            energy_tolerance_mj=0.125,
            energy_tolerance_fraction=0.0,
        )
        with self.assertRaises(ValueError):
            self.validate(
                summary,
                energy_tolerance_mj=0.124,
                energy_tolerance_fraction=0.0,
            )

    def test_relative_energy_tolerance_boundary(self):
        summary = valid_summary()
        summary["target_total_energy_mj"] = 12.625
        self.validate(
            summary,
            energy_tolerance_mj=0.0,
            energy_tolerance_fraction=0.01,
        )
        with self.assertRaises(ValueError):
            self.validate(
                summary,
                energy_tolerance_mj=0.0,
                energy_tolerance_fraction=0.009,
            )

    def test_exact_match_accepts_zero_tolerances(self):
        window = aligned_window()
        window["alignment"]["uncertainty_ms"] = 0.0
        self.validate(
            valid_summary(),
            window,
            duration_tolerance_ms=0.0,
            duration_tolerance_fraction=0.0,
            energy_tolerance_mj=0.0,
            energy_tolerance_fraction=0.0,
            max_alignment_uncertainty_ms=0.0,
        )

    def test_rejects_invalid_energy_tolerances(self):
        for policy in (
            {"energy_tolerance_mj": -1},
            {"energy_tolerance_mj": True},
            {"energy_tolerance_mj": float("inf")},
            {"energy_tolerance_fraction": float("nan")},
            {"energy_tolerance_fraction": 1.01},
        ):
            with self.subTest(policy=policy):
                with self.assertRaises(ValueError):
                    self.validate(valid_summary(), **policy)

    def test_rejects_derived_energy_overflow(self):
        window = aligned_window()
        window["end_us"] = 3000000
        window["window_duration_ms"] = 2000.0
        summary = valid_summary()
        summary["window_duration_ms"] = 2000.0
        summary["target_mean_power_mw"] = 1e308
        with self.assertRaises(ValueError):
            self.validate(summary, window)

    def test_serial_alignment_requires_acceptable_uncertainty(self):
        window = aligned_window()
        window["alignment"]["method"] = "serial"
        self.validate(valid_summary(), window)
        window["alignment"]["uncertainty_ms"] = 2.0
        with self.assertRaises(ValueError):
            self.validate(valid_summary(), window)


if __name__ == "__main__":
    unittest.main()
