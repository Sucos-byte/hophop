# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Local Week11 development replay only. No Week12 simulation or benchmark scoring."""
from pathlib import Path
import json
import sys
sys.path.insert(0,'tools/green_ops')
from analytical_reference import _json_bytes,_sha256
from fault_injection import build_artifact,make_intent,artifact_from_bytes
from fault_workflow import write_development,evaluate_artifact,report_from_bytes,ROOT,ASSUMPTIONS


def run(destination):
    root=Path(destination);summary=write_development(root)
    expected=Path('docs/results/week11/development/summary.json')
    if expected.exists() and expected.read_bytes()!=_json_bytes(summary):raise ValueError('development outputs differ from frozen archive')
    for path in sorted((root/'artifacts').glob('*.json')):
        data=path.read_bytes();a=artifact_from_bytes(data);rdata=(root/'reports'/path.name).read_bytes();report_from_bytes(rdata,data)
        r=json.loads(rdata)
        assert r['gatekeeper']['exit_code']==3 and r['execution_blocked'] and not r['positive_fault_detection']
        assert not r['predictor']['inputs_changed'] and not r['predictor']['predictions_changed']
    receipt=dict(reproduction_version=1,provenance='analytical_simulation',case_count=summary['case_count'],
        benchmark_scored=False,default_gate_exit=3,positive_detections=0,
        files={str(p.relative_to(root)):_sha256(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()},
        source_sha256={name:_sha256((ROOT/'tools/green_ops'/name).read_bytes()) for name in ('fault_injection.py','fault_workflow.py','fault_benchmark.py')})
    (root/'reproduction.json').write_bytes(_json_bytes(receipt))
    print('Verified40 development artifacts/reports; default ABSTAIN blocks, zero positive detections. Week12 UNSCORED.')


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python3 docs/results/week11/reproduce.py NEW_OUTPUT_DIRECTORY')
    run(sys.argv[1])
