# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Reserve and publish a related set of new text files without overwriting."""

import os
from pathlib import Path
import tempfile


class OutputReservation:
    """Own exclusive placeholder files until publication or rollback."""

    def __init__(self, paths):
        resolved = [Path(path).expanduser().resolve() for path in paths]
        if not resolved:
            raise ValueError("at least one output path is required")
        if len(set(resolved)) != len(resolved):
            raise ValueError("output paths must be distinct")
        for path in resolved:
            if not path.parent.is_dir():
                raise ValueError("output parent directories must already exist")

        self.paths = tuple(resolved)
        self._reserved = []
        self._temporary = []
        self._published = []
        self._closed = False
        try:
            for path in self.paths:
                with path.open("x", encoding="utf-8"):
                    pass
                self._reserved.append(path)
        except BaseException:
            self.rollback()
            raise

    def publish(self, outputs, *, append_newline=True):
        """Publish reserved UTF-8 text as a rollback group.

        Default behavior keeps legacy newline termination. Analytical source
        snapshots use append_newline=False to preserve their exact byte hashes.
        """
        if self._closed:
            raise RuntimeError("output reservation is already closed")
        normalized = {
            Path(path).expanduser().resolve(): content
            for path, content in outputs.items()
        }
        if set(normalized) != set(self.paths):
            raise ValueError("published paths must match reserved output paths")
        if any(not isinstance(content, str) for content in normalized.values()):
            raise ValueError("published output contents must be strings")

        try:
            for path in self.paths:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    newline="\n",
                    dir=path.parent,
                    delete=False,
                ) as stream:
                    temporary = Path(stream.name)
                    self._temporary.append(temporary)
                    content = normalized[path]
                    stream.write(content)
                    if append_newline and not content.endswith("\n"):
                        stream.write("\n")

            for temporary, path in zip(self._temporary, self.paths):
                os.replace(temporary, path)
                self._published.append(path)
            self._temporary.clear()
            self._reserved.clear()
            self._closed = True
        except BaseException:
            self.rollback()
            raise

    def rollback(self):
        """Remove only temporary and placeholder files owned by this object."""
        for path in self._temporary:
            path.unlink(missing_ok=True)
        self._temporary.clear()
        for path in (*self._published, *self._reserved):
            path.unlink(missing_ok=True)
        self._published.clear()
        self._reserved.clear()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        if not self._closed:
            self.rollback()
        return False


def reserve_outputs(paths):
    """Exclusively reserve output paths before input processing begins."""
    return OutputReservation(paths)


def publish_outputs(outputs):
    """Reserve, then publish a mapping of paths to newline-terminated text."""
    with reserve_outputs(outputs.keys()) as reservation:
        reservation.publish(outputs)
