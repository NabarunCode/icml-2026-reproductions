"""Claim 3 groundwork: throughput + correctness on real English text.

The paper's Claim 3 (Table 1) reports up to ~3.13x speedup of their
Rust incremental implementation over Hugging Face ``tokenizers``.
**A Python reproduction cannot test that speedup's sign** — Python-vs-
Rust constant factors swamp it (stated in docs/ROADMAP.md when the
Python-first decision was made). What this benchmark honestly can and
does establish, on the paper's own English dataset sample (Wikipedia
20231101, stride-42, Appendix H.2) with the GPT-2/R50K vocabulary:

1. ``correctness`` (not timed): our incremental tokenizer agrees
   token-for-token with HF ``tokenizers`` (BPE model, no pre-tokenizer,
   byte-mapped input — the identical whole-string problem) over the
   full measured slice; and we *measure* (not assume) how often
   whole-string BPE agrees with regex-pre-tokenized tiktoken output.
2. ``ours_feed`` vs ``ours_eager``: the eager-output overhead ratio.
   The paper reports ~10% for their O(1)-amortized mechanism
   (Table 5); ours is the definition-first eager implementation, so
   this measures our documented implementation gap, honestly labeled.
3. ``hf_bpe_word`` and ``tiktoken_r50k``: the production baselines'
   absolute throughput on the same slice, for context and for
   comparison against these same baselines when a Rust port of the
   incremental method exists.

Prerequisite: run ``scripts/fetch_wikipedia_sample.py`` first (needs
network); this script verifies the sample's provenance sidecar hash
before using it. Run from the repository root:

    uv run python papers/incremental-bpe-tokenization/benchmarks/claim3_throughput_gpt2.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import tiktoken
from incbpe.eager import new_eager_run
from incbpe.gpt2 import Gpt2Dictionary, bytes_to_unicode, load_gpt2
from incbpe.incremental import IncrementalTokenizer
from incbpe.successor_forest import build as build_forest
from tiktoken.load import data_gym_to_mergeable_bpe_ranks
from tokenizers import Tokenizer
from tokenizers.models import BPE

from repro_core.environment import write_environment
from repro_core.timing import BenchmarkResult, run_benchmark

PROTOCOL_VERSION = 1
WARMUP = 3
REPEATS = 10

BENCH_DIR = Path(__file__).resolve().parent
GPT2_DIR = BENCH_DIR / "data" / "gpt2"
SAMPLE = BENCH_DIR / "data" / "datasets" / "wikipedia_en_20231101_stride42.jsonl"

# Our Python implementation runs ~20-30 us/byte, so the timed slice is
# 500 kB (protocol-compliant repeats stay under ~5 minutes total);
# correctness is checked over the same slice. The definition-first eager
# implementation calibrated at ~1.7 ms/byte (~80x non-eager) on this
# vocabulary, so its series uses a 10 kB sub-slice - the ratio is
# per-byte-normalized and the huge overhead is itself the documented
# implementation-gap measurement (paper's own mechanism: ~10%).
SLICE_BYTES = 500_000
EAGER_SLICE_BYTES = 10_000

GPT2_PAT = r"""'s|'t|'re|'ve|'m|'ll|'d| ?[\p{L}]+| ?[\p{N}]+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""


def load_slice() -> bytes:
    sidecar = SAMPLE.with_suffix(".provenance.json")
    if not SAMPLE.exists() or not sidecar.exists():
        raise SystemExit("dataset sample missing - run scripts/fetch_wikipedia_sample.py first")
    provenance = json.loads(sidecar.read_text(encoding="utf-8"))
    digest = hashlib.sha256(SAMPLE.read_bytes()).hexdigest()
    if digest != provenance["output_sha256"]:
        raise SystemExit("dataset sample does not match its provenance sidecar hash")
    texts: list[str] = []
    total = 0
    with SAMPLE.open(encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            texts.append(record["text"])
            total += record["bytes"]
            if total >= SLICE_BYTES:
                break
    data = "".join(texts).encode("utf-8")[:SLICE_BYTES]
    # Never split a UTF-8 code point at the slice edge.
    while data and (data[-1] & 0xC0) == 0x80:
        data = data[:-1]
    return data


def main() -> None:
    out_dir = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "papers/incremental-bpe-tokenization/benchmarks/runs/claim3-throughput-gpt2"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    data = load_slice()
    text = data.decode("utf-8")
    print(f"slice: {len(data)} bytes", flush=True)

    g: Gpt2Dictionary = load_gpt2(GPT2_DIR / "vocab.json", GPT2_DIR / "merges.txt")
    ours = IncrementalTokenizer.build(g.normalized, build_forest(g.normalized))

    hf = Tokenizer(BPE.from_file(str(GPT2_DIR / "vocab.json"), str(GPT2_DIR / "merges.txt")))
    table = bytes_to_unicode()
    mapped = "".join(table[b] for b in data)

    ranks = data_gym_to_mergeable_bpe_ranks(
        vocab_bpe_file=str(GPT2_DIR / "merges.txt"),
        encoder_json_file=str(GPT2_DIR / "vocab.json"),
    )
    enc = tiktoken.Encoding(
        name="gpt2-local",
        pat_str=GPT2_PAT,
        mergeable_ranks=ranks,
        special_tokens={"<|endoftext|>": 50257},
    )

    # --- Correctness (not timed) -----------------------------------------
    run = ours.new_run()
    run.feed_all(data)
    ours_ids = g.to_gpt2_ids(run.tokens())
    hf_ids = hf.encode(mapped, add_special_tokens=False).ids
    assert ours_ids == hf_ids, "ours != HF tokenizers on the corpus slice"
    print(f"correctness vs HF tokenizers: OK ({len(ours_ids)} tokens)", flush=True)

    tk_ids = enc.encode(text, disallowed_special=())
    agreement = ours_ids == tk_ids
    print(
        f"whole-string BPE vs regex-pre-tokenized tiktoken: "
        f"{'identical' if agreement else 'different'} "
        f"({len(ours_ids)} vs {len(tk_ids)} tokens)",
        flush=True,
    )

    # --- Timed series -----------------------------------------------------
    results: list[dict[str, Any]] = []

    def ours_feed() -> None:
        r = ours.new_run()
        r.feed_all(data)
        r.tokens()

    eager_data = data[:EAGER_SLICE_BYTES]

    def ours_eager() -> None:
        er = new_eager_run(ours.new_run())
        for byte in eager_data:
            er.feed(byte)
        er.finish()

    def hf_bpe_word() -> None:
        hf.encode(mapped, add_special_tokens=False)

    def tiktoken_r50k() -> None:
        enc.encode(text, disallowed_special=())

    for name, fn, nbytes in [
        ("ours_feed", ours_feed, len(data)),
        ("ours_eager", ours_eager, len(eager_data)),
        ("hf_bpe_word", hf_bpe_word, len(data)),
        ("tiktoken_r50k", tiktoken_r50k, len(data)),
    ]:
        r: BenchmarkResult = run_benchmark(
            fn, name=f"{name}/slice={nbytes}", warmup=WARMUP, repeats=REPEATS
        )
        print(f"{r.name}: median {r.median_ns / nbytes:.0f} ns/byte", flush=True)
        results.append(r.to_dict())

    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "description": (
            "Claim 3 groundwork on the paper's English Wikipedia sample "
            "(stride-42, revision-pinned) with GPT-2/R50K: correctness at corpus "
            "scale vs HF tokenizers (asserted) and vs regex-pre-tokenized tiktoken "
            "(measured agreement), eager-vs-non-eager overhead, and baseline "
            "throughputs. Python absolute numbers carry no speedup information "
            "vs the paper's Rust (protocol section 7)."
        ),
        "command": (
            "uv run python papers/incremental-bpe-tokenization/benchmarks/claim3_throughput_gpt2.py"
        ),
        "seed": None,  # deterministic slice of a revision-pinned sample
        "slice_bytes": len(data),
        "tiktoken_agreement_with_whole_string_bpe": agreement,
        "environment_file": "environment.json",
        "benchmarks": results,
    }
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_environment(out_dir / "environment.json")
    print(f"wrote {out_dir}/results.json and environment.json", flush=True)


if __name__ == "__main__":
    main()
