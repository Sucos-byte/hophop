# Local Green Ops evidence demonstration

Implementation plan: [dashboard plan](plans/green-ops-dashboard-plan.md).
Read-only saved-artifact inspection; no live telemetry, hardware status or gate
execution. No cloud, database, external scripts/fonts or network data fetches.

## Display mapping (declared before UI implementation)

All numeric study values come from allowlisted, SHA-256-bound artifact snapshots,
not from these prose descriptions. A trusted local catalog identifies exact bytes;
hashes are identity/integrity checks, not authentication or physical validation.
Explicit schema adapters reject incompatible versions/provenance and missing
required fields. Unavailable sections show an error; no fallback demo numbers.

| View / value | Source and exact fields | Interpretation / validation |
|---|---|---|
| Overview architecture/milestones/gaps | `docs/green-ops-project-results.md` evidence table; `docs/green-ops-requirements-evidence-audit.md` R01–R16; observability sprint | Editorial architecture labels are labelled documentation; source documents are linked as inert text. Milestone/evidence table is parsed from source, not invented completion percentages |
| Overview study counters | Week12 `aggregate.json.overall` and `.by_split`; Week7/8 prediction `.rows` unique run/group identities | Counts are derived from records; prediction-record totals differ from unique runs/groups, no independence claim |
| Experiments | Week12 `cases.jsonl`: `case_id,parent,split,window_ms,seed,predictor.feature_order,baseline_inputs,feasibility,artifact_sha256,report_sha256` | Intended configuration, not actual state; planned bounded window duration only. Start/end raw timestamps unavailable here. Identity hashes link manifests, not fake measured traces |
| Prediction points/reference/errors | Week7 `evaluation/predictions.json.rows`: `truth,prediction,partition,target,model_role,run_id,group_id`; evaluation `.partitions[panel][target][model]`: MAE/RMSE/R²/unit/sample/group counts | Reference is analytical truth, not measurement; signed error=prediction−truth and absolute error in target units; missing labels remain missing; R² dimensionless, never percentage accuracy |
| Intervals/coverage/shift | Week8 `evaluation/predictions.json.rows`: `lower,upper,truth,prediction,unit,panel,assumption_shift`; `evaluation.json.panels[panel][target]`: `.point_metrics,.coverage,.q`; `.nominal_coverage,.coverage_unit` | Show row and family coverage separately with labeled-row/family denominators; panels share families. Nominal95% is a target, not a validated hardware guarantee |
| Baseline comparison | Week7 `.partitions[panel][target].baseline` versus `.chosen` and paired saved prediction rows | Training-mean baseline; Week8 has no mean-baseline prediction in its interval file: explicitly unavailable, no fabricated join across different studies |
| Gate decision/reasons/budgets | Week9 `demo-summary.json.cases[name]` report/policy SHA; matching `reports/name.json` validated by `green_ops_report.validate_decision` against matching policy | Saved research fixtures, not current candidate approvals. Show status, exit, block, `reason_codes,criteria,provenance,evidence_label,research_override_used,comparison_scope` plus identities/context/attributions/battery where present |
| Fault summary and strata | Week12 `aggregate.json`: `overall,by_split,by_fault_severity`, case-level `.oracle_violation,.positive_detection,.status,.blocked,.configured_fault,.observable,.inputs_changed,.predictions_changed` | Oracle energy vs predictor/gate remain separate. ABSTAIN/ERROR blocks are not detections. Control false alarms plus abstention blocks shown together. Cases dependent within parents |
| Evidence references | Catalog path/SHA, Week12 `execution.json.outputs_sha256`, `manifest.json.entries`, Week7 selection/Week8 recipe/model hash bindings | Only fixed catalog IDs can be read/downloaded; paths in artifact text are never followed. Frozen historical evidence only |

Implementation/launch/walkthrough and actual verification evidence will be added
after checks. Next backend work remains the separately documented observability
sprint, not tuning consumed results through this interface.

## Launch (from the repository root)

```bash
python3 tools/green_ops/dashboard.py
```

Open **http://127.0.0.1:8765** in a local browser. Stop with Ctrl+C.
Optional `--port 8766` changes only the local port. The address is fixed to IPv4
loopback; no bind-all option, cloud service, database or package install is needed.
Python3.14.4 was used for unit/HTTP verification; the isolated browser check also
ran the server under Python3.11.15. Opening index.html directly is unsupported:
the standard-library server supplies the validated snapshots and safe routes.
No browser is opened automatically and no service is installed.

At startup the server snapshots only resources listed in
`tools/green_ops/dashboard_assets/catalog.json`. The catalog pins historical
be90857 evidence; the UI identifies this evidence checkpoint separately from the
new dashboard implementation commit. Restart to reload snapshots. Missing,
modified, incompatible or unsupported artifacts show section-level errors.
Do not blindly re-pin hashes to suppress these errors; review source/schema
compatibility first. The catalog itself is trusted local application configuration,
not a signature. Frozen results remain untouched. Project evidence documents are
shown as text, not interpreted Markdown or active HTML.

## Views and navigation

- **Overview:** documented architecture, source-derived evidence/milestone table,
  benchmark counts, provenance boundaries, requirement gaps and next backend work.
- **Experiments:** paginated Week12 case identities, intended payload/interval/
  requested power, parent/split, declared observation duration, feasibility and
  exact artifact/report hashes. Filter split/mechanism or search case/parent ID.
  Raw start/end timestamps and actual states are not in this saved table.
- **Predictions:** Week7 training-mean versus frozen ridge, per-target MAE/RMSE/R²,
  analytical reference/point/signed+absolute error tables; Week8 saved intervals,
  separate family/row coverage and assumption-shift panels. Charts show only
  the first10 labeled records on the current page and have text/table equivalents.
- **Gate decisions:** all four statuses from validated saved research fixtures,
  reason codes, budget/units, actual point/interval units, baseline/regression
  comparisons, prediction context, uncertainty, attribution and battery details.
  PASS fixtures with explicit research overrides are prominently labelled. The
  default coverage fixture still ABSTAINs. No gate is executed by viewing it.
- **Fault benchmark:** five mechanisms plus controls, partition/severity strata,
  feasibility, known-oracle violations, positive FAIL/missed counts, all gate
  statuses, control false alarms/blocks, paired effects and observability gap.
  Cards use the selected partition; the mechanism filter narrows the table only.

Navigation uses ordinary keyboard-accessible links; Tab/Shift+Tab traverse links,
filters and controls, Enter activates them, native selects use keyboard choices.
Wide tables scroll inside a labelled focusable region (arrow keys when focused),
not by overflowing the page. All decisions have text labels; chart reference is
circle, prediction diamond, interval line with legend/units. Provenance banner
stays visible when scrolling. No timed refresh, animation or fake live activity.
Counts are formatted for readability; high-width seeds are transported as decimal
strings to avoid JavaScript integer precision loss. IDs/seeds are never features.

## Five-minute professor demonstration

1. **0:00–0:50 — Overview.** State “saved analytical evidence, no measured hardware
   validation.” Read the loaded benchmark counters. Explain that software
   implementation and energy-fault detection effectiveness are different results.
   Show source-derived evidence boundaries and architecture.
2. **0:50–1:35 — Experiments.** Keep locked evaluation, filter CPU busy-poll, open
   one hash/input detail and paginate. Point to intended configuration and its
   parent group. State that the window is analytical duration, not a physical
   capture or actual CPU-state trace.
3. **1:35–2:45 — Predictions.** Start Week7/test/mean power: compare the baseline
   and frozen ridge table and reference/prediction points. R² is dimensionless,
   not percentage accuracy. Switch Week8/primary; contrast row versus family
   coverage and their denominators, then choose airtime-high. Explain shared
   families, assumption shift, poor coverage and no hardware guarantee. Week8
   lacks a compatible saved mean-baseline comparison; it is not invented.
4. **2:45–3:45 — Gate decisions.** Show default coverage ABSTAIN, then filter PASS
   and read the explicit research-only override. Show FAIL/ERROR; distinguish
   software-smoke success from candidate approval. Expand criterion context or
   battery projection: years are an engineering projection, not certification.
5. **3:45–5:00 — Fault benchmark and next step.** Locked evaluation shows zero
   positive detections across its oracle violations and blanket abstention,
   including compliant controls. ABSTAIN/ERROR blocks are not positive detections.
   Explain unchanged permitted X → unchanged predictions. Return to Overview's
   observability sprint link: actual-execution capability/operation/logical-ID
   bookkeeping is the next backend task, followed by synchronized physical
   validation. Do not suggest tuning consumed data or inventing hardware traces.

## Validation and screenshots

The first full suite passed367 tests (353existing+14new). The final missing-label
case adds one meaningful dashboard test; final count/result is recorded in
`docs/results/dashboard-demo/verification.json`. Run all tests with:

```bash
python3 -W error::ResourceWarning -m unittest discover -s tools/green_ops/tests
```

Dashboard tests open ephemeral localhost sockets; a restricted execution sandbox
may require local-socket permission. The optional browser checker is separate
from the standard-library runtime. In an isolated development environment with
Playwright and its Chromium/system libraries installed:

```bash
python3 tools/green_ops/dashboard_browser_check.py build/dashboard-browser-new
```

The output directory must be new. It starts/stops its own loopback server,
verifies desktop1440×1000 and narrow390×844, keyboard navigation, pagination,
shift/status filtering, exact regression/battery units, inert hostile text,
missing evidence and absence of external requests, then saves PNGs/JSON.
Temporary browser tooling is not added to project dependencies. Do not interpret
these checks as GitHub Actions or physical execution. No ports/processes remain
running after the checker exits.

Representative screenshots and the actual browser/check receipt are under
[docs/results/dashboard-demo](results/dashboard-demo/browser-check.json):
[desktop overview](results/dashboard-demo/desktop-overview.png),
[desktop intervals](results/dashboard-demo/desktop-intervals.png),
[desktop fault benchmark](results/dashboard-demo/desktop-faults.png),
[narrow overview](results/dashboard-demo/narrow-overview.png),
[narrow intervals](results/dashboard-demo/narrow-intervals.png),
[narrow fault benchmark](results/dashboard-demo/narrow-faults.png).
Screenshots are saved-artifact UI captures, not measured power traces.

## Limits and security scope

Only explicit static routes, `/api/summary`, two paginated read APIs and
`/resource/<catalog-id>` are served. The whole repository, arbitrary paths,
symlinks/nonregular files and API execution routes are not exposed. Mutating
methods return405, unknown routes404, invalid queries400; Host/Origin checks,
no-CORS, CSP, no framing and nosniff reduce local-browser exposure. Resources
are immutable in-memory snapshots and served as text/plain. Artifact strings
use DOM textContent, never HTML interpolation. Paths embedded inside artifacts
are never followed. Localhost is not authentication against other local
processes/users; do not expose through a proxy/tunnel or treat it as a hosted app.

Browser evidence covers Chromium on this Linux laptop only. Firefox/Safari,
Windows browser/WSL forwarding, screen readers, a full accessibility audit and
real device observations remain unverified. Responsive checks permit intentional
horizontal scrolling inside data tables/navigation. No promises of offline
browser installation: once local runtime/assets exist, demonstration requests
need no network. Historical source citations in documents may refer to remote
sites; the application does not fetch them.

No retraining/recalibration, policy changes, benchmark re-scoring, new approval,
physical capture or consumed-data relabeling occurs. Next backend implementation
remains [the observability sprint](plans/green-ops-observability-sprint.md).
