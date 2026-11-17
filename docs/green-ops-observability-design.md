# Post-run execution observability design (proposed v1)

Status: design only, no new firmware hooks, validator, model or approval policy
implemented. Scope follows the [requirements audit](green-ops-requirements-evidence-audit.md).
Existing datasetv1/v2, feature-contract3, frozen Week7/8 models/calibration,
Week9 policies and Week12 benchmark/consumption records remain unchanged.

## Feasibility from inspected interfaces

“Requested” is intent, “submitted” is a call issued, “accepted” is immediate API
acceptance, “completed” is a result event, “received/accepted by peer” needs that
peer's evidence. Independent observation identifies behavior using a separate
measurement path; a software-maintained counter is instrumented evidence, not
an independent physical measurement. Keep layer/scope in field names.

| Mechanism | Existing source/interface | Feasible laptop-first instrumentation | Unsupported/unverified or hardware-dependent claim |
|---|---|---|---|
| CPU busy-poll | [Ping](../examples/src/bin/ping.rs) awaits `rx`, `time_get`, `tx`; no scheduler/CPU-state observer in reviewed Green Ops code | Count tagged application work sections/poll invocations and measure instrumented section elapsed time, explicitly wall-time only; host-test interval bookkeeping | Async call elapsed time includes waiting/other tasks/interrupts and is **not CPU-active time**. Actual application-core active/sleep residency requires audited executor/idle+ISR hooks or a validated hardware counter/trace backend. Counter frequency, wrap, sleep/debug behavior need proof. Modem/network-core activity remains separate/unobserved |
| TX power lock | [DectPhy::tx](../hophop/src/nrfxlib_phy/mod.rs) takes PCC/PDC, not an actual-power getter; Ping writes PCC byte0x70; completion returns result only | Log request header bytes, submitted channel/schedule and API result. Preserve raw power code with mapping revision, not an assumed dBm conversion | No actual local PA power/config readback exposed in reviewed wrapper. MAC association callback `rx_signal_info.transmit_power` describes received association signal, not local-TX readback. Remote advertised power bits are not a calibrated RF measurement. Need supported vendor diagnostic/readback API evidence or calibrated independent RF observation before claiming actual power; PPK2 alone cannot identify it |
| Retry storm | PHY one `tx` operation result; MAC `dlc_data_tx` callback fields transaction_id/status/flow_id/peer only; no per-attempt count | Add stable operation IDs and application retransmission counters in new workload, record attempts/results/timeout reasons at that layer | Do not infer internal modem/MAC retries from one API call, elapsed time, a success or sequence gaps. A modem attempt-level trace/counter must be documented/exposed/validated, otherwise null. Application retry evidence has narrower scope |
| Beacon hyper-wakeup | Ping `record_sync_beacon` only on decoded matching timestamp IE; MAC `cluster_beacon_ntf` parses notices | Count recognized beacon events; record each explicit RX submission and completion including timeout; later observe actual wake/sleep hooks if available | Received beacons ≠ wake count or wake duration. Wakeups with no decoded packet invisible today. Configured schedules ≠ actual RF residency; start/end events must be established or unknown |
| Fragmentation bloat | Ping constructs/pads a fixed33-byte PDC; no Green Ops fragment/reassembly counters; MAC DLC accepts whole data slice | New diagnostic workload can carry logical message/fragment IDs, payload/header lengths; count generated/submitted/completed fragment operations and receiver reassembly/duplicates separately | No claim to see modem-internal segmentation of a DLC submission. On-air fragmentation needs appropriate trace/receiver validation. Application fragmentation is an explicit new workload behavior, not proof of modem fragmentation |
| Unique delivery | `tx_successes` after successful await, decoded RX before full parsing; no logical offer/accept IDs in existing Ping; DLC RX exposes peer/flow/data | New bounded sender offer registry and receiver accepted logical-ID evidence, receiver duplicate filter, optional acknowledged reply | TX completion does not prove peer delivery. RX decoded frames may be invalid/duplicates. Queue/pool loss in `rx.rs`/MAC callbacks must be reported rather than silently treated as RF loss. Peer clocks require mapping for window membership |

Radio clocks: `nrfxlib_phy::TICKS_PER_SECOND=69_120_000` and `time_get()` return a
local modem timestamp through an async event. RX PCC `stf_start_time` is retained
in `Pcc.time`; it is an event timestamp with distinct semantics. TX completion
callback time exists in `DectEventOuter` but `tx()` discards it and it is not RF
start time. `latency.rs` verifies modem PHY2.0 operation transition constants at
startup; those are not measured packet RTT or CPU residency. Current `rx()`
requests70,000,000ticks (~1.013s at declared frequency), not a100ms sampler.
`RADIO_MODE=LOW_LATENCY` is a source setting, not measured power validation.
No additional vendor readbacks or OS scheduling APIs are assumed by this design.

## New artifact boundary and proposed strict contract

Introduce a separate `execution_observation_version=1` JSON artifact and profile
`post_run_diagnostic_v1`. It is **not** a new meaning for feature-contract3's
existing `post_run` profile. No loader fallback/migration into frozen models.
New observation/model binding must explicitly name this artifact/profile and
adapter capabilities. Default gate rejects an incompatible artifact (ERROR),
or abstains on valid unavailable evidence (ABSTAIN); it never silently accepts
post-run evidence as pre-run input.

Proposed top-level exact keys (future validator must reject unknown keys):

| Key | Meaning / constraints |
|---|---|
| `execution_observation_version`, `profile_id` | Integer1 and exact `post_run_diagnostic_v1` |
| `identity` | Exact run_id, window_id, boot_id, device_id, session_id, adapter_id, adapter_version, firmware_revision/full dirty-state digest, modem_revision, instrumentation_revision, capability_manifest_sha256; each identifier bounded/safe; unknown values explicit null+reason, hardware identity required for hardware assertions |
| `provenance` | source_kind/execution_kind/measurement_status with existing compatible vocabulary, plus observation_origin (`instrumented_firmware`, `synthetic_fixture`, `analytical_trace`) and raw source references/hashes. Hardware execution telemetry alone remains `measurement_status=unmeasured` for energy until a separately validated measured label is joined; no new enum silently added to old APIs |
| `window` | segment/boot continuity, one declared half-open observation interval, actual start/end ticks and snapshot bounds, clock IDs, rational ticks/second, planned versus actual duration, boundary ordering, maximum duration, clock mapping/uncertainty and alignment references |
| `requested` | Intended workload/configuration and raw modem/header request codes with documented mapping version. Never renamed actual or readback |
| `capabilities` | Exact supported/unsupported observation IDs, layer/component/scope, capture method/revision, counter widths/saturation/wrap semantics, temporal coverage and unit declarations. Profile capability is explicit, not inferred from numeric0 |
| `observations` | One entry for each field in the registry below, with availability/quality wrapper; null is allowed only with reason. No unregistered field may enter model input |
| `quality` | Snapshot/sequence discontinuity, dropped event count, buffer overflow, counter saturation/reset, time gaps, clock mapping validity, capture completeness, error records and explicit usable/unusable flags. Unknown dropped-count is unknown, not0 |
| `overhead` | Instrumentation mode, ring capacity/event sizes, timer cost metadata, bytes/event count/drop count, log transport and debug/LED state; independent overhead-study reference or `not_measured` |
| `references` | Hashes and safe relative references to immutable raw telemetry, capability manifest, intended workload, timing/alignment evidence and parser/config version; bounded file sizes, no path traversal/symlink escape |

Every observation entry has exact fields `value`, `unit`, `availability`,
`reason`, `method_id`, `scope`, `clock_id`, `coverage`, `evidence_refs`.
Availability is `available`, `unsupported`, `not_collected`, `invalid` or
`partial`. Only `available` with complete declared coverage can feed a model;
others carry null canonical value (partial raw values remain raw evidence, not
a complete-window count). Reason is null only for available fields. Reject bool
as numeric, NaN/Infinity/overflow, unknown units, negative counts/durations and
inconsistent scope/capability. A valid available0 means a complete observation
with no such event. Missing and zero must never collapse.

### Proposed observation field registry

These are potential fields, not a promise all are initially observable. Each
adapter must declare support; the first sprint supports application-level events
and leaves deeper fields unavailable. A diagnostic model's exact required subset
must be frozen before fitting; missing required fields cause abstention, not
zero-fill or model switching based on outcomes.

| Field(s) | Unit and exact meaning | Initial availability / interpretation |
|---|---|---|
| `app_cpu_active_us`, `app_cpu_sleep_us`, `app_cpu_unknown_us` | µs, disjoint app-core residency classes over window; include ISR activity according to declared hook method | unsupported until validated residency backend. No `.await` wall-time proxy. Sum must equal covered window only when method proves full partition |
| `app_work_section_elapsed_us` | µs wall time within identified work sections, possible interrupt/preemption time included | optional instrumented diagnostic, **not** active CPU or whole-device state energy input |
| `local_tx_power_readback_dbm` | dBm, local configuration reported by a verified API at timestamp; if changing, use timestamped series/distribution, not last value as whole-window state | unsupported in current wrapper; do not insert requested power. Configuration readback is still not measured radiated power |
| `rf_tx_power_observed_dbm` | dBm at documented observation point, calibrated RF instrument/method | unsupported without RF hardware; keep loss/antenna/calibration uncertainty and external clock alignment |
| `tx_submit_count`, `tx_accept_count`, `tx_complete_ok_count`, `tx_complete_error_count`, `tx_pending_at_end_count` | operations at adapter-declared PHY/DLC/application layer, each with unique operation ID and timestamps | future hooks feasible, not existing all-fields capture. Success is operation result, not receiver delivery |
| `app_retransmit_count`, `app_reply_timeout_count` | extra application submissions of same logical request ID; expiration of matched request deadline, respectively | new workload only. Timeout is not proof of radio packet loss; may reflect responder/queue delay |
| `modem_tx_attempt_count`, `modem_retry_count` | attempt events and retransmissions at an explicit modem/MAC layer | unsupported absent vendor evidence; never infer from application counters |
| `rx_submit_count`, `rx_complete_count`, `rx_timeout_count`, `rx_decode_ok_count`, `rx_decode_error_count` | operations versus decoded/error frames. Zero-frame completed operation/timeout separately defined; one RX can contain multiple frames | submits and decoded frames currently partially observable; need terminal/error/event hooks and quality/drop reporting for complete window |
| `recognized_beacon_count` | matching decoded beacon packets, once per packet | feasible existing counter semantics; not all beacons or all wakeups |
| `radio_wake_event_count`, `radio_rx_resident_us`, `radio_tx_resident_us`, `radio_idle_us`, `radio_unknown_us` | supported radio component transition events / exclusive residency durations | unsupported until actual transitions documented; planned operations/elapsed awaits do not supply these fields |
| `logical_offer_unique_count`, `logical_accept_unique_count`, `logical_duplicate_count` | IDs `(session,sender,sequence)` offered at sender, valid reassembled accepts at receiver and duplicate receives; one logical ID per message | new sender/receiver workload/evidence; retain missing peer coverage as unavailable. Offer at queue admission must be defined once; count failed sends as offered |
| `fragment_generated_count`, `fragment_tx_submit_count`, `fragment_tx_complete_ok_count`, `fragment_rx_accept_count` | application-layer fragments with `(logical_id,index,count)` and bounded lengths | new explicit application protocol only; not modem-internal fragment count |
| `logical_payload_bytes`, `fragment_payload_tx_bytes`, `fragment_header_tx_bytes` | offered useful payload bytes; submitted fragment payload/header bytes including separately defined retransmissions | new counters from actual submitted buffers. Not RF on-air bytes unless independently traced; avoid multiplying already counted retry bytes |
| `telemetry_event_drop_count`, `telemetry_snapshot_miss_count` | lost bounded-buffer events / missed scheduled snapshot deadlines | new quality instrumentation; a lost completion invalidates corresponding count partition |

Derived diagnostics (ratios/count deltas) must bind source fields, units and
validity. E.g. unique delivery ratio divides accepted offered-window IDs by
sender offers, never decoded frames by RX calls. Counter totals are cumulative
snapshots with explicit baseline subtraction; per-operation event lists permit
exact boundary assignment. Counter-only cross-boundary transactions cannot be
claimed an offered-cohort delivery result.

### Clock, window and concurrency rules

- Keep modem ticks, application monotonic ticks, receiver ticks and instrument
sample time as separate domains with declared rational frequency and mapping
revision. Convert using checked integer/rational arithmetic, retain raw ticks
and rounding uncertainty; don't truncate sub-microsecond time without an error
bound. Host serial arrival times are transport timestamps only.
- Canonical event membership is `[start,end)`, start inclusive/end exclusive.
Declare whether each count is submission-cohort or completion-in-window; never
mix the two silently. For submission cohorts retain pending/terminal outcomes
and a separate finite delivery follow-up deadline. Late accepts/replies are
reported late and excluded from an in-window target; no grace period invented
after outcomes. Receiver acceptance and offered-cohort delivery need separate
fields/evidence when they cover different windows.
- Start/end markers and counter snapshots have bounded bracketing timestamps.
One marker alone cannot prove clock rate/drift. Prefer two or more synchronized
edges/cross-timestamps and an independently bounded mapping residual/drift;
reject excessive uncertainty, resets, unobserved wraps and multi-boot segments.
Atomic snapshot or monotonic event sequence ordering is required; scheduler and
ISR counters need defined synchronization, not torn reads. Saturated existing
u32 counters invalidate deltas. A future wrap-aware scheme needs exact wrap
count/proven continuity; do not relax current reset/wrap rejection.
- A proposed100ms sampler is scheduled against absolute deadlines in a dedicated
non-blocking task, not by sleeping100ms after each radio await. Snapshot lateness,
coalescing and drops are explicit. It cannot infer100ms actual behavior from a
single1s RX operation. Sampling cadence, aggregation window and packet interval
are different parameters. If busy-poll starves sampling, preserve the miss as a
quality failure, not fabricated regular samples.
- Track operation IDs across submit/accepted/completed/cancelled/error states.
Snapshot of in-flight operations plus event history reconciles arrivals,
completions and pending counts. Reject duplicate terminal events, unknown IDs or
lost state transitions; record errors rather than preserving current `.unwrap()`
panics as a complete successful capture. Capture buffers must be bounded.

### Instrumentation overhead, provenance and leakage

Use feature-gated fixed-size records in a bounded ring with sequence/drop
counters; avoid formatting/serial I/O in callbacks or timing-critical sections.
Drain asynchronously after snapshots or capture completion. Count marker,
sampling and ring work as part of execution; measure instrumented-vs-disabled
energy/time/jitter on matched randomized runs. Report distributions and uncertainty
with debug/transport states. Do not subtract overhead automatically from total
energy or call overhead negligible before measurement. Overhead threshold and
jitter budget must be predeclared in pilot acceptance, not chosen after data.

Metadata/IDs, device/session splits, hash references, seeds, fault kind/severity,
oracle energy, generator state truth, gate outcome and target labels never enter
X. Separate observation collector input from labels and injected-fault metadata
at API/file boundaries. A synthetic/analytical observation fixture remains such;
serializing generator truth into this schema does not make it firmware telemetry.
State which production call/trace produces every available value. Reject model
artifacts bound to raw_pre_run_v1 when given post_run_diagnostic_v1 observations.
No retraining or calibration reuse of frozen studies follows from this design.

Post-run observations are unavailable at pre-run approval time: a diagnostic
can classify a completed run, not prevent that run's consumption. A later CI
measurement gate must actually execute representative workloads and validate
telemetry/evidence first. If required observability is missing, abstain. Field
selection and preprocessing fit use development only; split device/session/
configuration parents and keep related repeats/variants together. Reserve new
physical groups; old evaluation groups do not become fresh via new seeds.

Delivery counts in energy-per-delivery prediction share its denominator and
can create a nearly direct arithmetic relationship; demonstrate total-energy
prediction separately and compare the accounting baseline. Observed RTT is a
label/quality diagnostic, never a feature for predicting that same RTT. Measured
energy/current/energy-derived estimators must not enter energy X. Calibrated
state-current parameters fitted on training measurements are fixed model
parameters, not per-row measured-current leakage.

## RTT acquisition and supervisor decision

The existing Ping's remote scheduled timestamp and local receive time live on
different clocks and different events; their difference is neither one-way
latency nor RTT. No response correlation or timeout state machine exists.
`latency.rs`'s radio transition constants cannot fill this gap. CoAP resources
in `hophop/src/coap.rs` manage association/configuration; no Green Ops RTT probe
or target-evidence adapter is implemented there.

**Decision needed before latency implementation acceptance:** supervisor chooses
(A) measured RTT plus physical latency-regression prediction as core objective,
(B) measured RTT as a QoS constraint alongside energy, or (C) explicitly deferred
scope with title/objectives amended by agreement. Until then latency remains open,
not satisfied or removed. This design task needs no immediate answer to finish.

If A or B: add a separate feature-gated request/reply binary/protocol rather than
silently change existing beacon format. Initiator offers bounded payload with
session nonce, sender ID and monotonic sequence; responder echoes correlation
fields only after validating/reassembling request. Keep duplicate detection,
late replies, timeouts and responder service policy explicit. Payload overhead,
retransmissions and energy of replies are part of this workload, not free.

Predeclare application RTT `t_reply_accept - t_request_submit` on the **same
initiator monotonic clock**; submit timestamp immediately before adapter call,
accept timestamp at validated complete reply delivery. This includes local queue,
radio, responder and return-path delays. It is not pure RF RTT, CPU time or
one-way latency. Keep raw event timestamps and clock scale/calibration uncertainty;
software callback latency is part of this endpoint definition. A different
radio-to-radio estimand needs separately supported event timestamps and new name.

A single outstanding request first keeps correlation bounded; configurable
payload/period/deadline and finite follow-up horizon are frozen before captures.
Timeouts are right-censored/failures, not0ms or a successful RTT equal to timeout.
Report offers, replies, timeouts, duplicates, late/malformed replies, success
conditional distribution and observation denominator. Missing pairs stay null.
Self-check clock deltas/wrap and ISR-to-task delay; validate endpoints with GPIO/
logic capture where possible, without pretending it measures RF propagation.

Current hardware RTT is deliberately null in datasetv2. Future `rtt_evidence_v1`
(raw matching events, clock/window mapping and estimator) needs an explicit
versioned adapter and strict loader extension, not a nonnull edit to an old
manifest. New schema acceptance must preserve old hardware-RTT rejection and
all existing v1/v2 behavior until a new opt-in evidence path is implemented.

## Transparent state-accounting baseline

Before ML, compute an inspectable baseline from **observable and validated**
component states, with explicit parameter provenance:

`E_mJ = sum_s(V_V * I_s_mA * duration_s_us / 1_000_000)`;
`mean_power_mW = E_mJ / actual_window_s`;
`energy_per_unique_delivery_uJ = 1000 * E_mJ / delivered_unique`, or null at0.

Durations partition observation time **within each component** including unknown.
CPU and radio can overlap: don't add full-device CPU-busy current to full-device
radio current for the same time. Either use measured mutually exclusive joint
states spanning the chosen supply rail, or explicitly calibrated incremental
component currents above a single shared idle baseline with overlap rules.
Account for regulator/peripheral/measurement rail once, and never reapply duty
cycle to a run-average power. Unknown residency yields incomplete/unsupported
estimate or predeclared bounds, not an invented idle remainder.

Use sourced currents only under applicable voltage/mode/temperature conditions;
otherwise label configurable assumptions or fit parameters on development
physical data only. Parameter/observation/clock hashes, units and sensitivity
must be inspectable. Compare against measured aligned total energy and training
mean, then residual ML if justified. If X contains almost all state durations,
recovering this equation is a transparent accounting test, not discovery of
hidden physics. Report whether any gain over accounting survives new physical
parents, uncertainty and overhead. No retrospective fit to Week12 or existing
calibration/evaluation labels is proposed.
