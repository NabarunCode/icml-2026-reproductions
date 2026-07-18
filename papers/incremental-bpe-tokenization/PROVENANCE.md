# Provenance — Incremental BPE Tokenization reproduction

Scientific-integrity record: for every first-party source file in this
paper's reproduction, where it came from — an independent implementation
derived from the paper, or something influenced by the official
implementation ([ModelTC/mtc-inc-bpe](https://github.com/ModelTC/mtc-inc-bpe),
Rust, MIT OR Apache-2.0, pinned as a submodule at tag `v0.9.1` under
[`references/mtc-inc-bpe`](references/)). This distinction is never
blurred: an independent reproduction verifies the paper; re-running the
authors' code only verifies their build system.

## Classification key

- **A — Independent implementation.** Written from the paper's own
  definitions (and, where noted, from classic literature). Not
  translated from the reference code.
- **B — Reference-derived.** Content taken from or shaped by the
  official implementation (code or data), documented explicitly.

## The honest global caveat, stated up front

Phase 3 of our workflow deliberately studied the reference
implementation's **architecture** before any reproduction code was
written: [`notes/implementation-notes.md`](notes/implementation-notes.md)
maps the paper's sections to the reference's modules (`inc_bpe.rs`,
`suf_suc.rs`, `centroid.rs`, ...), and the reference's test suite was
*executed* (`cargo test -- --nocapture`) to capture ground-truth traces.
No function was translated line-by-line, and the Python code was written
from the paper with the reference closed — but because its structure was
studied first, this is **not a clean-room reproduction in the strict
legal/engineering sense**, and we do not claim that. What we claim, and
document below, is: independent implementation of every algorithm, with
the reference used as (a) an architectural map and (b) a source of
ground-truth *test data*.

Two facts corroborate independence at the algorithm level:

1. This implementation contains **deliberate divergences** from the
   reference (oracle-based canonicity instead of incremental
   bookkeeping; no square-root-tiled transition table; definition-first
   eager output) — a port would have none.
2. Centroid Decomposition (§5.3) is **absent**: reading the reference's
   `centroid.rs` was not enough to reconstruct its remainder-handling
   with confidence, so rather than transcribing code we did not fully
   understand, the gap is documented openly
   ([`experiments/README.md`](experiments/README.md), Limitations).
   An implementation that was actually a port could not have this gap.

## Per-file classification — `experiments/incbpe/`

| File | Class | Derivation |
|---|---|---|
| `vocab.py` | **A** | Token/vocabulary containers from §3.1. Plain data structures. |
| `dictionary.py` | **A** | Ordered merge-rule list from §3.1; field names (`pre`, `suc`) follow the **paper's** §3.3 notation, not the reference's. |
| `oracle.py` | **A** | From-scratch standard BPE per the paper's Eq. 1. This is the ground-truth definition everything else is differentially tested against — it must be independent for those tests to mean anything, and it is. |
| `normalize.py` | **A** (deliberate divergence) | Canonical-token detection from §3.3, implemented *via the oracle* ("is this token producible from its own string?"), an intentionally different mechanism from the reference's incremental bookkeeping. Byte-level atomicity only; the reference's UTF-8 mode is not ported. |
| `successor_forest.py` | **A** | Built from §3.4's definition (parent = `suc(t)` from the merge-rule decomposition). Resulting structure *validated against* the forest recovered by running the reference's tests — validation against outputs, not derivation from code. |
| `aho_corasick.py` | **A** (classic literature) | Textbook Aho–Corasick (Aho & Corasick, 1975): trie + BFS failure links + lazy failure-walk transitions. Derived from the classic algorithm, not from the paper's Appendix F engineering (no square-root-tiled table) and not from the reference's automaton code. |
| `dfs_interval.py` | **A** | §4.3's DFS linearization + valid-interval test. The three-case interval derivation was worked out independently — including an initially *wrong* derivation, caught and corrected by our own exhaustive differential tests (commit d03293c), not by consulting the reference. |
| `incremental.py` | **A** | Definition 4.1 / Theorem 4.2 search, three cross-checked strategies. The §5.3 centroid balancing is deliberately absent (see caveat above). |
| `eager.py` | **A** (deliberate divergence) | §6.1's *definition* implemented directly (longest common prefix of live candidates' backtrack chains) rather than §6.2's two-pointer mechanism. Correct but not O(1)-amortized; documented in Limitations. |
| `fast_bpe.py` | **A** (classic literature) | The standard dynamic-priority (SentencePiece/HF-style) merge loop, from the well-known algorithm — not from this paper's reference implementation. Its semantic difference from the fixed-schedule oracle is documented in the module docstring and pinned by differential tests; used only where validated (proper dictionaries). |
| `gpt2.py` | **A** (with one classic-code-derived table) | Loader for real GPT-2 vocab files. `bytes_to_unicode` reimplements the standard byte<->unicode bijection published in OpenAI's MIT-licensed GPT-2 code (the mapping is a fixed, well-known constant); everything else written for this reproduction. The data files it loads are third-party (see `benchmarks/data/README.md`). |
| `fixtures.py` | **B — reference-derived data** | The Figure-2-variant vocabulary and 13-rule list were recovered **verbatim** from the reference implementation's own test suite, and the expected θ-traces in `tests/test_incremental.py` were captured by *running* those tests (`cargo test ... -- --nocapture`). This is test **data**, not algorithm code, taken from MIT/Apache-2.0-licensed material with attribution in the file docstring and full recovery procedure in [`notes/implementation-notes.md`](notes/implementation-notes.md). It is our strongest ground truth precisely *because* it comes from the authors' code — and it is the only reference-derived content in the package. |

## Per-file classification — `experiments/tests/`

All test files are **A** (written for this reproduction), with one
qualification: `test_incremental.py` and `test_successor_forest.py`
assert against the reference-derived ground-truth data described above
(class B data used as expected values — that is the point of them).
`test_oracle.py` additionally checks the paper's own worked examples,
including the Appendix A.6 non-properizable dictionary.

## Shared infrastructure — `src/repro_core/`

**A**, and paper-agnostic: environment capture and the benchmark runner
have no relationship to this paper or its reference implementation.

## Licensing

- First-party code: MIT (repository `LICENSE`).
- Reference implementation: included **only** as a pinned git submodule;
  retains its own MIT OR Apache-2.0 license; never copied into the tree.
- Reference-derived fixture data (above): reproduced under those same
  permissive licenses, with attribution.

## Maintenance rule

Any future file that adapts, transcribes, or is structurally guided by
reference code **must** be added to the table above as class B *before*
it lands, per `CONTRIBUTING.md` rule 5. In particular: if Centroid
Decomposition is eventually implemented by following `centroid.rs`
closely rather than re-deriving from §5.3 + Appendix E, it will be
classified B with the specific borrowed mechanism named.
