"""Claim 4 on the paper's own tokenizer: tiktoken with CL100K.

The claim statement names this setting explicitly ("tiktoken (CL100K)
exhibits characteristic quadratic O(n^2) performance decay", Figure 3).
The GPT-2/R50K runs already established the version story; this script
measures the exact claimed tokenizer, using the hash-pinned
``cl100k_base.tiktoken`` under ``data/tiktoken/``.

Run it twice — once per baseline era; it detects the installed tiktoken
version, sizes its grid accordingly (the quadratic 0.8.0 needs a small
grid; current tiktoken is measured to 8 MB), and names the output
directory and series by the actual version:

    uv run python papers/incremental-bpe-tokenization/benchmarks/claim4_tiktoken_cl100k.py
    uv run --with tiktoken==0.8.0 python \\
        papers/incremental-bpe-tokenization/benchmarks/claim4_tiktoken_cl100k.py
"""

from __future__ import annotations

import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any

import tiktoken
from tiktoken.load import load_tiktoken_bpe

from repro_core.environment import write_environment
from repro_core.timing import BenchmarkResult, run_benchmark

PROTOCOL_VERSION = 1
WARMUP = 3
REPEATS = 10

DATA = Path(__file__).resolve().parent / "data" / "tiktoken" / "cl100k_base.tiktoken"
CL100K_SHA256 = "223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7"

# The cl100k_base pre-tokenization regex, as published in tiktoken itself.
CL100K_PAT = (
    r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}+|\p{N}{1,3}"""
    r"""| ?[^\s\p{L}\p{N}]++[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+"""
)

# Old (quadratic) tiktoken gets a small grid; current tiktoken runs to 8 MB.
SIZES_QUADRATIC_ERA = [10_000, 20_000, 50_000, 100_000, 200_000]
SIZES_CURRENT = [10_000, 50_000, 100_000, 500_000, 1_000_000, 2_000_000, 4_000_000, 8_000_000]


def load_encoding() -> tiktoken.Encoding:
    import hashlib

    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()
    if digest != CL100K_SHA256:
        raise SystemExit(f"cl100k_base.tiktoken hash mismatch: {digest}")
    ranks = load_tiktoken_bpe(str(DATA))
    return tiktoken.Encoding(
        name="cl100k-local", pat_str=CL100K_PAT, mergeable_ranks=ranks, special_tokens={}
    )


def bench(enc: tiktoken.Encoding, version: str, n: int) -> BenchmarkResult:
    text = "a" * n

    def work() -> None:
        enc.encode(text, disallowed_special=())

    return run_benchmark(
        work, name=f"tiktoken_cl100k_{version}/n={n}", warmup=WARMUP, repeats=REPEATS
    )


def main() -> None:
    version = importlib.metadata.version("tiktoken")
    sizes = SIZES_QUADRATIC_ERA if version.startswith("0.8.") else SIZES_CURRENT
    out_dir = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else f"papers/incremental-bpe-tokenization/benchmarks/runs/claim4-cl100k-tiktoken-{version}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    enc = load_encoding()
    results: list[dict[str, Any]] = []
    for n in sizes:
        r = bench(enc, version, n)
        print(f"{r.name}: median {r.median_ns / n:.0f} ns/byte", flush=True)
        results.append(r.to_dict())

    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "description": (
            "Claim 4's exact named setting: tiktoken with CL100K on 'a'*n. Grid "
            "sized by installed tiktoken version (quadratic-era 0.8.x kept small; "
            "current versions measured to 8 MB)."
        ),
        "command": (
            "uv run [--with tiktoken==0.8.0] python "
            "papers/incremental-bpe-tokenization/benchmarks/claim4_tiktoken_cl100k.py"
        ),
        "seed": None,  # fully deterministic workload
        "tiktoken_version": version,
        "data_files": {"cl100k_base.tiktoken": f"sha256 {CL100K_SHA256} (verified at load)"},
        "sizes": sizes,
        "environment_file": "environment.json",
        "benchmarks": results,
    }
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_environment(out_dir / "environment.json")
    print(f"wrote {out_dir}/results.json and environment.json", flush=True)


if __name__ == "__main__":
    main()
