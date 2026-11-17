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

## Authorized implementation refinement and pre-outcome freeze

Verified clean46b1b9c3f89306cfe36f4eae41bdb9144934202f; created branch
green-ops/week11-fault-injection. Read instructions (no AGENTS.md found), tracker,
remote receipt (exactff801898 run green), actual accounting/model/features/gate.
Incoming317 tests; no baseline rerun. No push/publication/merge/deploy this task;
standing local Windows status export remains separately requested.

Freeze fault assumptions/development policy/recipe before simulation. Development
parent(payload96bytes,interval200ms), windows1000ms,2 group-local repetitions.
Current19dBm supports sourced nominalTX; TX-lock intent14dBm baseline uses180mA
assumed current, lockdelta0/1/5dBm interpolates to original19dBm235mA. CPU additive
5mA in free-idle replacement state is an assumption(range0..20); lower TX current
range120..234mA, interpolation/idle-RX transfer assumption, no LTE substitution.
All added assumptions explicit, sensitivity checks planned at low/high bounds.

Mechanisms before energy integration: CPU replaces floor(free_idle*severity/1000)
with exclusive idle+CPU current; TX lock changes actual TX state current/power
without changing request; retry storm adds firstN forced failures on seeded
contiguous2-of4 packet bursts, then common baseline loss draws, actual cap3+N;
beacons addK prepare/RX services per complete slot; fragments split logical
payload into1+N parts with8-byte header per fragment only whenN>0, each gets its
own complete service/retries. Logical packet delivered iff all fragments succeed.
Scheduling keeps exclusive segments, half-open acceptance and full observation;
any service crossing its reserved slot is INFEASIBLE before integration, energy
labels null (never0). These are rejected simulations, not observed partial runs.

Every case compares a compliant baseline with the same intent/seed. severity0
and none are controls. Predeclared research oracle: total-energy increase>5%,
equality compliant. This is a scenario diagnostic, not a production gate override
or calibrated detection policy. Frozen production gate policy remains unchanged;
new harness scope has no calibrated interval, so gate ABSTAIN. Diagnostic frozen
linear predictions use ONLY intended4-column X; no actual power/state/fault/seed/
labels enter X. Mark extrapolated14dBm unsupported profile. Do not create fake
completed v2 reference records just to make prediction/gate APIs accept faults.
Use separate strict fault-artifact v1 with replay/hash validation; old v1/v2
builders remain unchanged. Exact gate0/1/2/3 and blocked flags recorded separately
from oracle violation, mechanism truth and positive detection.

Parent grouping coarsens to(payload,interval), excluding requestedTX too, so related
power variants stay together. Preserve source catalog, parameters/assumptions/
recipe/policy hashes and parent/child IDs. Week12 proposal reserves16 new parents
payload40/72/112/144 x interval65/110/220/360ms,8validation/8locked evaluation,
2windows x3repetitions, all fault/power variants grouped. No Week12 energy/score
will be generated in Week11; enumerate/freeze actual counts/IDs/lineage before
benchmark scoring. Do not optimize current code/model/5%policy on final outcomes.

Milestones: freeze (this commit); implementation/accounting tests; trusted
integration/replay and development examples; full suite/frozen benchmark proposal,
readiness/docs. Commit verified milestones and refresh tracker/handoff/Windows.
Current freeze; next implement five mechanisms and independent arithmetic tests.
