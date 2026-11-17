# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Atomic local decision+Markdown wrapper. Preserve gate exits0/1/2/3; rendering errors block1."""
from pathlib import Path
import sys
import tempfile
from analytical_reference import _sha256
from atomic_outputs import reserve_outputs
import green_ops_gatekeeper as gate
from green_ops_report import generate,validate_decision


def main(argv=None):
    parser=gate.make_parser();parser.description=__doc__
    parser.add_argument('--markdown-output',type=Path,required=True)
    try:
        args=parser.parse_args(argv);decision=args.output.expanduser().resolve();markdown=args.markdown_output.expanduser().resolve()
        inputs=[v.expanduser().resolve() for k,v in vars(args).items() if isinstance(v,Path) and k not in ('output','markdown_output')]
        if any(out==p or p in out.parents for out in (decision,markdown) for p in inputs):raise ValueError('output aliases or lies inside an input source')
        with reserve_outputs([decision,markdown]) as reservation:
            with tempfile.TemporaryDirectory(prefix='green-ops-gate-report-') as directory:
                temporary=Path(directory)/'decision.json';gate_args=[]
                for name,value in vars(args).items():
                    if name in ('output','markdown_output') or value is None:continue
                    flag='--'+name.replace('_','-')
                    if type(value) is bool:
                        if value:gate_args.append(flag)
                    else:gate_args += [flag,str(value)]
                code=gate.main(gate_args+['--output',str(temporary)])
                content=temporary.read_bytes();digest=_sha256(content);policy=args.policy.read_bytes()
                result=validate_decision(content,digest,policy)
                if result['exit_code']!=code:raise ValueError('gate returned status inconsistent with decision')
                text=generate(content,digest,policy)
                reservation.publish({decision:content.decode('utf-8'),markdown:text},append_newline=False)
        print(f'Local report generated; gate exit {code} preserved. No GitHub comment posted.')
        return code
    except (OSError,UnicodeError,ValueError,TypeError,KeyError,OverflowError) as error:
        print(f'ERROR: gate/report processing failed: {error}',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
