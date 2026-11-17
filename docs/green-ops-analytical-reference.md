# Analytical reference generation

Week 6 adds deterministic **synthetic / simulation / analytical_simulation**
artifacts through an explicit API, not through measured dataset/PPK2 APIs.
It preserves dataset v1 and the frozen dataset v2 fields and uses current
feature-contract 3 / table validation. No hardware accuracy is established.
The fixed Week 5 analytical contract fixtures remain separate test data.

## Sources and assumptions

The [source audit](green-ops-analytical-sources.md) pins official Nordic nRF9151
Product Specification 1.1 (June 2025), the named DECT NR+ current table/symbols,
and its common conditions. The shipped parameter file is
`tools/green_ops/models/nrf9151-dect-reference-v1.json`; its source catalog is
included in the parameter hash. `analytical-assumptions-v1.md` in that directory
is separately hashed and archived. No LTE currents are used for DECT behavior.

The profile is confined to minimum-latency mode, band 1, requested TX 19 dBm,
RX signal -90 dBm, 3.7 V and 25 C. Currents are exclusive VDD scenario totals.
No current scaling with TX power, voltage, temperature or payload is inferred.
Payload changes only assumed airtime. The application/board's real behavior
may differ. Deep sleep, CPU work, peripheral/board overhead, synchronization
beacons and interference are not modeled. No extra CPU/idle current is added
on top of the exclusive scenario values.

All preparation, airtime, ACK-wait and backoff durations, independent loss,
ACK/acceptance equivalence, current uncertainty envelope and optional RTT are
explicit assumptions. They carry numeric ranges in the profile. The assumed
current envelope is not a Nordic tolerance. These ranges are exploratory
scenario limits, not estimated distributions, joint extrema or confidence bands.

## State accounting and units

A reserved packet slot starts at `packet_index * interval_ms`. Each attempt
uses idle preparation, a TX phase, then an RX/ACK-wait phase. A failed attempt
may add idle backoff and retry. A successful attempt stops retries. Local TX
completions count all attempts; successful ACK decodes and logical deliveries
are different modeled outcomes. There is no independently simulated ACK loss
or application rejection. No synchronization beacon process is enabled.

Timing uses exact integer microseconds. The assumed packet TX duration is
`tx_base_us + payload_size_bytes * tx_per_byte_us`. Before sampling, every
packet's complete worst-case retry path must fit its slot, and all offered
packets must have complete slots inside the fixed window. Oversubscribed work
fails rather than being truncated or accepted only on lucky random outcomes.
Unused time, including preparation/backoff, is idle. Exclusive state times sum
exactly to the observation window. Offers belong to `[0,end)`; acceptance exactly
at `end` is separately retained as late and excluded from delivery/ACK counts.

For each state, energy in mJ is `voltage_V * current_mA * duration_us / 1e6`.
Total energy is the sum; mean power in mW is energy_mJ divided by duration_s.
Energy per delivery in uJ is energy_mJ times 1000 divided by positive unique
in-window deliveries. Zero traffic still consumes idle energy. No delivery
leaves that target null. Zero offered packets gives null delivery ratio.

Independent unit oracle: 100 ms at 10 mA and 900 ms at 1 mA accumulate 1.9 mC;
at 3 V this is 5.7 mJ, or 5.7 mW over one second. The tests also independently
calculate a complete packet schedule at the sourced point currents.

## Determinism and sensitivity

The versioned sampler SHA-256 hashes
`sha256-bernoulli-v1:seed:packet_index:attempt_index` as ASCII, interprets the
256-bit result as an unsigned uniform draw, and compares it to the loss
probability using integer arithmetic and its exact binary-float ratio. A draw
below the threshold means loss. No global PRNG, timestamps or random-current
sampling enters generation. Seed is an exact integer in [0,2**64-1].

Every nontrivial parameter range is checked at its low and high value, one
parameter at a time with common random draws. Variants are explicitly marked
assumptions, including changes to sourced point currents. The sensitivity file
records variant parameter digests, changed value/unit, energy/delivery/RTT
results, or an invalid status with reason. Invalid cases are retained, not
silently dropped. These cases are diagnostics, not extra independent training
rows. Changes in timing replace idle duration; they can change boundary outcomes.

RTT defaults to null. Setting rtt_extra_ms to an assumption parameter enables
mean modeled offer-to-ACK latency among delivered packets, including retries,
preparation and backoff, plus that extra delay. It excludes losses and late
acceptance, so it is conditional on success. The extra delay adds no local
radio time/energy; this limitation is explicit. No observed clock/latency is used.

## Strict APIs and schema

`analytical_reference.py` exports validate_model, validate_workload,
integrate_states, simulate_reference, sensitivity_analysis, and
`generate_analytical_artifact(parameters_bytes, workload_bytes,
assumptions_bytes, prediction_context_bytes=None)` (context is a keyword).
The latter returns a mapping of fixed file names to exact UTF-8 byte snapshots.
Model/workload validators return independent copies and reject unknown keys,
booleans as numbers, invalid units/ranges and nonfinite or overflowing values.
JSON readers reject duplicate keys, invalid UTF-8 and nonfinite constants.

Model schema 1 pins model_id, model_version, parameter_version, description,
conditions, source catalog, idle/TX/RX currents, five timing parameters, loss
probability and optional RTT. Each parameter has exactly value/min/max, unit,
basis (official_typical or assumption), source_id and range_note. Official
point values must match their catalog entry's value/unit and operating
conditions; unsupported extrapolations require an assumption basis and null
source_id. Catalog URLs must be official Nordic HTTPS addresses; human source
review remains necessary, since this is not runtime authenticity verification.

Workload schema 1 has exactly workload_version, run_id, evaluation_group_id,
seed, repetition, window_duration_ms, interval_ms, payload_size_bytes,
tx_power_dbm, offered_packets and max_attempts. Window/interval are positive
integer ms (up to one hour); payload is 1..4096 bytes, offers 0..10000 and attempts
1..16, with at most 100000 worst-case attempts. These are software bounds, not
radio specifications. TX power must equal the profile condition. Changing
parameters/assumptions should increment their declared versions; every byte
change is independently visible in hashes even if a caller forgets a version.

An explicit optional prediction-context file follows the existing contract.
Missing context selects no features. Pre-run qualification refers to a completed
**modeled** workload, never hardware execution. Post-run diagnostic features
here are simulation outputs; they cannot establish firmware/CI capability or
prospective candidate execution. Energy-derived values, seeds and groups remain
outside X. Later evaluation must ablate delivery counts for per-delivery labels.

## Reproduce two runs and a table

Choose a fresh parent directory (the commands below use `/tmp/green-ops-week6-demo`):

```bash
mkdir /tmp/green-ops-week6-demo
python3 tools/green_ops/green_ops_generate_analytical.py \
  --parameters tools/green_ops/models/nrf9151-dect-reference-v1.json \
  --assumptions tools/green_ops/models/analytical-assumptions-v1.md \
  --workload tools/green_ops/fixtures/analytical-workload-a.json \
  --prediction-context tools/green_ops/fixtures/analytical-context-pre.json \
  --output-dir /tmp/green-ops-week6-demo/a
python3 tools/green_ops/green_ops_generate_analytical.py \
  --parameters tools/green_ops/models/nrf9151-dect-reference-v1.json \
  --assumptions tools/green_ops/models/analytical-assumptions-v1.md \
  --workload tools/green_ops/fixtures/analytical-workload-b.json \
  --prediction-context tools/green_ops/fixtures/analytical-context-post.json \
  --output-dir /tmp/green-ops-week6-demo/b
python3 tools/green_ops/green_ops_build_table.py \
  --artifact /tmp/green-ops-week6-demo/a/dataset.csv /tmp/green-ops-week6-demo/a/manifest.json \
  --artifact /tmp/green-ops-week6-demo/b/dataset.csv /tmp/green-ops-week6-demo/b/manifest.json \
  --measurement-status analytical_simulation --require-target target_total_energy_mj \
  --table-output /tmp/green-ops-week6-demo/table.csv \
  --manifest-output /tmp/green-ops-week6-demo/table.json
```

Each bundle archives parameters.json, workload.json, assumptions.md, optional
prediction-context.json, configuration.json, state-accounting.json,
packet-evidence.json, delivery-summary.json, sensitivity.json, dataset.csv and
manifest.json. Delivery summary evidence is explicitly modeled; its hash binds
packet-evidence.json. The manifest records all source digests, model identity,
configuration/assumption digests and feature-contract roles/context. Parameter
version, seed and generator/sampler versions are in configuration/accounting.
Relative internal references make output bytes independent of destination paths.
No PPK2 summary or measured measurement window is generated.

The CLI refuses existing destinations and preserves input contents. Source
parsing and hashes use the same immutable snapshots, including missing trailing
newlines. Publication uses output reservation with rollback for ordinary errors;
this is not a crash-atomic multi-file transaction. Output parent must exist.
Failed publication removes only its owned outputs/empty directory. Invalid
contracts/files return 1; a successful complete bundle returns 0.

## Limits and next work

This is a conditioned analytical reference, not a calibrated DECT/DK simulator.
Independent physical traces are still needed to determine timing, current
variation, overhead, delivery semantics and latency. Group repetitions/shared
configurations/fault families together in later evaluation; distinct strings do
not prove independence. Keep held-out scenario/oracle checks independent from
the generator's own formula. Analytical fit accuracy cannot establish hardware
accuracy. Week 7 model training is outside this change; no validated model or
battery-autonomy claim follows from these generated labels.
