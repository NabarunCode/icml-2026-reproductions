"""Claim 2 microbenchmark: what the missing Centroid Decomposition costs.

Our reproduction implements the paper's per-level search mechanism (the
O(1) DFS-interval test + O(log branching) sibling binary search) but
NOT Section 5.3's Centroid Decomposition, which bounds the *number of
levels* visited to O(log t). This experiment measures exactly what that
gap costs, instead of assuming it.

Construction: a maximally deep, narrow Successor Forest. Vocabulary
``{a, b, ab, aab, ..., a^d b}`` with rules ``(a, b), (a, ab), ...``:
each token ``a^k b`` has ``suc = a^(k-1) b``, so the forest is a single
chain of depth d. Feeding ``a^d b`` makes the search walk that entire
chain — but only on the final ``b`` byte; the preceding ``a`` bytes are
shallow. (The stronger Appendix J construction exists to trap
rust-gems-style per-backtrack O(t^2) validation, which our search does
not perform.)

That density fact dictates *two* metrics, and both are reported:

1. ``chain_amortized`` — mean per-byte cost over the whole input. For
   this family the deep walk happens once per d+1 bytes, so an O(d)
   walk contributes O(1) amortized: prediction is a roughly FLAT curve.
   Flatness here is NOT evidence the gap is closed — it is evidence the
   gap does not hurt *throughput* on chain-completion-sparse inputs.
2. ``feed_max_latency`` — the worst single ``feed(byte)`` latency in a
   run. This is where O(depth) levels must show: prediction is roughly
   LINEAR growth in d, where the full paper algorithm (centroid-
   balanced) predicts polylogarithmic growth. For a streaming tokenizer
   this is tail latency, which is precisely what Section 5.3 buys.

Either metric coming out contrary to prediction is recorded, not
adjusted away.

Run from the repository root:

    uv run python papers/incremental-bpe-tokenization/benchmarks/claim2_depth_scaling.py \
        papers/incremental-bpe-tokenization/benchmarks/runs/claim2-depth-scaling
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from incbpe.dictionary import Dictionary
from incbpe.incremental import IncrementalTokenizer
from incbpe.normalize import NormalizedDict, normalize
from incbpe.oracle import tokenize as oracle_tokenize
from incbpe.successor_forest import build as build_forest
from incbpe.vocab import TokenId, Vocab

from repro_core.environment import write_environment
from repro_core.timing import BenchmarkResult, run_benchmark

PROTOCOL_VERSION = 1
WARMUP = 3
REPEATS = 10

DEPTHS = [16, 32, 64, 128, 256, 512]
REPEATS_PER_INPUT = 8  # feed the (d+1)-byte pattern this many times per timed run


def build_chain_dictionary(depth: int) -> tuple[Dictionary, NormalizedDict]:
    """Vocab {a, b, ab, ..., a^depth b}; forest = one chain of length depth."""
    tokens = ["", "a", "b"] + ["a" * k + "b" for k in range(1, depth + 1)]
    rules: list[tuple[str, str]] = [("a", "b")] + [("a", "a" * k + "b") for k in range(1, depth)]
    vocab = Vocab.new(tokens)
    dictionary = Dictionary.new(vocab, rules)
    normalized = normalize(dictionary, lambda _tid, token: len(token) == 1)
    return dictionary, normalized


def forest_max_depth(normalized: NormalizedDict) -> int:
    forest = build_forest(normalized)
    depth_of: dict[TokenId, int] = {}

    def depth(t: TokenId) -> int:
        if t not in depth_of:
            parent = forest.parent[t]
            depth_of[t] = 0 if parent is None else depth(parent) + 1
        return depth_of[t]

    return max(depth(t) for t in forest.parent)


def atomic_ids(vocab: Vocab, data: bytes) -> list[TokenId]:
    ids: list[TokenId] = []
    for byte in data:
        tid = vocab.find_token_id(bytes([byte]))
        assert tid is not None
        ids.append(tid)
    return ids


def make_tokenizer(depth: int) -> tuple[Dictionary, IncrementalTokenizer, bytes]:
    dictionary, normalized = build_chain_dictionary(depth)
    forest = build_forest(normalized)
    tokenizer = IncrementalTokenizer.build(normalized, forest)
    data = (b"a" * depth + b"b") * REPEATS_PER_INPUT

    # Correctness first (not timed): incremental must equal the oracle.
    run = tokenizer.new_run()
    run.feed_all(data)
    expected = oracle_tokenize(dictionary, atomic_ids(dictionary.vocab, data))
    assert run.tokens() == expected, f"incremental != oracle at depth={depth}"
    return dictionary, tokenizer, data


def bench_amortized(tokenizer: IncrementalTokenizer, data: bytes, depth: int) -> BenchmarkResult:
    def work() -> None:
        r = tokenizer.new_run()
        r.feed_all(data)

    return run_benchmark(
        work, name=f"chain_amortized/depth={depth}", warmup=WARMUP, repeats=REPEATS
    )


def bench_max_feed_latency(
    tokenizer: IncrementalTokenizer, data: bytes, depth: int
) -> BenchmarkResult:
    """Worst single feed(byte) latency per run; one sample per repeat.

    Reuses BenchmarkResult for reporting, but note the samples are
    *maxima of per-byte latencies*, not totals — recorded as such.
    """

    def one_run_max_ns() -> float:
        r = tokenizer.new_run()
        worst = 0
        for byte in data:
            start = time.perf_counter_ns()
            r.feed(byte)
            elapsed = time.perf_counter_ns() - start
            worst = max(worst, elapsed)
        return float(worst)

    for _ in range(WARMUP):
        one_run_max_ns()
    samples = tuple(one_run_max_ns() for _ in range(REPEATS))
    return BenchmarkResult(
        name=f"feed_max_latency/depth={depth}",
        warmup=WARMUP,
        repeats=REPEATS,
        inner_iterations=1,
        samples_ns=samples,
    )


def main() -> None:
    out_dir = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "papers/incremental-bpe-tokenization/benchmarks/runs/claim2-depth-scaling"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for d in DEPTHS:
        _, normalized = build_chain_dictionary(d)
        measured_depth = forest_max_depth(normalized)
        assert measured_depth == d, (
            f"construction error: wanted chain depth {d}, forest has {measured_depth}"
        )
        _, tokenizer, data = make_tokenizer(d)

        amortized = bench_amortized(tokenizer, data, d)
        per_byte = amortized.median_ns / len(data)
        print(f"{amortized.name}: median {per_byte:.0f} ns/byte", flush=True)
        results.append(amortized.to_dict())

        latency = bench_max_feed_latency(tokenizer, data, d)
        print(f"{latency.name}: median-of-maxima {latency.median_ns / 1000:.1f} us", flush=True)
        results.append(latency.to_dict())

    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "description": (
            "Cost of the missing Centroid Decomposition (Section 5.3) on a depth-d "
            "successor chain, input (a^d b) repeated. chain_amortized samples are "
            "whole-input totals (prediction: flat per-byte); feed_max_latency samples "
            "are per-run maxima of single feed(byte) latencies (prediction: linear "
            "in d without centroid balancing, polylog with it)."
        ),
        "command": (
            "uv run python papers/incremental-bpe-tokenization/benchmarks/claim2_depth_scaling.py"
        ),
        "seed": None,  # fully deterministic workload
        "depths": DEPTHS,
        "repeats_per_input": REPEATS_PER_INPUT,
        "environment_file": "environment.json",
        "benchmarks": results,
    }
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_environment(out_dir / "environment.json")
    print(f"wrote {out_dir}/results.json and environment.json", flush=True)


if __name__ == "__main__":
    main()
