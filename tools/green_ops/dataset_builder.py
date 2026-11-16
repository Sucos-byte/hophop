# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Build platform-independent Green-Ops dataset features from run artifacts."""

from converter import CSV_FIELDS, RUN_ID_PATTERN


COUNTER_COLUMNS = (
    "rx_attempts",
    "rx_data_packets",
    "sync_beacons",
    "tx_successes",
)
EVENTS = {"rx_data", "sync_beacon", "tx_success"}


def _nonnegative_integer(value, field):
    if type(value) is int:
        result = value
    elif isinstance(value, str) and value.isascii() and value.isdecimal():
        result = int(value)
    else:
        raise ValueError(f"{field} must be a non-negative integer")
    if result < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return result


def _optional_counter(value, field):
    if value == "" or value is None:
        return None
    return _nonnegative_integer(value, field)


def aggregate_telemetry(rows):
    """Aggregate cumulative event counters without crossing segment boundaries."""
    run_id = None
    source_kind = None
    segments = {}
    row_count = 0

    for row in rows:
        row_count += 1
        if not isinstance(row, dict) or set(row) != set(CSV_FIELDS):
            raise ValueError("telemetry rows must contain exactly the event CSV fields")

        current_run_id = row["run_id"]
        if (
            not isinstance(current_run_id, str)
            or RUN_ID_PATTERN.fullmatch(current_run_id) is None
        ):
            raise ValueError("telemetry run_id is invalid")
        if run_id is None:
            run_id = current_run_id
        elif current_run_id != run_id:
            raise ValueError("telemetry rows contain multiple run_id values")

        current_source_kind = row["source_kind"]
        if current_source_kind not in {"synthetic", "hardware"}:
            raise ValueError("telemetry source_kind must be synthetic or hardware")
        if source_kind is None:
            source_kind = current_source_kind
        elif current_source_kind != source_kind:
            raise ValueError("telemetry rows contain multiple source_kind values")

        if row["event"] not in EVENTS:
            raise ValueError("telemetry event is invalid")
        segment_id = _nonnegative_integer(row["segment_id"], "segment_id")
        segment = segments.setdefault(
            segment_id,
            {column: 0 for column in COUNTER_COLUMNS},
        )
        for column in COUNTER_COLUMNS:
            counter = _optional_counter(row[column], column)
            if counter is not None:
                segment[column] = max(segment[column], counter)

    if row_count == 0:
        raise ValueError("telemetry input is empty")

    for segment_id, segment in segments.items():
        if segment["rx_data_packets"] > segment["rx_attempts"]:
            raise ValueError(
                f"segment {segment_id}: delivered packets exceed receive attempts"
            )

    totals = {
        column: sum(segment[column] for segment in segments.values())
        for column in COUNTER_COLUMNS
    }
    attempts = totals["rx_attempts"]
    delivered = totals["rx_data_packets"]

    return {
        "run_id": run_id,
        "source_kind": source_kind,
        "segment_count": len(segments),
        "rx_attempts": attempts,
        "delivered_packets": delivered,
        "sync_beacons": totals["sync_beacons"],
        "tx_successes": totals["tx_successes"],
        "packet_delivery_ratio": delivered / attempts if attempts else None,
        "ping_rtt_latency_ms": None,
    }
