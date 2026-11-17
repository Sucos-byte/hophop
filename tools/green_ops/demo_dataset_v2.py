# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Run synthetic and analytical-contract demos in a new output directory."""

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from converter import CSV_FIELDS
from dataset_builder import _load_json_object
from green_ops_build_dataset import _dataset_csv, _manifest_v2


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"


def _write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None):
    from green_ops_build_dataset import ArgumentParser
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    try:
        output.mkdir()  # Fresh destination required; never overwrite prior evidence.
        pairs = []
        for i, fixture in enumerate(_load_json_object(FIXTURES / "dataset-v2-demo.json"), 1):
            paths = {name: output / f"synthetic-{i}-{name}.json"
                     for name in ("run_metadata", "measurement_window")}
            for name, path in paths.items():
                _write(path, fixture[name])
            telemetry = output / f"synthetic-{i}-telemetry.csv"
            with telemetry.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
                writer.writeheader(); writer.writerows(fixture["telemetry_rows"])
            dataset, manifest = output / f"synthetic-{i}.csv", output / f"synthetic-{i}.json"
            subprocess.run([sys.executable, str(ROOT / "green_ops_build_dataset.py"),
                "--dataset-version", "2", "--telemetry-csv", str(telemetry),
                "--run-metadata", str(paths["run_metadata"]),
                "--measurement-window", str(paths["measurement_window"]),
                "--dataset-output", str(dataset), "--manifest-output", str(manifest)], check=True)
            pairs += ["--artifact", str(dataset), str(manifest)]
        subprocess.run([sys.executable, str(ROOT / "green_ops_build_table.py"), *pairs,
            "--measurement-status", "unmeasured", "--table-output", str(output / "synthetic-table.csv"),
            "--manifest-output", str(output / "synthetic-table.json")], check=True)
        references = {"configuration": FIXTURES / "analytical-contract-configuration.json",
                      "assumptions_document": FIXTURES / "analytical-contract-assumptions.md"}
        pairs = []
        for i, row in enumerate(_load_json_object(FIXTURES / "analytical-contract-rows.json"), 1):
            dataset, manifest_path = output / f"analytical-{i}.csv", output / f"analytical-{i}.json"
            inputs = {**references, "contract_rows": FIXTURES / "analytical-contract-rows.json"}
            manifest = json.loads(_manifest_v2(row, inputs, {}))
            manifest["analytical_reference"] = dict(
                model_id="week5-contract-test", version="1",
                **{name + "_sha256": hashlib.sha256(path.read_bytes()).hexdigest()
                   for name, path in references.items()},
            )
            dataset.write_text(_dataset_csv(row), encoding="utf-8")
            _write(manifest_path, manifest)
            pairs += ["--artifact", str(dataset), str(manifest_path)]
        subprocess.run([sys.executable, str(ROOT / "green_ops_build_table.py"), *pairs,
            "--measurement-status", "analytical_simulation", "--require-target", "target_total_energy_mj",
            "--table-output", str(output / "analytical-table.csv"),
            "--manifest-output", str(output / "analytical-table.json")], check=True)
    except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print("Demo complete: two unmeasured rows and two analytical contract-test rows. No hardware capture.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
