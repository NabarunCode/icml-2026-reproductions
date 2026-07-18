"""Shared research-engineering infrastructure for all paper reproductions.

Nothing paper-specific belongs in this package. It currently provides:

- :mod:`repro_core.environment` — full environment capture (git, Python,
  OS, CPU, RAM, GPU, CUDA, Rust, installed packages) written alongside
  every benchmark result, per ``docs/BENCHMARK_PROTOCOL.md``.
- :mod:`repro_core.timing` — the repository-standard benchmark runner
  (warm-up, repeated samples, mean/stdev/median reporting).
"""

from repro_core.environment import capture_environment, write_environment
from repro_core.timing import BenchmarkResult, run_benchmark

__all__ = [
    "BenchmarkResult",
    "capture_environment",
    "run_benchmark",
    "write_environment",
]
