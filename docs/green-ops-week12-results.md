# Week 12 frozen fault benchmark results

All results **analytical_simulation** (synthetic/simulation), research only.
No physical measurement, calibrated fault detection or hardware assurance.

Protocol and evidence: [execution plan](plans/green-ops-week12-plan.md),
[execution receipt](results/week12/execution.json), [preflight](results/week12/preflight.json),
[reproduction](results/week12/reproduction.json), [all case records](results/week12/cases.jsonl),
[aggregate](results/week12/aggregate.json), [raw artifact hash manifest](results/week12/manifest.json).
Historical FROZEN_UNSCORED recipe/receipt are unchanged; both partitions are now
consumed. Tooling checkpoint2f3559c preceded scoring; no model, calibration,
policy, mechanisms, severity settings or outcome definitions changed/tuned.

1,920 unique cases,16 genuinely new coarsened payload+interval parents,48 streams;
8validation/8locked parents,960 cases each;109 historical parent exclusions,
zero parent/known-seed overlap. Requested-TX variants/windows/repetitions/faults
stay with their parent. New families are configuration-disjoint, not independent
physical experiments or new analytical laws. Archived transient source paths
need not exist for replay: frozen audit digest retained, historical grids and
known seeds rechecked. No protocol-invalidating correctness defect discovered.

## Split outcomes

Oracle truth is a paired analytical energy increase **strictly greater than5%**,
not a gate prediction. The unchanged200mW absolute point diagnostic is separate.
Rates below count dependent cases within8 parents per split; they do not support
population or hardware inference. Infeasible labels remain null, excluded from
oracle/effect denominators; invalid cases would abort execution and retain the
consumption receipt, not silently receive manufactured labels.

| Split (8parents each) | Cases | Feasible / infeasible / invalid | Oracle violations / known pairs | Positive FAIL / violations | Missed violations | Gate PASS / FAIL / ABSTAIN / ERROR | Absolute200mW violations |
|---|---:|---|---|---|---:|---|---:|
| locked_evaluation | 960 | 949 / 11 / 0 | 271 / 949 | 0 / 271 | 271 | 0 / 0 / 960 / 0 | 29 |
| validation | 960 | 950 / 10 / 0 | 281 / 950 | 0 / 281 | 281 | 0 / 0 / 960 / 0 | 32 |

Locked detection0/271 violating cases (eight parent groups); validation0/281.
All1920 gates ABSTAIN3/block; FAIL0,ERROR0,PASS0. These are **zero positive
detections**, not successful detection by conservative blocking. Both execution
processes return0 for successful offline software processing only. Default gate
semantics PASS0/ERROR1/FAIL2/ABSTAIN3 remain unchanged, with no overrides.

All576 zero-severity/none controls (288 per split) satisfy both analytical budgets;
FAIL false alarms0/288 but ABSTAIN blocks288/288 in each split. Blanket abstention
provides no evidence of good selectivity. All baseline point powers are below
200mW. Zero controls across different fault names share evidence and are not
independent compliant executions.

## Complete fault/severity accounting

Each row schedules48 cases across8 parents (3 streams ×2windows per parent).
Severity units are frozen in the recipe: CPU permille of idle budget, TX dBm
increment, retries forced initial failures per burst fragment, beacon wakes
per complete slot, fragmentation additional fragments per packet. Severity0
and none are controls. V=5% oracle violations; D=positive FAIL detections;
M=violations without positive detection. A=ABSTAIN, E=ERROR; PASS/FAIL both0 in
every row. C=controls, FA=control FAIL false alarms, CB=control abstention blocks.
X=permitted-input changes. Observable shows true/false/unknown counts; unknown
includes no realized mechanism or infeasible execution, not an observed fault.
Every V, D, M count uses feasible known-label pairs in its row; all48 scheduled
cases are the status denominator. No rates pool variants as IID replicates.

| Split / fault / severity | Feasible / infeasible / invalid | V / D / M | A / E | C / FA / CB | X | Observable T/F/? |
|---|---|---|---|---|---:|---|
| locked_evaluation/beacon_hyper_wakeup/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| locked_evaluation/beacon_hyper_wakeup/1 | 48/0/0 | 0/0/0 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| locked_evaluation/beacon_hyper_wakeup/20 | 48/0/0 | 18/0/18 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| locked_evaluation/beacon_hyper_wakeup/3 | 48/0/0 | 0/0/0 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| locked_evaluation/bursty_retry_storm/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| locked_evaluation/bursty_retry_storm/1 | 48/0/0 | 8/0/8 | 48/0 | 0/0/0 | 0 | 0/46/2 |
| locked_evaluation/bursty_retry_storm/3 | 48/0/0 | 27/0/27 | 48/0 | 0/0/0 | 0 | 0/46/2 |
| locked_evaluation/bursty_retry_storm/7 | 48/0/0 | 46/0/46 | 48/0 | 0/0/0 | 0 | 0/46/2 |
| locked_evaluation/cpu_busy_poll/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| locked_evaluation/cpu_busy_poll/1 | 48/0/0 | 0/0/0 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| locked_evaluation/cpu_busy_poll/1000 | 48/0/0 | 48/0/48 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| locked_evaluation/cpu_busy_poll/400 | 48/0/0 | 30/0/30 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| locked_evaluation/none/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| locked_evaluation/payload_fragmentation_bloat/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| locked_evaluation/payload_fragmentation_bloat/1 | 48/0/0 | 18/0/18 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| locked_evaluation/payload_fragmentation_bloat/15 | 37/11/0 | 37/0/37 | 48/0 | 0/0/0 | 0 | 0/37/11 |
| locked_evaluation/payload_fragmentation_bloat/3 | 48/0/0 | 39/0/39 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| locked_evaluation/tx_power_lock/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| locked_evaluation/tx_power_lock/1 | 48/0/0 | 0/0/0 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| locked_evaluation/tx_power_lock/5 | 48/0/0 | 0/0/0 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/beacon_hyper_wakeup/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| validation/beacon_hyper_wakeup/1 | 48/0/0 | 0/0/0 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/beacon_hyper_wakeup/20 | 48/0/0 | 30/0/30 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/beacon_hyper_wakeup/3 | 48/0/0 | 0/0/0 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/bursty_retry_storm/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| validation/bursty_retry_storm/1 | 48/0/0 | 6/0/6 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/bursty_retry_storm/3 | 48/0/0 | 30/0/30 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/bursty_retry_storm/7 | 48/0/0 | 45/0/45 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/cpu_busy_poll/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| validation/cpu_busy_poll/1 | 48/0/0 | 0/0/0 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/cpu_busy_poll/1000 | 48/0/0 | 48/0/48 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/cpu_busy_poll/400 | 48/0/0 | 18/0/18 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/none/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| validation/payload_fragmentation_bloat/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| validation/payload_fragmentation_bloat/1 | 48/0/0 | 27/0/27 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/payload_fragmentation_bloat/15 | 38/10/0 | 38/0/38 | 48/0 | 0/0/0 | 0 | 0/38/10 |
| validation/payload_fragmentation_bloat/3 | 48/0/0 | 39/0/39 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/tx_power_lock/0 | 48/0/0 | 0/0/0 | 48/0 | 48/0/48 | 0 | 0/0/48 |
| validation/tx_power_lock/1 | 48/0/0 | 0/0/0 | 48/0 | 0/0/0 | 0 | 0/48/0 |
| validation/tx_power_lock/5 | 48/0/0 | 0/0/0 | 48/0 | 0/0/0 | 0 | 0/48/0 |

## Paired practical effects

Means are descriptive over feasible paired cases only, including the declared
zero controls when severity0. mJ deltas mix1s/5s windows; mW and relative percent
make duration explicit. Denominator n is feasible pairs per row, grouped within
8 parents. No standardized IID effect size or significance claim. Aggregate JSON
also gives medians/ranges, per-parent effects and equal-parent means.

| Split / fault / severity | n | Mean Δenergy (mJ) | Mean Δpower (mW) | Mean paired increase (%) |
|---|---:|---:|---:|---:|
| locked_evaluation/beacon_hyper_wakeup/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| locked_evaluation/beacon_hyper_wakeup/1 | 48 | 1.193250 | 0.391275 | 0.262621 |
| locked_evaluation/beacon_hyper_wakeup/20 | 48 | 23.865000 | 7.825500 | 5.252411 |
| locked_evaluation/beacon_hyper_wakeup/3 | 48 | 3.579750 | 1.173825 | 0.787862 |
| locked_evaluation/bursty_retry_storm/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| locked_evaluation/bursty_retry_storm/1 | 48 | 11.327937 | 3.743628 | 2.512945 |
| locked_evaluation/bursty_retry_storm/3 | 48 | 33.983810 | 11.230883 | 7.538834 |
| locked_evaluation/bursty_retry_storm/7 | 48 | 79.295557 | 26.205395 | 17.590612 |
| locked_evaluation/cpu_busy_poll/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| locked_evaluation/cpu_busy_poll/1 | 48 | 0.053732 | 0.017922 | 0.012382 |
| locked_evaluation/cpu_busy_poll/1000 | 48 | 53.976007 | 18.001610 | 12.436007 |
| locked_evaluation/cpu_busy_poll/400 | 48 | 21.590151 | 7.200561 | 4.974348 |
| locked_evaluation/none/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| locked_evaluation/payload_fragmentation_bloat/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| locked_evaluation/payload_fragmentation_bloat/1 | 48 | 19.984930 | 6.567965 | 4.405649 |
| locked_evaluation/payload_fragmentation_bloat/15 | 37 | 183.019980 | 62.913501 | 43.744327 |
| locked_evaluation/payload_fragmentation_bloat/3 | 48 | 58.459556 | 19.183224 | 12.874254 |
| locked_evaluation/tx_power_lock/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| locked_evaluation/tx_power_lock/1 | 48 | 1.320328 | 0.431522 | 0.295718 |
| locked_evaluation/tx_power_lock/5 | 48 | 6.601642 | 2.157609 | 1.478589 |
| validation/beacon_hyper_wakeup/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| validation/beacon_hyper_wakeup/1 | 48 | 1.387500 | 0.457875 | 0.305431 |
| validation/beacon_hyper_wakeup/20 | 48 | 27.750000 | 9.157500 | 6.108623 |
| validation/beacon_hyper_wakeup/3 | 48 | 4.162500 | 1.373625 | 0.916293 |
| validation/bursty_retry_storm/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| validation/bursty_retry_storm/1 | 48 | 13.358005 | 4.442243 | 2.959707 |
| validation/bursty_retry_storm/3 | 48 | 40.074014 | 13.326730 | 8.879121 |
| validation/bursty_retry_storm/7 | 48 | 93.506032 | 31.095703 | 20.717948 |
| validation/cpu_busy_poll/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| validation/cpu_busy_poll/1 | 48 | 0.053438 | 0.017814 | 0.012183 |
| validation/cpu_busy_poll/1000 | 48 | 53.729217 | 17.910639 | 12.247068 |
| validation/cpu_busy_poll/400 | 48 | 21.491482 | 7.164188 | 4.898782 |
| validation/none/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| validation/payload_fragmentation_bloat/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| validation/payload_fragmentation_bloat/1 | 48 | 23.120826 | 7.628553 | 5.084502 |
| validation/payload_fragmentation_bloat/15 | 38 | 263.758992 | 86.661215 | 59.143494 |
| validation/payload_fragmentation_bloat/3 | 48 | 68.356244 | 22.513571 | 15.007371 |
| validation/tx_power_lock/0 | 48 | 0.000000 | 0.000000 | 0.000000 |
| validation/tx_power_lock/1 | 48 | 1.542754 | 0.512610 | 0.348849 |
| validation/tx_power_lock/5 | 48 | 7.713769 | 2.563049 | 1.744243 |

## Parent-level accounting

One parent is the dependence unit; each row has120 related cases. Violations
count cases, not independent events. Parent-level any-violation fractions are
8/8 in each split (parents as denominator, not a detection rate); with eight locked parents no population confidence or
100%-detection assertion is supported.

| Parent | Split | Feasible / infeasible | Oracle violations | Positive detections | Equal-parent contribution: mean paired ΔmJ |
|---|---|---|---:|---:|---:|
| fp-0ac3abd6dae2983f305753eb51d94ead | validation | 114/6 | 42 | 0 | 33.126715 |
| fp-1c9fb617dcdbd71266021e94072ac69e | locked_evaluation | 114/6 | 42 | 0 | 31.648745 |
| fp-32e283d2b4f09bf00876dc1d0db6e902 | locked_evaluation | 120/0 | 32 | 0 | 20.024432 |
| fp-522af99a3adbb05e27f343afc91be129 | validation | 120/0 | 23 | 0 | 12.611962 |
| fp-544fc9c19dc145f3840f09a3a165ae32 | locked_evaluation | 115/5 | 39 | 0 | 31.439395 |
| fp-6972ee86c211891a98cb52e01bf0b590 | locked_evaluation | 120/0 | 23 | 0 | 13.212972 |
| fp-8093b1e82ff40a91208f2bb32db13343 | validation | 120/0 | 41 | 0 | 38.095902 |
| fp-82ee9180ec7f17d6b994db330d6dc7e7 | validation | 120/0 | 41 | 0 | 36.521891 |
| fp-9a67741725ceb6c20fc681e310e6daf6 | validation | 116/4 | 38 | 0 | 38.596831 |
| fp-b50a4cbcb863d757d9e8ce251b67c093 | validation | 120/0 | 25 | 0 | 13.057468 |
| fp-d0f48437795bc81de309c288605287ac | validation | 120/0 | 41 | 0 | 37.634983 |
| fp-db7057fb9e1cd389a3eefb6c85ef3020 | locked_evaluation | 120/0 | 36 | 0 | 20.312527 |
| fp-de4b8748ffb217c90317211def1b047f | locked_evaluation | 120/0 | 42 | 0 | 35.640575 |
| fp-e72f35aa5b7a6101289154f6418e5009 | locked_evaluation | 120/0 | 27 | 0 | 13.690706 |
| fp-e812bc32e826b79d05b9466197eb9a5d | validation | 120/0 | 30 | 0 | 19.319138 |
| fp-f0cf4180e2f5f29d4eb3c2d4ee11cd88 | locked_evaluation | 120/0 | 30 | 0 | 19.446880 |

## Observability, assumptions and limitations

All1920 permitted input vectors and predictions are unchanged within each
baseline/fault pair. Hidden actual-state fields and fault identity never enter X.
A fixed model cannot distinguish a CPU/retry/beacon/fragment/TX execution change
from its baseline using identical requested payload, interval, power and window.
TX requests14dBm remain14dBm while actual locked power changes; this intended
power also lies outside the Week7 training power profile. Commit identity is not
an energy sensor. Existing calibration is deliberately not transferred to the
new engine scope; no intervals are fabricated. Week8 family coverage already
fell below nominal95% (28/30,28/30,26/30); no coverage/hardware assurance follows.

Fragmentation severity15 causes all21 infeasible schedules (11locked,10validation).
They are not zero-energy runs, oracle negatives or positive detections. CPU,
retry and fragmentation have large feasible increases; TX effects remain below
5% here. Beacon severity20 violates the relative budget in18locked and30validation
cases. Negative outcomes are preserved; no stronger faults or different policy
were selected after scoring. Some configured faults do not realize a mechanism;
case records distinguish configured, occurred and observable.

Nordic nRF9151 PS1.1(June2025) DECT NR+ source currents at3.7V/25°C/minimum-latency
conditions are37mA idle,47mA RX,235mA TX at19dBm; applicability is narrow.
CPU increment5mA(range0–20), lower-TX180mA(range120–234), all fault timing,
wakeup/fragment/retry and loss behavior are explicit model assumptions. TX
variants use common noise and no power-dependent link budget. Low/high current
sensitivity records are assumptions checks, not confidence intervals. RTT is
unobserved/null. No measured PPK2, battery endurance or physical RF validation.

## Reproduction and verification

Two fresh process executions produced3844 byte-identical files per run, including
all1920 replayable artifacts and1920 decisions. Independent rational arithmetic
checked3819 completed baseline/fault ledgers plus21 null infeasible ledgers in
**each** run: contiguous conserved time, V×I×duration energy, mJ/mW conversion,
5% truth, hashes and aggregates. Exact hashes are in reproduction.json. Original
artifact generation and decision evaluation replay the frozen engine; independent
arithmetic audits accounting, not physical validity or an alternative RF model.

Run `python3 docs/results/week12/reproduce.py /tmp/green-ops-week12-replay-new`
from a clean checkout (new directory required). Raw gzip artifacts remain in
ignored local build directories; committed manifests/cases/aggregates retain
exact hashes and regenerate through this command. Consumption receipts persist
on processing failure. Committed recipe/receipt remain historical unscored
freeze records; execution.json and the tracker record consumption/completion.

Local Python tests and prior remote CI are distinguished in the project summary.
No Week12 GitHub Actions execution, push, publication, merge or deployment.

## Unmet objectives and next gate

Useful execution-fault detection/selectivity is **not achieved**. Prioritize
actual-state telemetry and synchronized physical measurements before proposing
another detector. Preserve this consumed benchmark as regression evidence;
a changed predictor requires new parent-disjoint physical/development data,
predeclared policy and genuinely fresh evaluation groups. See the
[project results and prioritized follow-up](green-ops-project-results.md).
