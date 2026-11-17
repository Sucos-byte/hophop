# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Render the frozen descriptive results; no scoring/model changes."""
import json
from pathlib import Path
root=Path(__file__).resolve().parent
x=json.loads((root/'aggregate.json').read_bytes())
lines=['''# Week 12 frozen fault benchmark results

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
|---|---:|---|---|---|---:|---|---:|''']
for s,a in x['by_split'].items():
 f=a['feasibility'];q=a['statuses']
 lines.append(f"| {s} | {a['case_count']} | {f['COMPLETE']} / {f['INFEASIBLE']} / {f['INVALID']} | {a['oracle_violations']} / {a['oracle_known']} | {a['positive_FAIL_detections']} / {a['oracle_violations']} | {a['violations_without_positive_detection']} | {q['PASS']} / {q['FAIL']} / {q['ABSTAIN']} / {q['ERROR']} | {a['absolute_200mW_fault_violations']} |")
lines.append('''
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
|---|---|---|---|---|---:|---|''')
for key,a in x['by_fault_severity'].items():
 f=a['feasibility'];o=a['observability']
 lines.append(f"| {key} | {f['COMPLETE']}/{f['INFEASIBLE']}/{f['INVALID']} | {a['oracle_violations']}/{a['positive_FAIL_detections']}/{a['violations_without_positive_detection']} | {a['statuses']['ABSTAIN']}/{a['statuses']['ERROR']} | {a['control_count']}/{a['control_false_alarms']}/{a['control_abstention_blocks']} | {a['inputs_changed']} | {o['True']}/{o['False']}/{o['None']} |")
lines.append('''
## Paired practical effects

Means are descriptive over feasible paired cases only, including the declared
zero controls when severity0. mJ deltas mix1s/5s windows; mW and relative percent
make duration explicit. Denominator n is feasible pairs per row, grouped within
8 parents. No standardized IID effect size or significance claim. Aggregate JSON
also gives medians/ranges, per-parent effects and equal-parent means.

| Split / fault / severity | n | Mean Δenergy (mJ) | Mean Δpower (mW) | Mean paired increase (%) |
|---|---:|---:|---:|---:|''')
for key,a in x['by_fault_severity'].items():
 e=a['effects'];v=e['paired_energy_mj'];w=e['paired_power_mw'];p=e['paired_increase_percent']
 lines.append(f"| {key} | {v['count']} | {v['mean']:.6f} | {w['mean']:.6f} | {p['mean']:.6f} |")
lines.append('''
## Parent-level accounting

One parent is the dependence unit; each row has120 related cases. Violations
count cases, not independent events. Parent-level any-violation fractions are
8/8 in each split (parents as denominator, not a detection rate); with eight locked parents no population confidence or
100%-detection assertion is supported.

| Parent | Split | Feasible / infeasible | Oracle violations | Positive detections | Equal-parent contribution: mean paired ΔmJ |
|---|---|---|---:|---:|---:|''')
recipe=json.loads((root.parents[2]/'tools/green_ops/recipes/week12-fault-benchmark-v1.json').read_bytes())
for p,a in x['by_parent'].items():
 s=next(s for s,g in recipe['parent_splits'].items() if p in g)
 lines.append(f"| {p} | {s} | {a['feasibility']['COMPLETE']}/{a['feasibility']['INFEASIBLE']} | {a['oracle_violations']} | {a['positive_FAIL_detections']} | {a['effects']['paired_energy_mj']['mean']:.6f} |")
lines.append('''
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
''')
(root.parents[1]/'green-ops-week12-results.md').write_text('\n'.join(lines).rstrip()+'\n')
