# Claim 2 — Algorithm Design (Aho–Corasick + Centroid Decomposition + Eager Output)

**Status:** ◐ in progress — the search algorithm's *correctness* is
implemented and tested (Phase 4); the three specific mechanisms named in
the claim (Aho–Corasick, Centroid Decomposition, eager output) are **not
yet built** — see Implementation below. This claim cannot be marked
verified until they are.

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

**Built so far** (`experiments/incremental-bpe-tokenization/incbpe/incremental.py`):
a correct incremental search that finds θ(sc) by checking every canonical
suffix-token candidate of the buffer directly against Definition 4.1
(via a Successor-Forest ancestor walk), taking the longest one that
passes. This reproduces the *result* of the paper's search (same θ,
verified — see Claim 1) but not yet its *mechanism*: no Aho–Corasick
automaton (candidates are found by scanning lengths against the
vocabulary, O(t) instead of O(1)) and no Centroid Decomposition (each
candidate check is an O(depth) ancestor walk instead of an O(1)
DFS-interval test descending an O(log t)-height search tree). This was a
deliberate scoping decision (see `experiments/.../README.md`
"Limitations") to de-risk getting Definition 4.1 itself right before
adding the performance machinery on top — worth revisiting once the
correctness base is solid and Claim 3/4 benchmarking makes the speedup
necessary. **Not yet started:** eager output (Section 6) has no
implementation at all yet.

## Experiment

Done for the search-correctness half: `tests/test_incremental.py`
differentially tests the incremental search against the from-scratch
oracle across 200 random dictionaries/strings, the paper's repeated-
character family, and the real reference-implementation traces from
Phase 3 — "same tokenization result, every prefix of many random and
adversarial strings," exactly as originally planned here, just not yet
"faster" (see Implementation). Eager output and the Aho-Corasick/Centroid
pieces have no experiments yet since they don't exist yet.

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
