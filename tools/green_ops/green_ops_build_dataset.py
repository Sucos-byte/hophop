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
    DATASET_FIELDS,
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
    writer = csv.DictWriter(output, fieldnames=DATASET_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue()


def _manifest(row, input_paths):
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
    outputs = {
        "dataset": arguments.dataset_output,
        "manifest": arguments.manifest_output,
    }

    try:
        input_paths, output_paths = _validate_paths(inputs, outputs)
        with reserve_outputs(output_paths.values()) as reservation:
            row = build_dataset_row_from_files(
                input_paths["telemetry_csv"],
                input_paths["run_metadata"],
                input_paths.get("experiment_plan"),
                input_paths.get("ppk2_summary"),
            )
            reservation.publish({
                output_paths["dataset"]: _dataset_csv(row),
                output_paths["manifest"]: _manifest(row, input_paths),
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
