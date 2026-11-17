# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Explicit column roles and prediction-time inputs for dataset schemas v1/v2."""

import math

from dataset_builder import DATASET_FIELDS, DATASET_FIELDS_V2


FEATURE_CONTRACT_VERSION = 3

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


# Preserve legacy profiles explicitly while publishing v2 defaults.
_V1_METADATA = METADATA_IDENTIFIERS
_V1_PREDICTION = PREDICTION_TIME_FEATURES
_V1_PRE = PRE_RUN_FEATURES
_V1_POST = POST_RUN_FEATURES
METADATA_IDENTIFIERS = _V1_METADATA | {
    "delivery_status", "evaluation_group_id", "analytical_model_id",
}
PREDICTION_TIME_FEATURES = (_V1_PREDICTION - {"rx_attempts"}) | {
    "rx_operations", "rx_decoded_packets", "rx_decode_per_operation_ratio",
    "window_duration_ms", "offered_packets",
}
PRE_RUN_FEATURES = _V1_PRE + ("window_duration_ms",)
POST_RUN_FEATURES = PRE_RUN_FEATURES + (
    "rx_operations", "rx_decoded_packets", "sync_beacons", "tx_successes",
    "rx_decode_per_operation_ratio", "offered_packets", "delivered_packets",
    "packet_delivery_ratio",
)
_COUNTER_FIELDS = _COUNTER_FIELDS | {
    "rx_operations", "rx_decoded_packets", "offered_packets",
}


def feature_roles(schema_version):
    _validate_schema_version(schema_version)
    if schema_version == 1:
        return _V1_METADATA, _V1_PREDICTION, TARGET_COLUMNS
    return METADATA_IDENTIFIERS, PREDICTION_TIME_FEATURES, TARGET_COLUMNS


def _validate_schema_version(schema_version):
    if type(schema_version) is not int or schema_version not in {1, 2}:
        raise ValueError("unsupported dataset schema_version; expected integer 1 or 2")


def validate_feature_partition(fields, *, schema_version):
    """Require an exhaustive, disjoint classification of the selected schema."""
    _validate_schema_version(schema_version)
    if not isinstance(fields, tuple):
        raise ValueError("schema fields must be a tuple")
    if any(not isinstance(field, str) for field in fields):
        raise ValueError("schema field names must be strings")
    if len(fields) != len(set(fields)):
        raise ValueError("schema contains duplicate fields")

    roles = feature_roles(schema_version)
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
    _validate_schema_version(schema_version)
    fields = DATASET_FIELDS if schema_version == 1 else DATASET_FIELDS_V2
    validate_feature_partition(fields, schema_version=schema_version)
    if not isinstance(prediction_mode, str) or prediction_mode not in {
        "pre_run", "post_run"
    }:
        raise ValueError("prediction_mode must be pre_run or post_run")
    if not isinstance(available_fields, frozenset):
        raise ValueError("available_fields must be a frozenset")
    if any(not isinstance(field, str) for field in available_fields):
        raise ValueError("available field names must be strings")
    unknown = available_fields - set(fields)
    if unknown:
        raise ValueError(f"unknown available fields: {sorted(unknown)}")

    pre, post = ((_V1_PRE, _V1_POST) if schema_version == 1
                 else (PRE_RUN_FEATURES, POST_RUN_FEATURES))
    selected = (
        pre
        if prediction_mode == "pre_run"
        else post
    )
    if set(selected) - feature_roles(schema_version)[1]:
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
    elif field == "window_duration_ms":
        if value <= 0:
            raise ValueError(f"{field} must be positive")
    elif field in {"packet_delivery_ratio", "rx_decode_per_operation_ratio"}:
        if not 0 <= value <= 1:
            raise ValueError(f"{field} must be between zero and one")


def extract_features(row, *, prediction_mode, available_fields, prediction_context=None):
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
    if row["dataset_version"] == 2 and prediction_mode == "pre_run":
        validate_pre_run_context(row, prediction_context)
    result = {}
    for field in selected:
        value = row.get(field)
        _validate_feature_value(field, value)
        result[field] = value
    return result


def validate_pre_run_context(row, context):
    """Require explicit completion of the predeclared fixed-duration workload."""
    if not isinstance(context, dict) or set(context) != {
        "planned_window_duration_ms", "completed_as_planned",
    }:
        raise ValueError("v2 pre_run requires an explicit prediction context")
    if type(context["completed_as_planned"]) is not bool or not context["completed_as_planned"]:
        raise ValueError("pre_run requires a workload completed as planned")
    planned = context["planned_window_duration_ms"]
    _validate_feature_value("window_duration_ms", planned)
    _validate_feature_value("window_duration_ms", row.get("window_duration_ms"))
    if not math.isclose(planned, row["window_duration_ms"], rel_tol=0.0, abs_tol=0.001):
        raise ValueError("observed duration does not match planned fixed duration")


def describe_prediction_context(row, context):
    """Validate a manifest capability declaration; never infer it from a header."""
    if context is None:
        return [], {"pre_run": None, "post_run": None}, None
    if not isinstance(context, dict) or set(context) != {
        "available_fields", "planned_window_duration_ms", "completed_as_planned",
    }:
        raise ValueError("prediction context must contain exactly the documented fields")
    fields = context["available_fields"]
    if (not isinstance(fields, list) or any(not isinstance(f, str) for f in fields)
            or len(set(fields)) != len(fields) or set(fields) - PREDICTION_TIME_FEATURES):
        raise ValueError("prediction context requires unique prediction feature capabilities")
    if type(context["completed_as_planned"]) is not bool:
        raise ValueError("completed_as_planned must be boolean")
    planned = context["planned_window_duration_ms"]
    if planned is not None:
        _validate_feature_value("window_duration_ms", planned)
    if context["completed_as_planned"] and planned is None:
        raise ValueError("completed workload requires planned_window_duration_ms")
    for field in fields:
        if row.get(field) is None:
            raise ValueError(f"declared capability {field} is null")
    extraction_context = {key: context[key] for key in (
        "planned_window_duration_ms", "completed_as_planned",
    )}
    selected = {}
    for mode in ("pre_run", "post_run"):
        try:
            names = select_feature_names(schema_version=2, prediction_mode=mode,
                                         available_fields=frozenset(fields))
        except ValueError:
            selected[mode] = None
            continue
        if mode == "pre_run":
            try:
                validate_pre_run_context(row, extraction_context)
            except ValueError:
                selected[mode] = None
                continue
        extract_features(row, prediction_mode=mode, available_fields=frozenset(fields),
                         prediction_context=extraction_context)
        selected[mode] = list(names)
    normalized = {**context, "available_fields": sorted(fields)}
    return sorted(fields), selected, normalized
