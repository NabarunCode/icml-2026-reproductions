# Incremental BPE Tokenization — Python Reproduction

Independent Python reimplementation of the core incremental algorithm
from *Incremental BPE Tokenization* (Jiang & Gong, ICML 2026). This is
**not** a port of the official Rust crate (`ModelTC/mtc-inc-bpe`, vendored
at `../references/mtc-inc-bpe` for
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
| Aho–Corasick automaton | `incbpe/aho_corasick.py` | §5.2 | Done — O(1)-amortized longest-suffix lookup; used as a cross-check (see Limitations) |
| DFS linearization + O(1) valid-interval test | `incbpe/dfs_interval.py` | §4.3 | Done — includes the "Mutual Exclusion among Siblings" property, independently verified (see Verification) |
| Incremental theta(s) search | `incbpe/incremental.py` | §4 (Def. 4.1, Thm. 4.2), §5.1, §5.3 (partial) | Done, **O(depth) levels, O(1) per level; not yet centroid-balanced** (see Limitations) |
| Eager output | `incbpe/eager.py` | §6 | Done, **definition-first, not yet the O(1)-amortized two-pointer mechanism** (see Limitations) |
| Centroid Decomposition | — | §5.3 | **Not implemented yet** — the one remaining named mechanism from Claim 2 |
| Appendix A properization | — | Appendix A | **Not implemented yet** |

## Limitations (explicit, not silent)

This is still a **correctness-first** implementation, though the gap to
the paper's full complexity bound has narrowed to one specific,
well-understood piece:

1. **Finding theta(sc)** (`_search_binary_walk`, the primary search used
   by `feed()`) is a top-down walk of the Successor Forest that, at each
   *level*, finds the one valid child (if any) via the O(1) DFS-interval
   test plus an O(log branching-factor) binary search over pre-sorted,
   provably-disjoint sibling intervals (`dfs_interval.py`) — this part
   now matches the paper's own per-node mechanism (§4.3, §5.3's
   binary-search step). What's still missing is bounding the *number of
   levels* visited: nothing yet rebalances the raw Successor Forest into
   an O(log t)-height Centroid Search Tree, so a deliberately deep,
   narrow-branching dictionary (Appendix J's adversarial construction,
   depth ~t) would still cost close to O(t) here, not O(log²t). This was
   investigated during development - the reference implementation's
   specific centroid-removal mechanism (recursively re-decomposing the
   "remainder" left after each centroid extraction) proved intricate
   enough that implementing a plausible-but-unverified version seemed
   worse than leaving it as a precisely-scoped follow-up. Two older,
   slower search strategies (`_search_tree_walk`, `_search_by_length`)
   are kept specifically so `_search_binary_walk` can be continuously
   cross-checked against them - not dead code.
2. **A subtle correctness question resolved during this work, worth
   recording:** `_search_binary_walk` does *not* pre-filter candidate
   children by whether they're literally a string-suffix of the current
   buffer (unlike `_search_tree_walk`, which does). This is safe only
   because Appendix E's Claim 4 (the answer node has no child satisfying
   Definition 4.1) is proved for *every* forest child, not just
   buffer-matching ones - confirmed empirically here, not just assumed,
   by cross-checking both search strategies against each other on every
   byte across hundreds of test dictionaries.
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
also this fast in the worst case" (needed for Claims 3–4, not yet
attempted). Closing gap 1 (Centroid Decomposition specifically) is the
next planned step in Phase 4, before Phase 5 (benchmarking) can honestly
begin at adversarial scale — though ordinary-case benchmarking (Claim 3,
and possibly Claim 4's specific repeated-character test, which produces
a *wide, shallow* tree per the Phase 2 finding, not a deep one) may
already be meaningful with what exists now.

## Verification approach

Every claim of correctness here is backed by a test, not by inspection:

- **`tests/test_oracle.py`** — the oracle itself, checked against the
  hand-verified Phase 2 example and the paper's own Appendix A.6
  non-properizable-dictionary example.
- **`tests/test_normalize.py`**, **`tests/test_successor_forest.py`** —
  checked against the exact structure recovered from the reference
  implementation's own test suite in Phase 3 (see
  `../notes/implementation-notes.md`).
- **`tests/test_aho_corasick.py`** — the automaton checked against a
  brute-force "longest matching vocab suffix" scanner, on the recovered
  Figure-2-variant example and 100 randomized dictionaries.
- **`tests/test_dfs_interval.py`** — the O(1) interval test checked
  against the ancestor-walk oracle across *every possible* (candidate,
  history-value) pair, not just ones that arise in one run; the binary
  search (`find_valid_child`) separately checked against a plain linear
  scan using that same interval test, on the same exhaustive space.
- **`tests/test_sibling_disjointness.py`** — the paper's own "Mutual
  Exclusion among Siblings" corollary (Section 4.3), checked directly:
  every forest node's children have pairwise-disjoint valid intervals,
  across the Figure-2-variant example and 200 randomized dictionaries.
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
    binary-search walk against the plain tree walk *and* against the
    original length-scanning search (both kept specifically as reference
    oracles for this), and (c) asserts theta(sc) is never longer than
    tau(sc) from the Aho–Corasick automaton.
- **`tests/test_eager.py`** — concatenating every eagerly-emitted token
  (plus a final `finish()` flush) must exactly reproduce the non-eager
  `tokens()` output, checked on the same three test families above.

## Running the tests

From the repository root (this package is a uv-workspace member and is
installed by `uv sync --all-packages`):

```bash
uv run pytest papers/incremental-bpe-tokenization/experiments/tests
# or simply `uv run pytest` to run the whole repository
```

The `incbpe` package itself requires only the Python standard library
(no third-party runtime dependencies); pytest is a dev-only dependency.
CI runs the suite on Python 3.11 and 3.12.

## Why a fresh implementation, not a port

Per this repository's rules: reproducing the reference implementation's
*code* would just mean running the authors' work again, not
independently verifying it. Where this implementation diverges from the
reference (e.g. no DFS-interval trick yet, oracle-based canonicity
instead of the reference's incremental bookkeeping), that's recorded
above so any behavioral difference is traceable to a specific, known
scoping decision rather than an accidental deviation.
