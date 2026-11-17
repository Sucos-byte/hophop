# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Deterministic analytical DECT scenario accounting, never measured evidence."""

import copy
import hashlib
import math
import re
from urllib.parse import urlparse

GENERATOR_VERSION = "1.0.0"
SAMPLER_VERSION = "sha256-bernoulli-v1"
STATES = ("idle", "tx", "rx")
TIMINGS = ("prepare", "tx_base", "tx_per_byte", "rx", "backoff")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_MODEL_FIELDS = {
    "model_schema_version", "model_id", "model_version", "parameter_version", "description",
    "conditions", "sources", "currents_ma", "timing_us", "loss_probability", "rtt_extra_ms",
}
_WORKLOAD_FIELDS = {
    "workload_version", "run_id", "evaluation_group_id", "seed", "repetition",
    "window_duration_ms", "interval_ms", "payload_size_bytes", "tx_power_dbm",
    "offered_packets", "max_attempts",
}


def _fields(value, fields, name):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f"{name} must contain exactly the documented fields")


def _number(value, name, *, minimum=0, positive=False):
    try:
        valid = type(value) in {int, float} and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or value < minimum or (positive and value == 0):
        raise ValueError(f"{name} must be finite and within its numeric domain")
    return value


def _integer(value, name, *, minimum=0, maximum=2**63-1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def _identifier(value, name):
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise ValueError(f"{name} must be a safe 1-64 character identifier")


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def _conditions(data):
    _fields(data, {"supply_v", "temperature_c", "band", "tx_power_dbm", "rx_signal_dbm",
                   "modem_mode", "scope"}, "conditions")
    _number(data["supply_v"], "supply_v", positive=True)
    _number(data["temperature_c"], "temperature_c", minimum=-273.15)
    _number(data["rx_signal_dbm"], "rx_signal_dbm", minimum=-1000)
    _integer(data["band"], "band", minimum=1, maximum=255)
    _integer(data["tx_power_dbm"], "tx_power_dbm", minimum=-100, maximum=100)
    if data["modem_mode"] != "minimum_latency" or data["scope"] != "exclusive_VDD_scenario":
        raise ValueError("model supports exclusive minimum-latency VDD scenarios only")


def _parameter(data, name, unit, sources, conditions, *, integer=False):
    _fields(data, {"value", "min", "max", "unit", "basis", "source_id", "range_note"}, name)
    if data["unit"] != unit:
        raise ValueError(f"{name}: expected unit {unit}")
    for field in ("min", "value", "max"):
        (_integer if integer else _number)(data[field], f"{name}.{field}")
    if not data["min"] <= data["value"] <= data["max"]:
        raise ValueError(f"{name}: value must lie within declared range")
    _text(data["range_note"], f"{name}.range_note")
    if data["basis"] == "official_typical":
        source_id = data["source_id"]
        if not isinstance(source_id, str) or source_id not in sources:
            raise ValueError(f"{name}: official parameter requires a catalog source")
        source = sources[source_id]
        if source["value"] != data["value"] or source["unit"] != unit or source["conditions"] != conditions:
            raise ValueError(f"{name}: sourced value/unit/conditions mismatch; mark extrapolation as assumption")
    elif data["basis"] != "assumption" or data["source_id"] is not None:
        raise ValueError(f"{name}: assumptions require basis=assumption and source_id=null")


def validate_model(data):
    """Strict independent copy of a versioned model and source catalog."""
    _fields(data, _MODEL_FIELDS, "analytical model")
    if type(data["model_schema_version"]) is not int or data["model_schema_version"] != 1:
        raise ValueError("model_schema_version must be integer 1")
    for name in ("model_id", "model_version", "parameter_version"):
        _identifier(data[name], name)
    _text(data["description"], "description")
    _conditions(data["conditions"])
    sources = data["sources"]
    if not isinstance(sources, dict):
        raise ValueError("sources must be a catalog object (empty for all-assumption models)")
    for name, source in sources.items():
        _identifier(name, "source ID")
        _fields(source, {"url", "document", "revision", "section", "table", "symbol", "value", "unit", "conditions"}, name)
        for field in ("url", "document", "revision", "section", "table", "symbol", "unit"):
            _text(source[field], f"{name}.{field}")
        url = urlparse(source["url"])
        if url.scheme != "https" or url.hostname not in {"docs.nordicsemi.com", "www.nordicsemi.com", "nordicsemi.com"}:
            raise ValueError("catalog sources must use official Nordic HTTPS URLs")
        _number(source["value"], f"{name}.value")
        _conditions(source["conditions"])
    _fields(data["currents_ma"], STATES, "currents_ma")
    for state, parameter in data["currents_ma"].items():
        _parameter(parameter, state, "mA", sources, data["conditions"])
    _fields(data["timing_us"], TIMINGS, "timing_us")
    for name, parameter in data["timing_us"].items():
        _parameter(parameter, name, "us", sources, data["conditions"], integer=True)
    if data["timing_us"]["rx"]["min"] <= 0:
        raise ValueError("RX/ACK wait requires positive duration throughout its range")
    _parameter(data["loss_probability"], "loss_probability", "probability", sources, data["conditions"])
    if data["loss_probability"]["max"] > 1:
        raise ValueError("loss probability range must be within [0,1]")
    if data["rtt_extra_ms"] is not None:
        _parameter(data["rtt_extra_ms"], "rtt_extra_ms", "ms", sources, data["conditions"])
        if data["rtt_extra_ms"]["basis"] != "assumption":
            raise ValueError("modeled RTT must be explicitly marked as an assumption")
    return copy.deepcopy(data)


def validate_workload(data, *, model):
    """Validate workload bounds and reserve complete worst-case slots up front."""
    model = validate_model(model)
    _fields(data, _WORKLOAD_FIELDS, "analytical workload")
    if type(data["workload_version"]) is not int or data["workload_version"] != 1:
        raise ValueError("workload_version must be integer 1")
    for name in ("run_id", "evaluation_group_id"):
        _identifier(data[name], name)
    for name, minimum, maximum in (
        ("seed", 0, 2**64-1), ("repetition", 1, 1000000),
        ("window_duration_ms", 1, 3600000), ("interval_ms", 1, 3600000),
        ("payload_size_bytes", 1, 4096), ("offered_packets", 0, 10000),
        ("max_attempts", 1, 16), ("tx_power_dbm", -100, 100),
    ):
        _integer(data[name], name, minimum=minimum, maximum=maximum)
    if data["tx_power_dbm"] != model["conditions"]["tx_power_dbm"]:
        raise ValueError("requested TX power must match model conditions; no current extrapolation")
    if data["offered_packets"] * data["max_attempts"] > 100000:
        raise ValueError("workload exceeds 100000-attempt software resource policy")
    if data["offered_packets"] * data["interval_ms"] > data["window_duration_ms"]:
        raise ValueError("each offered packet must have a full slot inside the window")
    timing = {name: p["value"] for name, p in model["timing_us"].items()}
    tx_us = timing["tx_base"] + timing["tx_per_byte"] * data["payload_size_bytes"]
    if tx_us <= 0:
        raise ValueError("modeled packet TX duration must be positive")
    attempt_us = timing["prepare"] + tx_us + timing["rx"]
    worst_us = attempt_us * data["max_attempts"] + timing["backoff"] * (data["max_attempts"]-1)
    if data["offered_packets"] and worst_us > data["interval_ms"] * 1000:
        raise ValueError("worst-case retry path exceeds reserved interval slot")
    return copy.deepcopy(data)


def integrate_states(state_duration_us, currents_ma, *, voltage_v):
    """Integrate exclusive states: V * mA * us / 1e6 = mJ."""
    if not isinstance(state_duration_us, dict) or not state_duration_us or not isinstance(currents_ma, dict) or set(state_duration_us) != set(currents_ma):
        raise ValueError("state durations and currents must have identical nonempty keys")
    _number(voltage_v, "voltage_v", positive=True)
    energies = {}
    for state, duration in state_duration_us.items():
        _identifier(state, "state")
        _integer(duration, f"{state}.duration_us")
        _number(currents_ma[state], f"{state}.current_ma")
        try:
            energy = voltage_v * currents_ma[state] * (duration / 1000000)
        except OverflowError as error:
            raise ValueError(f"{state}: energy overflow") from error
        _number(energy, f"{state}.energy_mj")
        energies[state] = energy
    duration_us = sum(state_duration_us.values())
    if duration_us <= 0:
        raise ValueError("integrated window duration must be positive")
    try:
        energy = math.fsum(energies.values())
        power = energy / (duration_us / 1000000)
    except OverflowError as error:
        raise ValueError("integrated energy/power overflow") from error
    _number(energy, "total_energy_mj")
    _number(power, "mean_power_mw")
    return dict(state_energy_mj=energies, total_energy_mj=energy, mean_power_mw=power)


def _lost(seed, packet, attempt, probability):
    # Integer comparison against an exact binary-float probability avoids
    # platform-dependent float conversion of the 256-bit uniform sample.
    draw = int.from_bytes(hashlib.sha256(f"{SAMPLER_VERSION}:{seed}:{packet}:{attempt}".encode("ascii")).digest(), "big")
    numerator, denominator = float(probability).as_integer_ratio()
    return draw * denominator < numerator * 2**256


def simulate_reference(model, workload):
    """Generate explicit state/packet evidence using no PPK2 or physical claims."""
    model = validate_model(model)
    run = validate_workload(workload, model=model)
    timing = {name: p["value"] for name, p in model["timing_us"].items()}
    tx_us = timing["tx_base"] + timing["tx_per_byte"] * run["payload_size_bytes"]
    segments, packets = [], []
    durations = dict.fromkeys(STATES, 0)
    cursor, attempts = 0, 0

    def add(state, duration, phase, packet=None, attempt=None):
        nonlocal cursor
        if duration:
            segments.append(dict(state=state, phase=phase, start_us=cursor,
                                 duration_us=duration, packet_index=packet, attempt_index=attempt))
            durations[state] += duration
            cursor += duration

    for packet in range(run["offered_packets"]):
        offered_us = packet * run["interval_ms"] * 1000
        add("idle", offered_us - cursor, "between_packets")
        delivered = False
        for attempt in range(run["max_attempts"]):
            add("idle", timing["prepare"], "prepare", packet, attempt)
            add("tx", tx_us, "transmit", packet, attempt)
            add("rx", timing["rx"], "ack_wait", packet, attempt)
            attempts += 1
            delivered = not _lost(run["seed"], packet, attempt, model["loss_probability"]["value"])
            if delivered:
                break
            if attempt + 1 < run["max_attempts"]:
                add("idle", timing["backoff"], "retry_backoff", packet, attempt)
        late_acceptance = cursor if delivered and cursor == run["window_duration_ms"] * 1000 else None
        if late_acceptance is not None:
            delivered = False  # [start,end): an ACK at end is outside this run window.
        rtt = None
        if delivered and model["rtt_extra_ms"] is not None:
            rtt = (cursor - offered_us) / 1000 + model["rtt_extra_ms"]["value"]
            _number(rtt, "modeled RTT")
        packets.append(dict(packet_id=hashlib.sha256(f"{run['run_id']}:{packet}".encode("ascii")).hexdigest(),
                            offered_us=offered_us, attempts=attempt+1, delivered=delivered,
                            accepted_us=cursor if delivered else None, late_acceptance_us=late_acceptance,
                            modeled_rtt_ms=rtt))
    add("idle", run["window_duration_ms"] * 1000 - cursor, "window_remainder")
    if cursor != run["window_duration_ms"] * 1000 or sum(durations.values()) != cursor:
        raise ValueError("state-time conservation failure")
    energy = integrate_states(durations, {s:p["value"] for s,p in model["currents_ma"].items()},
                              voltage_v=model["conditions"]["supply_v"])
    rtts = [p["modeled_rtt_ms"] for p in packets if p["modeled_rtt_ms"] is not None]
    mean_rtt = math.fsum(value/len(rtts) for value in rtts) if rtts else None
    if mean_rtt is not None:
        _number(mean_rtt, "mean modeled RTT")
    return dict(generator_version=GENERATOR_VERSION, sampler_version=SAMPLER_VERSION,
                run_id=run["run_id"], seed=run["seed"], model_id=model["model_id"],
                model_version=model["model_version"], parameter_version=model["parameter_version"],
                conditions=model["conditions"], state_duration_us=durations, segments=segments,
                packets=packets, offered_packets=len(packets), delivered_packets=sum(p["delivered"] for p in packets),
                rx_operations=attempts, rx_decoded_packets=sum(p["delivered"] for p in packets),
                tx_successes=attempts, ping_rtt_latency_ms=mean_rtt, **energy)


def sensitivity_analysis(model, workload):
    """One-at-a-time low/high scenario checks, not calibrated uncertainty bands."""
    model = validate_model(model)
    baseline = simulate_reference(model, workload)
    cases = []
    parameters = [("currents_ma", name) for name in STATES] + [("timing_us", name) for name in TIMINGS]
    parameters += [("loss_probability", None)]
    if model["rtt_extra_ms"] is not None:
        parameters.append(("rtt_extra_ms", None))
    for section, name in parameters:
        parameter = model[section][name] if name is not None else model[section]
        if parameter["min"] == parameter["max"]:
            continue
        for bound in ("min", "max"):
            variant = copy.deepcopy(model)
            changed = variant[section][name] if name is not None else variant[section]
            changed.update(value=parameter[bound], basis="assumption", source_id=None)
            case = dict(parameter=f"{section}.{name}" if name is not None else section,
                        bound=bound, value=parameter[bound], unit=parameter["unit"],
                        basis="assumption", variant_parameters_sha256=_sha256(_json_bytes(variant)))
            try:
                result = simulate_reference(variant, workload)
                case.update(status="valid", total_energy_mj=result["total_energy_mj"],
                            state_duration_us=result["state_duration_us"],
                            delivered_packets=result["delivered_packets"],
                            ping_rtt_latency_ms=result["ping_rtt_latency_ms"],
                            energy_change_mj=result["total_energy_mj"]-baseline["total_energy_mj"])
            except ValueError as error:
                case.update(status="invalid", reason=str(error))
            cases.append(case)
    return dict(sensitivity_version=1, method="one_at_a_time_common_seed",
                baseline_energy_mj=baseline["total_energy_mj"], cases=cases)


def _json_bytes(value):
    import json
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _sha256(content):
    return hashlib.sha256(content).hexdigest()


def generate_analytical_artifact(parameters_bytes, workload_bytes, assumptions_bytes, *, prediction_context_bytes=None):
    """Return exact UTF-8 file snapshots for one v2 analytical artifact bundle.

    Parameters/assumptions are archived verbatim and hashed; no PPK2 artifact is
    accepted or fabricated. File names/references are relative and deterministic.
    """
    import json
    from pathlib import Path
    from dataset_builder import DATASET_FIELDS_V2, _json_from_bytes
    from dataset_table import validate_dataset_row, _validate_manifest
    from green_ops_build_dataset import _dataset_csv, _manifest_v2
    from measurement_window import validate_delivery_summary

    for name, content in (("parameters", parameters_bytes), ("workload", workload_bytes),
                          ("assumptions", assumptions_bytes)):
        if not isinstance(content, bytes):
            raise ValueError(f"{name} must be an immutable bytes snapshot")
    model = validate_model(_json_from_bytes(parameters_bytes))
    workload = validate_workload(_json_from_bytes(workload_bytes), model=model)
    _text(assumptions_bytes.decode("utf-8"), "assumptions document")
    if prediction_context_bytes is not None and not isinstance(prediction_context_bytes, bytes):
        raise ValueError("prediction context must be a bytes snapshot")
    context = _json_from_bytes(prediction_context_bytes) if prediction_context_bytes is not None else None
    result = simulate_reference(model, workload)
    sensitivity = sensitivity_analysis(model, workload)
    packet_bytes = _json_bytes(dict(evidence_version=1, provenance="modeled_logical_delivery",
                                    run_id=workload["run_id"], packets=result["packets"]))
    delivery = validate_delivery_summary(dict(
        summary_version=1, run_id=workload["run_id"], window_id=workload["run_id"],
        sender_id="analytical-sender", receiver_id="analytical-receiver",
        offered_packet_ids=[p["packet_id"] for p in result["packets"]],
        delivered_packet_ids=[p["packet_id"] for p in result["packets"] if p["delivered"]],
        evidence_sha256=_sha256(packet_bytes)),
        expected_run_id=workload["run_id"], expected_window_id=workload["run_id"])
    row = dict.fromkeys(DATASET_FIELDS_V2)
    row.update(dataset_version=2, run_id=workload["run_id"], adapter="analytical-reference-v1",
               feature_profile_id="dect-reference-v1", source_kind="synthetic", execution_kind="simulation",
               measurement_status="analytical_simulation", segment_count=1,
               payload_size_bytes=workload["payload_size_bytes"], interval_ms=workload["interval_ms"],
               tx_power_dbm=workload["tx_power_dbm"], window_duration_ms=workload["window_duration_ms"],
               seed=workload["seed"], repetition=workload["repetition"],
               evaluation_group_id=workload["evaluation_group_id"], analytical_model_id=model["model_id"],
               delivery_status="validated", offered_packets=result["offered_packets"],
               delivered_packets=result["delivered_packets"], rx_operations=result["rx_operations"],
               rx_decoded_packets=result["rx_decoded_packets"], sync_beacons=0,
               tx_successes=result["tx_successes"], ping_rtt_latency_ms=result["ping_rtt_latency_ms"],
               rx_decode_per_operation_ratio=(result["rx_decoded_packets"]/result["rx_operations"] if result["rx_operations"] else None),
               packet_delivery_ratio=(result["delivered_packets"]/result["offered_packets"] if result["offered_packets"] else None),
               target_total_energy_mj=result["total_energy_mj"], target_mean_power_mw=result["mean_power_mw"])
    if result["delivered_packets"]:
        row["target_energy_per_delivered_packet_uj"] = result["total_energy_mj"]*1000/result["delivered_packets"]
    row = validate_dataset_row(row, schema_version=2)
    configuration = dict(configuration_version=1, model_id=model["model_id"], model_version=model["model_version"],
                         parameter_version=model["parameter_version"], generator_version=GENERATOR_VERSION,
                         sampler_version=SAMPLER_VERSION, parameters_sha256=_sha256(parameters_bytes),
                         workload_sha256=_sha256(workload_bytes), assumptions_document_sha256=_sha256(assumptions_bytes),
                         prediction_context_sha256=_sha256(prediction_context_bytes) if prediction_context_bytes is not None else None,
                         workload=workload)
    snapshots = dict(parameters=parameters_bytes, workload=workload_bytes, assumptions_document=assumptions_bytes,
                     configuration=_json_bytes(configuration), state_accounting=_json_bytes(result),
                     packet_evidence=packet_bytes, delivery_summary=_json_bytes(delivery), sensitivity=_json_bytes(sensitivity))
    filenames = dict(parameters="parameters.json", workload="workload.json", assumptions_document="assumptions.md",
                     configuration="configuration.json", state_accounting="state-accounting.json",
                     packet_evidence="packet-evidence.json", delivery_summary="delivery-summary.json", sensitivity="sensitivity.json")
    if prediction_context_bytes is not None:
        snapshots["prediction_context"] = prediction_context_bytes
        filenames["prediction_context"] = "prediction-context.json"
    manifest = json.loads(_manifest_v2(row, {name:Path(filenames[name]) for name in snapshots}, {},
                                     prediction_context=context, source_bytes=snapshots))
    manifest["analytical_reference"] = dict(model_id=model["model_id"], version=model["model_version"],
                                           configuration_sha256=_sha256(snapshots["configuration"]),
                                           assumptions_document_sha256=_sha256(assumptions_bytes))
    _validate_manifest(row, manifest)
    files = {filenames[name]: content for name, content in snapshots.items()}
    files.update({"dataset.csv": _dataset_csv(row).encode("utf-8"), "manifest.json": _json_bytes(manifest)})
    return files
