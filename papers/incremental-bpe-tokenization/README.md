# Incremental BPE Tokenization

**Authors:** Shenghu Jiang¹², Ruihao Gong¹² (¹Beihang University, ²SenseTime
Research)
**Venue:** ICML 2026 (43rd International Conference on Machine Learning),
Seoul, South Korea. PMLR 306, 2026.
**Poster:** [icml.cc/virtual/2026/poster/63148](https://icml.cc/virtual/2026/poster/63148)
*(the ICML page linked from the HF challenge Space is broken — use this URL only)*

## Reproduction outcome (Phases 1-8 complete, 2026-07-19)

**Published logbook:** [hinabarun/repro-incremental-bpe-tokenization](https://huggingface.co/spaces/hinabarun/repro-incremental-bpe-tokenization)
([rendered](https://hinabarun-repro-incremental-bpe-tokenization.static.hf.space/)) —
entry #5623 in the [ICML 2026 reproducibility challenge](https://huggingface.co/spaces/ICML-2026-agent-repro/challenge).

| Claim | Verdict | Headline evidence |
|---|---|---|
| 1. Monotonic Path Property (Thm 4.2) | **Reproduced (empirically)** | zero violations: exhaustive cross-products, per-byte checks, 200 random dicts, real-50k-vocab consequence tests |
| 2. Algorithm design (§5-6) | **Partially reproduced** | composition verified end-to-end; missing §5.3/§6.2 mechanisms' absence *measured* (tail latency linear in depth; eager 34× vs paper's ~10%) |
| 3. Drop-in 3.13× speedup | **Equivalence reproduced; speedup untested by design** | token-for-token = HF `tokenizers` over the paper's English corpus recipe; speedup behind a measured 52× Python-vs-Rust constant |
| 4. Pathological robustness vs tiktoken | **Reproduced (era-appropriate baseline)** | ours slope 0.99 (flat) vs tiktoken 0.8.0 slopes 2.08/2.04 (R50K/CL100K, quadratic); finding: current tiktoken 0.13.0 fixed the quadratic upstream (1.14-1.16) |

Nothing falsified; every verdict links to committed, protocol-compliant
runs (`results/`, `benchmarks/runs/`, filled checklists, clean-tree
environment records). Full verdict write-ups: each
[`claims/<NN>-*/README.md`](claims/) Result/Discussion/Limitations/
Conclusion sections. File-by-file independence record:
[`PROVENANCE.md`](PROVENANCE.md).

**Rerun everything** (any machine, Python ≥3.11 + [uv](https://docs.astral.sh/uv/)):

```bash
git clone https://github.com/NabarunCode/icml-2026-reproductions.git && cd icml-2026-reproductions
uv sync --all-packages --all-extras && uv run pytest   # 44 tests / 2,126 subtests
uv run python papers/incremental-bpe-tokenization/benchmarks/claim4_real_vocab.py   # etc.
```

**Deliberately not done** (each documented with a measured acceptance
test, see [`experiments/README.md`](experiments/README.md) Limitations):
Centroid Decomposition (§5.3), two-pointer eager output (§6.2),
Appendix A properization (blocks CodeLlama/Claim 3's headline number),
O200K measurement, Appendix E line-by-line proof re-derivation.

## Links

| Resource | Link | Status |
|---|---|---|
| arXiv paper | [2605.30813](https://arxiv.org/abs/2605.30813) | ✅ Full text obtained (with alphaXiv annotations) — see [`paper/incremental-bpe-tokenization.pdf`](paper/incremental-bpe-tokenization.pdf) |
| OpenReview | id `ZbWgrDzCQo` | Preferred source per project policy; not directly fetchable from this sandbox (egress-restricted) — treat arXiv v1 as the working text until cross-checked |
| Official implementation | [ModelTC/mtc-inc-bpe](https://github.com/ModelTC/mtc-inc-bpe) | ✅ Vendored as a pinned git submodule at [`references/mtc-inc-bpe`](references/mtc-inc-bpe) (tag `v0.9.1`) — see [`references/official-implementation.md`](references/official-implementation.md) |
| ICML 2026 Challenge (HF Space) | [ICML-2026-agent-repro/challenge](https://huggingface.co/spaces/ICML-2026-agent-repro/challenge) | Paper #5623 in the challenge; 4 official claims recorded in `docs/ROADMAP.md` |

## One-paragraph summary

Byte Pair Encoding (BPE) tokenization is normally an *offline* process: the
whole input (or chunk) must be observed before a canonical tokenization can
be produced, which serializes tokenization and prefill in streaming/LLM
inference. This paper proves a structural property of standard BPE — that
tokenizations of every prefix of a string form a tree (the "Prefix Tree of
Tokens"), and that the suffix tokens capable of being the final token of a
growing prefix form a single monotonic path in a derived structure they
call the **Suffix-Successor Tree** (Theorem 4.2, the **Monotonic Path
Property**). Building on this, they give an algorithm — combining an
Aho–Corasick automaton with centroid decomposition — that updates the
tokenization of a string incrementally, per appended byte, in worst-case
**O(log²t)** time (t = max token length), for **O(n log²t)** overall, with
an *eager output* extension for streaming emission. Implemented in Rust as
a drop-in replacement, it reports up to ~3× speedup over Hugging Face's
`tokenizers` and avoids the O(n²) pathological blowup they measure in
OpenAI's `tiktoken`.

This is a **systems/algorithms** paper, not a modeling paper: no training,
no model weights, no accuracy claims. Reproduction here means (a)
independently verifying the algorithmic correctness and complexity claims,
and (b) independently re-measuring the reported speedups.

## Why this paper (fit for the repo's goals)

- Self-contained: no GPUs required for the core claims, no pretrained
  checkpoints to source.
- A genuine correctness proof to check (Theorem 4.2, Appendix E) — good
  practice reading a dense inductive/structural proof and turning it into
  an independently-checkable claim.
- A real reference implementation exists in a permissively-licensed repo,
  so Phase 3 (understand implementation) has ground truth to compare
  against.
- Directly relevant to **Inference X-Ray**: tokenization internals,
  Aho–Corasick automata, and streaming/eager emission are all strong
  candidate teaching chapters (flagged per-claim, see claim folders).

## Claims under verification

See [`docs/ROADMAP.md`](../../docs/ROADMAP.md) for the authoritative list
and status. Each claim has its own folder under [`claims/`](claims/):

1. [`01-monotonic-path-property`](claims/01-monotonic-path-property/) — the structural theorem (Theorem 4.2)
2. [`02-algorithm-design`](claims/02-algorithm-design/) — Aho–Corasick + centroid decomposition + eager output
3. [`03-speedup-benchmarks`](claims/03-speedup-benchmarks/) — up to ~3.13× speedup vs HF `tokenizers`
4. [`04-pathological-robustness`](claims/04-pathological-robustness/) — stable throughput vs `tiktoken`'s O(n²) decay

## Directory contents

This paper is a fully self-contained research project (see
`docs/ARCHITECTURE.md` at the repo root):

```
incremental-bpe-tokenization/
  README.md                # this file
  PROVENANCE.md            # per-file independence classification (integrity record)
  paper/                   # the paper PDF (with annotations)
  supplementary/           # supplementary material (empty so far)
  notes/                   # Phase 1-3 artifacts: reading / theory / implementation notes
  claims/                  # one folder per claim, per docs/WORKFLOW.md
  experiments/             # the reproduction itself: installable `incbpe` package + tests
  benchmarks/              # Phase 5 benchmark scripts + raw run output
  results/                 # curated final numbers + environment.json + checklists
  figures/                 # generated plots (committed with generating code)
  scripts/                 # paper-specific CLI helpers
  references/mtc-inc-bpe/  # pinned git submodule, official Rust implementation
  trackio/                 # Phase 7 logbook publishing recipe
```
