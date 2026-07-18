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
| 0. Repository setup | ☑ | Directory structure, docs, official resources, roadmap, Trackio prep done 2026-07-18. Repository-wide infrastructure hardening (uv workspace, CI, strict typing, benchmark protocol, provenance records, per-paper self-contained layout) completed same day — see `docs/ARCHITECTURE.md`. |
| 1. Read paper | ☑ | Full reading notes written 2026-07-18 — see `papers/incremental-bpe-tokenization/notes/reading-notes.md`. |
| 2. Understand theory | ☑ | First-principles write-up done 2026-07-18 — see `papers/incremental-bpe-tokenization/notes/theory-notes.md`. Built and mechanically verified our own minimal example (not the paper's Figure 2, which didn't extract as trustworthy structured data). |
| 3. Understand implementation | ☑ | Verified module map done 2026-07-18 — see `papers/incremental-bpe-tokenization/notes/implementation-notes.md`. Bonus: found the reference implementation's own test suite preserves a 13/14-rule variant of the paper's Figure 2 example; ran it with `cargo test` for authoritative ground-truth θ-traces and forest structure. |
| 4. Implement | ◐ | Core incremental search implemented in Python 2026-07-18 (`papers/incremental-bpe-tokenization/experiments/`), extended same day in two more passes: (2) real Aho-Corasick automaton, tree-walk search, eager output; (3) the O(1) DFS-interval test (§4.3) + binary search over provably-disjoint sibling intervals, replacing the O(depth) per-node check. 22/22 tests pass. Remaining gap, now narrowly scoped: Centroid Decomposition (§5.3) — bounds the *number of tree levels* to O(log t); everything else about the per-level mechanism now matches the paper. See `papers/incremental-bpe-tokenization/experiments/README.md` "Limitations". |
| 5. Benchmark | ☐ | Not started. HF Jobs GPU/compute credit confirmed available via `ICML-2026-agent-repro` org if local compute is insufficient. |
| 6. Verify claims | ☐ | See the 4 claims below, sourced from the official challenge listing. |
| 7. Trackio | ☐ | See `papers/incremental-bpe-tokenization/trackio/README.md`. Org already joined, GPU credit already granted. |
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

### Decisions (resolved 2026-07-18)

- **Reproduction language: Python-first.** The reference implementation is
  Rust, but the project owner reads/maintains Python, not Rust, so the
  reproduction (Phase 4) is implemented in Python by default. Fall back to
  Rust (or a small Rust extension for just the hot path) only if Python
  turns out to be a genuine blocker for demonstrating a claim — e.g., if
  Python overhead is so large that Claims 3–4 (throughput speedup,
  pathological-input robustness) can't show the paper's *qualitative*
  effect (relative speedup, O(n²) vs. near-linear shape) even though the
  absolute numbers won't match a bare-metal Rust build. Correctness claims
  (Claim 1, and most of Claim 2) are language-independent and have no
  reason to need Rust. Document the decision inline in each claim's
  `Implementation` section rather than assuming it's obvious from here.
- **Compute scope.** The paper's benchmarks use a 32-core bare-metal Xeon
  node; ours will not match that hardware. HF Jobs GPU/compute credit
  (via the already-joined `ICML-2026-agent-repro` org) is available if
  Phase 5 needs more consistent or larger-scale compute than this sandbox
  provides — note this workload is primarily CPU-bound (tokenization
  throughput), so a GPU specifically may not be the relevant lever, but
  HF Jobs also provisions CPU-only runs, which would help with the
  bare-metal-like isolation (pinned cores, no noisy neighbors) the paper's
  own methodology relies on. Either way, report our own honest environment
  (per the benchmarking standard) rather than claiming equivalence to the
  paper's hardware.

## Future papers

None queued yet. Add a new `## Paper N — <title>` section here when the
next paper is picked up; do not delete completed papers' sections.
