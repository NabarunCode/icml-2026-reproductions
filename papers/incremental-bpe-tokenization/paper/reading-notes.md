# Phase 1 — Reading Notes

Faithful notes on what the paper actually says, organized by its own
section structure. This is deliberately **not yet interpreted or
explained** — that's Phase 2 (`docs/WORKFLOW.md`). Where the paper states
something precisely (a theorem, a complexity bound, a benchmark number),
it is quoted or restated close to verbatim with a page/section pointer, so
Phase 2 has an accurate anchor to build an explanation from.

Source: arXiv 2605.30813v1, with alphaXiv annotations (local copy:
`incremental-bpe-tokenization.pdf`).

## Abstract (p.1)

- Problem: standard BPE tokenizers (HF `tokenizers`, OpenAI `tiktoken`) are
  offline — they need the whole input observed before producing a
  tokenization, serializing tokenization and prefill in streaming/LLM
  inference.
- Contribution: an algorithm that maintains BPE tokenization incrementally,
  for every prefix, in worst-case **O(log²t)** per input byte, i.e.
  **O(n log²t)** overall (n = input length, t = max token length).
- Drop-in replacement, reported up to **~3×** speedup over HF `tokenizers`,
  and avoids `tiktoken`'s degradation on pathological inputs.
- Also introduces **eager output**: streaming emission of tokens as soon
  as their boundaries are determined.
- Code: https://github.com/ModelTC/mtc-inc-bpe (vendored as our submodule).

## 1. Introduction (pp.1–2)

- BPE (Gage 1994, adapted to NLP by Sennrich et al. 2016) is the de facto
  LLM tokenization method.
- Figure 1's pipeline: Raw Text → Special-Token Splitting → Normalization
  (NFC, …) → Pre-Tokenization (Regex, …) → BPE Tokenization (per chunk).
  **The paper's scope is explicitly only the BPE stage** — it does not
  touch normalization or pre-tokenization, and states this pipeline
  framing up front.
- Existing implementations use heap-based priority queues (global,
  offline). Berglund & van der Merwe (2023) formalize BPE and show
  prefix tokenizations form a prefix tree — a structural fact this paper
  exploits but which the cited prior work doesn't turn into an algorithm.
- Contributions (paper's own bullet list, p.2):
  1. Incremental BPE algorithm, strict worst-case O(log²t) per byte,
     exactly equivalent to standard BPE.
  2. Eager output mechanism for real-time streaming/pipelining.
  3. Rust implementation, drop-in replacement, up to ~3× speedup.
  4. Claim that some traditional pipeline stages (that exist only to
     bound global BPE's cost) become unnecessary given this guarantee.
  5. Native support for "full-prefix" tasks (FIM, token healing) since all
     prefix tokenizations are maintained, not just the final one.

## 2. Related Work (p.2)

- BPE used by GPT-5, Qwen-3, etc.; alternatives WordPiece (BERT), Unigram
  (T5) exist but BPE dominates.
- HF `tokenizers`: general-purpose, priority-queue based. `tiktoken`:
  regex-based pre-segmentation to bound BPE cost, brittle on pathological
  input ("stack exhaustion" mentioned as a risk on very repetitive input).
- Berglund & van der Merwe (2023): formal BPE semantics, notes
  consistency under token-wise truncation — theoretical grounding this
  paper builds on, but "does not address the challenge of bounding the
  lookahead required for online updates."
- `bpe` crate in `rust-gems` (GitHub, discussed by van Antwerpen & Neubeck
  2024): existing incremental BPE using Aho–Corasick, **no formal
  worst-case guarantee** — this is the direct prior-art baseline compared
  in Appendix J.

## 3. Structural Foundations of Incremental BPE (pp.3–4)

Definitions, stated precisely because Phase 2/4 depend on exact wording:

- **Dictionary** D = ordered merge rules `[r1, ..., rm]`; rule priority =
  position in this list (r1 highest).
- **T_D(s)** = full BPE tokenization: `(T_rm ∘ ... ∘ T_r1)(φ0)`.
- **Note on semantics**: standard BPE (fixed priority schedule, this
  paper's definition) differs from **SentencePiece semantics** (dynamic
  priority queue, always takes the current global-max-priority pair).
  Appendix A ("Properizing") is entirely about reconciling this
  difference for dictionaries where it matters.
- **Lemma 3.1 (Prefix Consistency)**: for token sequence φ = T(s), any
  proper prefix µ of φ satisfies T(π(µ)) = µ. I.e. truncating a valid
  tokenization gives the valid tokenization of the truncated string.
  (Attributed to Berglund & van der Merwe 2023, Remark 3; independently
  proved in Appendix B.)
- **Last Token θ(s)** := last token in T(s). Recursive form:
  `T(s) = T(s_pre) ⊕ [θ(s)]`.
- **Prefix Tree of Tokens**: the tokenizations of all prefixes of s,
  connected via θ(·) backtracking, form a tree (with a virtual root for
  ε). Maintaining it explicitly is *not* required — backtracking via
  θ(·) suffices.
- **Incremental objective, stated precisely (p.3)**: given s' = sc (c a
  new appended character), find θ(s'), which lies in the intersection of
  suffixes of s' and the vocabulary V.
- **Normalization (§3.3)**: a token t is *canonical* if T_D(t) = [t].
  Normalized vocabulary V̄ = canonical tokens only; normalized dictionary
  D̄ = the specific merge rules producing them (a proven bijection).
  Appendix C shows T_D̄(s) ≡ T_D(s) — normalization changes nothing
  observable.
- **Predecessor/Successor**: for canonical non-atomic t produced by rule
  (x,y)→t, `pre(t) = x`, `suc(t) = y`. Both x, y are themselves canonical
  (closure property, Appendix C).
- **Successor Forest F_suc (§3.4)**: directed graph, edges
  `(u, suc(u))`. Acyclic (edges strictly shrink token length) → forest
  rooted at atomic tokens.
- **Suffix-Successor Tree (§3.5)**: for token t, `SufSucTree(t)` = the
  subgraph of F_suc induced by all canonical suffixes of t. Proven to be
  a single tree (not forest) rooted at t's unique atomic suffix.

## 4. The Monotonic Path Property (pp.4–7, proof in Appendix E)

- **Definition 4.1 (Prefix Last-Token Condition)**, exact statement: for
  non-empty s and suffix token t of s — atomic tokens always satisfy it;
  for non-atomic t, split on `s⁻suc(t)` (s with suc(t) removed) and
  require:
  1. **Reachability**: `θ(s⁻suc(t))` lies in `pre(t)`'s Successor-Forest
     subtree (or equals `pre(t)`).
  2. **Priority dominance**: if `θ(s⁻suc(t)) ≠ pre(t)`, letting u be the
     child of `pre(t)` on the ancestor path to `θ(s⁻suc(t))`, t's
     canonical rule must have strictly higher priority than u's.
- **Theorem 4.2 (Monotonic Path Property)**, exact statement: let k be
  the longest canonical suffix token of s, P the unique path from θ(s) to
  the root of `SufSucTree(k)`. A node t ∈ SufSucTree(k) satisfies the
  Prefix Last-Token Condition **iff** t lies on P.
- **§4.3 Linearization via DFS**: pre-order DFS over the Successor
  Forest gives `dfs_in`/`dfs_out` timestamps; children visited in
  increasing priority order. Membership in the "valid candidate set" C_t
  reduces to an **O(1) interval-membership test** `dfs_in(x) ∈ [L_t, R_t)`,
  with `L_t = dfs_in(pre(t))` and `R_t` = the first higher-or-equal-
  priority child's `dfs_in`, or `dfs_out(pre(t))` if none.
- **Mutual exclusion among siblings**: sibling nodes' valid intervals are
  provably disjoint — direct corollary of Theorem 4.2 — which is what
  lets the search algorithm (§5.3) pick a unique branch at each step.

## 5. Incremental Algorithm (pp.6–7)

- **Framework (§5.1)**: two-step search — (1) find `τ(sc)`, the longest
  suffix token, bounding the search to `SufSucTree(τ(sc))`; (2) find the
  deepest node on the (Theorem 4.2) valid path within that tree. Abstracts
  history access as `H(ℓ)` = last token of the prefix ℓ characters
  shorter than current.
- **§5.2 Aho–Corasick automaton**: maintained over V̄, annotated per-state
  with the deepest recognized vocabulary token (inherited via suffix
  links) so `τ(sc)` is O(1) to read off. Transition table stored via a
  **persistent square-root tiling** (Appendix F) for O(1) transitions
  with better memory than a full transition table.
- **§5.3 Centroid Decomposition**: precomputed **Centroid Search Tree
  (CST)** per canonical token τ, height O(log|τ|). Search descends the
  CST: at each centroid u, an O(1) interval check (via `H`) determines
  whether the valid path goes "up" (toward parent's component) or
  "down" (into a specific child's component, found via binary search
  over pre-sorted disjoint sibling intervals — O(log|τ|) per step,
  since intervals are disjoint per Theorem 4.2's corollary).
- **§5.4 Complexity**: automaton transition O(1); CST height
  O(log|τ|); per-node decision O(log|τ|) (binary search over ≤|τ|
  children) ⇒ **O(log²|τ|) per byte**, **O(n log²t) overall**.

## 6. Eager Output (pp.7–8, algorithm details in Appendix G)

- **§6.1 Active Frontier**: define `d(s)` = depth reached in the
  Aho–Corasick automaton by s (= length of longest recognized suffix).
  Any future token's parent must be `θ` of some prefix ending in
  `[|s|−d(s), |s|]` — the set of such θ's is the **Parental Candidates**
  `P`. Stable output = the common ancestral path shared by all of `P`.
- **§6.2 Maintenance**: `d(sc) ≤ d(s)+1` (automaton depth grows by at
  most 1 per char) ⇒ window start `|s|−d(s)` is monotonically
  non-decreasing ⇒ two-pointer algorithm suffices; candidates only
  "expire," never re-enter. Tokens emitted once all active paths converge
  to one child of the virtual root. Appendix G: amortized **O(1) per
  byte** overhead (each Prefix-Tree-of-Tokens node inserted/removed at
  most once).
- Explicitly stated trade-off: eager output adds real overhead (measured
  later at ~10%), so **non-eager is the default for the main benchmarks**
  unless eager output is specifically being measured.

## 7. Benchmarks (pp.7–9, full detail in Appendix H)

- **Setup (Appendix H.1)**: bare-metal server, Intel Xeon Platinum 8362 @
  2.80GHz, pinned to 1 NUMA node (32 physical cores, 128GB RAM), SMT/Turbo
  Boost/ASLR disabled, 30 parallel single-threaded worker processes,
  `mimalloc` global allocator, fixed hash seeds.
- **Datasets (Appendix H.2, Table 2)**: English & Chinese from Wikipedia
  (20231101 dump, strided sampling every 42nd/60th doc respectively, ~16.5M
  and ~16.3M bytes); Code from RedPajama's GitHub subset (~16.8M bytes,
  first 2,500 docs of a named file). Pathological inputs: 2^k repetitions
  of `'a'`.
- **Tokenizers (Appendix H.3, Tables 3–4)**: 9 HF `tokenizers` configs
  (CodeLlama, DeepSeek-3.2, Gemma-3†, GPT-OSS, Llama-3.1*, Llama-4,
  Mistral-3, Ouro, Qwen-3) and 4 `tiktoken` encodings (P50K, R50K, CL100K,
  O200K). † = improper/non-properizable dictionary (excluded from direct
  comparison in some contexts); * = properized dictionary.
- **Table 1 (main throughput result, "concat" setting)** — speedup factor
  (incremental ÷ baseline):
  - CodeLlama: **3.13×** (English), 1.10× (Chinese), 2.88× (Code) — no
    regex pre-tokenization, biggest win.
  - Qwen-3: 1.05× / 1.04× / 1.08×. Similar near-1.0× for most other
    regex-pre-tokenized HF models (DeepSeek-3.2, Ouro, Llama-3.1,
    GPT-OSS, Llama-4, Mistral-3) — several are actually *below* 1.0×
    on some datasets (e.g. DeepSeek-3.2 Chinese 0.93×).
  - `tiktoken`: English near/below 1.0× (0.96–0.99×); **Chinese 1.35–1.59×**
    (CL100K highest at 1.59×) — paper attributes this to Chinese getting
    coarser regex segmentation than English, exposing more of the
    original BPE bottleneck for the incremental method to fix.
- **§7.1 narrative**: three explicit regimes — "Absence of
  Pre-tokenization" (CodeLlama, biggest gains), "Coarse-Grained
  Segmentation" (Chinese + tiktoken, moderate gains), "Fine-Grained
  Segmentation" (English + most HF models, implementation constant
  factors dominate, sometimes slight *regression*).
- **§7.2 Pathological inputs (Figure 3)**: repeated-`'a'` inputs at
  increasing 2^k lengths; `tiktoken` shows visible O(n²)-consistent
  throughput decay; the incremental method's throughput stays flat.
  O200K specifically hits a **regex-stage error** before BPE at long
  enough inputs (paper's own footnote/annotation, not a bug we'd be
  introducing).
- **Eager output overhead**: ~10% throughput cost vs. non-eager,
  attributed to bookkeeping (Table 5 has the exact per-config numbers).
- **Appendix I profiling**: for HF `tokenizers` (Qwen-3, Code dataset),
  the BPE stage itself (`tokenize_without_cache`) is only **13.11%** of
  total runtime — normalization/pre-tokenization/result-construction
  dominate. For `tiktoken` (O200K, Code dataset), regex matching is
  **~80.25%** of CPU time, core BPE merge only **6.45%** — i.e. a >12×
  overhead from the pre-tokenization "guardrail" relative to the BPE
  stage it's protecting. This is the paper's evidentiary basis for its
  Future Work claim that pre-tokenization design deserves revisiting.

## 8. Future Work (p.9)

- States plainly that normalization and regex pre-tokenization remain
  offline-oriented and are often bottlenecks (per Appendix I profiling)
  even though BPE itself is now streaming-capable — framed as the next
  problem, explicitly **not** solved by this paper.

## 9. Conclusion / Impact Statement (p.9)

- Impact statement explicitly frames worst-case guarantees as mitigating
  "algorithmic complexity attacks (e.g., Denial-of-Service attacks
  triggered by carefully crafted input sequences)" — direct tie to Claim 4
  and a flagged Inference X-Ray angle.

## Appendices (index only — full read deferred to Phase 2/3 as needed)

| Appendix | Content |
|---|---|
| A | Properizing: standard-BPE vs. SentencePiece semantics, "Growing Tree," dependency graph + topological sort to reconcile them; non-properizable example: `[(aa,a),(a,a)]` on `"aaaa"` gives different results under the two semantics (`[aaa,a]` vs `[aa,aa]`) — **Gemma-3 is a real-world non-properizable tokenizer** found by the authors. |
| B | Proof of Lemma 3.1 (Prefix Consistency), by induction over merge steps, illustrated in Figure 4. |
| C | Normalization/equivalence details — canonical closure, `T_D̄(s) ≡ T_D(s)`. |
| D | Extended "boundary elimination" intuition for Theorem 4.2. |
| E | Full proof of Theorem 4.2 via four claims (upward closure, uniqueness, θ(s) satisfies the condition, θ(s) is maximal). |
| F | Square-root tiled transition table for the Aho–Corasick automaton — O(1) transitions, less memory than a dense table. |
| G | Eager output algorithm + amortized O(1)/byte proof. |
| H | Full experimental setup, datasets, tokenizer list, and the complete Table 5 (per-doc *and* concat evaluation, cache on/off) — more granular than the main-text Table 1. |
| I | perf/flamegraph profiling (Figures 5–7) — the pipeline-bottleneck evidence behind §8's Future Work claim. |
| J | **Direct comparison with `rust-gems`' `bpe` crate** (`encode_via_table`, `encode_via_backtracking`) — both O(nt²) worst case vs. this paper's O(n log²t); paper constructs an explicit adversarial input (merge depth K=4096 via 2-byte base alphabet) where their method takes **37ms** vs. **15.3s** / **23.9s** for the two `rust-gems` methods. Also gives space-complexity comparison and end-to-end benchmarks (Table 8, Figure 8) showing their method matching or beating both `rust-gems` methods across R50K/CL100K/O200K on all three datasets. |

## Things to carry into Phase 2 as explicit open questions

- The paper's own "best case" bound is Ω(n) (Table 6) — i.e. even in the
  best case, at least linear work is unavoidable per their own accounting.
  Phase 2 should explain *why* that floor exists, not just cite it.
- Appendix J's pathological construction (K=4096, base alphabet expanded
  to 2-byte pairs) is a stronger and more deliberately adversarial test
  than the simple repeated-`'a'` construction used for Figure 3 (Claim 4).
  Worth considering both when reproducing Claim 4, since they stress
  different things (regex-stage brittleness vs. BPE-merge-stage
  brittleness).
- Gemma-3's non-properizable dictionary (Appendix A.6) is a genuine
  real-world edge case the paper found, not a hypothetical — worth
  independently confirming during Phase 3/4 rather than taking on faith.
