# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analytical_reference as analytical
import atomic_outputs
import green_ops_generate_analytical as cli
from dataset_table import load_dataset_artifact, build_dataset_table
from feature_contract import PRE_RUN_FEATURES, POST_RUN_FEATURES, FEATURE_CONTRACT_VERSION
from tools.green_ops.tests.test_analytical_reference import model, workload, assumed_value, MODEL_PATH

ASSUMPTIONS = MODEL_PATH.parent / "analytical-assumptions-v1.md"


def json_bytes(value):
    return json.dumps(value, sort_keys=True).encode("utf-8")  # Intentionally no newline.


def bundle(*, data=None, run=None, context=None):
    return analytical.generate_analytical_artifact(json_bytes(model() if data is None else data),
        json_bytes(workload() if run is None else run), ASSUMPTIONS.read_bytes(),
        prediction_context_bytes=json_bytes(context) if context is not None else None)


def write_bundle(root, files):
    root.mkdir()
    for name, content in files.items():
        (root/name).write_bytes(content)
    return load_dataset_artifact(root/"dataset.csv", root/"manifest.json")


class AnalyticalArtifactTests(unittest.TestCase):
    def test_real_artifact_and_two_run_table_integration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = write_bundle(root/"a", bundle())
            b = write_bundle(root/"b", bundle(run=workload(run_id="analytical-002", evaluation_group_id="config-family-002", seed=7)))
            rows, manifest = build_dataset_table([b,a], schema_version=2,
                measurement_status="analytical_simulation", required_targets=("target_total_energy_mj",))
            self.assertEqual(len(rows), 2)
            self.assertEqual(manifest["group_ids"], ["config-family-001", "config-family-002"])
            self.assertEqual((rows,manifest), build_dataset_table([a,b], schema_version=2,
                measurement_status="analytical_simulation", required_targets=("target_total_energy_mj",)))
            for row in rows:
                self.assertEqual((row["source_kind"],row["execution_kind"],row["measurement_status"]),
                                 ("synthetic","simulation","analytical_simulation"))
                self.assertEqual(row["seed"], 42 if row["run_id"].endswith("001") else 7)
                self.assertIsNone(row["ping_rtt_latency_ms"])
            self.assertEqual(a["manifest"]["feature_contract_version"], FEATURE_CONTRACT_VERSION)
            self.assertEqual(a["manifest"]["available_fields"], [])
            self.assertNotIn("ppk2_summary", a["manifest"]["input_sha256"])

    def test_hashes_bind_parameters_assumptions_and_modeled_evidence(self):
        files = bundle()
        manifest = json.loads(files["manifest.json"])
        for name,path in manifest["input_paths"].items():
            self.assertEqual(manifest["input_sha256"][name], hashlib.sha256(files[path]).hexdigest())
        configuration = json.loads(files["configuration.json"])
        self.assertEqual(configuration["parameters_sha256"], hashlib.sha256(files["parameters.json"]).hexdigest())
        self.assertEqual(configuration["parameter_version"], model()["parameter_version"])
        self.assertEqual(configuration["sampler_version"], analytical.SAMPLER_VERSION)
        self.assertEqual(manifest["analytical_reference"]["configuration_sha256"], hashlib.sha256(files["configuration.json"]).hexdigest())
        delivery = json.loads(files["delivery-summary.json"])
        self.assertEqual(delivery["evidence_sha256"], hashlib.sha256(files["packet-evidence.json"]).hexdigest())
        self.assertEqual(files["parameters.json"], json_bytes(model()))

    def test_bytes_are_deterministic_and_parameter_or_assumption_edits_change_identity(self):
        first = bundle()
        self.assertEqual(first, bundle())
        changed = model(); assumed_value(changed["timing_us"]["prepare"], 600)
        self.assertNotEqual(first["configuration.json"], bundle(data=changed)["configuration.json"])
        other = analytical.generate_analytical_artifact(json_bytes(model()), json_bytes(workload()), ASSUMPTIONS.read_bytes()+b"\nAmended assumption.\n")
        self.assertNotEqual(first["manifest.json"], other["manifest.json"])

    def test_declared_prediction_context_and_zero_offer_labels(self):
        data = model(); assumed_value(data["loss_probability"], 0.0)
        context = dict(available_fields=list(POST_RUN_FEATURES), planned_window_duration_ms=1000,
                       completed_as_planned=True)
        files = bundle(data=data, context=context)
        manifest = json.loads(files["manifest.json"])
        self.assertEqual(manifest["selected_features"]["pre_run"], list(PRE_RUN_FEATURES))
        self.assertEqual(manifest["selected_features"]["post_run"], list(POST_RUN_FEATURES))
        with tempfile.TemporaryDirectory() as directory:
            a = write_bundle(Path(directory)/"zero", bundle(run=workload(offered_packets=0)))
            self.assertIsNone(a["row"]["target_energy_per_delivered_packet_uj"])
            self.assertIsNone(a["row"]["packet_delivery_ratio"])
            self.assertAlmostEqual(a["row"]["target_total_energy_mj"], 136.9)
        with self.assertRaises(ValueError):
            bundle(run=workload(offered_packets=0), context=context)  # null decode ratio is no capability

    def test_explicit_analytical_rtt_roundtrip(self):
        data = model(); assumed_value(data["loss_probability"], 0.0)
        data["rtt_extra_ms"] = dict(value=2.0, min=0, max=5, unit="ms", basis="assumption", source_id=None, range_note="Uncalibrated test assumption")
        with tempfile.TemporaryDirectory() as directory:
            a = write_bundle(Path(directory)/"rtt", bundle(data=data))
            rows, _ = build_dataset_table([a], schema_version=2, measurement_status="analytical_simulation", required_targets=("ping_rtt_latency_ms",))
            self.assertAlmostEqual(rows[0]["ping_rtt_latency_ms"], 5.256)

    def test_strict_json_and_assumption_loading(self):
        for content in (b'{"model_id":"a","model_id":"b"}', b'{"value":NaN}', b'\xff', b'[]'):
            with self.subTest(content=content), self.assertRaises((ValueError, UnicodeError)):
                analytical.generate_analytical_artifact(content, json_bytes(workload()), ASSUMPTIONS.read_bytes())
        for assumptions in (b'', b'\xff'):
            with self.subTest(assumptions=assumptions), self.assertRaises((ValueError, UnicodeError)):
                analytical.generate_analytical_artifact(json_bytes(model()), json_bytes(workload()), assumptions)


class AnalyticalSensitivityTests(unittest.TestCase):
    def test_each_parameter_range_is_checked_with_monotone_current_energy(self):
        result = analytical.sensitivity_analysis(model(), workload())
        self.assertEqual(len(result["cases"]), 18)  # 3 currents + 5 durations + loss, two bounds each
        self.assertEqual(result, analytical.sensitivity_analysis(model(), workload()))
        baseline = result["baseline_energy_mj"]
        for case in result["cases"]:
            self.assertEqual(case["basis"], "assumption")
            if case["parameter"].startswith("currents_ma"):
                self.assertEqual(case["status"], "valid")
                if case["bound"] == "min": self.assertLessEqual(case["total_energy_mj"], baseline)
                else: self.assertGreaterEqual(case["total_energy_mj"], baseline)
            if case["status"] == "valid":
                self.assertEqual(sum(case["state_duration_us"].values()), 1000000)

    def test_invalid_sensitivity_schedules_are_retained_with_reasons(self):
        data = model(); data["timing_us"]["tx_base"]["max"] = 1000000
        result = analytical.sensitivity_analysis(data, workload())
        case = next(c for c in result["cases"] if c["parameter"]=="timing_us.tx_base" and c["bound"]=="max")
        self.assertEqual(case["status"], "invalid")
        self.assertIn("slot", case["reason"])


class AnalyticalCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.params, self.run, self.assumptions = [self.root/name for name in ("params.json","run.json","assumptions.md")]
        self.params.write_bytes(json_bytes(model())); self.run.write_bytes(json_bytes(workload()))
        self.assumptions.write_bytes(b"Explicit assumption snapshot without newline")
        self.output = self.root/"result"
        self.arguments = ["--parameters",str(self.params),"--workload",str(self.run),"--assumptions",str(self.assumptions),"--output-dir",str(self.output)]

    def run_cli(self, arguments=None):
        return subprocess.run([sys.executable, str(Path(cli.__file__)), *(self.arguments if arguments is None else arguments)], capture_output=True, text=True)

    def test_cli_preserves_exact_snapshots_and_deterministic_output_bytes(self):
        result = self.run_cli(); self.assertEqual(result.returncode, 0, result.stderr)
        a = load_dataset_artifact(self.output/"dataset.csv",self.output/"manifest.json")
        self.assertEqual((self.output/"parameters.json").read_bytes(), self.params.read_bytes())
        self.assertEqual((self.output/"assumptions.md").read_bytes(), self.assumptions.read_bytes())
        other = self.root/"second"
        args = [str(other) if p==str(self.output) else p for p in self.arguments]
        self.assertEqual(self.run_cli(args).returncode, 0)
        self.assertEqual({p.name:p.read_bytes() for p in self.output.iterdir()}, {p.name:p.read_bytes() for p in other.iterdir()})
        result = subprocess.run([sys.executable,str(Path(cli.__file__).with_name("green_ops_build_table.py")),
            "--artifact",str(self.output/"dataset.csv"),str(self.output/"manifest.json"),
            "--measurement-status","analytical_simulation","--require-target","target_total_energy_mj",
            "--table-output",str(self.root/"table.csv"),"--manifest-output",str(self.root/"table.json")], capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_existing_or_alias_destination_is_preserved(self):
        self.output.mkdir(); (self.output/"keep").write_text("KEEP")
        self.assertEqual(self.run_cli().returncode,1)
        self.assertEqual((self.output/"keep").read_text(),"KEEP")
        args = [str(self.params) if p==str(self.output) else p for p in self.arguments]
        original = self.params.read_bytes()
        self.assertEqual(self.run_cli(args).returncode,1)
        self.assertEqual(self.params.read_bytes(),original)

    def test_invalid_contract_publishes_nothing(self):
        self.params.write_bytes(b'{"NaN": NaN}')
        self.assertEqual(self.run_cli().returncode,1)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.run_cli(["--bad-argument"]).returncode,1)

    def test_publication_failure_rolls_back_directory_and_sources(self):
        original = self.params.read_bytes()
        real_replace = atomic_outputs.os.replace
        def fail(source,destination):
            if Path(destination).name=="manifest.json": raise OSError("simulated publish failure")
            return real_replace(source,destination)
        with contextlib.redirect_stderr(io.StringIO()), mock.patch.object(atomic_outputs.os,"replace",side_effect=fail):
            self.assertEqual(cli.main(self.arguments),1)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.params.read_bytes(),original)
