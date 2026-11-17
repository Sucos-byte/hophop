<!-- SPDX-FileCopyrightText: 2026 Parth Shailesh Thite -->
<!-- SPDX-License-Identifier: MIT OR Apache-2.0 -->

# Green-Ops bounded PPK2 summary v2

validate_ppk2_summary_v2 validates a PPK2 summary against an explicit
measurement window and returns an independent copy.

The existing v1 validator and loader retain their original behavior.
The Week 4 dataset CLI still consumes v1; dataset v2 integration is pending.

## Required summary fields

- summary_version: integer 2
- run_id: matching run identifier
- instrument: nordic-ppk2
- target_mean_power_mw: finite positive number
- target_total_energy_mj: finite positive number
- window_id: matching measurement-window identifier
- window_duration_ms: finite positive number
- voltage_v: finite positive number
- raw_capture_sha256: 64 lowercase hexadecimal characters
- alignment_reference_sha256: matching window alignment reference hash

Unknown or missing fields are rejected. Boolean values are not numbers.

## Duration policy

The permitted duration difference is the larger of:

- duration_tolerance_ms, default 1.0 ms
- duration_tolerance_fraction times window duration, default fraction 0.001

The window is independently revalidated, including its default one-hour bound
and single-segment continuity requirement.

## Energy consistency

Expected energy in mJ equals:

mean power in mW * summary duration in ms / 1000

The permitted energy difference is the larger of:

- energy_tolerance_mj, default 0.001 mJ
- energy_tolerance_fraction times expected energy, default fraction 0.001

Reported mean power and energy must describe the same integration interval.
Derived nonfinite or zero energy is rejected.

Tolerances must be finite and nonnegative; fractional tolerances cannot exceed
one. These defaults are configurable engineering policies, not PPK2 accuracy
specifications. Record the applied values in the eventual dataset manifest.

## Alignment

The window alignment method must be gpio or serial.
Synthetic alignment is rejected. Declared uncertainty must not exceed
max_alignment_uncertainty_ms, default 1.0 ms.

The summary alignment reference must match the window reference.
A matching hash string does not prove that evidence exists, and equal durations
alone do not establish that acquisition intervals overlap. Acquisition and
dataset integration must verify the referenced evidence and clock mapping.

## Evidence and limitations

Tests use constructed summaries and windows. They validate software behavior
and do not constitute measured hardware results.

This API does not integrate a raw PPK2 trace, establish calibration, verify supply
wiring, authenticate evidence, or load v2 JSON files. It accepts an already
decoded dictionary. Strict file loading and dataset v2 integration are subsequent
work.
