# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""SOFTWARE VERIFICATION ONLY: require default ABSTAIN3, never approve candidate energy."""
from pathlib import Path
import json
import sys
import tempfile
from analytical_reference import _sha256
from green_ops_gatekeeper import REPO
from green_ops_gate_report import main as gate_report
from green_ops_report import generate


def verify(directory):
    root=Path(directory);policy=REPO/'tools/green_ops/policies/green_ops_budget.json';source=REPO/'docs/results/week9/source'
    hashes=[]
    for name in ('first','second'):
        decision=root/f'{name}.json';markdown=root/f'{name}.md'
        code=gate_report(['--policy',str(policy),'--candidate',str(source),'--output',str(decision),'--markdown-output',str(markdown)])
        if code!=3:raise ValueError(f'expected default ABSTAIN3, got{code}; software verification failed')
        content=decision.read_bytes();r=json.loads(content)
        if (r['status']!='ABSTAIN' or not r['blocks_ci'] or r['research_override_requested'] or r['research_override_used']
            or r['reason_codes']!=['observed_family_coverage_inadequate']):raise ValueError('default evidence/override smoke mismatch')
        expected=generate(content,_sha256(content),policy.read_bytes()).encode('utf-8')
        if markdown.read_bytes()!=expected:raise ValueError('Markdown reproduction mismatch')
        hashes.append((_sha256(content),_sha256(expected)))
    if hashes[0]!=hashes[1]:raise ValueError('gate/report bytes are nondeterministic')
    return hashes[0]


def main():
    try:
        with tempfile.TemporaryDirectory(prefix='green-ops-software-smoke-') as directory:hashes=verify(directory)
        print(f'SOFTWARE VERIFICATION PASSED: expected ABSTAIN3 verified, NOT candidate approval. JSON/Markdown SHA256: {hashes}')
        return 0
    except (OSError,UnicodeError,ValueError,KeyError,TypeError) as error:
        print(f'ERROR: software smoke failed: {error}',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
