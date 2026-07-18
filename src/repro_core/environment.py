"""Environment capture for reproducible benchmarks.

Every benchmark run in this repository must record the environment it ran
in (see ``docs/BENCHMARK_PROTOCOL.md`` and
``docs/REPRODUCIBILITY_CHECKLIST.md``). :func:`capture_environment`
gathers everything that can be collected automatically; anything that
cannot be detected on the current platform is recorded as ``None`` rather
than omitted or guessed, so a reader can always distinguish "not
applicable / not detectable" from "forgot to record".

Only the standard library is used, and every external probe (``git``,
``nvidia-smi``, ``rustc``, ...) is optional: a missing tool degrades to
``None``, never to an exception.
"""

from __future__ import annotations

import datetime as _dt
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

_PROBE_TIMEOUT_SECONDS = 10.0


def _run(args: list[str]) -> str | None:
    """Run a probe command, returning stripped stdout or None on any failure."""
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=_PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    return out if out else None


def _git_info() -> dict[str, Any]:
    commit = _run(["git", "rev-parse", "HEAD"])
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    # Untracked files are excluded (matching `git describe --dirty`
    # semantics): a benchmark's own freshly written output files must not
    # mark the run dirty. Modified/staged *tracked* files do.
    porcelain = _run(["git", "status", "--porcelain", "--untracked-files=no"])
    # `git status` prints nothing on a clean tree, which _run normalizes
    # to None — distinguish that from git being absent entirely.
    dirty = None if commit is None else porcelain is not None
    return {"commit": commit, "branch": branch, "dirty": dirty}


def _cpu_model() -> str | None:
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or None


def _memory_total_bytes() -> int | None:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        num_pages = os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        return None
    if page_size <= 0 or num_pages <= 0:
        return None
    return page_size * num_pages


def _gpu_info() -> dict[str, Any]:
    smi = _run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader",
        ]
    )
    devices: list[dict[str, str]] | None
    if smi is None:
        devices = None
    else:
        devices = []
        for line in smi.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                devices.append(
                    {"name": parts[0], "memory_total": parts[1], "driver_version": parts[2]}
                )
    cuda_version: str | None = None
    nvcc = _run(["nvcc", "--version"])
    if nvcc is not None:
        for token in nvcc.replace(",", " ").split():
            if token.startswith("V") and token[1:2].isdigit():
                cuda_version = token[1:]
                break
    return {"devices": devices, "cuda_version": cuda_version}


def _installed_packages() -> dict[str, str]:
    packages: dict[str, str] = {}
    for dist in importlib.metadata.distributions():
        packages[dist.name] = dist.version
    return dict(sorted(packages.items(), key=lambda kv: kv[0].lower()))


def capture_environment() -> dict[str, Any]:
    """Capture the current execution environment as a JSON-serializable dict.

    Undetectable values are ``None``, never omitted, so the schema is
    stable across platforms.
    """
    uname = platform.uname()
    return {
        "schema_version": SCHEMA_VERSION,
        "captured_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
        "git": _git_info(),
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "os": {
            "system": uname.system,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
        },
        "cpu": {
            "model": _cpu_model(),
            "logical_cores": os.cpu_count(),
        },
        "memory": {"total_bytes": _memory_total_bytes()},
        "gpu": _gpu_info(),
        "rust": {"rustc_version": _run(["rustc", "--version"])},
        "packages": _installed_packages(),
    }


def write_environment(path: str | Path) -> Path:
    """Capture the environment and write it as pretty-printed JSON.

    Parent directories are created if needed. Returns the written path.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(capture_environment(), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return target


def main() -> None:
    """CLI entry point: ``repro-env [output-path]`` (default: stdout)."""
    if len(sys.argv) > 1:
        written = write_environment(sys.argv[1])
        print(f"wrote {written}")
    else:
        print(json.dumps(capture_environment(), indent=2))


if __name__ == "__main__":
    main()
