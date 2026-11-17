# Week 5 code review — 17 November 2026

Reviewed the actual changes from `25b1aaa` through entry HEAD `eb6e936` against
`green-ops-week5-plan.md`, including source, existing tests, CLI/publisher and
new failing regression cases. Entry branch was
`green-ops/week5-measurement-contract`, working tree clean. No applicable
AGENTS.md was found. No delegated agents or remote publication were used.

## Findings and corrections

| Severity | Finding | Correction / regression evidence |
|---|---|---|
| High | Non-null columns were inferred as prediction capabilities; observed duration could qualify an early-terminated run for pre-run extraction. | Explicit prediction context and capability list; no context gives no selected profiles. Recorded pre-run rows require completed planned duration; post-run diagnostics can remain available. Tests cover missing context, mismatched duration, early termination, bool/target declarations, CLI round-trip and failure cleanup. |
| High | Validated delivery counts and energy-per-delivery labels could enter a table without a delivery-summary reference. | All validated delivery rows require delivery_summary path/hash, including modeled analytical delivery. Tests reproduce missing-reference rejection and acceptance with a reference. Summary authenticity remains separate. |
| High | Hardware RTT could be accepted using an arbitrary rtt_evidence hash without a correlated-evidence validator. | Hardware RTT rejected until that contract exists. Analytical RTT remains explicitly model-generated. Regression supplies an opaque hash and verifies rejection. |
| Medium | Files were read for parsing and then reopened for hashing; a changed file could produce a digest unrelated to the validated content. | Dataset v2 CLI/file loading and artifact loading use byte snapshots. Two regression cases mutate files after parsing and check that hashes still describe the consumed bytes. |
| Medium | CSV numeric columns were always parsed as floats, rounding valid exact integer energy targets above 2**53. | Preserve integer numeric tokens; retain float probability semantics. Test round-trips 2**53+1 exactly. |
| Medium | Unterminated quoted empty CSV cells could be accepted with an otherwise matching hash. | Strict CSV syntax; csv.Error becomes ValueError for v2 sources/artifacts. Regression reproduces the malformed accepted artifact. |
| Medium | Policy schema/value validation applied only to measured manifests, allowing invalid policies in excluded sources. | Validate declared policies for every source before filtering. Empty policies remain permitted for nonmeasured fixtures; measured sources require all policies. |

Feature contract version is now 3 because availability and recorded pre-run
qualification semantics changed. Dataset version 2 and its exact field order
are unchanged. Regenerate older v2 manifests from source artifacts; no automatic
promotion of legacy availability claims. V1 header, row builder, extraction
profiles, PPK2 v1 API and default CLI behavior remain compatible.

## Remaining plan checks

- Both v1/v2 feature partitions are exhaustive and disjoint. New tests freeze
  header order and reject v2 role overlap, duplicate and unclassified fields.
  Targets, seed and group IDs are excluded from X. Simulation loss context
  remains outside default profiles. Count ablation is still required for
  post-run energy-per-delivery modeling in later evaluation.
- Windows reject reset/saturation/multiple segments and subtract nonzero
  endpoints. Source observations must remain in bounds and nondecreasing.
  New integration coverage accepts both endpoint snapshots, rejects an
  observation below baseline, and preserves the expected delta. The event CSV
  has no device timestamps: half-open interval membership still requires raw
  acquisition evidence; this summary validator cannot independently prove it.
- PPK2 power/energy/duration and run/window/alignment validation remain enforced.
  New builder-level checks exercise the exact duration boundary, serial
  uncertainty threshold, hash mismatch and inconsistent energy. Configurable
  duration policy still propagates through callers.
- Tables validate sources before filtering, preserve nulls/groups, require
  analytical references, reject duplicate runs, and sort deterministically.
  Existing reversed-input/digest/rollback/alias tests pass. A reference digest
  establishes byte identity rather than physical truth or trusted authorship.
  External artifacts must enter through load_dataset_artifact; in-memory dict
  digests are trusted caller assertions, not an authentication mechanism.

## Verification

15 new review tests pass. Full suite: **197 passing tests**, with ResourceWarning
treated as errors. `git diff --check` passes. Reproduced the standard-library demo
in `/tmp/green-ops-week5-review-demo`: two synthetic unmeasured rows with null
labels and two separate analytical contract-test rows; both table builds pass.
These are fixed arbitrary contract fixtures, not physical/model accuracy data.

## Week 6 readiness

Ready to implement the sourced analytical generator using the corrected dataset
v2 / feature-contract 3 interface. Week 6 must add an explicit analytical API,
technical source/parameter audit, versioned assumptions/configuration, ranges,
seed/state-time integration, and independent energy oracles/scenarios. Model
labels must never be obtained by inventing measured PPK2 summaries.

Not ready to claim calibrated hardware accuracy or train a scientifically
validated model from the Week 5 fixtures. Actual raw lab acquisition remains
pending. Group independence, train-only preprocessing and count ablations are
later evaluation requirements. Prospective candidate inference needs a planned-
workload input path; recorded-run completion assertions must not be invented for
unexecuted candidates. Actual hours remain unreported. No push or publish.
