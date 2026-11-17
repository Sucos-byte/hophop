# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Run unchanged frozen benchmark twice, independently, then audit/compare."""
import argparse
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output_root',type=Path,help='new directory; approximately80MB for two full runs')
args=parser.parse_args();args.output_root.mkdir()
for label in ('a','b'):
    subprocess.run([sys.executable,str(root/'tools/green_ops/benchmark_evaluation.py'),
        '--output',str(args.output_root/label),'--consumption',str(args.output_root/f'{label}-consumed.json')],check=True,cwd=root)
subprocess.run([sys.executable,str(root/'tools/green_ops/benchmark_audit.py'),
    str(args.output_root/'a'),str(args.output_root/'b')],check=True,cwd=root)
# Exit0 verifies deterministic software, not candidate energy approval.
