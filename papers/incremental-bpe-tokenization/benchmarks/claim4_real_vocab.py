"""Claim 4 with the real GPT-2 vocabulary and the real tiktoken baseline.

The synthetic-dictionary run (``claim4_pathological.py``) established
the scaling *shapes* with a from-scratch Python baseline. This run uses
the paper's actual setting: the GPT-2/R50K vocabulary (committed with
provenance under ``data/gpt2/``) and the actual ``tiktoken`` library as
the baseline, constructed fully offline from those same files.

Measured on ``"a" * n`` (the Section 7.2 pathological family — a single
regex word, so tiktoken's merge loop bears the full cost):

1. ``ours_gpt2`` — our incremental implementation on the real 50k-token
   vocabulary. Prediction: flat per-byte cost (Python-slow in absolute
   terms, but size-independent).
2. ``tiktoken_gpt2`` — tiktoken's encode. Its merge phase is O(n^2) in
   the word length (paper Figure 7); the quadratic coefficient is small,
   so the grid extends to 2 MB where the n^2 term clearly dominates.
   Prediction: per-byte cost grows ~linearly with n (total ~quadratic).

Correctness first: on every size both tokenizers must produce the
identical token-id sequence (ours mapped to GPT-2 ids) — an external
token-for-token cross-check against a production tokenizer, not just
our own oracle.

Absolute Python-vs-Rust numbers are reported per protocol but carry no
speedup information (protocol section 7); the claim under test is the
shape contrast.

Run from the repository root:

    uv run python papers/incremental-bpe-tokenization/benchmarks/claim4_real_vocab.py \
        papers/incremental-bpe-tokenization/benchmarks/runs/claim4-real-vocab
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import tiktoken
from incbpe.gpt2 import Gpt2Dictionary, load_gpt2
from incbpe.incremental import IncrementalTokenizer
from incbpe.successor_forest import build as build_forest
from tiktoken.load import data_gym_to_mergeable_bpe_ranks

from repro_core.environment import write_environment
from repro_core.timing import BenchmarkResult, run_benchmark

PROTOCOL_VERSION = 1
WARMUP = 3
REPEATS = 10

DATA_DIR = Path(__file__).resolve().parent / "data" / "gpt2"

# GPT-2's pre-tokenization regex (from the MIT-licensed GPT-2 release);
# on "a"*n it matches the whole input as one word, as intended here.
GPT2_PAT = r"""'s|'t|'re|'ve|'m|'ll|'d| ?[\p{L}]+| ?[\p{N}]+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""

# Our Python implementation is ~30 us/byte, so its grid stays modest;
# tiktoken (Rust) needs MB-scale inputs before its n^2 term dominates.
OURS_SIZES = [5_000, 10_000, 20_000, 50_000, 100_000]
TIKTOKEN_SIZES = [10_000, 20_000, 50_000, 100_000, 200_000, 500_000, 1_000_000, 2_000_000]


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


def cross_check(g: Gpt2Dictionary, ours: IncrementalTokenizer, enc: tiktoken.Encoding) -> None:
    """Both tokenizers must agree token-for-token before anything is timed."""
    for n in OURS_SIZES:
        run = ours.new_run()
        run.feed_all(b"a" * n)
        ours_ids = g.to_gpt2_ids(run.tokens())
        tk_ids = enc.encode("a" * n, disallowed_special=())
        assert ours_ids == tk_ids, f"tokenization mismatch vs tiktoken at n={n}"


def bench_ours(ours: IncrementalTokenizer, n: int) -> BenchmarkResult:
    data = b"a" * n

    def work() -> None:
        run = ours.new_run()
        run.feed_all(data)
        run.tokens()

    return run_benchmark(work, name=f"ours_gpt2/n={n}", warmup=WARMUP, repeats=REPEATS)


def bench_tiktoken(enc: tiktoken.Encoding, n: int) -> BenchmarkResult:
    text = "a" * n

    def work() -> None:
        enc.encode(text, disallowed_special=())

    return run_benchmark(work, name=f"tiktoken_gpt2/n={n}", warmup=WARMUP, repeats=REPEATS)


def main() -> None:
    out_dir = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "papers/incremental-bpe-tokenization/benchmarks/runs/claim4-real-vocab"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    g = load_gpt2(DATA_DIR / "vocab.json", DATA_DIR / "merges.txt")
    ours = IncrementalTokenizer.build(g.normalized, build_forest(g.normalized))
    enc = load_tiktoken()

    cross_check(g, ours, enc)
    print("token-for-token cross-check vs tiktoken: OK", flush=True)

    results: list[dict[str, Any]] = []
    for n in OURS_SIZES:
        r = bench_ours(ours, n)
        print(f"{r.name}: median {r.median_ns / n:.0f} ns/byte", flush=True)
        results.append(r.to_dict())
    for n in TIKTOKEN_SIZES:
        r = bench_tiktoken(enc, n)
        print(f"{r.name}: median {r.median_ns / n:.0f} ns/byte", flush=True)
        results.append(r.to_dict())

    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "description": (
            "Claim 4 on the real GPT-2/R50K vocabulary: our incremental "
            "implementation (Python, prediction: flat per-byte) vs the actual "
            "tiktoken baseline built offline from the same committed files "
            "(prediction: per-byte cost growing ~linearly with n, i.e. O(n^2) "
            "total, dominating at MB scale). Token-for-token agreement between "
            "both tokenizers is asserted before timing."
        ),
        "command": (
            "uv run python papers/incremental-bpe-tokenization/benchmarks/claim4_real_vocab.py"
        ),
        "seed": None,  # fully deterministic workload
        "data_files": {
            "vocab.json": "sha256 196139668be63f3b5d6574427317ae82f612a97c5d1cdaf36ed2256dbf636783",
            "merges.txt": "sha256 1ce1664773c50f3e0cc8842619a93edc4624525b728b188a9e0be33b7726adc5",
        },
        "sizes": {"ours_gpt2": OURS_SIZES, "tiktoken_gpt2": TIKTOKEN_SIZES},
        "environment_file": "environment.json",
        "benchmarks": results,
    }
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_environment(out_dir / "environment.json")
    print(f"wrote {out_dir}/results.json and environment.json", flush=True)


if __name__ == "__main__":
    main()
