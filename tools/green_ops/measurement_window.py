# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Validate bounded observation windows and cumulative counter endpoints."""

import copy
import json
import math
from pathlib import Path
import re


_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_COUNTERS = (
    "rx_attempts",
    "rx_data_packets",
    "sync_beacons",
    "tx_successes",
)
_FIELDS = {
    "window_version", "run_id", "window_id", "clock_id",
    "start_us", "end_us", "window_duration_ms", "segment_id",
    "observed_segment_ids", "start_counters", "end_counters",
    "alignment", "evaluation_group_id",
}
_ALIGNMENT_FIELDS = {
    "method", "reference_artifact_sha256", "start_marker_id",
    "end_marker_id", "uncertainty_ms",
}


def _exact_fields(data, fields, name):
    if not isinstance(data, dict) or set(data) != fields:
        raise ValueError(f"{name} must contain exactly the documented fields")


def _identifier(value, field):
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"{field} must be a safe identifier of 1–64 characters")


def _integer(value, field):
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer")


def _number(value, field, *, positive=False):
    if type(value) not in {int, float}:
        raise ValueError(f"{field} must be a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite or value < 0 or (positive and value == 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{field} must be finite and {qualifier}")


def _validate_counters(counters, name):
    _exact_fields(counters, set(_COUNTERS), name)
    for field, value in counters.items():
        _integer(value, f"{name}.{field}")
        if value >= 2**32 - 1:
            raise ValueError(
                f"{name}.{field}: saturated or out-of-range counter"
            )


def validate_measurement_window(
    data, *, expected_run_id, max_window_duration_ms=3600000.0
):
    """Return an independent validated copy; raise ValueError on invalid input.

    Validation establishes internal consistency of the supplied summary.
    It cannot prove that markers or endpoint snapshots were physically captured.
    """
    _number(
        max_window_duration_ms, "max_window_duration_ms", positive=True
    )
    _identifier(expected_run_id, "expected_run_id")
    _exact_fields(data, _FIELDS, "measurement window")

    if type(data["window_version"]) is not int or data["window_version"] != 1:
        raise ValueError("window_version must be integer 1")

    for field in (
        "run_id", "window_id", "clock_id", "evaluation_group_id",
    ):
        _identifier(data[field], field)
    if data["run_id"] != expected_run_id:
        raise ValueError("measurement window run_id mismatch")

    for field in ("start_us", "end_us", "segment_id"):
        _integer(data[field], field)
    if data["end_us"] <= data["start_us"]:
        raise ValueError("end_us must be greater than start_us")

    duration = data["window_duration_ms"]
    _number(duration, "window_duration_ms", positive=True)
    try:
        elapsed_ms = (data["end_us"] - data["start_us"]) / 1000
    except OverflowError as error:
        raise ValueError("window timestamp interval is too large") from error

    if not math.isfinite(elapsed_ms) or elapsed_ms > max_window_duration_ms:
        raise ValueError("window exceeds max_window_duration_ms")
    if duration > max_window_duration_ms:
        raise ValueError("window_duration_ms exceeds configured maximum")
    if not math.isclose(duration, elapsed_ms, rel_tol=0.0, abs_tol=0.001):
        raise ValueError("window_duration_ms does not match timestamp interval")

    segments = data["observed_segment_ids"]
    if (
        not isinstance(segments, list)
        or len(segments) != 1
        or type(segments[0]) is not int
        or segments[0] != data["segment_id"]
    ):
        raise ValueError("window must contain exactly its declared segment")

    _validate_counters(data["start_counters"], "start_counters")
    _validate_counters(data["end_counters"], "end_counters")
    for field in _COUNTERS:
        if data["end_counters"][field] < data["start_counters"][field]:
            raise ValueError(f"{field}: counter reset or wrap within window")

    alignment = data["alignment"]
    _exact_fields(alignment, _ALIGNMENT_FIELDS, "alignment")
    method = alignment["method"]
    if not isinstance(method, str) or method not in {
        "synthetic_fixture", "gpio", "serial",
    }:
        raise ValueError("unsupported alignment method")
    digest = alignment["reference_artifact_sha256"]
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise ValueError("alignment reference must be a lowercase SHA-256")

    for field in ("start_marker_id", "end_marker_id"):
        _identifier(alignment[field], field)
    if alignment["start_marker_id"] == alignment["end_marker_id"]:
        raise ValueError("start and end marker IDs must differ")
    _number(alignment["uncertainty_ms"], "alignment.uncertainty_ms")

    return copy.deepcopy(data)


def compute_counter_deltas(window):
    """Subtract validated endpoints; never infer a zero baseline."""
    if not isinstance(window, dict):
        raise ValueError("measurement window must be a dictionary")
    validated = validate_measurement_window(
        window, expected_run_id=window.get("run_id")
    )
    return {
        field: (
            validated["end_counters"][field]
            - validated["start_counters"][field]
        )
        for field in _COUNTERS
    }


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"nonfinite JSON value: {value}")


def load_measurement_window(
    path, *, expected_run_id, max_window_duration_ms=3600000.0
):
    """Read strict UTF-8 JSON and return a validated independent object."""
    with Path(path).open(encoding="utf-8") as stream:
        data = json.load(
            stream,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    return validate_measurement_window(
        data,
        expected_run_id=expected_run_id,
        max_window_duration_ms=max_window_duration_ms,
    )


_DELIVERY_FIELDS = {
    "summary_version",
    "run_id",
    "window_id",
    "sender_id",
    "receiver_id",
    "offered_packet_ids",
    "delivered_packet_ids",
    "evidence_sha256",
}


def validate_delivery_summary(
    data, *, expected_run_id, expected_window_id
):
    """Validate unique logical packet delivery evidence.

    IDs must include session identity when summaries are constructed.
    A valid summary establishes internal consistency, not capture authenticity.
    """
    _identifier(expected_run_id, "expected_run_id")
    _identifier(expected_window_id, "expected_window_id")
    _exact_fields(data, _DELIVERY_FIELDS, "delivery summary")

    if (
        type(data["summary_version"]) is not int
        or data["summary_version"] != 1
    ):
        raise ValueError("summary_version must be integer 1")

    for field in ("run_id", "window_id", "sender_id", "receiver_id"):
        _identifier(data[field], field)

    if data["run_id"] != expected_run_id:
        raise ValueError("delivery summary run_id mismatch")
    if data["window_id"] != expected_window_id:
        raise ValueError("delivery summary window_id mismatch")

    packet_sets = {}
    for field in ("offered_packet_ids", "delivered_packet_ids"):
        identifiers = data[field]
        if not isinstance(identifiers, list):
            raise ValueError(f"{field} must be a list")
        for identifier in identifiers:
            _identifier(identifier, field)
        unique = set(identifiers)
        if len(unique) != len(identifiers):
            raise ValueError(f"{field} contains duplicate logical packet IDs")
        packet_sets[field] = unique

    if not packet_sets["delivered_packet_ids"].issubset(
        packet_sets["offered_packet_ids"]
    ):
        raise ValueError("delivered packets must be a subset of offered packets")

    digest = data["evidence_sha256"]
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise ValueError("evidence_sha256 must be a lowercase SHA-256")

    return copy.deepcopy(data)
