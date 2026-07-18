# Official Implementation Notes

**Repository:** [github.com/ModelTC/mtc-inc-bpe](https://github.com/ModelTC/mtc-inc-bpe)
**Vendored at:** [`mtc-inc-bpe`](mtc-inc-bpe) (git
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

## Module map — verified (Phase 3 complete)

Full verified mapping, with how each row was checked, is in
[`../notes/implementation-notes.md`](../notes/implementation-notes.md).
Condensed version:

```
src/
  lib.rs                    # crate entry point / public API surface
  dict.rs                   # §3.1 dictionary D (ordered Rule list)
  normalize.rs               # §3.3 normalization + Appendix A (properizing);
                              # NormalizedDictBuildError::ImproperDict = the
                              # Appendix A.6 non-properizable-dictionary detector
  vocab.rs                   # §3.1 vocabulary V
  successor.rs                # §3.4 Successor Forest (verified against real
                              # Figure-2-variant data, see implementation-notes.md)
  suf_suc.rs                  # §3.5 Suffix-Successor Tree + §4.3 DFS
                              # linearization / valid-interval computation
  centroid.rs                 # §5.3 Centroid Decomposition / Centroid Search Tree
  eager.rs                    # §6 Eager Output (Active Frontier, two-pointer alg.)
  inc_bpe.rs                  # §5.1 top-level incremental algorithm
  typed_vec.rs                 # generic infra, no paper correspondence
  aho_corasick/               # §5.2 Aho-Corasick automaton
    automaton.rs               # classic AC construction (BFS + failure links)
    heavy_light.rs             # NOT named in the paper text — heavy-light
                              # decomposition used only to relabel trie nodes
                              # for cache locality before the transition table
    index.rs                   # ACNodeId newtype
    relabeling.rs               # generic node-relabeling utility
    suf_link_tree.rs            # suffix links as a navigable parent->children tree
    trans.rs                    # Appendix F square-root tiled transition table
                              # (byte -> 4-bit/4-bit tile split, 16x16=256)
    trie.rs                     # plain trie storage
  sp_impl/
    bpe.rs, heap.rs             # NOT the incremental contribution — a from-scratch
                              # heap-based BPE oracle used internally by the
                              # crate's own tests for correctness cross-checks
tools/
  properize.py                 # Python properization tool (Appendix A) — not yet read
```

**Bonus finding:** the reference implementation's test suite
(`successor.rs`, `suf_suc.rs`, `centroid.rs`, `inc_bpe.rs`, `eager.rs`)
preserves (a 13-of-14-rule variant of) the paper's own Figure 2 worked
example as a regression test fixture. Running it
(`cargo test --lib <module>::tests::<test> -- --nocapture`) gave us
authoritative ground truth for the Successor Forest structure and several
concrete θ-traces — see `implementation-notes.md` for the full
reconstruction and cross-check against our own Phase 2 theory.

## What we will NOT do

We will not import or wrap this Rust crate as our "reproduction" — that
would just be running the authors' code, not reproducing their result. It
is reference ground truth for correctness cross-checks (e.g., differential
testing: our reimplementation vs. this crate on the same inputs) and for
understanding design decisions, per Phase 3.
