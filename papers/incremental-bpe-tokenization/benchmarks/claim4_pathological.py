"""Claim 4 benchmark: scaling shape on pathological repeated-character input.

The paper (Section 7.2, Figure 3) claims the incremental method holds
stable throughput on adversarial repeated-character inputs while
tiktoken-style from-scratch tokenization shows O(n^2) decay. This
experiment measures the *scaling shape* of three methods on ``"a" * n``:

1. ``incremental`` — our reproduction (``incbpe.incremental``), feeding
   the string byte by byte, then emitting all tokens: the streaming
   use-case the paper targets.
2. ``restart_per_byte`` — the honest quadratic baseline: after every
   appended byte, re-tokenize the whole prefix from scratch with the
   oracle. This is what any non-incremental tokenizer must do in a
   streaming setting, and is the mechanism behind the O(n^2) decay the
   paper ascribes to tiktoken. (tiktoken itself cannot run in this
   sandbox: its encoding files download from a CDN the egress policy
   blocks — recorded in the results, not silently substituted.)
3. ``batch_oracle`` — one from-scratch tokenization of the full string:
   the non-streaming reference cost, for context.

Absolute numbers are Python and prove nothing about the paper's Rust
throughput; the claim under test here is the *shape* (near-linear total
cost, i.e. flat per-byte cost, vs. quadratic growth). See
docs/BENCHMARK_PROTOCOL.md section 7.

Run from the repository root:

    uv run python papers/incremental-bpe-tokenization/benchmarks/claim4_pathological.py \
        papers/incremental-bpe-tokenization/benchmarks/runs/claim4-pathological
"""

from __future__ import annotations

import json
import sys
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

# The adversarial dictionary: powers of "a" with a doubling merge chain,
# the same repeated-character family the paper uses (Section 7.2 /
# Appendix H.2) and our differential tests already exercise. Per the
# Phase 2 finding this builds a *wide, shallow* Successor Forest - which
# is exactly why measuring (rather than assuming) the incremental
# method's behavior without Centroid Decomposition is meaningful here.
POWERS = [2**k for k in range(5)]  # 1, 2, 4, 8, 16
RULES = [("a" * p, "a" * p) for p in POWERS[:-1]]  # a+a, aa+aa, a4+a4, a8+a8

INCREMENTAL_SIZES = [1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000]
RESTART_SIZES = [125, 250, 500, 1_000, 2_000]  # quadratic: kept small on purpose
BATCH_SIZES = INCREMENTAL_SIZES


def build_dictionary() -> tuple[Dictionary, NormalizedDict]:
    vocab = Vocab.new(["", *("a" * p for p in POWERS)])
    dictionary = Dictionary.new(vocab, RULES)
    normalized = normalize(dictionary, lambda _tid, token: len(token) == 1)
    return dictionary, normalized


def atomic_ids(vocab: Vocab, data: bytes) -> list[TokenId]:
    ids: list[TokenId] = []
    for byte in data:
        tid = vocab.find_token_id(bytes([byte]))
        assert tid is not None
        ids.append(tid)
    return ids


def bench_incremental(tokenizer: IncrementalTokenizer, n: int) -> BenchmarkResult:
    data = b"a" * n

    def work() -> None:
        run = tokenizer.new_run()
        run.feed_all(data)
        run.tokens()

    return run_benchmark(work, name=f"incremental/n={n}", warmup=WARMUP, repeats=REPEATS)


def bench_restart_per_byte(dictionary: Dictionary, n: int) -> BenchmarkResult:
    ids = atomic_ids(dictionary.vocab, b"a" * n)

    def work() -> None:
        for prefix_len in range(1, n + 1):
            oracle_tokenize(dictionary, ids[:prefix_len])

    return run_benchmark(work, name=f"restart_per_byte/n={n}", warmup=WARMUP, repeats=REPEATS)


def bench_batch_oracle(dictionary: Dictionary, n: int) -> BenchmarkResult:
    ids = atomic_ids(dictionary.vocab, b"a" * n)

    def work() -> None:
        oracle_tokenize(dictionary, ids)

    return run_benchmark(work, name=f"batch_oracle/n={n}", warmup=WARMUP, repeats=REPEATS)


def verify_correctness(dictionary: Dictionary, tokenizer: IncrementalTokenizer) -> None:
    """Benchmarked code must be correct code: check incremental output
    against the oracle on every input size measured (not timed)."""
    for n in INCREMENTAL_SIZES:
        data = b"a" * n
        run = tokenizer.new_run()
        run.feed_all(data)
        expected = oracle_tokenize(dictionary, atomic_ids(dictionary.vocab, data))
        assert run.tokens() == expected, f"incremental != oracle at n={n}"


def main() -> None:
    out_dir = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "papers/incremental-bpe-tokenization/benchmarks/runs/claim4-pathological"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    dictionary, normalized = build_dictionary()
    forest = build_forest(normalized)
    tokenizer = IncrementalTokenizer.build(normalized, forest)

    verify_correctness(dictionary, tokenizer)
    print("correctness cross-check vs oracle: OK", flush=True)

    results: list[dict[str, Any]] = []
    for n in INCREMENTAL_SIZES:
        r = bench_incremental(tokenizer, n)
        print(f"{r.name}: median {r.median_ns / n:.0f} ns/byte", flush=True)
        results.append(r.to_dict())
    for n in RESTART_SIZES:
        r = bench_restart_per_byte(dictionary, n)
        print(f"{r.name}: median {r.median_ns / n:.0f} ns/byte", flush=True)
        results.append(r.to_dict())
    for n in BATCH_SIZES:
        r = bench_batch_oracle(dictionary, n)
        print(f"{r.name}: median {r.median_ns / n:.0f} ns/byte", flush=True)
        results.append(r.to_dict())

    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "description": (
            "Claim 4 scaling shape on 'a'*n: incremental (ours) vs restart-per-byte "
            "(quadratic baseline) vs batch oracle. tiktoken baseline unavailable in "
            "this environment (encoding CDN blocked by egress policy)."
        ),
        "command": (
            "uv run python papers/incremental-bpe-tokenization/benchmarks/claim4_pathological.py"
        ),
        "seed": None,  # fully deterministic workload
        "dictionary": {"vocab_powers_of_a": POWERS, "rules": RULES},
        "sizes": {
            "incremental": INCREMENTAL_SIZES,
            "restart_per_byte": RESTART_SIZES,
            "batch_oracle": BATCH_SIZES,
        },
        "environment_file": "environment.json",
        "benchmarks": results,
    }
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_environment(out_dir / "environment.json")
    print(f"wrote {out_dir}/results.json and environment.json", flush=True)


if __name__ == "__main__":
    main()
