<!-- SPDX-FileCopyrightText: 2026 Parth Shailesh Thite -->
<!-- SPDX-License-Identifier: MIT OR Apache-2.0 -->

# Green-Ops measurement window contract v1

measurement_window.py validates bounded observation summaries and computes
counter increments by subtracting explicit endpoint snapshots.

## Window fields

Required fields are window_version, run_id, window_id, clock_id, start_us,
end_us, window_duration_ms, segment_id, observed_segment_ids, start_counters,
end_counters, alignment and evaluation_group_id. Unknown fields are rejected.

Version is integer 1. Identifiers contain 1–64 safe ASCII characters.
Timestamps are nonnegative integer microseconds in the declared clock domain.
End must exceed start. Duration must match the timestamp difference within
0.001 ms absolute tolerance and stay within the configurable duration limit.
The default maximum is one hour.

Exactly one observed segment must match segment_id. Endpoint counters contain
rx_attempts, rx_data_packets, sync_beacons and tx_successes. Counter values must
be nonnegative integers below the saturated unsigned 32-bit value.
Decreases, wraps and saturated endpoints are rejected.

Counter deltas equal end minus start. A nonzero starting value is never
silently treated as zero. compute_counter_deltas currently applies the default
one-hour validation limit.

## Alignment

Alignment contains method, reference_artifact_sha256, start_marker_id,
end_marker_id and uncertainty_ms.

Methods are synthetic_fixture, gpio or serial. Marker identifiers must differ.
Uncertainty must be finite and nonnegative. Reference hashes contain exactly
64 lowercase hexadecimal characters.

This layer checks the supplied summary. It does not inspect raw captures,
establish clock synchronization, or impose a measured-run uncertainty budget.
Those checks belong to measured dataset integration and the acquisition protocol.

## Delivery evidence

validate_delivery_summary requires summary_version, run_id, window_id,
sender_id, receiver_id, offered_packet_ids, delivered_packet_ids and
evidence_sha256.

Version is integer 1. Run and window IDs must match the expected values.
Packet ID lists must contain unique safe identifiers. Delivered IDs must be
a subset of offered IDs. Empty offered and delivered lists are valid.

Adapters must construct logical packet IDs with session identity, preserve IDs
across retries and deduplicate receiver observations. Count delivered logical
packets from this evidence rather than receive-operation counters.

Summary validation establishes internal consistency. A syntactically valid hash
does not prove that its evidence exists or is authentic.

## API and loading

validate_measurement_window returns an independent validated copy.
compute_counter_deltas returns the four endpoint differences.
validate_delivery_summary returns an independent validated copy.

load_measurement_window reads strict UTF-8 JSON and rejects duplicate keys,
nonfinite constants and invalid schema values. File and decoding errors propagate.

## Synthetic fixture

fixtures/measurement-window-synthetic.json represents a one-second window
with nonzero starting counters. Expected increments are five receive attempts,
four decoded packets, one beacon and two successful transmit API calls.

Its alignment is synthetic_fixture and its hash is an illustrative placeholder.
It is software test data, not a physical acquisition record.

## Remaining integration

Dataset v2 must combine these contracts with telemetry continuity checks,
PPK2 duration/alignment validation and evidence-backed delivery counts.
The existing Week 4 builder does not yet consume these new contracts.
