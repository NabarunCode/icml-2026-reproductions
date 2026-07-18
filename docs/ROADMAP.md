# Research Roadmap

## Status legend

`☐` not started · `◐` in progress · `☑` complete · `✗` blocked/negative result

## Paper 1 — Incremental BPE Tokenization

Shenghu Jiang, Ruihao Gong. ICML 2026. Poster #63148.
arXiv: [2605.30813](https://arxiv.org/abs/2605.30813) · OpenReview id:
`ZbWgrDzCQo` · Challenge paper id: `#5623`.
Official implementation: [ModelTC/mtc-inc-bpe](https://github.com/ModelTC/mtc-inc-bpe)
(Rust, MIT/Apache-2.0, pinned at tag `v0.9.1`).

| Phase | Status | Notes |
|---|---|---|
| 0. Repository setup | ☑ | Directory structure, docs, official resources, roadmap, Trackio prep done 2026-07-18. |
| 1. Read paper | ☐ | PDF in hand (with alphaXiv annotations); notes not yet written. |
| 2. Understand theory | ☐ | Successor Forest / Suffix-Successor Tree / Monotonic Path Property need first-principles write-up. |
| 3. Understand implementation | ☐ | Reference repo structure scouted (module list only); no line-level mapping yet. |
| 4. Implement | ☐ | Not started. Target language TBD — see open question below. |
| 5. Benchmark | ☐ | Not started. HF Jobs GPU credit available via `ICML-2026-agent-repro` org if local compute is insufficient (CPU-bound workload, so may not be needed). |
| 6. Verify claims | ☐ | See the 4 claims below, sourced from the official challenge listing. |
| 7. Trackio | ☐ | See `trackio/README.md`. Org already joined, GPU credit already granted. |
| 8. GitHub documentation | ☐ | Not started. |

### The four claims to verify

Taken verbatim (condensed) from the official challenge listing for this
paper, cross-checked against the paper text:

1. **Monotonic Path Property** (Theorem 4.2) — valid suffix tokens capable of
   being the last token form a single monotonic path in the
   Suffix-Successor Tree, giving O(log²t) amortized per-byte cost and
   O(n log²t) overall (Section 4).
2. **Algorithm design** — the incremental algorithm combines an
   Aho–Corasick automaton (search-space identification) with centroid
   decomposition (tree navigation), plus an eager-output mechanism for
   streaming token emission (Sections 5–6).
3. **Drop-in speedup** — up to ~3.13× speedup over Hugging Face
   `tokenizers` on English text with the CodeLlama tokenizer, with much
   smaller gains elsewhere (e.g. ~1.05× on Qwen-3) (Table 1, Section 7.1).
4. **Pathological-input robustness** — the incremental method holds stable
   throughput on adversarial repeated-character inputs, while `tiktoken`
   shows O(n²) decay (Figure 3, Section 7.2).

Each will get its own folder under
`papers/incremental-bpe-tokenization/claims/`.

### Open questions to resolve before Phase 4

- **Reproduction language.** The reference implementation is Rust. A
  faithful reproduction of the *algorithm* doesn't require Rust, but a
  faithful reproduction of the *performance claims* (Claims 3–4) arguably
  does, since Python overhead could dominate at these throughputs. Decide
  whether to (a) port the core algorithm to Python for correctness/theory
  verification and separately reason about performance qualitatively, or
  (b) reproduce in Rust for a true apples-to-apples benchmark. Needs a
  decision before Phase 4 — flagged for discussion, not decided here.
- **Compute scope.** The paper's benchmarks use a 32-core bare-metal Xeon
  node. Our reproduction should report its own honest environment
  (per the benchmarking standard) rather than claiming equivalence to the
  paper's hardware.

## Future papers

None queued yet. Add a new `## Paper N — <title>` section here when the
next paper is picked up; do not delete completed papers' sections.
