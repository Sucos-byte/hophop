# Week11 analytical workload faults

All outputs use source_kind=synthetic,execution_kind=simulation,
measurement_status=analytical_simulation. No firmware fault/hardware measurement,
PPK2 trace or observed latency is created. Existing generator1.0.1, v1/v2 dataset/
feature contracts, models, calibration and production policies remain unchanged.

## Contracts and execution order

Core module tools/green_ops/fault_injection.py validates source parameters,
explicit extension assumptions, intended workload and fault kind/severity. It
constructs actual exclusive state/service behavior first, checks every service
against its slot, then integrates voltage*current*time. Target values are outputs
of this ledger, never inflated to make a detection example. State currents are
whole exclusive-state values; idle/CPU/radio losses are never counted twice.

Strict fault-artifact version1 is separate from reference-v2 source bundles.
It archives exact UTF8 model/assumption/intent/fault snapshots and hashes,
parent/baseline/child identities, baseline and fault ledgers/packets/energy,
plus low/high extension-current sensitivity. Loader verifies all hashes and
replays every segment, target and lineage field. It never invents a completed
reference-v2 execution to make the old frozen input loader accept a fault.
Existing dataset/table APIs are preserved; these extended diagnostics do not
silently introduce new prediction features or redefine old dataset-v2 semantics.

Intended workload is canonical and its group/ID validated. Parent key is payload
bytes+interval ms, coarsened across requested TX, durations, seeds, repetitions,
faults and severities. Group-local seeds repeat only within a parent for common
random numbers; child IDs include exact model/assumption/intent/fault hashes.
Actual injected power/cap/frames/wakeup/CPU states are separate from requested
configuration and never copied into pre-run X.

## The five actual mechanisms

| Kind / severity unit | Actual pre-integration behavior |
|---|---|
| cpu_busy_poll / permille free-idle | Replaces floor(free_idle_us*severity/1000) with exclusive cpu_busy state at idle current+declared CPU increment; does not overlap TX/RX/prepare/backoff. |
| tx_power_lock / dBm above request | Actual TX power increases while request is invariant. TX-state current changes using the explicit assumed lower point/interpolation up to the original19dBm source point. |
| bursty_retry_storm / forced initial failures | Seed phase selects contiguous2-of4 logical-packet bursts. Burst fragments incurN extra failed prepare/TX/RX services/backoffs before common baseline loss draws; actual retry cap increases byN. Non-burst packets retain baseline behavior. |
| beacon_hyper_wakeup / wakeups per complete slot | QueuesK extra prepare/listen-RX services at each complete slot start, before data service. Wake/beacon events do not count as delivered data. |
| payload_fragmentation_bloat / extra fragments | Splits each logical payload into1+N nonempty fragments, adds8 assumed header bytes to each whenN>0, and schedules full per-fragment prepare/TX/RX/retry service. Logical packet delivered only if every fragment succeeds. |

Severity0 and none are controls whose complete ledger/targets match baseline.
Valid ranges are CPU0..1000permille, TX0..(19-request), retries0..64, wakes0..1000,
fragments0..min(255,payload-1); computational service/slot enumeration capped100000.
No fractional/bool/negative/NaN/Inf severity accepted. Configurable assumptions
have explicit ranges; low/high sensitivity is not a calibrated confidence band.

The observation is [0,window). ACK exactly at global end is not delivered; its
TX/RX energy is still included. State segments cover the full window, including
idle remainder. Complete slots contain beacon and data service; partial tail
contains idle/CPU behavior but no additional per-complete-slot beacons. If any
service exceeds its slot, return INFEASIBLE with null energy/labels and a reason,
not a clipped schedule, zero energy or fabricated partial completion. No energy
integration runs on that rejected fault schedule. Malformed requests are ERROR,
not valid infeasibility. Zero logical deliveries retain null per-delivery energy.

## Sources and added assumptions

The archived original model remains authoritative for source revision/table/
conditions: nRF9151 Product Specification1.1(June2025), DECT NR+ current table,
3.7V/25C/band1/minimum-latency, declared19dBm/-90dBm RX condition. Currents idle37,
RX47,TX235mA are original typical values, not new measurements. Existing timings
and loss are assumptions. No LTE currents are substituted.

Added assumptions-v1.json declares CPU increment5mA (0..20), lower14dBm TX
current180mA (120..234), linear interpolation to the original19dBm point,8byte
fragment header, and burst2-of4. CPU-active and lower-power DECT current support
is missing; do not call these sourced Nordic curves. Idle/RX transfer unchanged
when request/actual power is below19dBm is also an assumption. Source catalog
conditions are retained verbatim rather than relabeled to fit new behavior.
All parameters/notes/ranges are embedded and hashed in every artifact.

## Predictor, gate and independent analytical oracle

fault_workflow.py consumes only replay-validated fault artifacts. It separately
computes frozen linear-model numeric diagnostics from intended payload/interval/
requestedTX/window only. Seed, fault identity, actualTX, state durations, attempts,
deliveries and energy do not enter X.14dBm is outside the original constant19dBm
training profile; output marks unsupported extrapolated diagnostics. No claim of
validated prediction availability or calibrated fault execution is made.

The trusted adapter passes exact model identity and intended feature context to
the existing pure gate engine, with new fault scope, no interval, and explicit
unavailable reason. Production policy/calibration remain frozen; default returns
ABSTAIN3 (or invalid processing ERROR1), not an invented energy FAIL/detection.
Hypothetical execution_blocked is the gate blocking flag: the offline analytical
simulation already ran; no physical firmware was actually blocked or executed.

Each report independently records:

- Analytical baseline/fault total mJ, mean mW and energy per logical delivery uJ;
  infeasible status/labels and actual mechanism occurrence.
- Predeclared development oracle: energy increase strictly>5%, equality compliant.
  Exact rational comparison of decoded values avoids rounding a boundary upward.
- Unchanged production policy absolute point-budget diagnostics (200mW currently),
  separate from the5% oracle and NOT a substitute for accepted gate evidence.
- Intended4-column X before/after, numeric predictions, changed-input/prediction
  flags, requested power outside training scope and hidden-information exclusion.
- Full gate decision/exit/block flag, observability in selected context, positive
  detection, undetected oracle violations, control false alarms and control blocks.

ABSTAIN/ERROR may block but never count as positive detection. The frozen
research definition requires gate FAIL, an observable input change and analytical
oracle violation for a positive; these hidden faults have unchanged X, so do not
pretend detection from commit labels or model contributions. Signed contributions
are model attributions, not physical causal proof. Default abstention blocks
compliant controls too; report that honestly instead of claiming a good detector.
No research gate override is enabled in this harness. The5% oracle is explicitly
an unvalidated development diagnostic, not a changed production gate policy.

## Commands, versioned output and safety

Run from repository root to a new output directory:

```sh
python3 tools/green_ops/fault_workflow.py development --output-dir build/green-ops-week11-development
python3 tools/green_ops/fault_workflow.py gate --artifact ARTIFACT.json --output NEW_FAULT_REPORT.json
python3 -W error::ResourceWarning -m unittest tools.green_ops.tests.test_fault_injection
```

Development driver returns0 only for completed SOFTWARE HARNESS processing,
never energy approval. Each case preserves its actual gate exit/block state.
Single-artifact gate command returns exactPASS0/ERROR1/FAIL2/ABSTAIN3; current
new scopes actually abstain. Malformed/hash/processing errors return1 with no
unverified report. Output aliases/collisions rejected; owned publications roll
back. Artifact/report loaders replay and reject forged targets, state ledgers,
hashes, lineage, status flags and positive-detection assertions.

Development recipe has one parent96bytes/200ms,1000ms windows,2 repetitions,
40cases spanning all5 faults and zero controls. Artifact/error/rollback tests
supplement real workload changes; they do not replace them. Versioned research
policy and all selected models/calibration/production-policy hashes remain frozen.
The new fault report container is not passed to the closed Week9 reference-only
Markdown validator as if it were its original source bundle; development summary
uses the same escaped-cell helper with an explicit fault diagnostic heading.

## Week12 frozen proposal, not benchmark outcomes

fault_benchmark.py plans source identities without invoking simulation, prediction
or benchmark scoring. Proposed16 new parent groups payload40/72/112/144 × interval
65/110/220/360ms,8validation/8locked evaluation,2 windows ×3 repetitions,
1920case identities (120/parent; power/fault/severity/zero-control variants grouped),
48group-local random streams. Parent/seed exclusions cover known Week6/7/8 grids,
archived prior workloads and Week11 development. New seeds alone are insufficient.

The frozen recipe stores exact memberships/IDs/counts and input/code/model/policy
hashes before benchmark energy generation or scoring. No Week12 outcomes are
computed in Week11. Freeze scoring definitions, ground-truth/normal controls and
model/policy before final labels; report undetected faults and false alarms,
plus abstention blocks separately. Logical5% oracle and200mW point violations
are distinct labels and must not be mixed to inflate detection counts. Analytical
parent disjointness is not physical independence or a new calibration guarantee.
