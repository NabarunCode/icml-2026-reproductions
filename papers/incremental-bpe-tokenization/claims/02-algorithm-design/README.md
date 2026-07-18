# Claim 2 — Algorithm Design (Aho–Corasick + Centroid Decomposition + Eager Output)

**Status:** ◐ in progress — Aho–Corasick, the O(1) DFS-interval test
(with its "Mutual Exclusion among Siblings" precondition independently
verified), and eager output all exist and are tested. The single
remaining gap is now narrow and precise: Centroid Decomposition, which
bounds the *number of tree levels* visited to O(log t) — everything else
(the O(1) per-level test, the O(log branching) binary search over
siblings) already matches the paper's mechanism. Eager output is also
not yet its specific O(1)-amortized two-pointer mechanism. This claim
cannot be marked verified until Centroid Decomposition closes that gap.

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
[`../../notes/theory-notes.md`](../../notes/theory-notes.md) §§6–9.
Summary: Aho–Corasick gives the longest currently-recognized vocabulary
suffix in O(1) per character (a well-known technique, correctly applied —
not this paper's novel contribution); Centroid Decomposition is what
turns "walk down a possibly `t`-deep Suffix-Successor Tree" into
"O(log t) branching decisions, each an O(log t) sibling binary search,"
giving O(log²t); eager output tracks a shrinking-only window of
"parental candidates" bounded by the automaton's current match depth, and
emits a token permanently once it's outside every live candidate's reach.

## Mathematics

See `../../notes/theory-notes.md` §7 for the plain-language derivation of
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

**Built now** (`../../experiments/incbpe/`):

- `aho_corasick.py` — a genuine Aho–Corasick automaton (trie + failure
  links + per-state longest-recognized-token, classic construction),
  giving τ(sc) in O(1) amortized per byte. Not yet the reference's
  eagerly-precomputed square-root-tiled transition table (Appendix F) —
  that's a memory/engineering optimization on top of the same automaton,
  not a different mechanism, and not needed for correctness.
- `dfs_interval.py` — the O(1) DFS-linearization valid-interval test
  (§4.3) exactly as described: pre-order DFS over the Successor Forest,
  children visited lowest-to-highest priority, each non-atomic
  canonical token's valid range computed from its own `pre()`'s sibling
  structure. Includes `find_valid_child`, a binary search over
  pre-sorted sibling intervals — sound specifically because of the
  paper's "Mutual Exclusion among Siblings" corollary, which is *not*
  just assumed here (see `tests/test_sibling_disjointness.py`).
- `incremental.py::_search_binary_walk` (now the primary search used by
  `feed()`) — walks the Successor Forest top-down, but finds the one
  valid child at each level via `find_valid_child` (O(1) test + O(log
  branching) binary search) instead of checking every child directly.
  This matches the paper's per-node mechanism; what it does *not* yet do
  is bound the *number of levels* to O(log t) — that requires Centroid
  Decomposition, which rebalances the raw (potentially O(t)-deep)
  Successor Forest into an O(log t)-height search tree. Investigated but
  not completed: the reference implementation's centroid-removal
  mechanism recursively re-decomposes the "remainder" left after
  extracting each centroid, and reconstructing that exactly (rather than
  a plausible-but-unverified approximation) needs more dedicated time
  than this pass had. A precisely-scoped follow-up, not a vague one.
- `eager.py` — a working eager-output implementation, built directly
  from Section 6.1's definition (gather every live candidate's full
  backtrack chain, take their longest common prefix) rather than
  Section 6.2's incremental two-pointer bookkeeping. Correct (see
  Experiment), but recomputes from scratch each byte rather than being
  O(1) amortized.

**Still not built:** Centroid Decomposition (§5.3) — the one remaining
gap, now narrowly scoped to "bound the number of tree levels," since
everything else about the per-level mechanism is done and verified.

## Experiment

- `tests/test_aho_corasick.py` — automaton output checked against a
  brute-force "longest matching vocab suffix" scan, on the recovered
  Figure-2-variant example and 100 randomized dictionaries.
- `tests/test_dfs_interval.py` — the O(1) interval test checked against
  the ancestor-walk oracle across *every possible* (candidate,
  history-value) pair (not just ones a specific run happens to hit);
  `find_valid_child` separately checked against a linear scan over the
  same space.
- `tests/test_sibling_disjointness.py` — directly verifies the paper's
  "Mutual Exclusion among Siblings" corollary holds (a precondition for
  the binary search to be sound), across 200 randomized dictionaries.
- `tests/test_incremental.py` — as before (200 random dictionaries, the
  repeated-character family, real reference-implementation traces),
  now *also* asserting on every byte that the binary-search walk agrees
  with both the plain tree walk and the original length-scanning search,
  and that θ(sc) never exceeds τ(sc) from the automaton. This also
  confirmed a subtle point empirically: `_search_binary_walk` skips the
  "is this candidate actually a string-suffix of the buffer" pre-filter
  the other two searches use, relying instead on Appendix E's Claim 4
  (proved for *every* forest child, not just buffer-matching ones) — the
  cross-check across hundreds of dictionaries is what gives confidence
  this shortcut is actually sound, not just plausible.
- `tests/test_eager.py` — concatenating every eagerly-emitted token
  (plus a final flush) exactly reproduces the non-eager tokenization,
  checked across the same three test families.

All of the above pass (22/22 tests). "Same tokenization result, faster"
is now true for the search at the per-level mechanism level — what's not
yet true is "bounded to O(log t) levels in the worst case," which needs
Centroid Decomposition specifically.

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
