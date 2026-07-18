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
| Successor Forest (parent + children) | `incbpe/successor_forest.py` | §3.4 | Done |
| Aho–Corasick automaton | `incbpe/aho_corasick.py` | §5.2 | Done — O(1)-amortized longest-suffix lookup; not yet wired as the search's own starting point (see Limitations) |
| Incremental theta(s) search | `incbpe/incremental.py` | §4 (Def. 4.1, Thm. 4.2), §5.1, §5.3 (partial) | Done, **tree-walk, not yet centroid-decomposed** (see Limitations) |
| Eager output | `incbpe/eager.py` | §6 | Done, **definition-first, not yet the O(1)-amortized two-pointer mechanism** (see Limitations) |
| Centroid Decomposition / DFS-interval O(1) test | — | §4.3, §5.3 | **Not implemented yet** |
| Appendix A properization | — | Appendix A | **Not implemented yet** |

## Limitations (explicit, not silent)

This is still a **correctness-first** implementation. Every mechanism
Claim 2 names now exists (Aho–Corasick, tree navigation, eager output),
but none has yet received the paper's specific O(1)/O(log t) speedup —
that's the one substantive gap left before Claims 3–4 (performance) can
be benchmarked at realistic or adversarial scale:

1. **Aho–Corasick gives tau(sc) in O(1) amortized** (`aho_corasick.py`),
   and is used as a cross-check (theta(sc) can never be longer than
   tau(sc), asserted on every byte when `verify_monotonic=True`) — but
   the search itself (`incremental.py::_search_tree_walk`) doesn't yet
   use it as its own starting point; it starts from the atomic root and
   walks down instead.
2. **Finding theta(sc) is a top-down tree walk**
   (`_search_tree_walk`), visiting real Successor Forest descendants of
   the root and checking each candidate child directly against
   Definition 4.1 (an O(depth) ancestor-walk check per node,
   `_satisfies_condition`), rather than the paper's O(1) DFS-interval
   test navigated via an O(log t)-height Centroid Search Tree (§4.3,
   §5.3). This is faster than the original length-scanning approach
   (only visits actual tree nodes, not every possible string length),
   but is not yet O(log²t) in the worst case — a maximally deep,
   narrow-branching dictionary (like Appendix J's adversarial
   construction) would still cost close to O(depth) per byte here.
3. **Eager output recomputes the common ancestral path directly from
   its definition** (`eager.py`) — gather every candidate's full
   backtrack chain and take their longest common prefix — rather than
   maintaining Section 6.2's two-pointer Active Frontier incrementally.
   Correct (verified against non-eager output on every test), but
   O(window size × chain length) per byte, not O(1) amortized.
4. **Byte-level atomicity only** (`normalize.py`) — the reference
   implementation's UTF-8-codepoint-level mode is not ported. This
   matches how real byte-level BPE tokenizers (GPT-style, CodeLlama,
   tiktoken encodings) actually work, so it's sufficient for Claim 3.
5. **No properization** (Appendix A) — dictionaries that need
   SentencePiece-semantics reconciliation (e.g. Gemma-3's tokenizer,
   per the paper's own Appendix A.6 finding) will have some tokens
   correctly detected as non-canonical rather than repaired. Needed
   before Claim 3 can use arbitrary real tokenizer vocabularies as-is.

None of this is a shortcut taken silently — each gap is exactly what's
still needed to move from "the algorithm is structurally and
mechanistically correct" (this implementation, now) to "the algorithm is
also this fast" (needed for Claims 3–4, not yet attempted). Closing gap 2
(Centroid Decomposition) is the next planned step in Phase 4, before
Phase 5 (benchmarking) can honestly begin.

## Verification approach

Every claim of correctness here is backed by a test, not by inspection:

- **`tests/test_oracle.py`** — the oracle itself, checked against the
  hand-verified Phase 2 example and the paper's own Appendix A.6
  non-properizable-dictionary example.
- **`tests/test_normalize.py`**, **`tests/test_successor_forest.py`** —
  checked against the exact structure recovered from the reference
  implementation's own test suite in Phase 3 (see
  `../../papers/incremental-bpe-tokenization/paper/implementation-notes.md`).
- **`tests/test_aho_corasick.py`** — the automaton checked against a
  brute-force "longest matching vocab suffix" scanner, on the recovered
  Figure-2-variant example and 100 randomized dictionaries.
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
    which — on every byte fed, not just the final answer — (a) empirically
    checks Theorem 4.2 / Claim 1's Upward Closure, (b) cross-checks the
    tree-walk search against the original length-scanning search (kept
    specifically as a reference oracle for this), and (c) asserts
    theta(sc) is never longer than tau(sc) from the Aho–Corasick
    automaton.
- **`tests/test_eager.py`** — concatenating every eagerly-emitted token
  (plus a final `finish()` flush) must exactly reproduce the non-eager
  `tokens()` output, checked on the same three test families above.

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
