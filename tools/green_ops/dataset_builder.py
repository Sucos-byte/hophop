# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Build platform-independent Green-Ops dataset features from run artifacts."""

import csv
import json
import math
from pathlib import Path
import re

from channel_loss import PROBABILITY_FIELDS, validate_loss_scenario
from converter import CSV_FIELDS, RUN_ID_PATTERN
from ppk2_summary import load_ppk2_summary, validate_ppk2_summary
from run_metadata import load_run_metadata, validate_run_metadata


COUNTER_COLUMNS = (
    "rx_attempts",
    "rx_data_packets",
    "sync_beacons",
    "tx_successes",
)
EVENTS = {"rx_data", "sync_beacon", "tx_success"}
DATASET_FIELDS = (
    "dataset_version",
    "run_id",
    "adapter",
    "feature_profile_id",
    "source_kind",
    "execution_kind",
    "measurement_status",
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
    "seed",
    "repetition",
    "segment_count",
    "rx_attempts",
    "delivered_packets",
    "sync_beacons",
    "tx_successes",
    "packet_delivery_ratio",
    "ping_rtt_latency_ms",
    "target_mean_power_mw",
    "target_total_energy_mj",
    "target_energy_per_delivered_packet_uj",
)
TELEMETRY_FIELDS = {
    "run_id",
    "source_kind",
    "segment_count",
    "rx_attempts",
    "delivered_packets",
    "sync_beacons",
    "tx_successes",
    "packet_delivery_ratio",
    "ping_rtt_latency_ms",
}
EXPERIMENT_FIELDS = {
    "run_id",
    "adapter_id",
    "feature_profile_id",
    "execution_kind",
    "state",
    "requested_settings",
}
SETTING_FIELDS = {
    "payload_size_bytes",
    "interval_ms",
    "tx_power_dbm",
    "loss_scenario",
    "seed",
    "repetition",
}
PLAN_FIELDS = {
    "plan_version",
    "plan_id",
    "adapter_id",
    "feature_profile_id",
    "execution_kind",
    "configuration_sha256",
    "experiments",
}
PLAN_EXPERIMENT_FIELDS = {"run_id", "state", "requested_settings"}
SHA256 = re.compile(r"[0-9a-f]{64}")


def _nonnegative_integer(value, field):
    if type(value) is int:
        result = value
    elif isinstance(value, str) and value.isascii() and value.isdecimal():
        result = int(value)
    else:
        raise ValueError(f"{field} must be a non-negative integer")
    if result < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return result


def _optional_counter(value, field):
    if value == "" or value is None:
        return None
    return _nonnegative_integer(value, field)


def aggregate_telemetry(rows):
    """Aggregate cumulative event counters without crossing segment boundaries."""
    run_id = None
    source_kind = None
    segments = {}
    row_count = 0

    for row in rows:
        row_count += 1
        if not isinstance(row, dict) or set(row) != set(CSV_FIELDS):
            raise ValueError("telemetry rows must contain exactly the event CSV fields")

        current_run_id = row["run_id"]
        if (
            not isinstance(current_run_id, str)
            or RUN_ID_PATTERN.fullmatch(current_run_id) is None
        ):
            raise ValueError("telemetry run_id is invalid")
        if run_id is None:
            run_id = current_run_id
        elif current_run_id != run_id:
            raise ValueError("telemetry rows contain multiple run_id values")

        current_source_kind = row["source_kind"]
        if current_source_kind not in {"synthetic", "hardware"}:
            raise ValueError("telemetry source_kind must be synthetic or hardware")
        if source_kind is None:
            source_kind = current_source_kind
        elif current_source_kind != source_kind:
            raise ValueError("telemetry rows contain multiple source_kind values")

        if row["event"] not in EVENTS:
            raise ValueError("telemetry event is invalid")
        segment_id = _nonnegative_integer(row["segment_id"], "segment_id")
        segment = segments.setdefault(
            segment_id,
            {column: 0 for column in COUNTER_COLUMNS},
        )
        for column in COUNTER_COLUMNS:
            counter = _optional_counter(row[column], column)
            if counter is not None:
                segment[column] = max(segment[column], counter)

    if row_count == 0:
        raise ValueError("telemetry input is empty")

    for segment_id, segment in segments.items():
        if segment["rx_data_packets"] > segment["rx_attempts"]:
            raise ValueError(
                f"segment {segment_id}: delivered packets exceed receive attempts"
            )

    totals = {
        column: sum(segment[column] for segment in segments.values())
        for column in COUNTER_COLUMNS
    }
    attempts = totals["rx_attempts"]
    delivered = totals["rx_data_packets"]

    return {
        "run_id": run_id,
        "source_kind": source_kind,
        "segment_count": len(segments),
        "rx_attempts": attempts,
        "delivered_packets": delivered,
        "sync_beacons": totals["sync_beacons"],
        "tx_successes": totals["tx_successes"],
        "packet_delivery_ratio": delivered / attempts if attempts else None,
        "ping_rtt_latency_ms": None,
    }


def _strict_integer(value, field, *, minimum=None):
    if type(value) is not int or (minimum is not None and value < minimum):
        suffix = f" at least {minimum}" if minimum is not None else ""
        raise ValueError(f"{field} must be an integer{suffix}")


def _optional_nonnegative_number(value, field):
    if value is None:
        return
    if (
        type(value) not in {int, float}
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError(f"{field} must be null or a finite non-negative number")


def _validate_aggregated_telemetry(telemetry):
    if not isinstance(telemetry, dict) or set(telemetry) != TELEMETRY_FIELDS:
        raise ValueError("aggregated telemetry must contain exactly the documented fields")
    if (
        not isinstance(telemetry["run_id"], str)
        or RUN_ID_PATTERN.fullmatch(telemetry["run_id"]) is None
    ):
        raise ValueError("aggregated telemetry run_id is invalid")
    if telemetry["source_kind"] not in {"synthetic", "hardware"}:
        raise ValueError("aggregated telemetry source_kind is invalid")
    _strict_integer(telemetry["segment_count"], "segment_count", minimum=1)
    for field in (
        "rx_attempts",
        "delivered_packets",
        "sync_beacons",
        "tx_successes",
    ):
        _strict_integer(telemetry[field], field, minimum=0)
    if telemetry["delivered_packets"] > telemetry["rx_attempts"]:
        raise ValueError("delivered packets exceed receive attempts")

    expected_ratio = (
        telemetry["delivered_packets"] / telemetry["rx_attempts"]
        if telemetry["rx_attempts"]
        else None
    )
    if telemetry["packet_delivery_ratio"] != expected_ratio:
        raise ValueError("packet_delivery_ratio does not match telemetry counters")
    _optional_nonnegative_number(
        telemetry["ping_rtt_latency_ms"], "ping_rtt_latency_ms"
    )


def _validate_experiment(experiment, metadata):
    if not isinstance(experiment, dict) or set(experiment) != EXPERIMENT_FIELDS:
        raise ValueError("experiment must contain exactly the documented fields")
    for field in ("run_id", "adapter_id", "feature_profile_id", "execution_kind"):
        metadata_field = "run_id" if field == "run_id" else field
        if experiment[field] != metadata[metadata_field]:
            raise ValueError(f"experiment {field} does not match run metadata")
    if experiment["state"] != "planned":
        raise ValueError("experiment state must be planned")

    settings = experiment["requested_settings"]
    if not isinstance(settings, dict) or set(settings) != SETTING_FIELDS:
        raise ValueError("requested_settings must contain exactly the documented fields")
    _strict_integer(settings["payload_size_bytes"], "payload_size_bytes", minimum=1)
    _strict_integer(settings["interval_ms"], "interval_ms", minimum=1)
    _strict_integer(settings["tx_power_dbm"], "tx_power_dbm")
    _strict_integer(settings["seed"], "seed", minimum=0)
    _strict_integer(settings["repetition"], "repetition", minimum=1)
    validate_loss_scenario(settings["loss_scenario"])


def build_dataset_row(run_metadata, telemetry, experiment=None, ppk2_summary=None):
    """Join validated artifacts into one platform-independent dataset row."""
    validate_run_metadata(run_metadata)
    _validate_aggregated_telemetry(telemetry)
    if telemetry["run_id"] != run_metadata["run_id"]:
        raise ValueError("telemetry run_id does not match run metadata")

    execution_kind = run_metadata["execution_kind"]
    expected_source_kind = "hardware" if execution_kind == "hardware" else "synthetic"
    if telemetry["source_kind"] != expected_source_kind:
        raise ValueError("telemetry source_kind does not match execution_kind")

    if experiment is not None:
        _validate_experiment(experiment, run_metadata)

    power_provenance = run_metadata["target_provenance"]["target_power_draw_mw"]
    if ppk2_summary is None and power_provenance == "measured":
        raise ValueError("measured power provenance requires a PPK2 summary")
    if ppk2_summary is not None:
        validate_ppk2_summary(
            ppk2_summary,
            expected_run_id=run_metadata["run_id"],
        )
        if execution_kind != "hardware" or telemetry["source_kind"] != "hardware":
            raise ValueError("PPK2 measurements require hardware artifacts")
        if power_provenance != "measured":
            raise ValueError("PPK2 measurements require measured power provenance")

    row = dict.fromkeys(DATASET_FIELDS)
    row.update({
        "dataset_version": 1,
        "run_id": run_metadata["run_id"],
        "adapter": run_metadata["adapter_id"],
        "feature_profile_id": run_metadata["feature_profile_id"],
        "source_kind": telemetry["source_kind"],
        "execution_kind": execution_kind,
        "measurement_status": "measured" if ppk2_summary is not None else "unmeasured",
        "segment_count": telemetry["segment_count"],
        "rx_attempts": telemetry["rx_attempts"],
        "delivered_packets": telemetry["delivered_packets"],
        "sync_beacons": telemetry["sync_beacons"],
        "tx_successes": telemetry["tx_successes"],
        "packet_delivery_ratio": telemetry["packet_delivery_ratio"],
        "ping_rtt_latency_ms": telemetry["ping_rtt_latency_ms"],
    })

    if experiment is not None:
        settings = experiment["requested_settings"]
        scenario = settings["loss_scenario"]
        row.update({
            "payload_size_bytes": settings["payload_size_bytes"],
            "interval_ms": settings["interval_ms"],
            "tx_power_dbm": settings["tx_power_dbm"],
            "loss_model": scenario["model"],
            "loss_preset": scenario["preset"],
            "loss_initial_state": scenario["initial_state"],
            "seed": settings["seed"],
            "repetition": settings["repetition"],
        })
        for field in PROBABILITY_FIELDS:
            row[field] = scenario[field]

    if ppk2_summary is not None:
        total_energy_mj = ppk2_summary["target_total_energy_mj"]
        delivered = telemetry["delivered_packets"]
        row.update({
            "target_mean_power_mw": ppk2_summary["target_mean_power_mw"],
            "target_total_energy_mj": total_energy_mj,
            "target_energy_per_delivered_packet_uj": (
                total_energy_mj * 1000 / delivered if delivered else None
            ),
        })

    return row


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"nonfinite JSON value: {value}")


def _load_json_object(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(
            stream,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )


def _load_telemetry_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != CSV_FIELDS:
            raise ValueError("telemetry CSV header does not match the event schema")
        return aggregate_telemetry(reader)


def _select_experiment(plan, metadata):
    if not isinstance(plan, dict) or set(plan) != PLAN_FIELDS:
        raise ValueError("experiment plan must contain exactly the documented fields")
    if type(plan["plan_version"]) is not int or plan["plan_version"] != 2:
        raise ValueError("plan_version must be integer 2")
    for field in ("plan_id", "adapter_id", "feature_profile_id"):
        value = plan[field]
        if not isinstance(value, str) or RUN_ID_PATTERN.fullmatch(value) is None:
            raise ValueError(f"plan {field} is invalid")
    if plan["execution_kind"] not in {"synthetic", "simulation", "hardware"}:
        raise ValueError("plan execution_kind is invalid")
    if (
        not isinstance(plan["configuration_sha256"], str)
        or SHA256.fullmatch(plan["configuration_sha256"]) is None
    ):
        raise ValueError("configuration_sha256 must be 64 lowercase hexadecimal digits")
    if not isinstance(plan["experiments"], list):
        raise ValueError("plan experiments must be a list")

    matches = []
    for entry in plan["experiments"]:
        if not isinstance(entry, dict) or set(entry) != PLAN_EXPERIMENT_FIELDS:
            raise ValueError("plan experiment must contain exactly the documented fields")
        entry_run_id = entry["run_id"]
        if (
            not isinstance(entry_run_id, str)
            or RUN_ID_PATTERN.fullmatch(entry_run_id) is None
        ):
            raise ValueError("plan experiment run_id is invalid")
        if entry_run_id == metadata["run_id"]:
            matches.append(entry)
    if len(matches) != 1:
        raise ValueError("plan must contain exactly one experiment matching run_id")

    selected = matches[0]
    return {
        "run_id": selected["run_id"],
        "adapter_id": plan["adapter_id"],
        "feature_profile_id": plan["feature_profile_id"],
        "execution_kind": plan["execution_kind"],
        "state": selected["state"],
        "requested_settings": selected["requested_settings"],
    }


def build_dataset_row_from_files(
    telemetry_csv,
    run_metadata_json,
    experiment_plan_json=None,
    ppk2_summary_json=None,
):
    """Load strict run artifacts and return one validated dataset row."""
    metadata = load_run_metadata(run_metadata_json)
    telemetry = _load_telemetry_csv(telemetry_csv)
    experiment = None
    if experiment_plan_json is not None:
        experiment = _select_experiment(
            _load_json_object(experiment_plan_json),
            metadata,
        )
    energy = None
    if ppk2_summary_json is not None:
        energy = load_ppk2_summary(
            ppk2_summary_json,
            expected_run_id=metadata["run_id"],
        )
    return build_dataset_row(metadata, telemetry, experiment, energy)
