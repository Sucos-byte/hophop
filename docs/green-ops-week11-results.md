# Week11 — five analytical faults, accounting and honest observability

All outputs are **analytical_simulation**. No firmware/hardware detection,
measured PPK2 evidence, physical current validation or calibrated fault coverage
is claimed. Faults change execution scheduling/state/current before integration;
target labels are never inflated to manufacture a detection.

Entry clean46b1b9c; branch green-ops/week11-fault-injection. Pre-outcome contracts/
assumptions/development policy frozen d0d6331; implementation24b746a verified
with341 full-suite tests. [Plan](plans/green-ops-week11-plan.md) and
[API/accounting guide](green-ops-fault-injection.md) document units and boundaries.

## Implemented mechanisms

| Fault | Actual modeled effect before energy calculation |
|---|---|
| CPU busy-poll | Replaces selected free-idle microseconds with exclusive idle+CPU current state; no overlap with radio/prepare/backoff. |
| TX power lock | Requested14dBm stays unchanged; actual power rises toward19dBm and TX current changes. Lower current/interpolation explicitly assumed. |
| Bursty retry storm | Seeded contiguous2-of4 packet bursts incur extra failed prepare/TX/RX/backoff services before common baseline draws; actual cap grows. |
| Beacon hyper-wakeup | Adds queued wake preparation and listen/RX services per complete slot; no data-delivery credit. |
| Payload fragmentation bloat | Adds nonempty fragments, per-fragment headers/services/retries; logical reassembly required for one delivered packet. |

Exclusive segments cover the entire observation window including idle remainder.
Voltage*mA*us/1e6 integrates mJ exactly once. Logical per-delivery energy stays
null with no delivery; an ACK at the global end is excluded under[start,end).
Any service crossing its slot is INFEASIBLE before fault energy integration,
not clipped or assigned zero targets. An archived
[infeasible example](results/week11/infeasible-artifact.json) and
[gate report](results/week11/infeasible-report.json) show null labels, ABSTAIN3
and no positive detection; severe/invalid boundaries are also tested.

## Development outcomes (not benchmark scores)

One parent payload96bytes/interval200ms,1000ms windows,2 reproducible group-local
streams. Requested power19dBm except TX-lock intent14dBm.40 cases include12
compliant zero/none controls and28 active fault cases. The predeclared research
oracle is total energy increase strictly>5%; equality compliant. This diagnostic
is distinct from unchanged production200mW point-budget checks and from accepted
prediction/gate evidence. No policy was tuned after outcomes.

| Mechanism | Cases including zero controls | 5% oracle violations | Actual200mW point violations | Positive gate detections |
|---|---:|---:|---:|---:|
| CPU busy-poll |8|4|0|0|
| TX power lock |6|0|0|0|
| Bursty retry storm |8|3|0|0|
| Beacon hyper-wakeup |8|0|0|0|
| Fragmentation bloat |8|4|2|0|
| None controls |2|0|0|0|

All40 default gate decisions are **ABSTAIN3**, all would block execution.
These are offline analytical simulations, not actual firmware executions that
were prevented. ABSTAIN/ERROR blocking is not positive fault detection.

The11 oracle violations remain undetected; the2 actual production point-budget
violations also do not produce accepted predictive FAILs. All12 compliant controls
are blocked by unsupported-scope abstention:0 gateFAIL false alarms does NOT mean
good selectivity or a successful detector. Preserve these false blocks separately.
TX-lock and beacon cases really alter actual behavior/energy but do not cross
this5% oracle here; we did not increase severities or tune thresholds to claim
success. These40 related cases are one parent development group, not40 independent
evaluation observations. No Week12 scoring was performed.

Illustrative maximum-severity first-stream total energies[mJ]: baseline142.247092
for19dBm intent; CPU160.434072, retry157.218950, beacon147.797092,
fragment207.375676. TX intent14 baseline140.838872 changes to142.247092 when
actual lock reaches19dBm. This window is1second, so numeric mean mW equals mJ;
other durations require explicit conversion. Full seeds/lineage/ledgers and all
baseline/fault values appear in [summary](results/week11/development/summary.json),
[escaped development table](results/week11/development/summary.md) and per-case
artifacts/reports under docs/results/week11/development/.

## Prediction and gate observability

The permitted four inputs are intended payload, interval, requestedTX and planned
duration. Baseline/fault X is identical for every pair. Actual locked power,
CPU duration, retries, beacon wakes, fragment counts, outcomes, seed and fault
identity never enter X. The frozen model predictions consequently stay identical
for every pair. Model labels/contributions are not physical causal proof.

14dBm is outside the original constant19dBm training profile and is marked an
unsupported numeric diagnostic. All extended execution scopes lack calibrated
intervals; no Week8 marginal intervals were reused or silently extrapolated.
The trusted replay adapter invokes the existing unchanged gate engine with
explicit unavailable evidence. Default production policy, model selection and
calibration are frozen; no override is enabled. Compliant controls in this new
artifact scope also have no accepted interval evidence.

A positive in the frozen research definition requires gateFAIL, observable input
change and an oracle violation; none qualifies. This week delivers a transparent
harness, not a claim that the old pre-run regressor detects hidden execution faults.
Future diagnostics would need appropriate actual-execution observables/context
and separate validated evidence; do not leak ground-truth labels into predictors.
Keep5% change labels and200mW point labels separate in later benchmarking.

## Sources versus assumptions

Original source catalog/conditions are archived unchanged: nRF9151 DECT NR+
minimum-latency reference at3.7V/25C, declared19dBm and -90dBm RX conditions,
Product Specification1.1(June2025), current table37mA idle/47mA RX/235mA TX.
Original timings/loss remain assumptions; no LTE values substituted. Loss draws
are deliberately held independent of TX-power changes and common across paired
baselines where applicable; no RF link-budget or power-dependent delivery model
is validated.

New CPU increment5mA(range0..20), lower14dBm current180mA(range120..234), linear
interpolation, idle/RX transfer at lower power,8byte fragment headers and extra
wake scheduling are explicit assumptions, not sourced current curves or measured
behavior. Low/high assumption-current sensitivity is archived for each case;
it is not a probabilistic or calibrated uncertainty interval. Invalid/infeasible
cases are retained or rejected explicitly, not turned into passing examples.

## Tests, replay and compatibility

Full release suite **341 passes** (24 new,111.869s), ResourceWarning errors enabled.
Independent expected values include1V/1-3mA/100ms baseline0.103mJ and CPU
replacement0.152mJ, per-attempt retry increments, beacon RX deltas and per-fragment
wire-time overhead. Tests cover all five mechanisms, zero controls, seeded bursts,
logical delivery/null labels/half-open boundary, time/energy conservation,
integration-not-called-on-infeasible-fault, input leakage, lineage, strict snapshot/
hash/target/status replay, malformed/resources/ranges, exact0/1/2/3 propagation,
output collisions and rollback. Artifact/error tests supplement the mechanisms.

Two reproduced outputs contain85 files each. The
[receipt](results/week11/development/reproduction.json) binds84 payload files
(including40 artifacts/40 reports) plus implementation hashes; the85th file is
the receipt itself. Two complete
independent runs produce identical bytes; report/source replay is verified for
every case. Legacy v1/v2 builders/reference generator, selected model files,
calibration and existing gate policies/workflows/locks are unchanged. This task
has no remote push or Actions run. Earlier remoteff801898 success is historical,
not a claim that current Week11 code ran remotely. No unchanged Rust/firmware
checks were repeated for this Python-only implementation.

```sh
python3 docs/results/week11/reproduce.py build/green-ops-week11-fresh
python3 -W error::ResourceWarning -m unittest discover -s tools/green_ops/tests
```

The development CLI returns0 for SOFTWARE HARNESS completion, never approval;
single-artifact gate CLI returns its exact blocking exit. Invalid artifacts return
ERROR1 without publishing unverified output. All files use fresh destinations.

## Frozen Week12 benchmark proposal (UNSCORED)

[Recipe](../tools/green_ops/recipes/week12-fault-benchmark-v1.json) and
[freeze receipt](results/week11/week12-freeze.json) bind source/code, assumptions,
feature/model selection, calibration inventory and production/research policies.
Planning enumerated IDs only; no benchmark energy, predictions or score computed.

- 16 genuinely new parents: payload40/72/112/144 x interval65/110/220/360ms.
- 8 validation /8 locked evaluation parents,960 cases each;1920 unique child IDs.
- 2 windows1000/5000ms x3 repetitions;48 unique parent-local streams, repeated
 across durations/power/fault variants within parents only.
- 109 historical/development parent configurations excluded; zero parent/seed
 overlap. Requested-power variants coarsened into the same payload/interval group.
- Zero controls/severity variants share baseline evidence and are not independent
 samples.16 parents, not1920 cases, are the grouping units.

The design follows predeclared axes/severities and must not be optimized against
its locked outcomes. Week12 scoring must distinguish mechanism truth, the two
analytical budget labels, model/gate outcomes, misses, false alarms and abstention
blocks. No current ABSTAIN is a positive detection or a new calibrated coverage
claim. New recorded groups remain governed by the same assumed analytical law;
parent disjointness is not physical independence.

Next: separately authorized Week12 benchmark implementation/scoring under this
frozen proposal. Physical validation, sourced CPU/lower-TX/wakeup behavior and
actual-context detectability remain gaps. No required user/hardware action now;
no push, publication, merge or deployment in Week11. Tracker/handoff and local
Windows status export remain authoritative/explicitly requested respectively.
