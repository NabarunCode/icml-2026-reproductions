"""Tests for repro_core.timing (the standard benchmark runner)."""

from __future__ import annotations

import gc

import pytest

from repro_core.timing import run_benchmark


def test_basic_run_produces_expected_sample_count() -> None:
    result = run_benchmark(lambda: sum(range(100)), name="sum100", warmup=2, repeats=5)
    assert result.name == "sum100"
    assert len(result.samples_ns) == 5
    assert all(s > 0 for s in result.samples_ns)
    assert result.min_ns <= result.median_ns <= result.max_ns
    assert result.min_ns <= result.mean_ns <= result.max_ns


def test_warmup_calls_are_made_but_not_timed() -> None:
    calls = {"n": 0}

    def fn() -> None:
        calls["n"] += 1

    result = run_benchmark(fn, name="counter", warmup=3, repeats=4, inner_iterations=2)
    assert calls["n"] == 3 + 4 * 2
    assert len(result.samples_ns) == 4


def test_single_repeat_has_zero_stdev() -> None:
    result = run_benchmark(lambda: None, name="noop", warmup=0, repeats=1)
    assert result.stdev_ns == 0.0


def test_gc_state_restored_after_run() -> None:
    assert gc.isenabled()
    run_benchmark(lambda: None, name="noop", warmup=0, repeats=2)
    assert gc.isenabled()


def test_gc_state_restored_after_exception() -> None:
    def boom() -> None:
        raise RuntimeError("intentional")

    assert gc.isenabled()
    with pytest.raises(RuntimeError):
        run_benchmark(boom, name="boom", warmup=0, repeats=1)
    assert gc.isenabled()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"warmup": -1}, "warmup"),
        ({"repeats": 0}, "repeats"),
        ({"inner_iterations": 0}, "inner_iterations"),
    ],
)
def test_invalid_parameters_rejected(kwargs: dict[str, int], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        run_benchmark(lambda: None, name="bad", **kwargs)


def test_to_dict_is_complete_and_serializable() -> None:
    result = run_benchmark(lambda: None, name="noop", warmup=1, repeats=3)
    d = result.to_dict()
    assert d["name"] == "noop"
    assert d["repeats"] == 3
    assert len(d["samples_ns"]) == 3
    assert d["mean_ns"] == pytest.approx(sum(d["samples_ns"]) / 3)
