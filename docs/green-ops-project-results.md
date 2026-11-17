# Green Ops project results and limitations through Week12

The software research pipeline is implemented and reproducible. Useful physical
firmware energy-regression detection has **not** been demonstrated. Every current
study result is synthetic/simulation/analytical_simulation, not measured PPK2.

| Evidence level | Delivered | Practical limit |
|---|---|---|
| Implemented software | Telemetry/logging contracts; datasetv1/v2; window/counter/PPK2 evidence validation; versioned analytical generator; stdlib ridge/mean training; grouped evaluation; family intervals/attributions/ablations; strict gate/battery/report contracts; CI; five behavior-level fault mechanisms; frozen benchmark executor/audit | Tests prove implemented contracts/accounting, not device accuracy or physical detection |
| Analytical evidence | Frozen models/calibration/policies and reproducible group-disjoint configuration studies;1920 frozen fault cases | Formula recovery from one assumed energy law; repeated variants dependent; hidden execution faults leave permitted X unchanged |
| Remote CI verification | Fork SHA ff801898b3f7db47f49d9752fd5eed2444068f05, [run44080696563](https://github.com/Sucos-byte/hophop/actions/runs/44080696563): Rust host/standalone telemetry tests, ARM no_std build,317Python tests and expected-ABSTAIN smoke passed | Historical Week10 runner evidence only. No current Week11/12 remote execution or push. Expected ABSTAIN success is software verification, not energy approval |
| Physical validation | Contracts, capture/build conventions and proposed telemetry path | No synchronized hardware PPK2 measurements, firmware-injected detection study, RF/loss validation, device calibration or battery-life validation performed |

Week7 standard-library mean/ridge uses training-only preprocessing and disjoint
configuration-family selection/evaluation. Representative selected held-out RMSE
is6.3664mW,51.185mJ,991.183µJ/delivered packet; this is analytical generator
prediction, not an execution observation. The1620 held-out prediction records
are3panels×3targets×2models×90rows, not1620 independent groups. Previous
training/validation/test/stress sets remain consumed.

Week8 used30new calibration and30evaluation families. Nominal95% family coverage
was28/30 power,28/30 total energy and26/30 per-delivery energy; high-airtime shift
23/30,23/30,24/30. Coverage is below nominal and cannot be promised for hardware
or the new fault engine. Model influences indicate numerical sensitivity, not
physical causes; correlated features and within-duration permutations limit
interpretation. Existing model/interval choices remain frozen.

Week9 gate PASS0/ERROR1/FAIL2/ABSTAIN3 blocks all except PASS. Default evidence
restrictions are preserved; research overrides require explicit policy+flag.
Battery projections integrate declared capacity, voltage, usable fraction,
efficiency and compatible workload power. Missing workload abstains. Aging,
self-discharge, environment and battery chemistry dynamics are omitted; five
years is a configurable engineering objective, not legal certification.

[Week12 report](green-ops-week12-results.md):1920cases,16new parents,48streams;
8validation/8locked parents. Locked949feasible/11infeasible/0invalid,271relative
5% oracle violations; validation950/10/0,281violations. Positive FAIL detections
0/271locked and0/281validation. All1920ABSTAIN/block, including576 compliant
controls. Zero FAIL false alarms with blanket abstention is not good selectivity.
61feasible analytical200mW point violations are also not positively detected.
Both partitions are consumed; no tuning or protocol changes followed outcomes.
Two independent process runs reproduced3844files exactly; rational ledger audits
checked state conservation/energy/units/oracle independently of engine integration.
Only8locked parent groups exist; no population/detection/hardware guarantee.

Nordic nRF9151 Product Specification1.1 (June2025) supports narrowly conditioned
DECT NR+ currents (3.7V,25°C,minimum latency;19dBm TX). Assumed durations,
CPU/lower-TX currents, loss/retry/wakeup/fragment behavior and common random
streams do not establish physical accuracy. No LTE substitution, fake measured
PPK2, observed RTT, validated95% family coverage or compliance claim is made.

Prioritized follow-up:

1. **Make execution observable.** Add versioned actual TX-power/state residency,
CPU busy/sleep time, retry/attempt/ACK/delivery counters, beacon wake counts and
fragment/payload-overhead telemetry. Include clock/window IDs, counter baselines,
reset/wrap/missing-data handling and requested-versus-actual configuration.
Keep this post-run/telemetry profile separate from the current pre-run profile;
never silently feed unavailable actual states into pre-run predictions.
2. **Validate measurements and mechanisms.** Synchronize device markers/logs with
PPK2 voltage/current captures over the same observation window. Characterize
sample alignment, duration, baseline subtraction, instrument uncertainty and
energy/delivery evidence; independently verify each firmware fault occurred.
Measure source-condition drift, power-dependent loss and CPU/sleep behavior on
multiple devices/workloads. Require explicit user hardware actions then.
3. **Predeclare a new physical study.** Build development/calibration/evaluation
sets with genuinely disjoint device/workload/configuration parents and sessions;
keep related repeats/variants together. Freeze telemetry feature availability,
model/policy, effect threshold, uncertainty scope and denominators before scoring.
Old analytical or consumed groups cannot become a fresh test via new seeds.
4. **Evaluate detection and selectivity honestly.** Compare measured paired energy
and practical effects; distinguish oracle truth, positive FAIL, missed faults,
false alarms and abstention blocks. Establish supported coverage/applicability
before a scoped approval policy. Do not weaken default restrictions to obtain
passes; keep legacy analytical benchmark as descriptive regression evidence.
5. **Reverify deployment prerequisites separately.** If later authorized, run the
new SHA in fork CI and inspect exact runner outcomes. Current task performs only
local verification. Physical accuracy, telemetry overhead, real battery aging and
any deployment/approval decision require separate evidence and authorization.

Current gatekeeper is research software, not an operational physical regression
approval system. The highest-priority gap is observability, followed by paired
physical validation and a new frozen study, rather than hyperparameter tuning.
