# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Deterministic analytical workload grids and conservative pre-training audit.

This is a software-design audit, not a model fit or a physical independence test.
Single-run artifact and dataset/table contracts remain unchanged.
"""

import hashlib
import math
from pathlib import Path

from analytical_reference import (
    GENERATOR_VERSION, SAMPLER_VERSION, STATES, _integer, _identifier, _json_bytes,
    _number, _sha256, validate_model, validate_workload, simulate_reference,
)
from dataset_builder import _json_from_bytes
from dataset_table import load_dataset_artifact
from feature_contract import PRE_RUN_FEATURES, TARGET_COLUMNS, describe_prediction_context

FAMILY_FIELDS = ("payload_size_bytes", "interval_ms", "tx_power_dbm")


def configuration_family(workload):
    """Group duration/repetition/seed/model variants of the same traffic family."""
    if not isinstance(workload, dict):
        raise ValueError("workload must be an object")
    for name in FAMILY_FIELDS:
        _integer(workload.get(name), name, minimum=-100 if name == "tx_power_dbm" else 1)
    return "af-" + _sha256(_json_bytes({f:workload[f] for f in FAMILY_FIELDS}))[:32]


def plan_workload_grid(model, *, payload_sizes_bytes, intervals_ms, window_durations_ms,
                       repetitions, master_seed, max_attempts=3, variant_id="nominal"):
    """Plan full-slot offers and group-local seeds; return normalized workloads.

    variant_id changes run identity, never family or random draws. Reuse the same
    grid for model stress variants, and keep those panels separate from primary
    fixed-parameter training. No targets or random outcomes enter planning.
    """
    model = validate_model(model)
    _integer(repetitions, "repetitions", minimum=1, maximum=10000)
    _integer(master_seed, "master_seed", maximum=2**64-1)
    _integer(max_attempts, "max_attempts", minimum=1, maximum=16)
    _identifier(variant_id, "variant_id")
    levels = []
    for name, values in (("payload_sizes_bytes",payload_sizes_bytes),
                         ("intervals_ms",intervals_ms), ("window_durations_ms",window_durations_ms)):
        if not isinstance(values, tuple) or not values:
            raise ValueError(f"{name} must be a nonempty tuple of unique integer levels")
        for value in values:
            _integer(value, name, minimum=1, maximum=3600000)
        if len(set(values)) != len(values):
            raise ValueError(f"{name} contains duplicate levels")
        levels.append(sorted(values))
    if math.prod(len(level) for level in levels) * repetitions > 10000:
        raise ValueError("grid exceeds 10000-run planning policy")
    planned, seeds = [], {}
    for payload in levels[0]:
        for interval in levels[1]:
            family = configuration_family(dict(payload_size_bytes=payload, interval_ms=interval,
                                                tx_power_dbm=model["conditions"]["tx_power_dbm"]))
            for repetition in range(1,repetitions+1):
                seed = int.from_bytes(hashlib.sha256(
                    f"analytical-design-v1:{master_seed}:{family}:{repetition}".encode("ascii")).digest()[:8],"big")
                if seed in seeds and seeds[seed] != (family,repetition):
                    raise ValueError("derived seed collision; change master_seed")
                seeds[seed] = (family,repetition)
                for duration in levels[2]:
                    identity = dict(family=family, repetition=repetition, duration_ms=duration,
                                    variant_id=variant_id, master_seed=master_seed, max_attempts=max_attempts)
                    run = dict(workload_version=1, run_id="ar-"+_sha256(_json_bytes(identity))[:32],
                               evaluation_group_id=family, seed=seed, repetition=repetition,
                               window_duration_ms=duration, interval_ms=interval, payload_size_bytes=payload,
                               tx_power_dbm=model["conditions"]["tx_power_dbm"],
                               offered_packets=duration//interval, max_attempts=max_attempts)
                    planned.append(validate_workload(run,model=model))
    return sorted(planned,key=lambda run:run["run_id"])


def _close(actual, expected, name):
    if expected is None:
        if actual is not None:
            raise ValueError(f"{name}: unexpected value")
    else:
        _number(actual, name)
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"{name}: does not match analytical replay")


def load_design_record(directory):
    """Verify archived source hashes, identities and replay before design audit.

    Existing table loading checks CSV/manifest identity. This additional audit
    opens the local analytical source bundle; references must stay inside it.
    It supports reference generator 1.0.0 and the arithmetic correction 1.0.1.
    """
    root = Path(directory).resolve()
    artifact = load_dataset_artifact(root/"dataset.csv", root/"manifest.json")
    row, manifest = artifact["row"], artifact["manifest"]
    if (row["source_kind"],row["execution_kind"],row["measurement_status"]) != ("synthetic","simulation","analytical_simulation"):
        raise ValueError("design audit requires analytical_simulation bundles")
    required = {"parameters","workload","assumptions_document","configuration","state_accounting",
                "packet_evidence","delivery_summary","sensitivity"}
    if not required <= manifest["input_paths"].keys():
        raise ValueError("design audit requires a complete analytical reference bundle")
    snapshots = {}
    for name, relative in manifest["input_paths"].items():
        path = (root/relative).resolve()
        if Path(relative).is_absolute() or root not in path.parents:
            raise ValueError("analytical source reference escapes bundle directory")
        snapshots[name] = path.read_bytes()
        if _sha256(snapshots[name]) != manifest["input_sha256"][name]:
            raise ValueError(f"{name}: archived source hash mismatch")
    model = validate_model(_json_from_bytes(snapshots["parameters"]))
    workload = validate_workload(_json_from_bytes(snapshots["workload"]),model=model)
    configuration = _json_from_bytes(snapshots["configuration"])
    report = _json_from_bytes(snapshots["state_accounting"])
    if not isinstance(configuration,dict) or not isinstance(report,dict):
        raise ValueError("configuration and accounting must be objects")
    expected_fields = dict(configuration_version=1, model_id=model["model_id"],
        model_version=model["model_version"], parameter_version=model["parameter_version"],
        sampler_version=SAMPLER_VERSION, parameters_sha256=_sha256(snapshots["parameters"]),
        workload_sha256=_sha256(snapshots["workload"]),
        assumptions_document_sha256=_sha256(snapshots["assumptions_document"]),
        prediction_context_sha256=_sha256(snapshots["prediction_context"]) if "prediction_context" in snapshots else None,
        workload=workload)
    if set(configuration) != set(expected_fields) | {"generator_version"}:
        raise ValueError("configuration schema mismatch")
    for name,value in expected_fields.items():
        if _json_bytes(configuration[name]) != _json_bytes(value):
            raise ValueError(f"configuration {name} mismatch")
    if configuration["generator_version"] not in {"1.0.0", GENERATOR_VERSION}:
        raise ValueError("unsupported analytical generator version; regenerate or use its audited implementation")
    if manifest["analytical_reference"]["version"] != model["model_version"]:
        raise ValueError("model reference version mismatch")
    for name in ("run_id","evaluation_group_id","seed","repetition","payload_size_bytes",
                 "interval_ms","tx_power_dbm","window_duration_ms","offered_packets"):
        if row[name] != workload[name]:
            raise ValueError(f"row {name} does not match source workload")
    if row["analytical_model_id"] != model["model_id"]:
        raise ValueError("row model identity mismatch")
    replay = simulate_reference(model,workload)
    if set(report) != set(replay):
        raise ValueError("state accounting schema mismatch")
    for name,value in replay.items():
        if name in {"total_energy_mj","mean_power_mw"}:
            _close(report[name],value,name)
        elif name == "state_energy_mj":
            if not isinstance(report[name],dict) or set(report[name]) != set(STATES):
                raise ValueError("state energy fields mismatch")
            for state in STATES:
                _close(report[name][state],value[state],f"{state} energy")
        elif name == "generator_version":
            if report[name] != configuration[name]:
                raise ValueError("generator versions mismatch")
        elif _json_bytes(report[name]) != _json_bytes(value):
            raise ValueError(f"state accounting {name} does not match replay")
    for name in ("rx_operations","rx_decoded_packets","tx_successes","delivered_packets"):
        if row[name] != replay[name]:
            raise ValueError(f"row {name} does not match replay")
    if row["sync_beacons"] != 0:
        raise ValueError("reference model does not generate synchronization beacons")
    for name,value in (("target_total_energy_mj",replay["total_energy_mj"]),
                       ("target_mean_power_mw",replay["mean_power_mw"]),
                       ("ping_rtt_latency_ms",replay["ping_rtt_latency_ms"])):
        _close(row[name],value,name)
    evidence = _json_from_bytes(snapshots["packet_evidence"])
    expected_evidence = dict(evidence_version=1,provenance="modeled_logical_delivery",
                             run_id=workload["run_id"],packets=replay["packets"])
    if _json_bytes(evidence) != _json_bytes(expected_evidence):
        raise ValueError("modeled packet evidence does not match replay")
    from measurement_window import validate_delivery_summary
    summary = validate_delivery_summary(_json_from_bytes(snapshots["delivery_summary"]),
        expected_run_id=workload["run_id"],expected_window_id=workload["run_id"])
    if (summary["offered_packet_ids"] != [p["packet_id"] for p in replay["packets"]]
            or summary["delivered_packet_ids"] != [p["packet_id"] for p in replay["packets"] if p["delivered"]]
            or summary["evidence_sha256"] != _sha256(snapshots["packet_evidence"])):
        raise ValueError("delivery summary does not match modeled packet evidence")
    context = _json_from_bytes(snapshots["prediction_context"]) if "prediction_context" in snapshots else None
    _,_,normalized = describe_prediction_context(row,context)
    if _json_bytes(manifest["prediction_context"]) != _json_bytes(normalized):
        raise ValueError("prediction context does not match archived declaration")
    point = dict(conditions=model["conditions"],currents={k:v["value"] for k,v in model["currents_ma"].items()},
        timings={k:v["value"] for k,v in model["timing_us"].items()},loss=model["loss_probability"]["value"],
        rtt=model["rtt_extra_ms"]["value"] if model["rtt_extra_ms"] is not None else None)
    realization = {k:v for k,v in workload.items() if k not in {"run_id","evaluation_group_id","repetition"}}
    return dict(row=row,manifest=manifest,workload=workload,family=configuration_family(workload),
                parameter_sha256=_sha256(snapshots["parameters"]),
                assumption_sha256=_sha256(snapshots["assumptions_document"]),
                realization_sha256=_sha256(_json_bytes(dict(point=point,workload=realization))))


def audit_reference_dataset(directories, *, minimum_groups=6):
    """Reject known split leakage; report readiness for a fixed-parameter pilot."""
    _integer(minimum_groups,"minimum_groups",minimum=2,maximum=10000)
    roots = [Path(path).resolve() for path in directories]
    if not roots or len(set(roots)) != len(roots):
        raise ValueError("audit needs nonempty unique bundle directories")
    records = [load_design_record(root) for root in roots]
    records.sort(key=lambda record:record["row"]["run_id"])
    families, seeds, runs, realizations = {}, {}, set(), set()
    for record in records:
        row,run = record["row"],record["workload"]
        group,family = row["evaluation_group_id"],record["family"]
        if row["run_id"] in runs or record["realization_sha256"] in realizations:
            raise ValueError("duplicate run or duplicate analytical realization")
        runs.add(row["run_id"]);realizations.add(record["realization_sha256"])
        if family in families and families[family] != group:
            raise ValueError("related configuration/repetition/parameter variants split across groups")
        if run["seed"] in seeds and seeds[run["seed"]] != group:
            raise ValueError("shared sampler seed across groups; derive group-local seeds")
        families[family]=group;seeds[run["seed"]]=group
    groups=sorted(set(families.values()))
    reasons=[]
    if any(r["workload"]["offered_packets"] != r["workload"]["window_duration_ms"]//r["workload"]["interval_ms"] for r in records):
        reasons.append("offered count is not determined by full-slot pre-run workload policy")
    if len({r["workload"]["max_attempts"] for r in records}) != 1:
        reasons.append("retry limit varies outside current pre-run inputs")
    if len({r["parameter_sha256"] for r in records}) != 1:
        reasons.append("model parameters vary outside current pre-run inputs; separate stress panels")
    if len({r["assumption_sha256"] for r in records}) != 1:
        reasons.append("assumptions vary; separate design panels")
    declared = all(r["manifest"]["selected_features"]["pre_run"] == list(PRE_RUN_FEATURES) for r in records)
    ranges={}
    for target in sorted(TARGET_COLUMNS):
        values=[r["row"][target] for r in records if r["row"][target] is not None]
        ranges[target]=dict(min=min(values) if values else None,max=max(values) if values else None,
                            missing_count=len(records)-len(values))
    energy_varies = any(ranges[t]["min"] is not None and ranges[t]["min"] != ranges[t]["max"]
                        for t in ("target_mean_power_mw","target_total_energy_mj"))
    return dict(design_audit_version=1,row_count=len(records),family_fields=list(FAMILY_FIELDS),
        family_count=len(families),group_count=len(groups),group_ids=groups,
        minimum_groups=minimum_groups,pre_run_profile_declared=declared,
        primary_scope_issues=reasons,feature_distinct_counts={f:len({r["row"][f] for r in records}) for f in PRE_RUN_FEATURES},
        target_ranges=ranges,energy_targets_vary=energy_varies,
        ready_for_grouped_software_pilot=(len(groups)>=minimum_groups and not reasons and declared and energy_varies),
        runs=[dict(run_id=r["row"]["run_id"],group_id=r["row"]["evaluation_group_id"],
                   family_id=r["family"],seed=r["workload"]["seed"],parameter_sha256=r["parameter_sha256"],
                   assumption_sha256=r["assumption_sha256"]) for r in records])
