# Analytical assumptions v1 — reference model 1.0.0

The nRF9151 DECT minimum-latency profile uses exclusive idle/TX/RX VDD scenario
currents at the documented nominal conditions; it is not a deep-sleep model.
CPU/peripheral contributions are not independently added. Board overhead,
retention, frequency/voltage/temperature response and firmware costs are omitted.
There is no TX-power interpolation: the sourced profile requires requested
19 dBm, band 1, 3.7 V, 25 C, -90 dBm RX and the minimum-latency modem mode.
Actual firmware/device agreement with this mode has not been demonstrated.

The current envelope is assumed +/-20%, with no confidence or guarantee claim.
Preparation, TX fixed/per-byte durations, RX/ACK wait and backoff are arbitrary
configurable timing assumptions in microseconds; their full ranges are in the
parameter JSON. They are not measured firmware timing or standardized airtime.
A packet's complete worst-case retry path must fit its reserved fixed slot.
Slots start at 0 and are wholly inside [0,window_duration); unused time is idle.
Preparation and backoff use idle current; TX and RX states replace that current.
Every attempted local TX completes; each attempt then listens in RX for an ACK.
Independent Bernoulli loss determines receiver acceptance/ACK decode together;
ACK loss and application rejection are not separate modeled processes. Retry
success ends the logical packet; retry exhaustion records an undelivered offer.
Logical delivery IDs are unique per run/packet and explicitly modeled evidence.

The SHA-256-counter Bernoulli sampler is keyed by versioned domain, seed, packet
index and attempt index. It does not sample currents or durations implicitly.
Sensitivity reuses those draws and varies one declared parameter at a time.
Invalid range scenarios (e.g. a slot overflow) remain recorded as invalid.
These one-at-a-time envelopes are not joint extrema or prediction intervals.

RTT defaults to null. If rtt_extra_ms is explicitly configured as an assumption,
reported RTT is the mean offer-to-ACK completion time over delivered packets,
including preparation, retries and backoffs, plus that assumed extra delay.
The extra delay is a diagnostic latency assumption outside the local energy
schedule; it does not create additional local radio activity. No observed
latency or real correlated-clock evidence is claimed. No deliveries gives null.

Source metadata and the parameter file are hashed separately from this document.
Changing assumptions or parameters requires new versions and artifact hashes.
Analytical labels support software experiments only. Physical calibration,
independent scenarios and later grouped evaluation are still required.
