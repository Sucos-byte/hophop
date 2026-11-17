# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analytical_reference as analytical

MODEL_PATH = Path(__file__).resolve().parents[1] / "models/nrf9151-dect-reference-v1.json"


def model():
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def workload(**changes):
    data = dict(workload_version=1, run_id="analytical-001", evaluation_group_id="config-family-001",
                seed=42, repetition=1, window_duration_ms=1000, interval_ms=100,
                payload_size_bytes=64, tx_power_dbm=19, offered_packets=2, max_attempts=3)
    return {**data, **changes}


def assumed_value(parameter, value):
    parameter.update(value=value, min=min(value, parameter["min"]), max=max(value, parameter["max"]),
                     basis="assumption", source_id=None)


class AnalyticalAccountingTests(unittest.TestCase):
    def test_independent_voltage_current_time_unit_oracle(self):
        result = analytical.integrate_states({"active": 100000, "idle": 900000},
                                             {"active": 10.0, "idle": 1.0}, voltage_v=3.0)
        # Independent charge: (10 mA * .1 s + 1 mA * .9 s)=1.9 mC;
        # E=3 V * 1.9 mC=5.7 mJ; over 1 second P=5.7 mW.
        self.assertAlmostEqual(result["total_energy_mj"], 5.7)
        self.assertAlmostEqual(result["mean_power_mw"], 5.7)
        self.assertAlmostEqual(result["state_energy_mj"]["active"], 3.0)

    def test_zero_traffic_is_idle_not_zero_energy(self):
        result = analytical.simulate_reference(model(), workload(offered_packets=0))
        self.assertEqual(result["state_duration_us"], dict(idle=1000000, tx=0, rx=0))
        self.assertAlmostEqual(result["total_energy_mj"], 136.9)  # 37mA * 3.7V * 1s
        self.assertEqual(result["delivered_packets"], 0)
        self.assertIsNone(result["ping_rtt_latency_ms"])

    def test_no_loss_hand_computed_schedule_and_energy(self):
        data = model(); assumed_value(data["loss_probability"], 0.0)
        result = analytical.simulate_reference(data, workload(offered_packets=1, max_attempts=1))
        # One packet: 500us prepare, 1000+64*4=1256us TX, 1500us RX,
        # then 996744us remaining idle; total idle includes preparation.
        self.assertEqual(result["state_duration_us"], dict(idle=997244, tx=1256, rx=1500))
        expected = 3.7 * (37 * .997244 + 235 * .001256 + 47 * .0015)
        self.assertAlmostEqual(result["total_energy_mj"], expected)
        self.assertEqual(result["rx_operations"], 1)
        self.assertEqual(result["rx_decoded_packets"], 1)
        self.assertEqual(result["tx_successes"], 1)
        self.assertEqual(result["delivered_packets"], 1)
        self.assertIsNone(result["ping_rtt_latency_ms"])

    def test_total_loss_retries_conserve_state_time_and_offer_count(self):
        data = model(); assumed_value(data["loss_probability"], 1.0)
        result = analytical.simulate_reference(data, workload(offered_packets=2, max_attempts=3))
        self.assertEqual(result["rx_operations"], 6)
        self.assertEqual(result["tx_successes"], 6)
        self.assertEqual(result["delivered_packets"], 0)
        self.assertEqual(len(result["packets"]), 2)
        self.assertEqual(sum(result["state_duration_us"].values()), 1000000)
        cursor = 0
        for segment in result["segments"]:
            self.assertEqual(segment["start_us"], cursor)
            cursor += segment["duration_us"]
        self.assertEqual(cursor, 1000000)

    def test_seeded_generator_is_deterministic_and_nonmutating(self):
        data, run = model(), workload(offered_packets=10)
        originals = copy.deepcopy((data, run))
        first = analytical.simulate_reference(data, run)
        self.assertEqual(first, analytical.simulate_reference(data, run))
        self.assertEqual((data, run), originals)
        # More than one seed changes stochastic packet outcomes in this fixture.
        outcomes = {tuple(p["attempts"] for p in analytical.simulate_reference(data, workload(seed=s, offered_packets=10))["packets"]) for s in range(10)}
        self.assertGreater(len(outcomes), 1)
        self.assertEqual(len({p["packet_id"] for p in first["packets"]}), 10)

    def test_modeled_rtt_is_explicit_and_includes_retry_elapsed_time(self):
        data = model(); assumed_value(data["loss_probability"], 0.0)
        data["rtt_extra_ms"] = dict(value=2.0, min=0.0, max=5.0, unit="ms", basis="assumption", source_id=None, range_note="Test assumption")
        result = analytical.simulate_reference(data, workload(offered_packets=1))
        self.assertAlmostEqual(result["ping_rtt_latency_ms"], 5.256)  # 500+1256+1500us plus 2ms
        self.assertEqual(result["packets"][0]["accepted_us"], 3256)
        assumed_value(data["loss_probability"], 1.0)
        self.assertIsNone(analytical.simulate_reference(data, workload())["ping_rtt_latency_ms"])


class AnalyticalValidationTests(unittest.TestCase):
    def test_invalid_model_scalars_keys_units_and_ranges(self):
        for field, value in (("value", True), ("value", float("inf")), ("min", -1), ("unit", "A"), ("max", 1)):
            data = model(); data["currents_ma"]["tx"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                analytical.validate_model(data)
        data = model(); data["extra"] = 1
        with self.assertRaises(ValueError):
            analytical.validate_model(data)
        data = model(); data["timing_us"]["rx"]["value"] = 1.5
        with self.assertRaises(ValueError):
            analytical.validate_model(data)

    def test_official_values_and_conditions_cannot_be_silently_changed(self):
        for change in ("current", "conditions", "url"):
            data = model()
            if change == "current": data["currents_ma"]["tx"]["value"] = 240
            elif change == "conditions": data["conditions"]["supply_v"] = 3.3
            else: data["sources"]["dect-tx"]["url"] = "https://example.com/unverified"
            with self.subTest(change=change), self.assertRaises(ValueError):
                analytical.validate_model(data)

    def test_invalid_workload_and_oversubscribed_slot(self):
        for field, value in (("seed", True), ("seed", -1), ("window_duration_ms", 0),
                ("payload_size_bytes", 0), ("offered_packets", 11), ("max_attempts", 0),
                ("tx_power_dbm", 0), ("interval_ms", 1), ("run_id", "bad/id")):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                analytical.simulate_reference(model(), workload(**{field:value}))

    def test_integrator_rejects_bad_units_shapes_and_derived_overflow(self):
        for durations, currents, voltage in (({"x": True},{"x":1},3), ({"x":0},{"x":1},3),
                ({"x":1},{"y":1},3), ({"x":1},{"x":float("nan")},3),
                ({"x":1000000},{"x":1e308},3.7)):
            with self.subTest(durations=durations), self.assertRaises(ValueError):
                analytical.integrate_states(durations, currents, voltage_v=voltage)


class AnalyticalWindowBoundaryTests(unittest.TestCase):
    def test_acceptance_at_end_is_late_and_excluded_from_delivery(self):
        data = model()
        assumed_value(data["loss_probability"], 0.0)
        for name, value in dict(prepare=0, tx_base=500, tx_per_byte=0, rx=500).items():
            assumed_value(data["timing_us"][name], value)
            if name == "rx": data["timing_us"][name]["min"] = 1
        result = analytical.simulate_reference(data, workload(window_duration_ms=1, interval_ms=1,
                                                             offered_packets=1, max_attempts=1))
        self.assertEqual(result["state_duration_us"], dict(idle=0, tx=500, rx=500))
        self.assertEqual(result["delivered_packets"], 0)
        self.assertEqual(result["rx_decoded_packets"], 0)
        self.assertEqual(result["packets"][0]["late_acceptance_us"], 1000)
        self.assertIsNone(result["packets"][0]["accepted_us"])


class AnalyticalNumericBoundaryTests(unittest.TestCase):
    def test_integer_intermediate_energy_overflow_is_a_contract_error(self):
        with self.assertRaises(ValueError):
            analytical.integrate_states({"active":1000000}, {"active":10**308}, voltage_v=10**308)

    def test_large_finite_assumed_rtt_uses_overflow_safe_mean(self):
        data = model(); assumed_value(data["loss_probability"],0.0)
        data["rtt_extra_ms"] = dict(value=1e308,min=0,max=1e308,unit="ms",basis="assumption",source_id=None,range_note="Numeric boundary test only")
        result = analytical.simulate_reference(data,workload(offered_packets=2))
        self.assertEqual(result["ping_rtt_latency_ms"],1e308)

    def test_zero_duration_state_has_zero_energy_without_intermediate_overflow(self):
        result = analytical.integrate_states({"idle":1000000,"unused":0},
            {"idle":1,"unused":1e308}, voltage_v=3.7)
        self.assertEqual(result["state_energy_mj"]["unused"],0)
        self.assertAlmostEqual(result["total_energy_mj"],3.7)
