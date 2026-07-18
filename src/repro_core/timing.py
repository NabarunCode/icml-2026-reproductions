"""The repository-standard benchmark runner.

Implements the methodology fixed in ``docs/BENCHMARK_PROTOCOL.md``:
explicit warm-up runs that are discarded, multiple timed repetitions,
garbage collection disabled around each timed sample, and results
reported as a distribution (mean, standard deviation, median, min, max)
— never as a single number.

Timing uses :func:`time.perf_counter_ns`, the highest-resolution
monotonic clock the standard library offers.
"""

from __future__ import annotations

import gc
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BenchmarkResult:
    """A completed benchmark: raw samples plus derived statistics.

    ``samples_ns`` holds one entry per timed repetition — the raw data is
    always preserved so statistics can be recomputed or re-analyzed later.
    When ``inner_iterations > 1``, each sample is already divided by the
    iteration count, i.e. samples are per-single-call times.
    """

    name: str
    warmup: int
    repeats: int
    inner_iterations: int
    samples_ns: tuple[float, ...] = field(repr=False)

    @property
    def mean_ns(self) -> float:
        return statistics.fmean(self.samples_ns)

    @property
    def stdev_ns(self) -> float:
        if len(self.samples_ns) < 2:
            return 0.0
        return statistics.stdev(self.samples_ns)

    @property
    def median_ns(self) -> float:
        return statistics.median(self.samples_ns)

    @property
    def min_ns(self) -> float:
        return min(self.samples_ns)

    @property
    def max_ns(self) -> float:
        return max(self.samples_ns)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable form, in the shape BENCHMARK_PROTOCOL.md specifies."""
        return {
            "name": self.name,
            "warmup": self.warmup,
            "repeats": self.repeats,
            "inner_iterations": self.inner_iterations,
            "mean_ns": self.mean_ns,
            "stdev_ns": self.stdev_ns,
            "median_ns": self.median_ns,
            "min_ns": self.min_ns,
            "max_ns": self.max_ns,
            "samples_ns": list(self.samples_ns),
        }


def run_benchmark(
    fn: Callable[[], object],
    *,
    name: str,
    warmup: int = 3,
    repeats: int = 10,
    inner_iterations: int = 1,
) -> BenchmarkResult:
    """Time ``fn`` per the repository benchmark protocol.

    ``warmup`` untimed calls are made first (caches, JIT-like effects,
    lazy initialization), then ``repeats`` timed samples are taken. When
    a single call is too fast to time reliably, set ``inner_iterations``
    so each sample times a loop of that many calls and reports the
    per-call average.

    Garbage collection is disabled around each timed sample (and restored
    afterward, even on exception) so collection pauses land between
    samples, not inside them.
    """
    if warmup < 0:
        raise ValueError(f"warmup must be >= 0, got {warmup}")
    if repeats < 1:
        raise ValueError(f"repeats must be >= 1, got {repeats}")
    if inner_iterations < 1:
        raise ValueError(f"inner_iterations must be >= 1, got {inner_iterations}")

    for _ in range(warmup):
        fn()

    samples: list[float] = []
    gc_was_enabled = gc.isenabled()
    try:
        for _ in range(repeats):
            gc.collect()
            gc.disable()
            start = time.perf_counter_ns()
            for _ in range(inner_iterations):
                fn()
            elapsed = time.perf_counter_ns() - start
            if gc_was_enabled:
                gc.enable()
            samples.append(elapsed / inner_iterations)
    finally:
        if gc_was_enabled:
            gc.enable()

    return BenchmarkResult(
        name=name,
        warmup=warmup,
        repeats=repeats,
        inner_iterations=inner_iterations,
        samples_ns=tuple(samples),
    )
