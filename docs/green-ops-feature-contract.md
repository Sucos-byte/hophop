# Green-Ops versioned feature contract

The registry partitions dataset schema v1 into metadata, potential prediction
features, and targets. Classification is exhaustive and roles are disjoint.
Schema changes require explicit classification.

Targets are mean power, total energy, energy per delivered packet, and RTT.
Identifiers, provenance, seeds, repetitions and segment count are metadata.

The pre_run profile selects payload_size_bytes, interval_ms and tx_power_dbm.
These describe requested configuration; acquisition must separately verify
whether the workload applied that configuration.

The post_run profile additionally selects rx_attempts, delivered_packets,
sync_beacons, tx_successes and packet_delivery_ratio. It requires diagnostics
from the evaluated run. The v1 delivery fields retain their legacy decoded
receive semantics; they do not establish end-to-end packet delivery.

Loss-scenario fields are potential features but are excluded from both default
profiles. They require a future explicit capability profile.

available_fields declares which inputs the execution system can supply.
A CSV header alone does not establish availability. Selected missing, null,
boolean, nonfinite, incorrectly typed or out-of-domain values are rejected.
Extraction does not mutate rows or impute missing values.

Feature extraction validates selected values. Complete artifact validation,
counter consistency and provenance checks remain separate requirements.
A post-run ratio can be individually valid while inconsistent with other
counters; the dataset validator must reject that inconsistency.

Disjoint columns prevent direct target inclusion. They do not by themselves
prevent leakage through collection timing, related experiment groups,
preprocessing or energy-derived inputs. Training must enforce those rules.

Post-run delivery counters also relate to the energy-per-delivery target's
denominator. Report this diagnostic prediction context and evaluate an ablation
without those counters before interpreting predictive performance.

The legacy profiles above preserve the Week 4 dataset schema; the v2 registry
below supplies the bounded Week 5 contract.

## Registry v2

`FEATURE_CONTRACT_VERSION=2` adds a separate exhaustive schema-v2 partition.
`feature_roles(1)` and the v1 selectors preserve the legacy classification and
profiles; public role/profile constants now describe v2.

V2 pre-run inputs are payload size, interval, requested TX power and planned
`window_duration_ms`. Use that profile only for a fixed-duration workload that
completed as planned; an early termination needs a separate post-run context.
V2 post-run adds `rx_operations`, `rx_decoded_packets`, `sync_beacons`,
`tx_successes`, `rx_decode_per_operation_ratio`, `offered_packets`,
`delivered_packets` and `packet_delivery_ratio`. A missing delivery capability
prevents selecting this full diagnostic profile; it never becomes zero.
Delivery status, evaluation group and analytical model identity are metadata.
