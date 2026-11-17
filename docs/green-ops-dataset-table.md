# Green-Ops dataset v2 tables

Tables contain complete homogeneous v2 rows. They preserve provenance and nulls;
model-specific X/y extraction remains separate. V1 CSVs must be regenerated
from original artifacts using the explicit v2 builder, window and delivery
contracts. Renaming an old header cannot supply missing evidence.

## Reproduce the acceptance demonstration

From the repository root, choose a new directory whose parent already exists:

```bash
python3 tools/green_ops/demo_dataset_v2.py /tmp/green-ops-demo-new
```

The runner refuses an existing destination. It loads saved source fixtures,
invokes the dataset CLI twice, and builds `synthetic-table.csv` with two distinct
runs and evaluation groups, null energy and null RTT. It separately writes two
fixed analytical **contract-test** rows and builds `analytical-table.csv` with
power/energy labels, model ID/version, configuration and assumptions hashes.
These arbitrary numbers test provenance interfaces; they are neither calibrated
predictions nor physical measurements. The Week 6 generator remains separate.
No PPK2 summary is constructed to label analytical data as measured.

Saved sources are `tools/green_ops/fixtures/dataset-v2-demo.json` and the
`analytical-contract-*` files alongside it. Generated artifacts belong in the
fresh output directory. PPK2/GPIO unit fixtures are simulated contract checks,
not hardware captures. Lab work remains pending; see the
[acquisition protocol](green-ops-measurement-readiness.md).

## Table command

```bash
python3 tools/green_ops/green_ops_build_table.py \
  --artifact /tmp/green-ops-demo-new/synthetic-1.csv /tmp/green-ops-demo-new/synthetic-1.json \
  --artifact /tmp/green-ops-demo-new/synthetic-2.csv /tmp/green-ops-demo-new/synthetic-2.json \
  --dataset-version 2 --measurement-status unmeasured \
  --table-output /tmp/green-ops-demo-new/audit.csv \
  --manifest-output /tmp/green-ops-demo-new/audit.json
```

Repeat `--artifact CSV MANIFEST` once per run. Select exactly one status:
`unmeasured`, `measured` or `analytical_simulation`. All sources are validated
before filtering, including sources whose status will be excluded. Duplicate
runs or artifact references fail. Mixed versions and incompatible schemas fail;
matching schema meanings permit multiple adapters but establish no claim of
cross-platform transfer.

Use repeated `--require-target TARGET` for a labeled selection. Missing targets
fail by default; `--missing-target-policy exclude` records excluded run IDs and
reasons. An unmeasured audit selection should request no targets. Unmeasured
energy cannot enter a labeled training table. Supported targets are exactly
mean power, total energy, energy per delivery and RTT from the feature registry.

Outputs must be distinct new files and cannot alias sources. Successful nonempty
selection returns 0 and prints accepted/excluded counts. Argument, encoding,
file, schema or empty-selection failures return 1. The existing publisher reserves
both destinations and rolls back ordinary publication failures. This is not a
multi-file crash transaction. Sources are never overwritten.

Rows sort by run ID. Manifests include table/dataset/registry versions, selected
status and target policy, sorted IDs/groups, source CSV and manifest hashes,
included/excluded counts with reasons, per-target null counts and output CSV
hash. No volatile timestamps are added. Input order does not affect table bytes
or manifest bytes. Group IDs are preserved, but independent scientific groups
must be established from collection history.

## Frozen v2 scalar types

The exact order is documented in [dataset builder migration](green-ops-dataset-builder.md)
and frozen by `DATASET_FIELDS_V2`. No duplicate names are allowed.

| Type | Columns |
|---|---|
| Exact integers | dataset_version, payload_size_bytes, interval_ms, tx_power_dbm, seed, repetition, segment_count, rx_operations, rx_decoded_packets, sync_beacons, tx_successes, offered_packets, delivered_packets |
| Finite numeric values | good_to_bad_probability, bad_to_good_probability, good_state_loss_probability, bad_state_loss_probability, rx_decode_per_operation_ratio, packet_delivery_ratio, window_duration_ms, ping_rtt_latency_ms, target_mean_power_mw, target_total_energy_mj, target_energy_per_delivered_packet_uj |
| Strings | run_id, adapter, feature_profile_id, source_kind, execution_kind, measurement_status, loss_model, loss_preset, loss_initial_state, delivery_status, evaluation_group_id, analytical_model_id |

Only unavailable configuration/loss fields, seed/repetition, optional delivery
counts/ratios, analytical model ID and targets may be null. Duration and bounded
radio counters are required. Integers reject booleans and fractional notation;
CSV empty cells become null, never zero. JSON duplicate keys, unknown manifest
keys, nonfinite values and invalid UTF-8 fail. Counter/ratio and energy-per-
delivery relationships are revalidated. V2 manifests use exact keys emitted by
the dataset CLI, including `prediction_context` (object or null); analytical
manifests add only `analytical_reference`. Feature contract version 3 requires
regenerating older v2 manifests from source artifacts.

The analytical reference has exactly `model_id`, `version` (nonempty string),
`configuration_sha256`, and `assumptions_document_sha256`. Hashes must match
`input_sha256.configuration` and `input_sha256.assumptions_document`; reference
identity must match the row. Status alone cannot establish analytical provenance.
Source digests establish byte identity rather than authorship or physical truth.
The loader does not require archived source paths to remain locally accessible;
source capture review is a separate acceptance step.


## Reviewed evidence and integrity boundaries

Validated delivery counts require a `delivery_summary` input path/hash, even
when the energy-per-delivery target is null or zero deliveries were observed.
A status string and count arithmetic alone do not establish a delivery source.
Measured/hardware RTT stays null until a correlated-evidence validator exists;
an opaque hash alone is insufficient. Analytical RTT is model-generated and
requires the analytical model reference.

The artifact loader reads CSV/manifest snapshots once and hashes exactly the
bytes parsed. Malformed CSV quoting is rejected; integer-valued numeric targets
retain precision rather than being rounded through binary floats. All declared
policy values are checked, including sources subsequently excluded by filtering.
Use `load_dataset_artifact` for external files before `build_dataset_table`;
in-memory dictionaries and their supplied digests are trusted caller inputs,
not an authenticated serialization format. The table does not reopen archived
raw traces to establish their physical truth.
