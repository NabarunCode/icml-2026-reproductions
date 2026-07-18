# Incremental BPE Tokenization — Python Reproduction

Independent Python reimplementation of the core incremental algorithm
from *Incremental BPE Tokenization* (Jiang & Gong, ICML 2026). This is
**not** a port of the official Rust crate (`ModelTC/mtc-inc-bpe`, vendored
at `../../papers/incremental-bpe-tokenization/reference/mtc-inc-bpe` for
reference/comparison only) — it is a from-scratch implementation, scoped
and tested against that reference where useful.

## What's implemented

| Piece | Module | Paper section | Status |
|---|---|---|---|
| Vocabulary | `incbpe/vocab.py` | §3.1 | Done |
| Dictionary (ordered merge rules) | `incbpe/dictionary.py` | §3.1 | Done |
| Standard-BPE oracle (from scratch) | `incbpe/oracle.py` | §3.1, Eq. 1 | Done — this is the ground-truth definition everything else is tested against |
| Normalization (canonical tokens) | `incbpe/normalize.py` | §3.3 | Done, byte-level atomicity only (see Limitations) |
| Successor Forest | `incbpe/successor_forest.py` | §3.4 | Done — parent pointers only (see Limitations) |
| Incremental theta(s) search | `incbpe/incremental.py` | §4 (Def. 4.1, Thm. 4.2), §5.1 | Done, **not yet asymptotically optimal** (see Limitations) |
| Eager output | — | §6 | **Not implemented yet** |
| Aho–Corasick automaton | — | §5.2 | **Not implemented yet** |
| Centroid Decomposition | — | §5.3 | **Not implemented yet** |
| Appendix A properization | — | Appendix A | **Not implemented yet** |

## Limitations (explicit, not silent)

This is a **correctness-first** implementation, deliberately scoped to
verify Claim 1 (Monotonic Path Property) and the structural half of
Claim 2 (the algorithm's design correctness), not yet the performance
claims (3, 4), which need the pieces marked "not implemented yet" above:

1. **Finding the longest suffix token** is done by scanning candidate
   lengths directly against the vocabulary (`incremental.py::_search`),
   O(t) per byte, instead of O(1) via an Aho–Corasick automaton
   (Section 5.2).
2. **Finding theta(sc) among candidates** is done by checking every
   candidate independently via a direct ancestor-walk implementation of
   Definition 4.1 (`incremental.py::_satisfies_condition`), O(depth) per
   check, instead of O(log t) via the DFS-interval + Centroid
   Decomposition machinery (Sections 4.3, 5.3). Worst case this is
   O(t · depth) per byte, not the paper's O(log²t).
3. **Byte-level atomicity only** (`normalize.py`) — the reference
   implementation's UTF-8-codepoint-level mode is not ported. This
   matches how real byte-level BPE tokenizers (GPT-style, CodeLlama,
   tiktoken encodings) actually work, so it's sufficient for Claim 3.
4. **No properization** (Appendix A) — dictionaries that need
   SentencePiece-semantics reconciliation (e.g. Gemma-3's tokenizer,
   per the paper's own Appendix A.6 finding) will have some tokens
   correctly detected as non-canonical rather than repaired. Needed
   before Claim 3 can use arbitrary real tokenizer vocabularies as-is.
5. **No eager output** (Section 6) yet — Claim 2's algorithm-design
   description is only partially reproduced (the incremental search,
   not the streaming-emission half).

None of this is a shortcut taken silently — each gap is exactly what's
still needed to move from "the algorithm is structurally correct" (this
implementation, now) to "the algorithm is also this fast" (needed for
Claims 3–4, not yet attempted). Closing gaps 1–2 is the next planned
step in Phase 4, before Phase 5 (benchmarking).

## Verification approach

Every claim of correctness here is backed by a test, not by inspection:

- **`tests/test_oracle.py`** — the oracle itself, checked against the
  hand-verified Phase 2 example and the paper's own Appendix A.6
  non-properizable-dictionary example.
- **`tests/test_normalize.py`**, **`tests/test_successor_forest.py`** —
  checked against the exact structure recovered from the reference
  implementation's own test suite in Phase 3 (see
  `../../papers/incremental-bpe-tokenization/paper/implementation-notes.md`).
- **`tests/test_incremental.py`**:
  - Exact reproduction of the real θ-traces captured by running the
    reference implementation's own tests (`cargo test ... -- --nocapture`,
    Phase 3) — the strongest test, since it's checked against the paper
    authors' own code, not just our own oracle.
  - 200 randomized differential tests against the from-scratch oracle,
    across randomly generated small dictionaries and strings.
  - The paper's own repeated-character pathological-input family
    (Section 7.2 / Appendix H.2), across several rule sets that build
    deep merge chains.
  - Every single one of the above also runs with `verify_monotonic=True`,
    which empirically checks Theorem 4.2 / Claim 1's Upward Closure on
    every byte fed, not just the final answer — i.e., every test doubles
    as a Theorem 4.2 stress test.

## Running the tests

```bash
cd experiments/incremental-bpe-tokenization
PYTHONPATH=. python3 -m unittest discover -v -s tests
```

Requires only the Python 3 standard library (no third-party
dependencies). Developed and tested against Python 3.11.15 in this
sandbox; the project's stated target is Python 3.12 — no known
3.12-incompatible constructs are used, but this has not been separately
confirmed on 3.12.

## Why a fresh implementation, not a port

Per this repository's rules: reproducing the reference implementation's
*code* would just mean running the authors' work again, not
independently verifying it. Where this implementation diverges from the
reference (e.g. no DFS-interval trick yet, oracle-based canonicity
instead of the reference's incremental bookkeeping), that's recorded
above so any behavioral difference is traceable to a specific, known
scoping decision rather than an accidental deviation.
