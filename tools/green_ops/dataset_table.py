# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Strict v2 artifact loading and deterministic provenance-filtered tables."""

import copy
import csv
import hashlib
import math
from pathlib import Path
import re

from dataset_builder import DATASET_FIELDS_V2, _load_json_object
from feature_contract import FEATURE_CONTRACT_VERSION, TARGET_COLUMNS

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_HASH = re.compile(r"[0-9a-f]{64}")
INTEGER_FIELDS = frozenset({
    "dataset_version", "payload_size_bytes", "interval_ms", "tx_power_dbm",
    "seed", "repetition", "segment_count", "rx_operations", "rx_decoded_packets",
    "sync_beacons", "tx_successes", "offered_packets", "delivered_packets",
})
NUMBER_FIELDS = TARGET_COLUMNS | {
    "window_duration_ms", "rx_decode_per_operation_ratio", "packet_delivery_ratio",
    "good_to_bad_probability", "bad_to_good_probability",
    "good_state_loss_probability", "bad_state_loss_probability",
}
OPTIONAL = frozenset({
    "payload_size_bytes", "interval_ms", "tx_power_dbm", "loss_model", "loss_preset",
    "loss_initial_state", "seed", "repetition", "offered_packets", "delivered_packets",
    "analytical_model_id", "rx_decode_per_operation_ratio", "packet_delivery_ratio",
}) | NUMBER_FIELDS - {"window_duration_ms"}
PROVENANCE = {
    ("synthetic", "synthetic", "unmeasured"),
    ("synthetic", "simulation", "unmeasured"),
    ("hardware", "hardware", "unmeasured"),
    ("synthetic", "simulation", "analytical_simulation"),
    ("hardware", "hardware", "measured"),
}
IDENTITIES = ("run_id", "adapter", "feature_profile_id", "evaluation_group_id")
MANIFEST_IDENTITIES = IDENTITIES + (
    "source_kind", "execution_kind", "measurement_status", "analytical_model_id",
)


def _finite(value, name):
    try:
        valid = type(value) in {int, float} and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{name} must be a finite number")


def _ratio(row, numerator, denominator, field):
    expected = row[numerator] / row[denominator] if row[denominator] else None
    if row[field] != expected:
        raise ValueError(f"{field} inconsistent with counts")


def validate_dataset_row(row, *, schema_version):
    """Validate exact types, derived values and declared provenance; copy input."""
    if type(schema_version) is not int or schema_version != 2:
        raise ValueError("tables require dataset v2; regenerate v1 from source artifacts")
    if not isinstance(row, dict) or set(row) != set(DATASET_FIELDS_V2):
        raise ValueError("dataset row must contain exactly the v2 fields")
    for field, value in row.items():
        if value is None:
            if field not in OPTIONAL:
                raise ValueError(f"{field} is required")
            continue
        if field in INTEGER_FIELDS:
            if type(value) is not int:
                raise ValueError(f"{field} must be an exact integer")
            if field != "tx_power_dbm" and value < 0:
                raise ValueError(f"{field} must be nonnegative")
        elif field in NUMBER_FIELDS:
            _finite(value, field)
            if value < 0:
                raise ValueError(f"{field} must be nonnegative")
        elif not isinstance(value, str) or not value:
            raise ValueError(f"{field} must be a nonempty string")
    if row["dataset_version"] != 2:
        raise ValueError("row dataset_version must be 2")
    for field in IDENTITIES + ("analytical_model_id",):
        if row[field] is not None and _ID.fullmatch(row[field]) is None:
            raise ValueError(f"invalid {field}")
    for field in ("payload_size_bytes", "interval_ms", "repetition", "segment_count", "window_duration_ms"):
        if row[field] is not None and row[field] <= 0:
            raise ValueError(f"{field} must be positive")
    if row["segment_count"] != 1:
        raise ValueError("bounded v2 row must have one segment")
    provenance = tuple(row[f] for f in ("source_kind", "execution_kind", "measurement_status"))
    if provenance not in PROVENANCE:
        raise ValueError("unsupported dataset provenance combination")
    if row["rx_decoded_packets"] > row["rx_operations"]:
        raise ValueError("decoded packets exceed receive operations")
    _ratio(row, "rx_decoded_packets", "rx_operations", "rx_decode_per_operation_ratio")
    if row["delivery_status"] == "unavailable":
        if any(row[f] is not None for f in ("offered_packets", "delivered_packets", "packet_delivery_ratio", "target_energy_per_delivered_packet_uj")):
            raise ValueError("unavailable delivery evidence requires null delivery values")
    elif row["delivery_status"] == "validated":
        if row["offered_packets"] is None or row["delivered_packets"] is None:
            raise ValueError("validated delivery requires counts")
        if row["delivered_packets"] > row["offered_packets"]:
            raise ValueError("deliveries exceed offers")
        _ratio(row, "delivered_packets", "offered_packets", "packet_delivery_ratio")
    else:
        raise ValueError("invalid delivery_status")
    probabilities = ("good_to_bad_probability", "bad_to_good_probability", "good_state_loss_probability", "bad_state_loss_probability")
    for field in probabilities:
        if row[field] is not None and row[field] > 1:
            raise ValueError(f"{field} exceeds one")
    loss_fields = ("loss_model", "loss_preset", "loss_initial_state") + probabilities
    if any(row[f] is not None for f in loss_fields):
        from channel_loss import validate_loss_scenario
        validate_loss_scenario({
            "model": row["loss_model"], "preset": row["loss_preset"],
            "initial_state": row["loss_initial_state"],
            **{f: row[f] for f in probabilities},
        })
    if row["measurement_status"] == "unmeasured":
        if any(row[f] is not None for f in TARGET_COLUMNS - {"ping_rtt_latency_ms"}):
            raise ValueError("unmeasured rows require null energy targets")
        if row["source_kind"] == "synthetic" and row["ping_rtt_latency_ms"] is not None:
            raise ValueError("synthetic unmeasured RTT must be null")
    else:
        if row["target_mean_power_mw"] is None or row["target_total_energy_mj"] is None:
            raise ValueError("labeled rows require power and energy")
        expected = row["target_mean_power_mw"] * (row["window_duration_ms"] / 1000)
        _finite(expected, "derived energy")
        # Measured rows may have a tolerated capture/window duration difference;
        # the source manifest supplies the policies checked below.
        if row["measurement_status"] == "analytical_simulation" and not math.isclose(row["target_total_energy_mj"], expected, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("analytical energy inconsistent with power and duration")
        try:
            per_delivery = (row["target_total_energy_mj"] * 1000 / row["delivered_packets"]
                            if row["delivered_packets"] else None)
        except OverflowError as error:
            raise ValueError("derived energy per delivery overflow") from error
        if per_delivery is not None:
            _finite(per_delivery, "derived energy per delivery")
        if row["target_energy_per_delivered_packet_uj"] != per_delivery:
            raise ValueError("energy per delivery inconsistent")
    if (row["measurement_status"] == "analytical_simulation") != (row["analytical_model_id"] is not None):
        raise ValueError("analytical model identity must match analytical provenance")
    return copy.deepcopy(row)


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _validate_manifest(row, manifest):
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    for field, expected in (("manifest_version", 2), ("dataset_version", 2),
                            ("dataset_rows", 1), ("feature_contract_version", FEATURE_CONTRACT_VERSION)):
        if type(manifest.get(field)) is not int or manifest[field] != expected:
            raise ValueError(f"invalid manifest {field}")
    for field in MANIFEST_IDENTITIES:
        if field not in manifest or manifest[field] != row[field]:
            raise ValueError(f"manifest {field} mismatch")
    required_keys = {
        "manifest_version", "dataset_version", "dataset_rows", "feature_contract_version",
        "column_roles", "selected_features", "available_fields", "policies",
        "dataset_sha256", "input_paths", "input_sha256", *MANIFEST_IDENTITIES,
    }
    if row["measurement_status"] == "analytical_simulation":
        required_keys.add("analytical_reference")
    if set(manifest) != required_keys:
        raise ValueError("manifest must contain exactly the documented fields")
    from feature_contract import feature_roles, select_feature_names
    capabilities = manifest["available_fields"]
    if not isinstance(capabilities, list) or any(not isinstance(f, str) for f in capabilities) or len(set(capabilities)) != len(capabilities) or set(capabilities) - set(DATASET_FIELDS_V2):
        raise ValueError("invalid manifest capabilities")
    if any(row[f] is None for f in capabilities):
        raise ValueError("manifest capability has null value")
    expected_selected = {}
    for mode in ("pre_run", "post_run"):
        try:
            expected_selected[mode] = list(select_feature_names(
                schema_version=2, prediction_mode=mode, available_fields=frozenset(capabilities)))
        except ValueError:
            expected_selected[mode] = None
    if manifest["selected_features"] != expected_selected:
        raise ValueError("manifest selected features mismatch")
    if not isinstance(manifest["policies"], dict):
        raise ValueError("invalid manifest policies")
    if row["measurement_status"] == "measured":
        from ppk2_summary import _v2_finite_number
        if set(manifest["policies"]) != {"duration_tolerance_ms", "duration_tolerance_fraction", "max_alignment_uncertainty_ms"}:
            raise ValueError("measured manifest requires acquisition policies")
        for name, value in manifest["policies"].items():
            _v2_finite_number(value, name)
        if manifest["policies"]["duration_tolerance_fraction"] > 1:
            raise ValueError("invalid duration tolerance fraction")
        if row["target_mean_power_mw"] <= 0 or row["target_total_energy_mj"] <= 0:
            raise ValueError("measured energy and power must be positive")
        try:
            expected_energy = row["target_mean_power_mw"] * (row["window_duration_ms"] / 1000)
            duration_difference = max(manifest["policies"]["duration_tolerance_ms"],
                                      manifest["policies"]["duration_tolerance_fraction"] * row["window_duration_ms"])
            duration_energy_difference = row["target_mean_power_mw"] * (duration_difference / 1000)
            permitted_difference = duration_energy_difference + max(
                0.001, 0.001 * (expected_energy + duration_energy_difference))
        except OverflowError as error:
            raise ValueError("measured energy consistency overflow") from error
        _finite(expected_energy, "derived measured energy")
        _finite(permitted_difference, "energy tolerance")
        if abs(row["target_total_energy_mj"] - expected_energy) > permitted_difference:
            raise ValueError("measured energy inconsistent with duration/power policies")
    roles = dict(zip(("metadata", "features", "targets"), (sorted(r) for r in feature_roles(2))))
    if manifest.get("column_roles") != roles:
        raise ValueError("manifest column roles mismatch")
    for name in ("input_paths", "input_sha256"):
        if not isinstance(manifest.get(name), dict) or not manifest[name]:
            raise ValueError(f"invalid {name}")
    if set(manifest["input_paths"]) != set(manifest["input_sha256"]):
        raise ValueError("manifest input references mismatch")
    for value in manifest["input_paths"].values():
        if not isinstance(value, str) or not value:
            raise ValueError("invalid input path")
    for value in manifest["input_sha256"].values():
        if not isinstance(value, str) or _HASH.fullmatch(value) is None:
            raise ValueError("invalid input digest")
    if row["measurement_status"] == "analytical_simulation":
        reference = manifest.get("analytical_reference")
        if not isinstance(reference, dict) or set(reference) != {"model_id", "version", "configuration_sha256", "assumptions_document_sha256"}:
            raise ValueError("analytical rows require an explicit model reference")
        if reference["model_id"] != row["analytical_model_id"] or not isinstance(reference["version"], str) or not reference["version"]:
            raise ValueError("analytical reference identity mismatch")
        for field in ("configuration_sha256", "assumptions_document_sha256"):
            value = reference[field]
            if not isinstance(value, str) or _HASH.fullmatch(value) is None or manifest["input_sha256"].get(field.removesuffix("_sha256")) != value:
                raise ValueError(f"analytical reference {field} mismatch")
    elif row["measurement_status"] == "measured":
        if not {"ppk2_summary", "measurement_window", "telemetry_csv", "run_metadata"} <= manifest["input_sha256"].keys():
            raise ValueError("measured manifest requires bounded source references")
    if row["ping_rtt_latency_ms"] is not None and row["measurement_status"] != "analytical_simulation":
        if "rtt_evidence" not in manifest["input_sha256"]:
            raise ValueError("hardware RTT requires correlated evidence reference")
    return copy.deepcopy(manifest)


def load_dataset_artifact(csv_path, manifest_path):
    """Load one strict row and verify its manifest's byte digest and identities."""
    with Path(csv_path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(DATASET_FIELDS_V2):
            raise ValueError("dataset header must be v2; regenerate v1 artifacts")
        rows = list(reader)
    if len(rows) != 1 or set(rows[0]) != set(DATASET_FIELDS_V2):
        raise ValueError("dataset artifact must contain exactly one complete row")
    row = {}
    for field, value in rows[0].items():
        if value is None:
            raise ValueError(f"missing CSV cell: {field}")
        if value == "":
            row[field] = None
        elif field in INTEGER_FIELDS:
            if re.fullmatch(r"-?(0|[1-9][0-9]*)", value) is None:
                raise ValueError(f"invalid integer CSV value: {field}")
            row[field] = int(value)
        elif field in NUMBER_FIELDS:
            if re.fullmatch(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?", value) is None:
                raise ValueError(f"invalid numeric CSV value: {field}")
            try:
                row[field] = float(value)
            except ValueError as error:
                raise ValueError(f"invalid numeric CSV value: {field}") from error
        else:
            row[field] = value
    row = validate_dataset_row(row, schema_version=2)
    manifest = _validate_manifest(row, _load_json_object(manifest_path))
    csv_sha256 = _digest(csv_path)
    if manifest.get("dataset_sha256") != csv_sha256:
        raise ValueError("dataset CSV digest mismatch")
    return dict(row=row, manifest=manifest, csv_sha256=csv_sha256,
                manifest_sha256=_digest(manifest_path))


def build_dataset_table(artifacts, *, schema_version, measurement_status,
                        required_targets=(), missing_target_policy="error"):
    """Validate every artifact before filtering and return stable rows/manifest."""
    if type(schema_version) is not int or schema_version != 2:
        raise ValueError("tables require dataset v2; regenerate v1 from source artifacts")
    if not isinstance(measurement_status, str) or measurement_status not in {"unmeasured", "measured", "analytical_simulation"}:
        raise ValueError("invalid measurement_status selection")
    if not isinstance(required_targets, tuple) or any(not isinstance(t, str) or t not in TARGET_COLUMNS for t in required_targets) or len(set(required_targets)) != len(required_targets):
        raise ValueError("required_targets must be unique target column names")
    if not isinstance(missing_target_policy, str) or missing_target_policy not in {"error", "exclude"}:
        raise ValueError("invalid missing_target_policy")
    accepted, excluded, sources = [], [], []
    seen = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {"row", "manifest", "csv_sha256", "manifest_sha256"}:
            raise ValueError("invalid artifact structure")
        row = validate_dataset_row(artifact["row"], schema_version=2)
        _validate_manifest(row, artifact["manifest"])
        for field in ("csv_sha256", "manifest_sha256"):
            if not isinstance(artifact[field], str) or _HASH.fullmatch(artifact[field]) is None:
                raise ValueError("invalid artifact digest")
        if artifact["csv_sha256"] != artifact["manifest"].get("dataset_sha256"):
            raise ValueError("artifact CSV digest mismatch")
        if row["run_id"] in seen:
            raise ValueError("duplicate run_id or artifact reference")
        seen.add(row["run_id"])
        sources.append(dict(run_id=row["run_id"], csv_sha256=artifact["csv_sha256"], manifest_sha256=artifact["manifest_sha256"]))
        reason = None
        if row["measurement_status"] != measurement_status:
            reason = "measurement_status"
        else:
            missing = sorted(t for t in required_targets if row[t] is None)
            if missing:
                if missing_target_policy == "error":
                    raise ValueError(f"{row['run_id']}: missing required targets {missing}")
                reason = "missing targets: " + ", ".join(missing)
        if reason:
            excluded.append(dict(run_id=row["run_id"], reason=reason))
        else:
            accepted.append(row)
    if not accepted:
        raise ValueError("table selection contains zero rows")
    accepted.sort(key=lambda row: row["run_id"])
    manifest = dict(
        table_version=1, dataset_version=2, feature_contract_version=FEATURE_CONTRACT_VERSION,
        selection_policy=dict(measurement_status=measurement_status,
                              required_targets=sorted(required_targets), missing_target_policy=missing_target_policy),
        row_count=len(accepted), run_ids=[r["run_id"] for r in accepted],
        group_ids=sorted({r["evaluation_group_id"] for r in accepted}),
        source_artifacts=sorted(sources, key=lambda s: s["run_id"]),
        included_count=len(accepted), excluded_count=len(excluded),
        exclusions=sorted(excluded, key=lambda e: e["run_id"]),
        target_missing_counts={t: sum(r[t] is None for r in accepted) for t in sorted(TARGET_COLUMNS)},
    )
    return accepted, manifest
