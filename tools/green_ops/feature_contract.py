# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Explicit column roles and prediction-time inputs for dataset schema v1."""

import math

from dataset_builder import DATASET_FIELDS


FEATURE_CONTRACT_VERSION = 1

METADATA_IDENTIFIERS = frozenset({
    "dataset_version",
    "run_id",
    "adapter",
    "feature_profile_id",
    "source_kind",
    "execution_kind",
    "measurement_status",
    "seed",
    "repetition",
    "segment_count",
})

TARGET_COLUMNS = frozenset({
    "target_mean_power_mw",
    "target_total_energy_mj",
    "target_energy_per_delivered_packet_uj",
    "ping_rtt_latency_ms",
})

PREDICTION_TIME_FEATURES = frozenset({
    "payload_size_bytes",
    "interval_ms",
    "tx_power_dbm",
    "loss_model",
    "loss_preset",
    "loss_initial_state",
    "good_to_bad_probability",
    "bad_to_good_probability",
    "good_state_loss_probability",
    "bad_state_loss_probability",
    "rx_attempts",
    "delivered_packets",
    "sync_beacons",
    "tx_successes",
    "packet_delivery_ratio",
})

PRE_RUN_FEATURES = (
    "payload_size_bytes",
    "interval_ms",
    "tx_power_dbm",
)

POST_RUN_FEATURES = PRE_RUN_FEATURES + (
    "rx_attempts",
    "delivered_packets",
    "sync_beacons",
    "tx_successes",
    "packet_delivery_ratio",
)

_COUNTER_FIELDS = frozenset({
    "rx_attempts",
    "delivered_packets",
    "sync_beacons",
    "tx_successes",
})


def _validate_schema_version(schema_version):
    if type(schema_version) is not int or schema_version != 1:
        raise ValueError("unsupported dataset schema_version; expected integer 1")


def validate_feature_partition(fields, *, schema_version):
    """Require an exhaustive, disjoint classification of the v1 schema."""
    _validate_schema_version(schema_version)
    if not isinstance(fields, tuple):
        raise ValueError("schema fields must be a tuple")
    if any(not isinstance(field, str) for field in fields):
        raise ValueError("schema field names must be strings")
    if len(fields) != len(set(fields)):
        raise ValueError("schema contains duplicate fields")

    roles = (
        METADATA_IDENTIFIERS,
        PREDICTION_TIME_FEATURES,
        TARGET_COLUMNS,
    )
    for index, left in enumerate(roles):
        for right in roles[index + 1:]:
            if left & right:
                raise ValueError("feature roles overlap")

    classified = set().union(*roles)
    if set(fields) != classified:
        raise ValueError(
            "schema classification mismatch: "
            f"unclassified={sorted(set(fields) - classified)}, "
            f"missing={sorted(classified - set(fields))}"
        )


def select_feature_names(
    *, schema_version, prediction_mode, available_fields
):
    """Select a fixed feature profile, requiring every selected capability."""
    validate_feature_partition(DATASET_FIELDS, schema_version=schema_version)
    if not isinstance(prediction_mode, str) or prediction_mode not in {
        "pre_run", "post_run"
    }:
        raise ValueError("prediction_mode must be pre_run or post_run")
    if not isinstance(available_fields, frozenset):
        raise ValueError("available_fields must be a frozenset")
    if any(not isinstance(field, str) for field in available_fields):
        raise ValueError("available field names must be strings")
    unknown = available_fields - set(DATASET_FIELDS)
    if unknown:
        raise ValueError(f"unknown available fields: {sorted(unknown)}")

    selected = (
        PRE_RUN_FEATURES
        if prediction_mode == "pre_run"
        else POST_RUN_FEATURES
    )
    if set(selected) - PREDICTION_TIME_FEATURES:
        raise ValueError("selected profile contains a forbidden feature")
    missing = set(selected) - available_fields
    if missing:
        raise ValueError(f"unavailable required features: {sorted(missing)}")
    return selected


def _validate_feature_value(field, value):
    if type(value) not in {int, float}:
        raise ValueError(f"{field} must be a finite numeric value")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{field} must be a finite numeric value")

    if field in {"payload_size_bytes", "interval_ms"}:
        if type(value) is not int or value <= 0:
            raise ValueError(f"{field} must be a positive integer")
    elif field == "tx_power_dbm":
        if type(value) is not int:
            raise ValueError(f"{field} must be an integer")
    elif field in _COUNTER_FIELDS:
        if type(value) is not int or value < 0:
            raise ValueError(f"{field} must be a nonnegative integer")
    elif field == "packet_delivery_ratio":
        if not 0 <= value <= 1:
            raise ValueError(f"{field} must be between zero and one")


def extract_features(row, *, prediction_mode, available_fields):
    """Extract typed model inputs without mutating or imputing the row.

    This validates selected features, not the complete dataset artifact.
    Dataset provenance and counter consistency require the dataset validator.
    """
    if not isinstance(row, dict):
        raise ValueError("dataset row must be a dictionary")
    selected = select_feature_names(
        schema_version=row.get("dataset_version"),
        prediction_mode=prediction_mode,
        available_fields=available_fields,
    )
    result = {}
    for field in selected:
        value = row.get(field)
        _validate_feature_value(field, value)
        result[field] = value
    return result
