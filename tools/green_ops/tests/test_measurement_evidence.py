# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import measurement_window as windows
from tools.green_ops.tests.test_measurement_window import valid_window


def valid_delivery():
    return {
        "summary_version": 1,
        "run_id": "run-001",
        "window_id": "window-001",
        "sender_id": "sender-001",
        "receiver_id": "receiver-001",
        "offered_packet_ids": ["session1-p1", "session1-p2"],
        "delivered_packet_ids": ["session1-p2"],
        "evidence_sha256": "b" * 64,
    }


class WindowLoaderTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "window.json"
            path.write_text(json.dumps(valid_window()), encoding="utf-8")
            self.assertEqual(
                windows.load_measurement_window(
                    path, expected_run_id="run-001"
                ),
                valid_window(),
            )

    def test_rejects_duplicate_keys_and_nonfinite_json(self):
        valid = json.dumps(valid_window())
        invalid_documents = (
            '{"run_id":"first","run_id":"second"}',
            valid.replace('"uncertainty_ms": 0.5', '"uncertainty_ms": NaN'),
            valid.replace('"uncertainty_ms": 0.5', '"uncertainty_ms": Infinity'),
            "{",
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "window.json"
            for document in invalid_documents:
                with self.subTest(document=document):
                    path.write_text(document, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        windows.load_measurement_window(
                            path, expected_run_id="run-001"
                        )

    def test_rejects_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "window.json"
            path.write_bytes(b"\xff")
            with self.assertRaises(UnicodeError):
                windows.load_measurement_window(
                    path, expected_run_id="run-001"
                )


class DeliveryEvidenceTests(unittest.TestCase):
    def validate(self, data):
        return windows.validate_delivery_summary(
            data,
            expected_run_id="run-001",
            expected_window_id="window-001",
        )

    def test_valid_delivery_returns_independent_copy(self):
        data = valid_delivery()
        original = copy.deepcopy(data)
        result = self.validate(data)
        self.assertEqual(result, original)
        result["delivered_packet_ids"].append("session1-p1")
        self.assertEqual(data, original)

    def test_empty_delivery_and_empty_workload_are_valid(self):
        data = valid_delivery()
        data["delivered_packet_ids"] = []
        self.validate(data)
        data["offered_packet_ids"] = []
        self.validate(data)

    def test_rejects_duplicates_and_packets_not_offered(self):
        cases = (
            ("offered_packet_ids", ["p1", "p1"]),
            ("delivered_packet_ids", ["session1-p2", "session1-p2"]),
            ("delivered_packet_ids", ["never-offered"]),
            ("offered_packet_ids", "p1"),
            ("delivered_packet_ids", [True]),
        )
        for field, value in cases:
            data = valid_delivery()
            data[field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    self.validate(data)

    def test_rejects_invalid_identity_version_and_hash(self):
        cases = (
            ("run_id", "different"),
            ("window_id", "different"),
            ("summary_version", True),
            ("summary_version", 2),
            ("sender_id", ""),
            ("receiver_id", "=unsafe"),
            ("evidence_sha256", "not-a-hash"),
        )
        for field, value in cases:
            data = valid_delivery()
            data[field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    self.validate(data)

    def test_requires_exact_schema(self):
        data = valid_delivery()
        data["unknown"] = 1
        with self.assertRaises(ValueError):
            self.validate(data)
        del data["unknown"]
        del data["sender_id"]
        with self.assertRaises(ValueError):
            self.validate(data)


if __name__ == "__main__":
    unittest.main()
