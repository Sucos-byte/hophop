# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Build a deterministic homogeneous table from validated v2 artifacts."""

import csv
import hashlib
import io
import json
from pathlib import Path
import sys

from atomic_outputs import reserve_outputs
from dataset_builder import DATASET_FIELDS_V2
from dataset_table import build_dataset_table, load_dataset_artifact
from green_ops_build_dataset import ArgumentParser, _resolved


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", nargs=2, action="append", required=True,
                        metavar=("DATASET_CSV", "MANIFEST_JSON"))
    parser.add_argument("--dataset-version", type=int, choices=(2,), default=2)
    parser.add_argument("--measurement-status", required=True,
                        choices=("unmeasured", "measured", "analytical_simulation"))
    parser.add_argument("--table-output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--require-target", action="append", default=[])
    parser.add_argument("--missing-target-policy", choices=("error", "exclude"), default="error")
    args = parser.parse_args(argv)
    try:
        pairs = [tuple(_resolved(Path(p)) for p in pair) for pair in args.artifact]
        sources = [p for pair in pairs for p in pair]
        if len(set(sources)) != len(sources):
            raise ValueError("duplicate source artifact reference")
        outputs = [_resolved(args.table_output), _resolved(args.manifest_output)]
        if len(set(outputs)) != 2 or set(outputs) & set(sources):
            raise ValueError("source and output paths must all differ")
        # Resolve symlinks above and detect hard-link aliases as well.
        for output in outputs:
            if output.exists() and any(output.samefile(source) for source in sources):
                raise ValueError("source/output alias")
        for source in sources:
            if not source.is_file():
                raise ValueError(f"input path is not a file: {source}")
        with reserve_outputs(outputs) as reservation:
            artifacts = [load_dataset_artifact(*pair) for pair in pairs]
            rows, manifest = build_dataset_table(
                artifacts, schema_version=args.dataset_version,
                measurement_status=args.measurement_status,
                required_targets=tuple(args.require_target),
                missing_target_policy=args.missing_target_policy,
            )
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=DATASET_FIELDS_V2, lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
            content = stream.getvalue()
            manifest["table_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
            reservation.publish({outputs[0]: content,
                                 outputs[1]: json.dumps(manifest, indent=2, sort_keys=True) + "\n"})
    except (OSError, UnicodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Accepted {manifest['included_count']} rows; excluded {manifest['excluded_count']} rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
