# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ppk2_summary import load_ppk2_summary, validate_ppk2_summary


def example():
    return {
        "summary_version": 1,
        "run_id": "lab-000001",
        "instrument": "nordic-ppk2",
        "target_mean_power_mw": 12.5,
        "target_total_energy_mj": 250.0,
    }


class Ppk2SummaryTests(unittest.TestCase):
    def test_valid_summary_is_accepted_without_mutation(self):
        data = example()
        original = copy.deepcopy(data)
        self.assertIsNone(validate_ppk2_summary(data))
        self.assertEqual(data, original)

    def test_expected_run_id_must_match(self):
        self.assertIsNone(
            validate_ppk2_summary(example(), expected_run_id="lab-000001")
        )
        with self.assertRaisesRegex(ValueError, "run_id"):
            validate_ppk2_summary(example(), expected_run_id="lab-000002")

    def test_schema_fields_are_exact(self):
        missing = example()
        del missing["instrument"]
        extra = example()
        extra["duration_s"] = 20
        for data in (missing, extra, [], None):
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_ppk2_summary(data)

    def test_scalar_fields_are_strict(self):
        cases = {
            "summary_version": [True, 1.0, 0, 2, "1"],
            "run_id": [None, "", "=formula", "bad\nvalue", "a" * 65],
            "instrument": [None, "PPK2", "nordic_ppk2", False],
        }
        for field, values in cases.items():
            for value in values:
                data = example()
                data[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    validate_ppk2_summary(data)

    def test_energy_values_must_be_finite_positive_numbers(self):
        invalid = [True, False, None, "1", 0, 0.0, -1, -0.1,
                   math.nan, math.inf, -math.inf]
        for field in ("target_mean_power_mw", "target_total_energy_mj"):
            for value in invalid:
                data = example()
                data[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    validate_ppk2_summary(data)

    def test_integer_energy_values_are_accepted(self):
        data = example()
        data["target_mean_power_mw"] = 1
        data["target_total_energy_mj"] = 2
        self.assertIsNone(validate_ppk2_summary(data))

    def test_json_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ppk2.json"
            path.write_text(json.dumps(example()), encoding="utf-8")
            self.assertEqual(
                load_ppk2_summary(path, expected_run_id="lab-000001"),
                example(),
            )

    def test_loader_rejects_duplicate_keys_invalid_json_and_nonfinite_values(self):
        valid = json.dumps(example())
        cases = [
            "{",
            valid.replace(
                '"summary_version": 1',
                '"summary_version": 2, "summary_version": 1',
            ),
            valid.replace('"target_mean_power_mw": 12.5',
                          '"target_mean_power_mw": NaN'),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ppk2.json"
            for content in cases:
                path.write_text(content, encoding="utf-8")
                with self.subTest(content=content), self.assertRaises(ValueError):
                    load_ppk2_summary(path)

    def test_loader_rejects_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ppk2.json"
            path.write_bytes(b"\xff")
            with self.assertRaises(UnicodeDecodeError):
                load_ppk2_summary(path)


if __name__ == "__main__":
    unittest.main()
