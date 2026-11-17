# Week 6 review before Week 7 training

Reviewed actual `1726971..9ed6b96` source, profiles, artifact/table/feature
contracts and tests, then verified local corrections. Entry branch:
`green-ops/week6-analytical-reference`, clean at
`9ed6b96906bf4cd475aadbab14603c2360cb6e25`. No applicable AGENTS.md found.
No training, push or publication was performed.

## Findings and corrections

| Severity | Finding | Correction / evidence |
|---|---|---|
| High | Identical pre-run X can hide different offered counts, retry limits and model coefficients. The old demo's partial offers cannot be inferred from its inputs. | New full-slot workload planner derives offers as floor(duration/interval). Readiness audit rejects primary scope when offers are not derivable or retry/parameter/assumption settings vary outside X. A test demonstrates identical X with different offer counts/energy. General single-run APIs stay compatible. |
| High | Arbitrary group strings and per-run seeds did not establish safe split units. Same seed reuses SHA-256 draws across unrelated configurations. | Stable traffic-family IDs; all duration, repetition and parameter variants stay together. Group-local seed derivation, common draws only within a group. Audit rejects split families, cross-group seed reuse and duplicate realizations, including numeric-spelling-only variants. |
| High | Table CSV/manifest hashes alone do not verify archived model/workload/report relationships for training. | Additional bundle audit verifies local source hashes, configuration/row identity, modeled delivery/context, and replays state/packet and sensitivity accounting. Tests reject changed sources, coherently rehashed but mismatched source joins, forged counts/diagnostics, empty assumptions and escaping paths. |
| Medium | V*I could overflow or underflow before duration scaling even when final energy was representable. | Complete product is evaluated with an explicit isolated Decimal context before float conversion. Tests cover balanced extremes, genuine overflow, and independence from caller decimal settings. Generator arithmetic patch 1.0.1. |
| Readiness gap | Two rows and sensitivity diagnostics do not form a grouped evaluation dataset. | Deterministic grid API plus a verified 96-row primary panel and 192 separately scoped stress rows. Group counts, feature/target variation and pre-run scope are audited. Sensitivity cases are not training repetitions. |

Verified correction milestone: `f8c35bf`; subsequent targeted checks also cover
numeric-spelling duplicate detection and isolated arithmetic context. V1 APIs,
dataset v2 fields, feature-contract 3 and single-run/table behavior are unchanged.
Legacy generator 1.0.0 bundles remain readable/auditable; replay tolerates only
small arithmetic rounding differences. No automatic promotion to measured data.

## 1. Source revision, units and applicability

Rechecked these official Nordic pages on 17 November 2026:

- [Revision history](https://docs.nordicsemi.com/r/bundle/ps_nrf9151/page/chapters/rev_history/nrf9151_rev_history.html): PS 1.1, June 2025.
- [DECT NR+ current table](https://docs.nordicsemi.com/r/bundle/ps_nrf9151/page/_tmp/alta.nrf9151/autodita/application.current/parameters.id_current_dect_nr.html): typical TX 235 mA at requested level 13 / 19 dBm, RX 47 mA at -90 dBm, idle 37 mA, minimum-latency mode. The HTML table is unnumbered; symbols/section are pinned in the catalog.
- [Current consumption, Table 1](https://docs.nordicsemi.com/r/bundle/ps_nrf9151/page/chapters/current_consumption/doc/frontpage.html): nominal 3.7 V/25 C and application-side common conditions, documented in the source audit.

The source supports these mode-conditioned point currents, not the workload's
airtime, retry probabilities or RTT. The shipped profile pins band 1; no LTE
PSM/eDRX/RRC figures, other-power current scaling or deep-sleep model are used.
Idle reference power is 136.9 mW, not a microamp sleep claim. All timings,
independent loss, ACK/acceptance equivalence, ±20% envelopes and optional RTT
remain configurable assumptions. The current/table scope is used as an
exclusive VDD scenario approximation, not a validated whole-DK measurement.
Human source review remains necessary: editable catalogs, URL allowlists and
hashes do not establish manufacturer authenticity or real firmware applicability.
See [full source audit](../green-ops-analytical-sources.md).

## 2. State-time, retry energy and boundaries

Exclusive integer-microsecond idle/TX/RX traces conserve the window. Active
states replace idle; prepare and backoff use idle current, so they do not add
another baseline. There is no additive CPU/peripheral estimate. Their actual
costs are omitted assumptions, not established zero-cost firmware behavior.
Worst-case attempts must fit complete reserved slots before any draw. No
outcome-dependent truncation or successful-only schedule selection occurs.

New independent retry oracle: three 1256 us TX and three 1500 us RX phases leave
991732 us idle in a one-second run. Energy is
3.7*(235*0.003768 + 47*0.0045 + 37*0.991732) mJ. This passes without reusing the
integrator to calculate the expectation. A separate test distinguishes an
internal slot boundary from the observation end: acceptance at 1000 us in a
2000 us window counts, while acceptance at 2000 us is late and excluded.
Zero traffic, total loss, retry exhaustion, exact conservation, source-order
segments and true numeric overflow continue to pass existing checks.

## 3. Provenance, hashes and determinism

All generated rows stay synthetic/simulation/analytical_simulation. Model,
parameter version, assumptions, seed and source digests are archived. No fake
PPK2 or observed RTT is constructed. The new design loader checks archived
bytes against hashes, source/configuration/row identity, packet IDs and delivery
summary, and deterministic replay. It refuses unsupported generator versions
or references outside the bundle. The general table loader remains compatible;
its byte-identity contract is not silently changed into source authentication.

Grid ordering and family/seed/run IDs are deterministic and target-independent.
variant_id changes run identity but not family/random draws. Reversing grid
levels or audit input order yields the same result. Related variant draws are
intentionally paired, so they are grouped rather than counted as independent.

## 4. Multi-configuration acceptance

Executed `/tmp/verify_week6_design.py`; artifacts and reports are under
`/tmp/green-ops-week6-review-panel`. These are local generated artifacts, not
committed source fixtures or physical evidence. Exact recipe is in design.json.

| Panel | Rows | Declared traffic families | Timing coefficient | Mean-power range (mW) |
|---|---:|---:|---|---:|
| Primary nominal | 96 | 24 | 4 us/byte | 138.570–191.823 |
| Separate airtime-low stress | 96 | same 24 | assumed 1 us/byte | 138.500–164.817 |
| Separate airtime-high stress | 96 | same 24 | assumed 10 us/byte | 138.711–245.836 |

Axes: payload (16,32,64,128,256,512) bytes; interval (50,100,200,400) ms; window
(1000,2000) ms; two group-local seeded repetitions. Fixed requested TX 19 dBm,
retry cap 3 and nominal loss 0.1. All full-slot schedules validate. Each panel
has 48 distinct pre-run configurations, 24 groups and 48 random streams (the
shorter/longer windows reuse prefixes within groups). It is not 96 IID samples.
The primary panel builds through the existing table CLI with 96 accepted rows.
The combined 288-row audit retains 24 groups and correctly refuses to qualify
mixed hidden-coefficient panels as one primary pre-run problem. The original
two-row demo still loads but fails the offered-count/readiness policy.

## 5. Grouping and proposed Week 7 training dataset

The implemented traffic-family key is (payload_size_bytes, interval_ms,
tx_power_dbm); it excludes run IDs, seed, repetition, duration and model variant.
Each family maps to exactly one evaluation group. More conservative coarsening
is allowed: deliberately related parent configurations that alter these keys
must be assigned one shared parent group in the design, across all their runs.
Software cannot infer undisclosed parentage or true physical independence.
Group membership and source lineage must be frozen before seeing fit results.

Proposed primary pilot (not trained in this review):

| Element | Predeclared design |
|---|---|
| Model scope | One parameter hash and assumption hash; current nominal minimum-latency profile, fixed loss 0.1 and retry cap 3 |
| Payload levels | 16, 32, 64, 128, 256, 512 bytes |
| Interval levels | 50, 75, 100, 150, 250, 500 ms |
| Windows | 1000, 5000, 10000 ms; full-slot offers derived from those inputs |
| Repetitions | Five group-local seeds, generated before outcomes |
| Size | 36 families × 3 durations × 5 seeds = 540 rows |
| Split | Fixed group split: 24 train / 6 validation / 6 test families (360/90/90 rows), assigned by a recorded seed/hash before fitting |
| Stress evaluation | Two assumed airtime variants for the six untouched test families only: 90 rows each, 180 additional diagnostic rows; never pool them into primary training |

Keep every duration/seed/repetition/parameter variant of a family in its single
partition. A secondary parameter-holdout study must also hold out configuration
families; it cannot train on nominal siblings of its purported independent test
variants. Validate any alternate leave-payload/interval-level-out study as a
separate predeclared experiment. Do not optimize splits by labels. Reject bad
schedules with explicit reasons rather than silently deleting inconvenient rows.
Archive axes, group policy/lineage, seed policy, parameter/assumption hashes and
split assignments with the dataset. Six groups in the audit is a configurable
software-pilot minimum, not a statistical sample-size claim; the proposed 36
families remain a pilot design whose adequacy must be assessed per target.

## 6. Prediction inputs and what learning demonstrates

Primary pre-run X remains exactly payload, interval, requested TX power and
planned fixed duration. TX power is constant here, so the dataset cannot teach
power scaling. Offers are determined by a declared scheduling policy; retry
cap/loss/parameters are fixed global scope. If any of these vary, separate the
panels or define a future explicit versioned pre-run profile with planned inputs.
Do not silently reclassify post-run counts, overload GE loss fields with IID
loss, or place model IDs/parameter hashes into X as shortcuts.

Exclude labels, mean-power-derived energy, measured/state energy, state durations
reconstructed from targets, seeds, IDs, groups and future outcomes from X. Any
preprocessing is fit on training groups only. Input-only transforms such as
inverse interval or planned offer rate are computable before execution; they
must be declared and distinguished from actual delivery/attempt telemetry.

Optional post-run diagnostic models can nearly reconstruct this generator's
formula from attempts/payload/time. For energy-per-delivery, ablate ALL delivery
proxies: delivered_packets, rx_decoded_packets (equal to delivery in this model),
packet_delivery_ratio and rx_decode_per_operation_ratio. Dropping one count
while keeping a ratio/proxy is not a valid ablation. Label missingness/zero
deliveries must be filtered per target, never filled with zero. RTT remains
absent unless a separately declared analytical timing assumption is enabled.

Use constant and linear baselines plus an independent expected-energy oracle.
For full nonboundary slots with n offers, fixed loss p and retry cap m,
E[attempts per packet] = sum(p**k for k in range(m)). Thus expected total energy
is idle_power*T + n*E[attempts]*((TX_power-idle_power)*TX_seconds +
(RX_power-idle_power)*RX_seconds), using mW and seconds to obtain mJ. Compare this independently coded oracle and
simulation group means with unit/Monte Carlo checks. It is a comparator rather
than an input derived from labels. Expected per-delivery energy is not in
general E[energy]/E[deliveries]; its ratio and missing-label conditioning need
separate treatment. Realized state durations/attempt totals are diagnostic
evidence and cannot enter primary pre-run X. Report per-target MAE/RMSE and R² only when
truth varies, with group counts and failure/missing-label counts.

A successful fit demonstrates recovery/approximation of a known synthetic
accounting law and tests pipeline/group/generalization behavior under its
assumptions. It does NOT validate DECT physics, firmware costs, actual link
loss/latency, confidence intervals, battery autonomy or hardware accuracy.
Stress rows generated by the same implementation are robustness diagnostics,
not an independent physical validation set. Real raw lab captures remain needed.

## Verification and readiness

Targeted review/design tests cover numeric extremes/context isolation, independent
retry energy and boundaries, grid determinism, grouping/seed/duplicate policies,
source hashes/paths/joins/replay, old bundle compatibility and identical-X hidden
offers. **246 tests pass**, including **22 new review/design tests**, with ResourceWarning
treated as errors. `git diff --check` passes. All 288 acceptance bundles were
re-audited with final source/packet/sensitivity replay; reports were unchanged.
The old generator 1.0.0 demo remains auditable and is correctly rejected as a
primary training design. No fitting, split optimization or model selection ran.

**Week 7 is ready for a scoped grouped software pilot using audited fixed-scope
data. The old two-row demo and an indiscriminately pooled parameter grid are not
training-ready.** No physical-validation or calibrated-model readiness is claimed.
The proposed 540+180 design and frozen splits should be materialized/audited
before actual training; this review performed no fit or model selection.

Verified final correction/report commit: `ba268d8` (initial corrections
`f8c35bf`). A documentation-only tracker/handoff checkpoint follows. Test and
acceptance evidence above applies to that verified code; no suite rerun is
needed for the final documentation-only checkpoint.
