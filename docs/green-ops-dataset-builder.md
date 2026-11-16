<!-- SPDX-FileCopyrightText: 2026 Parth Shailesh Thite -->
<!-- SPDX-License-Identifier: MIT OR Apache-2.0 -->

# Green-Ops dataset builder

The builder joins validated telemetry CSV, run metadata, and optional experiment
plan and PPK2 summary artifacts into one dataset row and a provenance manifest.
It uses the Python standard library.

## Usage

Run from the repository root:

```bash
python3 tools/green_ops/green_ops_build_dataset.py \
  --telemetry-csv events.csv \
  --run-metadata run.json \
  --dataset-output dataset.csv \
  --manifest-output manifest.json
