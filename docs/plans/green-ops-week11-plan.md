# Week11 readiness plan — five analytical workload faults

Planning/readiness only; implementation has not begun. Entry requires reading
tracker, remote-verification report, actual analytical/state/delivery contracts
and current APIs. Preserve standard-library installation, frozen Week7 models,
Week8 calibration/evidence and gate/report exit semantics. No hardware fault,
physical measurement, calibration retuning, live radio or deployment authorized.

## Required core scope (artifact errors are supplemental)

| Fault | Required modeled mechanism / observation | Accounting and evidence cautions |
|---|---|---|
| CPU busy-poll | Requested idle/sleep time replaced by explicit CPU-active duration or incremental CPU load | Current model has only idle/rx/tx currents, no sourced CPU-active profile. New CPU-current delta and busy timing must be sourced appropriately or declared configurable assumptions with ranges. Avoid adding an entire overlapping CPU+radio current twice. |
| TX power lock | Separate intended TX-power policy from modeled actual fixed-high setting; record requested/actual divergence | Existing sourced profile only19dBm at3.7V/25C/minimum-latency. Do not invent a sourced lower-power DECT current curve or substitute LTE. Intent mismatch can be observable while quantitative lower-power energy remains an explicit assumption/unknown. |
| Retry storm | Excess attempts/retries from explicit retry/loss/control fault, retaining per-attempt TX/RX/backoff/prepare accounting | Keep logical delivered-packet denominator; never replace missing energy-per-delivery with0. Bound attempts by actual window; no free retry energy or hidden time overflow. |
| Beacon hyper-wakeup | Explicit beacon/wakeup rate above intended schedule, with extra preparation/listen/RX durations | Current generator sync_beacons baseline0; add versioned modeled semantics rather than relabeling ordinary data packets. Unsupported wake timings/currents are assumptions. Beacons are not delivered data packets. |
| Fragmentation-bloat | Excess fragments/header/handshake overhead per logical payload, with per-fragment attempt energy and reassembly outcome | Keep logical payload/offers distinct from transmitted fragment bytes/counts. Delivery requires declared complete logical reassembly; no per-fragment denominator disguised as per-packet energy. |

All five must exist as actual workload/state/energy analytical cases, not merely
corrupted JSON, parser exceptions or output collisions. Artifact tampering,
missing inputs, policy errors and rollback are extra robustness tests only.

## Pre-implementation contracts and controls

1. Freeze a versioned fault recipe, intended-versus-actual control/state contract,
   model/parameter/assumption IDs and SHA256s, fault IDs/severity units/ranges,
   parent-family lineage, seeds and window semantics before examining outcomes.
   Every baseline/fault/repetition/parameter variant stays with one parent group.
   Consumed Week7/8 calibration/evaluation/stress sets cannot be called fresh.
2. Use source_kind=synthetic,execution_kind=simulation,
   measurement_status=analytical_simulation. No fake PPK2/observed RTT. Distinguish
   sourced currents/conditions from added CPU/power/wakeup/fragment assumptions.
3. Declare state overlap rules, time conservation and bounded-horizon behavior.
   If severity makes a complete planned workload infeasible, record incomplete
   execution or reject explicitly; never silently discard time/energy. Integrate
   all included states exactly once and preserve window/delivery alignment.
4. Freeze normal/zero-fault controls and each fault's activation/ground-truth
   mechanism. A structured analytical violation/oracle is separate from an
   energy budget, model residual or physical detection claim. No threshold tuning
   on already consumed evaluation outcomes.
5. Preserve model feature availability: same permitted pre-run X and fixed model
   cannot observe hidden CPU/retry/beacon/fragment/control divergence merely from
   commit labels. Record those blind spots. Fault ground-truth annotations must
   not enter X or be passed off as learned predictive detection.
6. New fault model/assumption scopes generally fall outside frozen calibration;
   default gate must ABSTAIN, not silently reuse marginal95% intervals. Explicit
   research override never establishes hardware or shifted-distribution coverage.
   Do not count ABSTAIN automatically as successful fault detection.

## Task-by-task implementation proposal after authorization

1. Inspect current model source/state APIs and available Nordic support; define
   the above five fault/control contracts with explicit source gaps, defaults,
   ranges and sensitivity checks. Commit verified plan/recipe before cases.
2. Implement deterministic standard-library workload/state fault generation and
   independent energy/time/delivery oracles. Preserve v1/v2 tables and existing
   model/feature contracts; version any genuinely extended fault artifacts.
3. Verify every core fault with zero/boundary/severe cases, independent simple
   expected energy values/units, time conservation, logical delivery, no duplicate
   loss/idle accounting, deterministic seeds/hashes and parent-group isolation.
   Test cases that cannot fit the window without hiding incomplete execution.
4. Integrate compatible research diagnostic/gate/Markdown output with explicit
   intended/actual divergence, analytical attributions/assumptions and unsupported
   calibration/observability results. Preserve0/1/2/3 and failure propagation.
5. Add artifact-error/rollback tests as supplemental coverage; run all core
   workload fault tests plus existing suite/build/smoke checks. Commit each
   verified milestone, update tracker/handoff and atomic Windows snapshot.
6. Save inspectable normal+five-fault examples and honest oracle/model/gate
   outcomes without labeling failed coverage as energy approval. Prepare Week12
   detection/false-positive/severity/boundary benchmark design; do not replace
   the five faults with artifact-error success counts.

## Readiness limitations

Remote software verification can establish runner/toolchain/test/smoke behavior,
not physical fault detectability, CPU current accuracy or validated battery life.
Fork push does not exercise the PR-only legacy Build workflow, fork-PR approval
policies or full board/application matrix. Those remain separately scoped checks.
No measured hardware accuracy, validated95% coverage, universal battery compliance
or deployability follows from a successful software run.
