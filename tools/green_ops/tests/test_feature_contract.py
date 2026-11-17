# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dataset_builder import DATASET_FIELDS
import feature_contract as contract


class FeatureContractTests(unittest.TestCase):
    def test_roles_cover_schema_without_overlap(self):
        roles = (
            *contract.feature_roles(1),
        )
        self.assertEqual(set().union(*roles), set(DATASET_FIELDS))
        for index, left in enumerate(roles):
            for right in roles[index + 1:]:
                self.assertFalse(left & right)
        contract.validate_feature_partition(DATASET_FIELDS, schema_version=1)

    def test_energy_and_rtt_are_targets(self):
        self.assertEqual(contract.TARGET_COLUMNS, frozenset({
            "target_mean_power_mw",
            "target_total_energy_mj",
            "target_energy_per_delivered_packet_uj",
            "ping_rtt_latency_ms",
        }))

    def test_schema_changes_require_explicit_classification(self):
        invalid_schemas = (
            DATASET_FIELDS + ("new_unclassified_field",),
            DATASET_FIELDS + (DATASET_FIELDS[0],),
            DATASET_FIELDS[:-1],
        )
        for fields in invalid_schemas:
            with self.subTest(fields=fields):
                with self.assertRaises(ValueError):
                    contract.validate_feature_partition(
                        fields, schema_version=1
                    )

    def test_pre_run_selection_excludes_observed_outcomes(self):
        selected = contract.select_feature_names(
            schema_version=1,
            prediction_mode="pre_run",
            available_fields=frozenset(DATASET_FIELDS),
        )
        self.assertEqual(selected, (
            "payload_size_bytes", "interval_ms", "tx_power_dbm",
        ))
        self.assertFalse(set(selected) & contract.TARGET_COLUMNS)
        self.assertFalse(set(selected) & contract.METADATA_IDENTIFIERS)

    def test_post_run_selection_adds_explicit_diagnostics(self):
        selected = contract.select_feature_names(
            schema_version=1,
            prediction_mode="post_run",
            available_fields=frozenset(DATASET_FIELDS),
        )
        self.assertEqual(selected, (
            "payload_size_bytes", "interval_ms", "tx_power_dbm",
            "rx_attempts", "delivered_packets", "sync_beacons",
            "tx_successes", "packet_delivery_ratio",
        ))
        self.assertFalse(set(selected) & contract.TARGET_COLUMNS)
        self.assertFalse(set(selected) & contract.METADATA_IDENTIFIERS)

    def test_missing_capability_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "tx_power_dbm"):
            contract.select_feature_names(
                schema_version=1,
                prediction_mode="pre_run",
                available_fields=frozenset({"payload_size_bytes", "interval_ms"}),
            )

    def test_invalid_version_or_mode_is_rejected(self):
        for version, mode in (
            (99, "pre_run"), (True, "pre_run"), (1, "unknown"),
        ):
            with self.subTest(version=version, mode=mode):
                with self.assertRaises(ValueError):
                    contract.select_feature_names(
                        schema_version=version,
                        prediction_mode=mode,
                        available_fields=frozenset(DATASET_FIELDS),
                    )

    def test_extracts_only_selected_features_without_mutation(self):
        row = dict.fromkeys(DATASET_FIELDS)
        row.update({
            "dataset_version": 1,
            "run_id": "example-001",
            "payload_size_bytes": 32,
            "interval_ms": 1000,
            "tx_power_dbm": -10,
            "target_total_energy_mj": 99.0,
            "ping_rtt_latency_ms": 12.0,
        })
        original = row.copy()
        result = contract.extract_features(
            row,
            prediction_mode="pre_run",
            available_fields=frozenset(DATASET_FIELDS),
        )
        self.assertEqual(result, {
            "payload_size_bytes": 32,
            "interval_ms": 1000,
            "tx_power_dbm": -10,
        })
        self.assertEqual(row, original)

    def test_missing_or_invalid_selected_value_is_rejected(self):
        for value in (None, True, float("nan"), float("inf"), "32"):
            row = dict.fromkeys(DATASET_FIELDS)
            row.update({
                "dataset_version": 1,
                "payload_size_bytes": value,
                "interval_ms": 1000,
                "tx_power_dbm": 0,
            })
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "payload_size_bytes"):
                    contract.extract_features(
                        row,
                        prediction_mode="pre_run",
                        available_fields=frozenset(DATASET_FIELDS),
                    )


if __name__ == "__main__":
    unittest.main()


class FeatureBoundaryTests(unittest.TestCase):
    def valid_row(self):
        row = dict.fromkeys(DATASET_FIELDS)
        row.update({
            "dataset_version": 1,
            "payload_size_bytes": 32,
            "interval_ms": 1000,
            "tx_power_dbm": -10,
            "rx_attempts": 5,
            "delivered_packets": 4,
            "sync_beacons": 0,
            "tx_successes": 2,
            "packet_delivery_ratio": 0.8,
        })
        return row

    def extract(self, row):
        return contract.extract_features(
            row,
            prediction_mode="post_run",
            available_fields=frozenset(DATASET_FIELDS),
        )

    def test_rejects_invalid_selected_numeric_values(self):
        for field in contract.select_feature_names(
            schema_version=1, prediction_mode="post_run",
            available_fields=frozenset(DATASET_FIELDS),
        ):
            for value in (None, True, "1", float("nan"), float("inf")):
                with self.subTest(field=field, value=value):
                    row = self.valid_row()
                    row[field] = value
                    with self.assertRaisesRegex(ValueError, field):
                        self.extract(row)

    def test_rejects_out_of_domain_values(self):
        invalid = {
            "payload_size_bytes": (0, -1, 1.5),
            "interval_ms": (0, -1, 1.5),
            "tx_power_dbm": (1.5,),
            "rx_attempts": (-1, 1.5),
            "delivered_packets": (-1, 1.5),
            "sync_beacons": (-1, 1.5),
            "tx_successes": (-1, 1.5),
            "packet_delivery_ratio": (-0.01, 1.01),
        }
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    row = self.valid_row()
                    row[field] = value
                    with self.assertRaisesRegex(ValueError, field):
                        self.extract(row)

    def test_accepts_zero_counters_and_ratio_boundaries(self):
        for ratio in (0.0, 1.0):
            row = self.valid_row()
            for field in (
                "rx_attempts", "delivered_packets",
                "sync_beacons", "tx_successes",
            ):
                row[field] = 0
            row["packet_delivery_ratio"] = ratio
            self.assertEqual(
                self.extract(row)["packet_delivery_ratio"], ratio
            )

    def test_rejects_unknown_or_invalid_capability_declarations(self):
        for available in (
            frozenset(DATASET_FIELDS) | {"unknown_feature"},
            frozenset({1}),
            set(DATASET_FIELDS),
        ):
            with self.subTest(available=available):
                with self.assertRaises(ValueError):
                    contract.select_feature_names(
                        schema_version=1,
                        prediction_mode="pre_run",
                        available_fields=available,
                    )

    def test_missing_selected_column_is_rejected(self):
        row = self.valid_row()
        del row["tx_power_dbm"]
        with self.assertRaisesRegex(ValueError, "tx_power_dbm"):
            self.extract(row)
