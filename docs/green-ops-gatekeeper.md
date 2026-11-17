# Research energy-budget gatekeeper and battery projection

The gate consumes replay-verified analytical artifacts and frozen Week7/8 model,
calibration and attribution references. It never retrains/recalibrates or trusts
an editable prediction JSON as evidence. It produces deterministic JSON and
exit0(PASS),1(ERROR),2(FAIL),3(ABSTAIN). Both2 and3 block CI; no CI workflow or
Markdown PR reporter is installed (Week10 scope). A PASS is confined to explicit
research policy assumptions, never hardware assurance or compliance certification.

## Policy contract v1

Example: tools/green_ops/policies/green_ops_budget.json. Its exact required fields:

| Field | Meaning |
|---|---|
| budget_version | Integer1; bool rejected |
| policy_id | Nonempty descriptive identifier |
| research_only | Must be true |
| feature_contract_version / feature_profile |3 / raw_pre_run_v1 |
| scope | provenance(analytical_simulation or requested measured), prediction_mode(pre_run), exact model_sha256 map for all3 targets |
| uncertainty | minimum_family_coverage0.95, allow_unvalidated_research_intervals bool, allow_assumption_shift bool |
| criteria | Required criterion objects; empty only when battery gate present |
| battery | Null or explicit battery/workload contract below |

Each criterion has exactly id,kind,target,unit,threshold. IDs unique, `battery`
reserved. Kinds absolute_upper,regression_absolute,regression_relative. Targets
are target_mean_power_mw(mW),target_total_energy_mj(mJ),
target_energy_per_delivered_packet_uj(uJ). Relative unit is percent. Thresholds
finite, nonnegative; no implicit unit conversion. Unknown keys, duplicate JSON
keys, NaN/Infinity, unsupported contracts and malformed types are ERROR. No
criteria means ERROR, not a vacuous PASS. Requested measured provenance is a
valid unsupported scope and abstains with current analytical inputs; the file
adapter does not accept invented physical measurements.

## Evidence, outcomes and uncertainty

The CLI verifies exact model/selection/recipe and calibration inventory/file
hashes, archived Week8 coverage/explanation hashes, source manifest/CSV and
analytical state/energy replay. It recomputes frozen predictions and compatible
signed influences from source snapshots. Planned duration, completion and
available pre-run inputs are checked. A valid different parameter/assumption/
retry/offer configuration or interval schedule abstains; malformed source,
wrong model, feature contract or units errors. Raw state observations/outcomes
never enter X. Pure decide() takes trusted resolved evidence from FrozenEvidence;
it is not a public serialized-evidence ingestion bypass.

Default nominal family coverage is insufficient:28/30 power,28/30 total energy,
26/30 per delivery versus required0.95. All such criteria abstain, irrespective
of a generous numeric ceiling. Lowering the evidence requirement in v1 is
rejected. Override requires BOTH allow_unvalidated_research_intervals=true in
the policy AND --allow-research-override at invocation; every report records
request/use and prominently labels UNVALIDATED RESEARCH ONLY with no validated
95% coverage/hardware assurance. Shift applicability requires additionally
allow_assumption_shift=true. No shift has calibrated coverage assurance.
No implicit point-only fallback can PASS an interval criterion.

For accepted candidate range[L,U] and upper ceilingT: PASS U<=T, FAIL L>T,
otherwise ABSTAIN. Thus upper equality passes; lower equality with upper excess
abstains. Every required criterion is evaluated; aggregate ERROR > FAIL >
ABSTAIN > PASS. A known accepted violation cannot be hidden by another criterion's
missing evidence. Evidence-inapplicable criteria abstain before numeric comparison.

For absolute regression allowanceA, PASS candidate.U<=baseline.L+A, FAIL
candidate.L>baseline.U+A, otherwise ABSTAIN. For relativeR percent, compare to
baseline.L*(1+R/100) and baseline.U*(1+R/100); both baseline endpoints must be
positive. Missing baseline or zero/nonpositive baseline for relative gates
abstains; absolute comparisons permit zero. Point delta and percent are
separate diagnostics (percent null for nonpositive baseline). Allowance comparisons
use exact rationals of decoded numeric values to avoid rounded-up boundaries;
nonfinite representability/overflow errors. No arbitrary epsilon widens budgets.

Comparability requires same model, provenance, parameters/assumptions, payload,
interval, TX, duration/window, offers, retry cap, random seed, adapter/profile,
prediction context and domain. IDs/commit labels do not establish comparability.
These are logical comparisons of marginal ranges; they do not subtract two
marginal intervals and claim a calibrated interval/CI for the difference, nor
promise joint95% coverage. Separate target procedures are not a joint guarantee.

Identical permitted features give identical predictions under a fixed model,
regardless of code commit labels. A same-configuration regression demonstration
therefore reports point change0 and execution_regression_observable_from_commit_identity=false.
Configuration estimates can inform a research budget but cannot detect code
energy regressions without actual execution telemetry/measured evidence and a
suitable observable model. Signed influences are labeled model attributions,
not physical root causes; within-duration permutation's duration blind spot and
all physical-validation limitations from Week8 remain in force.

## Battery contract, units and boundaries

Battery requires exactly capacity_mah,voltage_v,usable_fraction,
conversion_efficiency,year_days,target_years,power_basis,workload_profile.
All capacity/voltage/year/target values positive finite; both fractions in(0,1].
Power basis must be load_side_before_conversion. Example year365.25days =8766h.
Five years is a configurable engineering policy target, not a universal battery
autonomy mandate or evidence of EU compliance/certification.

Load energy[mWh] = capacity[mAh] * nominal voltage[V] * usable fraction *
conversion efficiency. Lifetime[h] = load energy[mWh] / mean load power[mW].
Years = hours/(24*year_days). Usable fraction excludes conversion loss; efficiency
is applied once to energy, never also divided into power. Example1000mAh,3.6V,
usable0.8,efficiency0.9 =>2592mWh; at1mW =>2592h =>0.2956879years on365.25days.

A missing workload_profile is valid insufficient evidence: ABSTAIN for battery.
Two explicit profile forms are supported:

- run_average: exactly kind,repeat=continuous_same_workload,duty_cycle_included=true.
  Uses candidate run-average prediction/range; duty cycle is already incorporated.
  Extra duty fraction is rejected, not applied again. The run includes idle and
  active accounting and is assumed to repeat continuously for the projection.
- component_states: exactly kind,compatible_states_confirmed(bool),compatibility_id,
  complete_cycle(bool),states. Each state has state_id,power_mw,interval_mw,time_fraction.
  IDs unique; powers load-side, nonnegative; endpoint pair/null; fraction0..1;
  fractions sum1 (absolute tolerance1e-12, no renormalization). All states must
  refer to one compatible, mutually exclusive complete cycle at the same power
  boundary/conditions; confirmation/complete-cycle false abstains. State values
  are declared engineering assumptions, not new measurements or calibrated
  model states. Research override required; cannot bypass input applicability.

Mean load power = sum(fraction*state power) only for the explicit component-state
form. A separate run-average duty multiplier is prohibited. Missing bounds,
zero/negative mean power or nonpositive lower power abstains rather than emitting
infinity, clipping or promising infinite life. Overflow/underflow is ERROR.
For positive accepted[Plo,Phi], lifetime range[E/Phi,E/Plo] converts the engineering
bounds, not a new confidence interval. PASS when lifetime lower>=target; FAIL
when upper<target; crossing ABSTAIN. Projection can be descriptive even when the
gate abstains for coverage; its presence never implies acceptance.

Omitted effects: aging, self-discharge, temperature/environment, load-dependent
capacity/voltage, replacement and transients. Nominal voltage and capacity are
constant assumptions. Physical measurements, stochastic workload validation and
independent physical calibration/evaluation remain pending.

## CLI and output safety

From repository root:

```sh
python3 tools/green_ops/green_ops_gatekeeper.py --policy tools/green_ops/policies/green_ops_budget.json --candidate ARTIFACT_DIR --output NEW_DECISION.json
```

Optional --baseline ARTIFACT_DIR, --candidate-revision LABEL, --baseline-revision
LABEL, --domain/--baseline-domain primary|declared_stress. Model/calibration/
original-recipe/study-recipe/reference-dir options default to frozen repository
snapshots. Override flag is explicit as above. Reports contain statuses/reasons,
per-criterion values/ranges/thresholds/units, policy and artifact hashes, scope,
override details, attribution method/units, battery assumptions/omissions and
limitations. ERROR reports preserve the available policy hash without claiming
established provenance. A publication/argument/output-collision error returns1
and cannot guarantee a report at the requested path; stderr explains why.

Reserve a new output before processing; publish via completed sibling temporary
and replacement, rolling back owned placeholder/temporary on failure. Refuse
existing destinations, symlink aliases and any destination inside input source
directories. Never overwrite policy, baseline, candidate or frozen references.
Structured JSON only in Week9; GitHub Actions/full PR Markdown remain Week10.

End-to-end labeled research fixtures (fresh destination required):

```sh
python3 docs/results/week9/reproduce.py build/green-ops-week9-demo
```

The driver regenerates exactly one existing frozen nominal workload as synthetic
simulation, uses unchanged model/calibration, and verifies all exit codes. It
creates inspectable policy/source/decision JSON and a hash summary; no passing
physical measurements are invented and no model outputs are edited. The same
source is used for all illustrative thresholds and the baseline. A second run
to a different fresh directory must produce byte-identical reports/summary.
