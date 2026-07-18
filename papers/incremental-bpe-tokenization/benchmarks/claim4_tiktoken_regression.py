"""Claim 4 baseline archaeology: old tiktoken really was O(n^2).

The main real-vocab run (``claim4_real_vocab.py``) found that current
tiktoken (0.13.0) shows only mild ~n^1.2 growth on ``"a" * n`` up to
8 MB — not the O(n^2) decay the paper reports (Figure 3/7). A version
probe explained the discrepancy: **tiktoken 0.8.0** (2024-era) exhibits
clear quadratic behavior. This script makes that measurement
protocol-grade, so the claim's verdict can say precisely: *reproduced
against the era-appropriate baseline; the baseline has since been
optimized upstream.*

Must be run with the old tiktoken layered over the project environment:

    uv run --with tiktoken==0.8.0 python \
        papers/incremental-bpe-tokenization/benchmarks/claim4_tiktoken_regression.py

The script hard-asserts the tiktoken version so a result produced with
the wrong baseline cannot be recorded by accident. The grid stops at
200 kB because the quadratic cost makes larger sizes take minutes per
sample (that blow-up being, of course, the point).
"""

from __future__ import annotations

import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any

import tiktoken
from tiktoken.load import data_gym_to_mergeable_bpe_ranks

from repro_core.environment import write_environment
from repro_core.timing import BenchmarkResult, run_benchmark

PROTOCOL_VERSION = 1
WARMUP = 3
REPEATS = 10

EXPECTED_TIKTOKEN = "0.8.0"

DATA_DIR = Path(__file__).resolve().parent / "data" / "gpt2"
GPT2_PAT = r"""'s|'t|'re|'ve|'m|'ll|'d| ?[\p{L}]+| ?[\p{N}]+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""

SIZES = [10_000, 20_000, 50_000, 100_000, 200_000]


def load_tiktoken() -> tiktoken.Encoding:
    ranks = data_gym_to_mergeable_bpe_ranks(
        vocab_bpe_file=str(DATA_DIR / "merges.txt"),
        encoder_json_file=str(DATA_DIR / "vocab.json"),
    )
    return tiktoken.Encoding(
        name="gpt2-local",
        pat_str=GPT2_PAT,
        mergeable_ranks=ranks,
        special_tokens={"<|endoftext|>": 50257},
    )


def bench(enc: tiktoken.Encoding, n: int) -> BenchmarkResult:
    text = "a" * n

    def work() -> None:
        enc.encode(text, disallowed_special=())

    return run_benchmark(
        work, name=f"tiktoken_{EXPECTED_TIKTOKEN}/n={n}", warmup=WARMUP, repeats=REPEATS
    )


def main() -> None:
    version = importlib.metadata.version("tiktoken")
    if version != EXPECTED_TIKTOKEN:
        raise SystemExit(
            f"this regression run requires tiktoken=={EXPECTED_TIKTOKEN}, got {version}; "
            "run via: uv run --with tiktoken==0.8.0 python "
            "papers/incremental-bpe-tokenization/benchmarks/claim4_tiktoken_regression.py"
        )

    out_dir = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "papers/incremental-bpe-tokenization/benchmarks/runs/claim4-tiktoken-0.8.0"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    enc = load_tiktoken()
    results: list[dict[str, Any]] = []
    for n in SIZES:
        r = bench(enc, n)
        print(f"{r.name}: median {r.median_ns / n:.0f} ns/byte", flush=True)
        results.append(r.to_dict())

    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "description": (
            "Era-appropriate Claim 4 baseline: tiktoken 0.8.0 (2024) on 'a'*n with "
            "the GPT-2/R50K vocabulary, expected to show the O(n^2) merge-phase decay "
            "the paper reports - in contrast to tiktoken 0.13.0 (see the "
            "claim4-real-vocab run), where upstream optimization removed it."
        ),
        "command": (
            "uv run --with tiktoken==0.8.0 python "
            "papers/incremental-bpe-tokenization/benchmarks/claim4_tiktoken_regression.py"
        ),
        "seed": None,  # fully deterministic workload
        "tiktoken_version": version,
        "data_files": {
            "vocab.json": "sha256 196139668be63f3b5d6574427317ae82f612a97c5d1cdaf36ed2256dbf636783",
            "merges.txt": "sha256 1ce1664773c50f3e0cc8842619a93edc4624525b728b188a9e0be33b7726adc5",
        },
        "sizes": SIZES,
        "environment_file": "environment.json",
        "benchmarks": results,
    }
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_environment(out_dir / "environment.json")
    print(f"wrote {out_dir}/results.json and environment.json", flush=True)


if __name__ == "__main__":
    main()
