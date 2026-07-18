# Claim 2 — Algorithm Design (Aho–Corasick + Centroid Decomposition + Eager Output)

**Status:** ◐ in progress — all three named mechanisms now exist and are
tested (Aho–Corasick, tree navigation, eager output), but tree navigation
is not yet the specific Centroid-Decomposition/O(1)-interval mechanism
the claim describes, and eager output is not yet its specific O(1)-
amortized two-pointer mechanism — see Implementation below. This claim
cannot be marked verified until the *mechanisms*, not just the
*results*, match.

## Claim statement

> The incremental algorithm combines an Aho–Corasick automaton for search-
> space identification with centroid decomposition for tree navigation,
> plus an eager output mechanism for emitting completed tokens.
>
> — Sections 5 (Incremental Algorithm) and 6 (Eager Output)

Concretely, three separate mechanisms are claimed to compose correctly:

1. An Aho–Corasick automaton over the vocabulary identifies τ(sc), the
   longest suffix token of the string-so-far, in O(1) per new character
   (Section 5.2), using a square-root tiled transition table (Appendix F).
2. A precomputed **Centroid Search Tree** per canonical token lets the
   algorithm find the deepest node on the (Claim 1) monotonic path in
   O(log²t) rather than walking the path linearly (Section 5.3).
3. An **eager output** mechanism (Section 6) tracks a sliding "active
   frontier" of parental candidates and emits tokens once they become
   provably stable — with amortized O(1) overhead per byte (Appendix G).

## Explanation

Full write-up in
[`../../paper/theory-notes.md`](../../paper/theory-notes.md) §§6–9.
Summary: Aho–Corasick gives the longest currently-recognized vocabulary
suffix in O(1) per character (a well-known technique, correctly applied —
not this paper's novel contribution); Centroid Decomposition is what
turns "walk down a possibly `t`-deep Suffix-Successor Tree" into
"O(log t) branching decisions, each an O(log t) sibling binary search,"
giving O(log²t); eager output tracks a shrinking-only window of
"parental candidates" bounded by the automaton's current match depth, and
emits a token permanently once it's outside every live candidate's reach.

## Mathematics

See `../../paper/theory-notes.md` §7 for the plain-language derivation of
why O(log t) × O(log t) = O(log²t) (CST height × sibling binary search),
and §9 for why eager output's overhead is amortized O(1)/byte (each
Prefix-Tree-of-Tokens node enters and leaves the tracked window at most
once). Not yet independently re-derived against the paper's own Appendix G
line-by-line — flagged as the same kind of "verify by testing, not just
by reading" concern as Claim 1, since amortized arguments are exactly
where subtle correctness bugs hide, and eager output is the one place in
this paper that hasn't yet been reduced to a single hand-checked numeric
example the way Claim 1's tree search has.

## Implementation

**Built now** (`experiments/incremental-bpe-tokenization/incbpe/`):

- `aho_corasick.py` — a genuine Aho–Corasick automaton (trie + failure
  links + per-state longest-recognized-token, classic construction),
  giving τ(sc) in O(1) amortized per byte. Not yet the reference's
  eagerly-precomputed square-root-tiled transition table (Appendix F) —
  that's a memory/engineering optimization on top of the same automaton,
  not a different mechanism, and not needed for correctness.
- `incremental.py::_search_tree_walk` — replaces the original length-
  scanning search with a genuine top-down walk of the Successor Forest:
  starts at the atomic root for the new byte, descends into whichever
  child (at most one, per Theorem 4.2's mutual-exclusion corollary)
  still satisfies Definition 4.1, stops when none does. This is real
  tree navigation, cross-checked against τ(sc) (must never exceed it)
  and against the original length-scanning search on every single test
  run — but the per-node check is still an O(depth) ancestor walk
  (`_satisfies_condition`), not the paper's O(1) DFS-interval test, and
  there is no Centroid Search Tree — so it's not yet O(log²t) on a
  deliberately deep, narrow dictionary (Appendix J's adversarial
  construction).
- `eager.py` — a working eager-output implementation, built directly
  from Section 6.1's definition (gather every live candidate's full
  backtrack chain, take their longest common prefix) rather than
  Section 6.2's incremental two-pointer bookkeeping. Correct (see
  Experiment), but recomputes from scratch each byte rather than being
  O(1) amortized.

**Still not built:** the DFS-interval O(1) test and Centroid
Decomposition (§4.3, §5.3) — the one substantive remaining gap, flagged
consistently across this repository rather than silently dropped.

## Experiment

- `tests/test_aho_corasick.py` — automaton output checked against a
  brute-force "longest matching vocab suffix" scan, on the recovered
  Figure-2-variant example and 100 randomized dictionaries.
- `tests/test_incremental.py` — as before (200 random dictionaries, the
  repeated-character family, real reference-implementation traces),
  now *also* asserting on every byte that the tree-walk search agrees
  with the original length-scanning search and that θ(sc) never exceeds
  τ(sc) from the automaton.
- `tests/test_eager.py` — concatenating every eagerly-emitted token
  (plus a final flush) exactly reproduces the non-eager tokenization,
  checked across the same three test families.

All of the above pass. "Same tokenization result, faster" is now true
for the search (real tree navigation replacing brute-force length
scanning) and eager output now exists and is verified — what's not yet
true is "as fast as the paper's specific claimed complexity," which
needs Centroid Decomposition.

## Benchmark

Per-mechanism microbenchmarks (automaton transition cost, CST traversal
depth vs. tree size, eager-output overhead vs. non-eager) — separate from
the end-to-end throughput numbers in Claim 3, per the paper's own
Table 5 breakdown (they report eager output separately, ~10% overhead).

## Result

*(Phase 6 — to be written. No fabricated numbers.)*

## Discussion

*(Phase 6 — to be written.)*

## Limitations

*(Phase 6 — to be written.)*

## Conclusion

*(Phase 6 — to be written.)*

---

> **Inference X-Ray candidate:** Yes, strongly, on two separate fronts:
> (1) Aho–Corasick automata are broadly useful beyond tokenization and are
> rarely explained well ("multi-pattern matching in one pass"); (2) the
> eager-output / streaming-emission idea generalizes to *any* incremental
> parser feeding a model that wants to start consuming tokens before the
> full input is seen — directly relevant to Inference X-Ray's inference-
> pipeline framing. Two candidate chapters, not one.
