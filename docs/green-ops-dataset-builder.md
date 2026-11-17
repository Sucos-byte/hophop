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
```

## Optional inputs

- `--experiment-plan plan.json`: supplies matching planned experiment settings.
- `--ppk2-summary ppk2.json`: supplies validated measured energy and mean power.

Run identities and provenance must agree across inputs. Output directories must
exist. Output paths must differ from inputs and each other. Existing outputs
are refused.

Outputs are reserved exclusively. Caught publication failures trigger cleanup.
The two outputs are not a filesystem transaction; abrupt termination may leave
files requiring inspection.

Exit status is 0 on success and 1 for argument, validation, or file errors.

## Counter interpretation

Each dataset row represents one run.

For each segment, aggregation takes the maximum of each cumulative counter.
It then sums those maxima across segments. This assumes a zero counter baseline
for each segment. A capture beginning partway through a run can include activity
that occurred before logging started.

`delivered_packets` currently counts decoded receive packets.
`packet_delivery_ratio` divides decoded packets by receive attempts, or is empty
when attempts are zero. Receive attempts do not independently count transmitted
packets, so this ratio does not establish end-to-end radio delivery.

`tx_successes` counts successful transmit API calls, not confirmed remote receipt.
RTT remains empty because the current telemetry does not measure it.

## Energy targets

Without a PPK2 summary, measurement_status is unmeasured and energy targets
remain empty.

With a validated PPK2 summary and matching hardware provenance:

- target_mean_power_mw comes from the summary.
- target_total_energy_mj comes from the summary.
- target_energy_per_delivered_packet_uj equals total_energy_mj * 1000 /
  delivered_packets, or is empty when delivered_packets is zero.

Hardware experiments must establish calibration and confirm that energy and
packet counts cover the same measurement interval. Schema validation alone
does not establish these conditions.

## Provenance manifest

The manifest records run identity, source and execution kinds, measurement
status, input paths, input SHA-256 hashes, row count, and feature and target
column names.

The feature list describes available columns. Prediction-time feature selection
and target-leakage prevention require a separate training design.

## Synthetic demonstration

The synthetic-demo.log fixture, converted using run ID synthetic-demo-001,
produces two segments, three receive attempts, three decoded packets, two
beacons, and two successful transmit API calls.

Pair it with synthetic run metadata and missing power and RTT provenance.
Energy targets and RTT remain empty. Experiment settings remain empty unless
an experiment plan is supplied.

Synthetic fixtures demonstrate software behavior and provide no measured
energy labels for model training.

See green-ops-log-parser.md and green-ops-run-metadata.md for input creation.

## Validation

Run from the repository root:

```bash
python3 -W error::ResourceWarning -m unittest discover \
  -s tools/green_ops/tests -v
```

## Explicit bounded dataset v2

Use `--dataset-version 2 --measurement-window WINDOW.json` with the existing
CLI arguments. Optional `--delivery-summary DELIVERY.json` supplies unique
logical packet evidence. V1 remains the default and rejects v2-only flags.
Measured v2 requires a bounded PPK2 summary v2; regenerate summaries from the
source capture rather than changing a version number.

V2 column order is the frozen v1 order with `rx_attempts` renamed to
`rx_operations`, old `delivered_packets` to `rx_decoded_packets`, and old
`packet_delivery_ratio` to `rx_decode_per_operation_ratio`; append, in order:
`window_duration_ms`, `offered_packets`, `delivery_status`,
`evaluation_group_id`, `analytical_model_id`, `delivered_packets`,
`packet_delivery_ratio`. Counts are exact integers, ratios/power/energy/duration
are finite numbers, identity/status/configuration categories are strings.
Unavailable optional values are null (empty CSV cells). The new delivered count
uses unique receiver acceptance divided by unique sender offers for its ratio.
No correlated RTT evidence is accepted by this API yet, so RTT stays null.

Counters use endpoint subtraction, with observations required to be in the
single declared segment, between endpoints and nondecreasing in source order.
No delivery evidence means all application delivery values and energy per
delivery remain null. Zero offered packets gives a null ratio; zero delivered
packets gives null energy per delivery. Synthetic unmeasured energy stays null.
Analytical generation is a later explicit API; this builder cannot label a
simulation as measured through a PPK2 summary.

CLI tolerances are `--duration-tolerance-ms` (default 1),
`--duration-tolerance-fraction` (0.001), and
`--max-alignment-uncertainty-ms` (1). The Python API additionally supports a
`max_window_duration_ms` policy propagated through all validators (default one
hour). These are software policies, not instrument specifications.

The v2 manifest records input hashes, CSV hash, policies, schema/registry
versions, roles and selected profiles. Profiles with missing capabilities are
null. The existing output reservation and rollback protect normal failures;
this does not establish multi-file crash atomicity or evidence authenticity.
