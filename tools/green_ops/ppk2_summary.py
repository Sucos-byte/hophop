# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Validate measured Nordic PPK2 summaries for Green-Ops dataset targets."""

import json
import math
from pathlib import Path
import re


IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
FIELDS = {
    "summary_version",
    "run_id",
    "instrument",
    "target_mean_power_mw",
    "target_total_energy_mj",
}


def _identifier(value, field):
    if not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None:
        raise ValueError(
            f"{field} must be a safe ASCII identifier of 1–64 characters"
        )


def _positive_finite_number(value, field):
    if type(value) not in {int, float} or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{field} must be a finite positive number")


def validate_ppk2_summary(data, *, expected_run_id=None):
    """Raise ValueError for invalid PPK2 metadata; leave valid input unchanged."""
    if not isinstance(data, dict) or set(data) != FIELDS:
        raise ValueError("PPK2 summary must contain exactly the documented fields")
    if type(data["summary_version"]) is not int or data["summary_version"] != 1:
        raise ValueError("summary_version must be integer 1")

    _identifier(data["run_id"], "run_id")
    if data["instrument"] != "nordic-ppk2":
        raise ValueError("instrument must be nordic-ppk2")

    for field in ("target_mean_power_mw", "target_total_energy_mj"):
        _positive_finite_number(data[field], field)

    if expected_run_id is not None:
        _identifier(expected_run_id, "expected_run_id")
        if data["run_id"] != expected_run_id:
            raise ValueError("PPK2 summary run_id does not match expected run_id")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"nonfinite JSON value: {value}")


def load_ppk2_summary(path, *, expected_run_id=None):
    """Read strict UTF-8 JSON and return a validated PPK2 summary."""
    with Path(path).open(encoding="utf-8") as stream:
        data = json.load(
            stream,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    validate_ppk2_summary(data, expected_run_id=expected_run_id)
    return data


_V2_FIELDS = {
    "summary_version",
    "run_id",
    "instrument",
    "target_mean_power_mw",
    "target_total_energy_mj",
    "window_id",
    "window_duration_ms",
    "voltage_v",
    "raw_capture_sha256",
    "alignment_reference_sha256",
}


def _v2_finite_number(value, field, *, positive=False):
    if type(value) not in {int, float}:
        raise ValueError(f"{field} must be a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite or value < 0 or (positive and value == 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{field} must be finite and {qualifier}")


def validate_ppk2_summary_v2(
    data,
    *,
    expected_run_id,
    window,
    duration_tolerance_ms=1.0,
    duration_tolerance_fraction=0.001,
    max_alignment_uncertainty_ms=1.0,
    energy_tolerance_mj=0.001,
    energy_tolerance_fraction=0.001,
):
    """Return a validated independent copy of a bounded PPK2 summary.

    Checks summary consistency and declared alignment, not physical authenticity.
    Tolerances are engineering policy settings, not instrument specifications.
    """
    import copy
    from measurement_window import validate_measurement_window

    policies = {
        "duration_tolerance_ms": duration_tolerance_ms,
        "duration_tolerance_fraction": duration_tolerance_fraction,
        "max_alignment_uncertainty_ms": max_alignment_uncertainty_ms,
        "energy_tolerance_mj": energy_tolerance_mj,
        "energy_tolerance_fraction": energy_tolerance_fraction,
    }
    for field, value in policies.items():
        _v2_finite_number(value, field)
    for field in (
        "duration_tolerance_fraction", "energy_tolerance_fraction",
    ):
        if policies[field] > 1:
            raise ValueError(f"{field} must not exceed one")

    validated_window = validate_measurement_window(
        window, expected_run_id=expected_run_id
    )
    if not isinstance(data, dict) or set(data) != _V2_FIELDS:
        raise ValueError("PPK2 v2 summary must contain exactly the documented fields")
    if type(data["summary_version"]) is not int or data["summary_version"] != 2:
        raise ValueError("bounded measurement requires summary_version integer 2")

    for field in ("run_id", "window_id"):
        _identifier(data[field], field)
    if data["run_id"] != expected_run_id:
        raise ValueError("PPK2 summary run_id mismatch")
    if data["window_id"] != validated_window["window_id"]:
        raise ValueError("PPK2 summary window_id mismatch")
    if data["instrument"] != "nordic-ppk2":
        raise ValueError("instrument must be nordic-ppk2")

    for field in (
        "target_mean_power_mw", "target_total_energy_mj",
        "window_duration_ms", "voltage_v",
    ):
        _v2_finite_number(data[field], field, positive=True)

    for field in ("raw_capture_sha256", "alignment_reference_sha256"):
        value = data[field]
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError(f"{field} must be a lowercase SHA-256")

    alignment = validated_window["alignment"]
    if alignment["method"] not in {"gpio", "serial"}:
        raise ValueError("PPK2 measurement requires physical alignment evidence")
    if alignment["uncertainty_ms"] > max_alignment_uncertainty_ms:
        raise ValueError("alignment uncertainty exceeds policy")
    if (
        data["alignment_reference_sha256"]
        != alignment["reference_artifact_sha256"]
    ):
        raise ValueError("PPK2 alignment reference mismatch")

    expected_duration = validated_window["window_duration_ms"]
    permitted_duration_difference = max(
        duration_tolerance_ms,
        duration_tolerance_fraction * expected_duration,
    )
    if (
        abs(data["window_duration_ms"] - expected_duration)
        > permitted_duration_difference
    ):
        raise ValueError("PPK2 duration does not match measurement window")

    try:
        expected_energy = (
            data["target_mean_power_mw"]
            * (data["window_duration_ms"] / 1000.0)
        )
    except OverflowError as error:
        raise ValueError("derived energy is outside numeric range") from error
    _v2_finite_number(expected_energy, "derived energy", positive=True)

    permitted_energy_difference = max(
        energy_tolerance_mj,
        energy_tolerance_fraction * expected_energy,
    )
    if (
        abs(data["target_total_energy_mj"] - expected_energy)
        > permitted_energy_difference
    ):
        raise ValueError("PPK2 energy is inconsistent with mean power and duration")

    return copy.deepcopy(data)
