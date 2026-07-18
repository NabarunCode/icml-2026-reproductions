# Claim 2 — Algorithm Design (Aho–Corasick + Centroid Decomposition + Eager Output)

**Status:** ☐ not started (Phase 0 scaffold only)

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

*(Phase 1–2 — to be written.)*

## Mathematics

*(Phase 2 — to be written.)* Complexity bookkeeping: O(1) automaton
transition, O(log|τ|) CST traversal, O(log|τ|) binary search per decision
step → O(log²|τ|) per byte (Section 5.4). Eager output's amortized O(1)
argument (Appendix G) rests on each Prefix-Tree-of-Tokens node being
inserted/removed from the tracked subgraph at most once each — needs its
own careful check, since amortized arguments are exactly where subtle
correctness bugs hide.

## Implementation

*(Phase 3–4 — to be written.)* This is where Phase 3 (reference
implementation mapping, see
`../../resources/official-implementation.md`) does the most work: the
`aho_corasick/`, `centroid.rs`, and `eager.rs` modules should map directly
onto the three mechanisms above. Our reproduction should implement each
piece separately and unit-test it in isolation before integrating, rather
than reimplementing the whole pipeline monolithically.

## Experiment

*(Phase 4–5 — to be written.)* Differential testing against a brute-force
"re-tokenize from scratch after every appended byte" reference is the
right correctness harness here — the same tokenization result, faster,
per every prefix of many random and adversarial strings.

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
