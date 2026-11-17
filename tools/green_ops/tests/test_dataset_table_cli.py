# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

import contextlib
import io
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atomic_outputs
import green_ops_build_table as cli
from green_ops_build_dataset import _dataset_csv
from tools.green_ops.tests.test_dataset_table import artifact


class TableCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.arguments = []
        for number in (1, 2):
            a = artifact(f"run-00{number}")
            source = self.root / f"row{number}.csv"
            manifest = self.root / f"row{number}.json"
            source.write_text(_dataset_csv(a["row"]), encoding="utf-8")
            manifest.write_text(json.dumps(a["manifest"]), encoding="utf-8")
            self.arguments += ["--artifact", str(source), str(manifest)]
        self.output, self.manifest = self.root / "table.csv", self.root / "table.json"
        self.arguments += ["--measurement-status", "unmeasured", "--table-output", str(self.output), "--manifest-output", str(self.manifest)]

    def run_cli(self, arguments=None):
        return subprocess.run([sys.executable, str(Path(cli.__file__)), *(arguments or self.arguments)], capture_output=True, text=True)

    def test_subprocess_success_hash_nulls_and_determinism(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(self.manifest.read_text())
        self.assertEqual(manifest["table_sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        with self.output.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["target_total_energy_mj"], "")
        args = [str(self.root / "second.csv") if arg == str(self.output) else str(self.root / "second.json") if arg == str(self.manifest) else arg for arg in self.arguments]
        self.assertEqual(self.run_cli(args).returncode, 0)
        self.assertEqual(self.output.read_bytes(), (self.root / "second.csv").read_bytes())
        self.assertEqual(self.manifest.read_bytes(), (self.root / "second.json").read_bytes())

    def test_existing_destination_preserved(self):
        self.manifest.write_text("KEEP")
        self.assertEqual(self.run_cli().returncode, 1)
        self.assertEqual(self.manifest.read_text(), "KEEP")
        self.assertFalse(self.output.exists())

    def test_source_output_alias_and_invalid_utf8(self):
        original = (self.root / "row1.csv").read_bytes()
        args = [str(self.root / "row1.csv") if arg == str(self.output) else arg for arg in self.arguments]
        self.assertEqual(self.run_cli(args).returncode, 1)
        self.assertEqual((self.root / "row1.csv").read_bytes(), original)
        (self.root / "row1.json").write_bytes(b'\xff')
        self.assertEqual(self.run_cli().returncode, 1)
        self.assertFalse(self.output.exists()); self.assertFalse(self.manifest.exists())

    def test_second_publication_failure_rolls_back_both(self):
        real_replace = atomic_outputs.os.replace
        def fail_second(source, destination):
            if Path(destination) == self.manifest:
                raise OSError("simulated second publication failure")
            return real_replace(source, destination)
        with contextlib.redirect_stderr(io.StringIO()), mock.patch.object(atomic_outputs.os, "replace", side_effect=fail_second):
            self.assertEqual(cli.main(self.arguments), 1)
        self.assertFalse(self.output.exists()); self.assertFalse(self.manifest.exists())
        self.assertEqual(len(list(self.root.iterdir())), 4)

    def test_invalid_argument_returns_one(self):
        result = self.run_cli(["--bad-argument"])
        self.assertEqual(result.returncode, 1)
