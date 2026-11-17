# Week9 — research-only energy-budget gate and battery projection

All demonstrations remain **analytical_simulation**. No model retraining,
calibration changes, physical measurements, hardware action or evaluated-set
tuning occurred. PASS is an explicit unvalidated research-policy result; default
95% evidence requirements abstain with current Week8 coverage failures.

## Verified entry and implemented behavior

Verified clean340a5b7; branch green-ops/week9-gatekeeper. Policy semantics/default
example frozen060a7fc before implementation. Tested implementationbbc187c.
[Plan](plans/green-ops-week9-plan.md) and [contract/API documentation](green-ops-gatekeeper.md)
record exact boundaries, assumptions, status precedence and output safety.

- Strict version1 green_ops_budget.json accepts absolute mW/mJ/uJ budgets and
  candidate-versus-baseline absolute/percent regression allowances.
- Replays source bundles, checks frozen model/calibration/evidence/recipe and
  feature hashes, prediction context, workload/windows and provenance. Recomputes
  frozen estimates instead of trusting user-edited prediction JSON.
- PASS0,ERROR1,FAIL2,ABSTAIN3 with deterministic structured criteria/reasons,
  thresholds, values/ranges/units, full artifact hashes, resolved workloads,
  contexts/domains, model attributions and explicit no-hardware-assurance flags.
- Default evidence requires observed nominal family coverage>=0.95; two-part
  research override is required to use current inadequate evidence. Assumption
  shift additionally needs explicit policy permission and has no coverage claim.
- Inspectable battery energy/loss/year accounting and inverse-power projection;
  missing workload abstains, run-average duty cycle cannot be applied twice.
- Existing point/interval APIs, v1 behavior and standard-library installation are
  unchanged. No GitHub Actions or full PR Markdown reporter (Week10 scope).

## Evidence limitations retained

Week8 nominal family coverage is28/30(power),28/30(total),26/30(per-delivery),
93.33%/93.33%/86.67%, below95%. High assumed-airtime shift23/30,23/30,24/30
is worse. Same30 evaluation families recur across sensitivity panels; neither
rows nor panels are independent family samples. All Week8 calibration/evaluation/
stress sets are consumed; this week uses their fixed published results as
compatibility/evidence metadata, never for recalibration or model/policy tuning.

Frozen half-widths remain13.3224071mW,177.3732002mJ,6977.1560577uJ. The
nominal point RMSE5.7813mW,48.5603mJ,2027.3085uJ is unchanged. No confidence
claim for an interval difference, joint target coverage or hardware follows.
Signed feature influences describe the fitted analytical model. The Week8
within-duration permutation blind spot still cannot establish duration importance;
contributions/ablations show strong duration dependence for total energy.

## Reproducible research demonstrations

[Driver](results/week9/reproduce.py) regenerates one existing frozen nominal
Week8 evaluation workload (lexicographically first), with exact original
parameters/assumptions, prediction context, and no outcome-based selection.
All cases share that unchanged source and models/calibration. Policy ceilings
100/150/200mW are predeclared toy fixtures for decision boundaries, not optimized
or validated engineering budgets. They do not manufacture a physical PASS.

Power prediction148.0601303mW; original marginal range
[134.7377232,161.3825374]mW. [Saved source](results/week9/source/manifest.json),
[policy files](results/week9/policies/pass_upper.json) and
[hash summary](results/week9/demo-summary.json) are inspectable.

| Case | Policy / evidence | Result / exit |
|---|---|---|
| pass_upper | Upper200mW; policy opt-in AND override flag | PASS0, prominently UNVALIDATED RESEARCH ONLY |
| fail_upper | Upper100mW, same override; range wholly above | FAIL2 |
| abstain_crossing | Upper150mW, same override; range crosses | ABSTAIN3 |
| default_coverage_abstain | Upper200mW, no override;28/30 coverage<95% | ABSTAIN3 |
| error_wrong_units | mW target incorrectly assignedW | ERROR1, strict policy rejection |
| battery_five_years_fail | Explicit battery/repeating workload, research override | FAIL2 |
| battery_missing_workload_abstain | Battery workload profile absent | ABSTAIN3 |
| same_features_regression | Same source, different commit labels,25% allowance, override | PASS0 for configuration estimate; point delta0%, not execution observability |

Every FAIL and ABSTAIN reports blocks_ci=true. Every passing fixture records
both override request/use, research-only label, hardware_assurance=false,
validated_95_percent_coverage=false and configuration-estimate scope. Default
policies cannot quietly pass by lowering minimum coverage or ignoring intervals.
Detailed reasons and all values are under docs/results/week9/reports/.

Upper budget equality U==T passes; L==T with U>T abstains; L>T fails. Absolute
and relative regression compare candidate upper to baseline lower allowance for
PASS, candidate lower to baseline upper allowance for FAIL. Overlap abstains.
These are logical marginal-range comparisons, not a calibrated difference CI.
Zero baseline abstains for relative gates; absent baseline abstains for regression.
Exact rational comparisons of decoded values avoid rounding an allowance upward
and accepting a one-ULP excess; no numerical tolerance expands budgets.

A fixed pre-run model cannot observe a code regression from a commit label.
Identical permitted features produce identical estimates; the same-feature
example exposes that limitation with0% point regression and an explicit false
execution-observability field. Different workload/windows/seed/context must
abstain for comparisons; absolute configuration budgets remain separate.

## Battery example and physical omissions

Nominal capacity1000mAh, voltage3.6V, usable fraction0.8, efficiency0.9 gives
2592mWh load-side energy. Fractions apply once, to energy. Continuous repetition
of the existing148.0601303mW run average yields:

- Point0.00199708years (about17.51h).
- Inverse-power engineering range[0.00183222,0.00219454]years.
- Year explicitly365.25days/8766h; configured target5years, hence FAIL.

This range simply propagates accepted research input bounds; it is not validated
battery-life coverage or a metric confidence interval. The run average already
contains idle/active duty accounting and receives no second duty factor.
Alternative explicit component-state profiles use mutually exclusive compatible
states, complete cycle and fractions summing1; those are declared engineering
assumptions requiring explicit research override, not measured radio states.

Aging, self-discharge, temperature/environment, voltage/capacity changes under
load and transients are omitted. Missing workload, unconfirmed compatible states,
missing power bounds or nonpositive lower power abstains; numeric overflow is
ERROR rather than infinity or a fabricated lifetime. Five years is a configurable
engineering policy target, not a universal EU battery-autonomy mandate or
compliance certification. No deployment or battery assurance is established.

## Test and reproduction evidence

Release full suite305 passes (21 new,108.867s), ResourceWarning errors enabled;
this includes the final report audit enrichment and targeted source checks.
Tests cover upper equality/crossing, relative/absolute thresholds and zero/missing
baseline, one-ULP relative excess, independent2592mWh/1mW/year calculations,
duty/efficiency double counting, incompatible contexts/workloads/provenance,
coverage/shift opt-ins, model/reference/source tampering, malformed JSON/nonfinite/
overflow, aggregate precedence, all four exit codes, collisions/alias prevention
and atomic publication rollback. No tests fit or recalibrate the gate's models.

Two final end-to-end runs to independent fresh output directories produced
byte-identical source/policy/reports/summary. [Receipt](results/week9/reproduction.json)
records all file hashes and expected exits. Original draft demos are retained
locally at build/green-ops-week9-demo; final reports add audit context only,
with unchanged rules, thresholds, predictions and statuses. Python runtime is
recorded in the summary; dependencies are standard-library only.

Reproduce from repository root:

```sh
python3 docs/results/week9/reproduce.py build/green-ops-week9-fresh
python3 -W error::ResourceWarning -m unittest discover -s tools/green_ops/tests
```

All original Week7 models/selection and Week8 calibration/results remain frozen.

## Week10 readiness

Ready for separately authorized CI plumbing and full PR Markdown reporting:
preserve exact0/1/2/3 exits, block both FAIL and ABSTAIN, publish deterministic
JSON as the authoritative decision, and render override/scope/coverage failures
prominently. Report immutable artifact hashes and comparable windows; never
infer physical root causes or energy regressions from commit identity alone.
Output/report publication failures must block the gate too.

Not ready for hardware assurance, validated95% interval claims, automated energy
optimization or regulatory certification. Physical telemetry/measurement alignment,
validated workload/conditions and new genuinely group-disjoint calibration/
assessment are still needed. Any future model/interval/policy tuning must reserve
new final data; these consumed study sets cannot become untouched evidence again.
No Actions workflow, full Markdown reporter, push, remote publication or deployment
was performed in Week9. Windows planning snapshots are refreshed separately by
explicit user instruction; the repository tracker remains authoritative.
