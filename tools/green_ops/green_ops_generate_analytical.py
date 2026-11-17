# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Publish one deterministic analytical reference bundle in a fresh directory."""

from pathlib import Path
import sys

from analytical_reference import generate_analytical_artifact
from atomic_outputs import reserve_outputs
from green_ops_build_dataset import ArgumentParser


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--workload", type=Path, required=True)
    parser.add_argument("--assumptions", type=Path, required=True)
    parser.add_argument("--prediction-context", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output_dir.expanduser().resolve()
    created = False
    try:
        if output.exists():
            raise ValueError("output directory must be a new destination")
        files = generate_analytical_artifact(args.parameters.read_bytes(), args.workload.read_bytes(),
            args.assumptions.read_bytes(), prediction_context_bytes=args.prediction_context.read_bytes()
            if args.prediction_context is not None else None)
        output.mkdir()  # Refuse existing directories, files and resolved aliases.
        created = True
        paths = {output/name:content.decode("utf-8") for name,content in files.items()}
        with reserve_outputs(paths) as reservation:
            reservation.publish(paths, append_newline=False)  # Preserve exact source snapshot bytes.
    except (OSError, UnicodeError, ValueError) as error:
        if created:
            try:
                output.rmdir()  # Never remove unexpected files owned by another actor.
            except OSError:
                pass
        print(f"error: {error}", file=sys.stderr)
        return 1
    print("Generated one analytical_simulation bundle; no hardware measurement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
