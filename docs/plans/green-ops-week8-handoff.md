# Week8 current task / next step

Branch green-ops/week8-uncertainty-explainability, clean entry00c19c2.
Freeze3e0dd39; tested methods/data6da8dba; ablations3e491f9; calibration4d66d51
committed before actual evaluation. Read week8 plan, docs/green-ops-week8.md and
results doc. Original Week7 selection/models unchanged, no held-out tuning.

Current: Week8 complete; release suite284 passes (108.5s), ResourceWarning
errors enabled. Exact replay passes after final dataset-digest and seed/run
compatibility guards, with no numerical changes. Final verified results/evidence
committed541bda5; next separately authorized Week9 work.
Read docs/green-ops-week8-results.md and docs/results/week8/reproduction.json.

Real data build/green-ops-week8-data, independent regeneration -data-replay;
committed snapshots docs/results/week8/{ablations,calibration,evaluation}.
1800 sources;450cal/450eval/900stress;60 genuinely new families,30cal/30eval.
4050 interval predictions but only30 eval families shared by stress panels.
Nominal family coverage93.3/93.3/86.7%, below95%; high shift76.7/76.7/80%.
Do not retune. Permutation within duration cannot identify duration importance;
contributions/ablation show its strong total-energy effect. Report this blind spot.

Week9: research-only gatekeeper can proceed with scope/provenance/abstention
checks and explicit coverage failures. No physical95% guarantee or deployment
readiness. All new sets now consumed; tuning requires new group-disjoint final
data. No hardware actuation, fake PPK2, push/publish or inferred research hours.

Final verified results/compatibility commit541bda5. Week8 complete; no pending
implementation. Next separately authorized Week9 work. Verify clean Git status.

Standing user instruction: refresh the Windows status export after each verified
milestone/local commit, before requesting input and before stopping. See
[export policy](green-ops-status-export.md) for exact external paths and atomic
publication requirements. Repository tracker remains authoritative; no polling
service or second agent. Export success does not mean the Windows chat read it.
