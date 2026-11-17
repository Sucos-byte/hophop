# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Build a one-row Green-Ops analysis dataset and provenance manifest."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

from atomic_outputs import reserve_outputs
from dataset_builder import (
    DATASET_FIELDS, DATASET_FIELDS_V2,
    _build_dataset_row_v2_from_bytes, _json_from_bytes,
    build_dataset_row_from_files,
)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def parse_arguments():
    parser = ArgumentParser(
        description="Build one validated Green-Ops dataset row from run artifacts."
    )
    parser.add_argument("--telemetry-csv", required=True, type=Path)
    parser.add_argument("--run-metadata", required=True, type=Path)
    parser.add_argument("--experiment-plan", type=Path)
    parser.add_argument("--ppk2-summary", type=Path)
    parser.add_argument("--dataset-output", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--dataset-version", type=int, choices=(1, 2), default=1)
    parser.add_argument("--measurement-window", type=Path)
    parser.add_argument("--delivery-summary", type=Path)
    parser.add_argument("--prediction-context", type=Path)
    parser.add_argument("--duration-tolerance-ms", type=float)
    parser.add_argument("--duration-tolerance-fraction", type=float)
    parser.add_argument("--max-alignment-uncertainty-ms", type=float)
    return parser.parse_args()


def _resolved(path):
    return path.expanduser().resolve()


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dataset_csv(row):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=(DATASET_FIELDS_V2 if row["dataset_version"] == 2 else DATASET_FIELDS), lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue()


def _manifest(row, input_paths, policies=None, prediction_context=None, source_bytes=None):
    if row["dataset_version"] == 2:
        return _manifest_v2(row, input_paths, policies, prediction_context=prediction_context, source_bytes=source_bytes)
    named_inputs = {
        "telemetry_csv": input_paths["telemetry_csv"],
        "run_metadata": input_paths["run_metadata"],
    }
    if "experiment_plan" in input_paths:
        named_inputs["experiment_plan"] = input_paths["experiment_plan"]
    if "ppk2_summary" in input_paths:
        named_inputs["ppk2_summary"] = input_paths["ppk2_summary"]
    digests = {
        name: _sha256(path)
        for name, path in named_inputs.items()
    }
    manifest = {
        "manifest_version": 1,
        "run_id": row["run_id"],
        "adapter": row["adapter"],
        "source_kind": row["source_kind"],
        "execution_kind": row["execution_kind"],
        "measurement_status": row["measurement_status"],
        "dataset_rows": 1,
        "feature_columns": sorted(
            field for field in DATASET_FIELDS
            if field not in {
                "dataset_version", "run_id", "adapter", "feature_profile_id",
                "source_kind", "execution_kind", "measurement_status",
                "target_mean_power_mw", "target_total_energy_mj",
                "target_energy_per_delivered_packet_uj",
            }
        ),
        "target_columns": sorted([
            "target_mean_power_mw",
            "target_total_energy_mj",
            "target_energy_per_delivered_packet_uj",
        ]),
        "input_paths": {name: str(path) for name, path in named_inputs.items()},
        "input_sha256": digests,
    }
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def _manifest_v2(row, input_paths, policies, *, prediction_context=None, source_bytes=None):
    from feature_contract import FEATURE_CONTRACT_VERSION, feature_roles, describe_prediction_context
    roles = feature_roles(2)
    available, selected, context = describe_prediction_context(row, prediction_context)
    manifest = {
        "manifest_version": 2, "dataset_version": 2, "dataset_rows": 1,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "column_roles": dict(zip(("metadata", "features", "targets"),
                                 (sorted(role) for role in roles))),
        "selected_features": selected, "available_fields": available,
        "prediction_context": context,
        "policies": policies,
        "dataset_sha256": hashlib.sha256(_dataset_csv(row).encode("utf-8")).hexdigest(),
        "input_paths": {name: str(path) for name, path in input_paths.items()},
        "input_sha256": {name: (hashlib.sha256(source_bytes[name]).hexdigest()
                                if source_bytes is not None else _sha256(path))
                         for name, path in input_paths.items()},
    }
    for field in ("run_id", "adapter", "feature_profile_id", "source_kind",
                  "execution_kind", "measurement_status", "evaluation_group_id",
                  "analytical_model_id"):
        manifest[field] = row[field]
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def _validate_paths(inputs, outputs):
    input_paths = {name: _resolved(path) for name, path in inputs.items()}
    output_paths = {name: _resolved(path) for name, path in outputs.items()}
    if len(set(output_paths.values())) != len(output_paths):
        raise ValueError("dataset and manifest output paths must differ")
    if set(input_paths.values()) & set(output_paths.values()):
        raise ValueError("input paths must differ from output paths")
    for path in input_paths.values():
        if not path.is_file():
            raise ValueError(f"input path is not a file: {path}")
    for path in output_paths.values():
        if not path.parent.is_dir():
            raise ValueError("output parent directories must already exist")
    return input_paths, output_paths


def main():
    arguments = parse_arguments()
    inputs = {
        "telemetry_csv": arguments.telemetry_csv,
        "run_metadata": arguments.run_metadata,
    }
    if arguments.experiment_plan is not None:
        inputs["experiment_plan"] = arguments.experiment_plan
    if arguments.ppk2_summary is not None:
        inputs["ppk2_summary"] = arguments.ppk2_summary
    for name in ("measurement_window", "delivery_summary", "prediction_context"):
        if getattr(arguments, name) is not None:
            inputs[name] = getattr(arguments, name)
    outputs = {
        "dataset": arguments.dataset_output,
        "manifest": arguments.manifest_output,
    }

    try:
        policies = {
            "duration_tolerance_ms": arguments.duration_tolerance_ms,
            "duration_tolerance_fraction": arguments.duration_tolerance_fraction,
            "max_alignment_uncertainty_ms": arguments.max_alignment_uncertainty_ms,
        }
        if arguments.dataset_version == 1 and (
            arguments.measurement_window is not None or arguments.delivery_summary is not None
            or arguments.prediction_context is not None
            or any(value is not None for value in policies.values())
        ):
            raise ValueError("v2-only flags require --dataset-version 2")
        if arguments.dataset_version == 2 and arguments.measurement_window is None:
            raise ValueError("dataset v2 requires --measurement-window")
        policies = {name: value if value is not None else default
                    for (name, value), default in zip(policies.items(), (1.0, 0.001, 1.0))}
        input_paths, output_paths = _validate_paths(inputs, outputs)
        with reserve_outputs(output_paths.values()) as reservation:
            source_bytes = None
            context = None
            if arguments.dataset_version == 2:
                source_bytes = {name: path.read_bytes() for name, path in input_paths.items()}
                row = _build_dataset_row_v2_from_bytes(source_bytes, **policies)
                if "prediction_context" in source_bytes:
                    context = _json_from_bytes(source_bytes["prediction_context"])
            else:
                row = build_dataset_row_from_files(
                    input_paths["telemetry_csv"],
                    input_paths["run_metadata"],
                    input_paths.get("experiment_plan"),
                    input_paths.get("ppk2_summary"),
                )
            reservation.publish({
                output_paths["dataset"]: _dataset_csv(row),
                output_paths["manifest"]: _manifest(row, input_paths, policies, context, source_bytes),
            })
    except (OSError, UnicodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(
        f"Wrote one {row['measurement_status']} dataset row for run {row['run_id']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
