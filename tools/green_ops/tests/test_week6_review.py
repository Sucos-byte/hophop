# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analytical_reference as analytical
from tools.green_ops.tests.test_analytical_reference import model, workload, assumed_value


class AccountingReviewTests(unittest.TestCase):
    def test_finite_energy_does_not_overflow_before_time_scaling(self):
        result = analytical.integrate_states({"active":1,"idle":999999}, {"active":1e308,"idle":0}, voltage_v=3.7)
        self.assertTrue(math.isfinite(result["total_energy_mj"]))
        self.assertAlmostEqual(result["total_energy_mj"]/1e302,3.7)

    def test_balanced_small_factors_do_not_underflow_before_integration(self):
        result = analytical.integrate_states({"active":10**18}, {"active":1e-4}, voltage_v=1e-320)
        self.assertGreater(result["total_energy_mj"],0)
        self.assertAlmostEqual(result["total_energy_mj"]/(1e-320*(1e-4*1e12)),1.0)

    def test_retry_energy_counts_exclusive_states_once(self):
        data = model(); assumed_value(data["loss_probability"],1.0)
        result = analytical.simulate_reference(data,workload(offered_packets=1,max_attempts=3))
        # Three complete attempts, 1256us TX and 1500us RX each. Preparation
        # and two backoffs replace other idle time, rather than add energy twice.
        expected = 3.7*(235*.003768 + 47*.0045 + 37*.991732)
        self.assertEqual(result["state_duration_us"],dict(idle=991732,tx=3768,rx=4500))
        self.assertAlmostEqual(result["total_energy_mj"],expected)
        self.assertEqual(result["tx_successes"],3)
        self.assertEqual(result["delivered_packets"],0)

    def test_internal_slot_boundary_is_not_the_observation_window_end(self):
        data = model(); assumed_value(data["loss_probability"],0.0)
        for name,value in dict(prepare=0,tx_base=500,tx_per_byte=0,rx=500).items():
            assumed_value(data["timing_us"][name],value)
        data["timing_us"]["rx"]["min"]=1
        result = analytical.simulate_reference(data,workload(window_duration_ms=2,interval_ms=1,
                                                            offered_packets=2,max_attempts=1))
        self.assertEqual(result["delivered_packets"],1)
        self.assertEqual(result["packets"][0]["accepted_us"],1000)
        self.assertEqual(result["packets"][1]["late_acceptance_us"],2000)
        self.assertEqual(sum(result["state_duration_us"].values()),2000)

    def test_energy_does_not_depend_on_callers_decimal_context(self):
        from decimal import localcontext,Inexact
        with localcontext() as context:
            context.Emax=2
            context.traps[Inexact]=True
            result=analytical.integrate_states({"active":100000,"idle":900000},
                {"active":10,"idle":1},voltage_v=3)
            self.assertAlmostEqual(result["total_energy_mj"],5.7)
            self.assertEqual(context.Emax,2)
            self.assertTrue(context.traps[Inexact])
