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
