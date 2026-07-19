# Claim 3 — Groundwork on the paper's English dataset (measured)

**Run:** [`../benchmarks/runs/claim3-throughput-gpt2/`](../benchmarks/runs/claim3-throughput-gpt2/)
(commit `f96e5c49`, clean tree) ·
**Script:** [`../benchmarks/claim3_throughput_gpt2.py`](../benchmarks/claim3_throughput_gpt2.py) ·
**Dataset:** English Wikipedia 20231101, stride-42, revision-pinned
(`b04c8d1c`), 3 709 docs / 16 502 234 bytes — the paper's own Appendix
H.2 recipe; regenerable via `scripts/fetch_wikipedia_sample.py` and
verified against the committed provenance sidecar's SHA256.

## Scope, stated up front

The claim is "up to ~3.13× speedup over HF `tokenizers`" (Table 1) —
**a Python reproduction cannot test that speedup's sign** (Python-vs-
Rust constant factors are ~50×; this was pre-declared in the Python-
first decision, `docs/ROADMAP.md`). What this run honestly establishes
on a 500 kB slice of the paper's English sample with GPT-2/R50K:

## Results

**Correctness at corpus scale (the strongest result here):** our
incremental tokenizer produced **token-for-token identical output to
Hugging Face `tokenizers`** — the claim's own baseline library — across
the full slice: 114 399 tokens, zero divergences (asserted before any
timing).

**Pre-tokenization semantics, measured not assumed:** whole-string BPE
(our setting, and the paper's "Absence of Pre-tokenization" regime)
produces **0.86% fewer tokens** than regex-pre-tokenized tiktoken on
the same bytes (114 399 vs 115 391) — merges crossing regex word
boundaries, quantified.

| series | median | note |
|---|---|---|
| `ours_feed` (Python) | 28.0 µs/byte | flat, consistent with the 'a'*n runs (19.7 µs/byte there; real text walks deeper) |
| `ours_eager` (Python, 10 kB sub-slice) | 964.5 µs/byte | **34× non-eager** — our definition-first eager implementation's documented gap, now quantified; the paper's O(1)-amortized mechanism reports **~10%** overhead (Table 5). This measures our implementation, not the paper's mechanism. |
| `hf_bpe_word` (Rust, same whole-string problem) | 536 ns/byte | ~52× faster than our Python — the target line for any future Rust port |
| `tiktoken_r50k` (Rust, full regex pipeline) | 85 ns/byte | production reference point |

## What this means for the claim's verdict (Phase 6 preview)

- The *correctness* half of "drop-in" is fully demonstrated at corpus
  scale against the actual baseline library.
- The *speedup* half remains **untestable in Python** — an honest
  scope limit, not a failure. Paths to testing it: a Rust port of the
  hot path (the pre-approved fallback), or profiling-based argument.
- The eager-overhead comparison (34× vs the paper's ~10%) measures the
  distance between our definition-first implementation and the paper's
  §6.2 two-pointer mechanism — it is evidence about *our gap*, and
  becomes the acceptance test for implementing §6.2.

## Noise and limitations

- Single 500 kB slice (eager: 10 kB) of one dataset; CVs in
  `results.json`.
- Same shared-sandbox caveats as all Phase 5 runs.
- `hf_bpe_word` runs the HF BPE model without a pre-tokenizer on
  byte-mapped input so both sides solve the identical problem; it is
  not the full production GPT-2 HF pipeline.
