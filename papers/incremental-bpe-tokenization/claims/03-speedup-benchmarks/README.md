# Claim 3 — Drop-in Speedup vs. Hugging Face `tokenizers`

**Status:** ☐ not started (Phase 0 scaffold only)

## Claim statement

> As a drop-in replacement, the method achieves up to a 3.13× speedup over
> Hugging Face's `tokenizers` on English text with the CodeLlama
> tokenizer, versus smaller gains (e.g., 1.05×) on Qwen-3.
>
> — Table 1, Section 7.1

The paper is explicit that the size of the win depends heavily on whether
the tokenizer's pre-tokenization stage does regex-based pre-segmentation:
CodeLlama does none (biggest win, up to 3.13× on English, 2.88× on Code),
while regex-heavy tokenizers (Qwen-3, Llama-4, Mistral-3, GPT-OSS,
DeepSeek-3.2) see gains close to 1.0×, because pre-segmentation already
bounds the per-chunk BPE cost, leaving little for an asymptotically-better
BPE stage to win back. This is the load-bearing mechanistic explanation we
need to reproduce, not just the headline "3×" number.

## Explanation

*(Phase 1–2 — to be written.)*

## Mathematics

Not applicable in the proof sense — this is an empirical throughput claim.
The relevant background is the complexity comparison: HF `tokenizers` uses
a heap-based priority queue (log-linear in the *chunk* length), ours is
O(n log²t) with no dependency on chunk boundaries.

## Implementation

*(Phase 3–4 — to be written.)* Python-first per `docs/ROADMAP.md`. Since
this claim is about *relative* speedup and *shape* of behavior rather than
matching the paper's absolute MiB/s numbers, a Python reimplementation
should still be able to demonstrate the qualitative effect (bigger win on
CodeLlama-style no-pre-tokenization configs than on regex-heavy ones) even
if Python's constant-factor overhead changes the absolute magnitude. If
Python overhead turns out to swamp the effect entirely, fall back to Rust
for this claim specifically, per the documented decision — note that
explicitly here if it happens, rather than silently switching.

## Experiment

*(Phase 4–5 — to be written.)* Needs: the same tokenizer vocabularies used
in the paper (CodeLlama, Qwen-3, others — see paper Table 3, all sourced
from public Hugging Face model repos), a comparable dataset (paper uses
Wikipedia + RedPajama subsets, see paper Appendix H.2 — publicly
available, so should be replicable rather than proxied).

## Benchmark

Must follow the repo-wide benchmarking standard (root `README.md`):
warm-up runs, multiple iterations, mean **and** variance reported, full
environment recorded. Our hardware will not match the paper's 32-core
bare-metal Xeon node — report our own numbers honestly rather than
rescaling to compare directly.

## Result

*(Phase 6 — to be written. No fabricated numbers.)*

## Discussion

*(Phase 6 — to be written.)*

## Limitations

*(Phase 6 — to be written.)*

## Conclusion

*(Phase 6 — to be written.)*

---

> **Inference X-Ray candidate:** Possibly, as a case study rather than a
> standalone concept chapter: "why does the *same* algorithmic
> improvement give a 3× win in one tokenizer config and a 1.05× win in
> another?" — a good worked example of how pipeline stage interactions
> (pre-tokenization bounding BPE cost) can hide an asymptotic improvement
> in practice. Revisit after Phase 5 produces our own numbers.
