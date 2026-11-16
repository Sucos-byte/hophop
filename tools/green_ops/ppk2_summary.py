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
