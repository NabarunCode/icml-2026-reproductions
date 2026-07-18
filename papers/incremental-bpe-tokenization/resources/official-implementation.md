# Official Implementation Notes

**Repository:** [github.com/ModelTC/mtc-inc-bpe](https://github.com/ModelTC/mtc-inc-bpe)
**Vendored at:** [`../reference/mtc-inc-bpe`](../reference/mtc-inc-bpe) (git
submodule, pinned to tag `v0.9.1`, commit `0152526`)
**Language:** Rust (edition 2024)
**License:** dual MIT / Apache-2.0 — permissive, reference use and
comparison are unambiguously fine.
**Published:** also distributed as the `mtc-inc-bpe` crate on crates.io,
with docs on docs.rs.

## Why a submodule, not a copy

The repo is pinned by commit so our reproduction always compares against a
fixed, citable version of the reference code, without vendoring (and
silently drifting from) its source. Update the pin deliberately, with a
note in this file, if a newer release becomes relevant.

## Module map (for Phase 3)

Observed structure at `v0.9.1` (not yet annotated with paper section
correspondences — that's Phase 3 work):

```
src/
  lib.rs                    # crate entry point
  dict.rs                   # merge-rule dictionary, likely §3.1/§3.3 (normalization)
  normalize.rs               # dictionary normalization — likely §3.3 / Appendix A (properizing)
  vocab.rs                   # vocabulary representation
  successor.rs                # Successor Forest — §3.4
  suf_suc.rs                  # Suffix-Successor Tree — §3.5
  centroid.rs                 # Centroid Decomposition / Centroid Search Tree — §5.3
  eager.rs                    # Eager Output mechanism — §6
  inc_bpe.rs                  # top-level incremental algorithm, ties the above together — §5.1
  typed_vec.rs                 # utility
  aho_corasick/               # Aho–Corasick automaton — §5.2
    automaton.rs
    heavy_light.rs             # possibly related to the Suffix-Successor Tree's heavy path structure
    index.rs
    relabeling.rs               # likely the DFS linearization of §4.3
    suf_link_tree.rs
    trans.rs                    # likely the square-root tiled transition table — Appendix F
    trie.rs
  sp_impl/
    bpe.rs                      # reference/baseline BPE implementation for correctness checks
    heap.rs                      # heap-based baseline (standard priority-queue BPE), for correctness cross-checks
tools/
  properize.py                 # Python tool implementing dictionary properization (Appendix A) — worth reading before we reimplement properization ourselves
```

This mapping is a first-pass guess from filenames only; it has **not**
been verified by reading the code line-by-line. Phase 3 will replace this
table with a verified mapping (file/function → paper section/theorem),
and correct anything wrong here.

## What we will NOT do

We will not import or wrap this Rust crate as our "reproduction" — that
would just be running the authors' code, not reproducing their result. It
is reference ground truth for correctness cross-checks (e.g., differential
testing: our reimplementation vs. this crate on the same inputs) and for
understanding design decisions, per Phase 3.
