# Green-Ops feature contract v1

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

This version preserves the Week 4 dataset schema. Dataset v2 and measurement
window contracts are subsequent Week 5 increments.
