# Claim 1 — The Monotonic Path Property (Theorem 4.2)

**Status:** ☐ not started (Phase 0 scaffold only)

## Claim statement

> Let *k* be the longest canonical suffix token of a string *s*. Consider
> the Suffix-Successor Tree `SufSucTree(k)`. Let *P* be the unique path
> from the true last token θ(s) to the tree's root. Then a node
> `t ∈ SufSucTree(k)` satisfies the **Prefix Last-Token Condition** if and
> only if *t* lies on *P*.
>
> — Theorem 4.2, Section 4.2

Practically: among all suffix tokens of a growing string that *could*
plausibly be the final token of its BPE tokenization, only those forming a
single contiguous path (from the true answer up to the tree root) are ever
actually valid. This is what makes an O(log²t)-per-byte search possible —
without it, the search space would not collapse to a single path and the
complexity bound would not hold.

## Explanation

*(Phase 1–2 — to be written.)* Plain-language walkthrough of why boundary
elimination during BPE merges forces this monotonic structure, building on
the "boundary elimination" intuition in Appendix D before touching the
formal proof in Appendix E.

## Mathematics

*(Phase 2 — to be written.)* The paper's proof (Appendix E) proceeds via
four claims: upward closure, uniqueness of the satisfying child, that
θ(s) itself satisfies the condition, and that θ(s) is maximal (no child
also satisfies it). Our job here is to restate this proof in our own words
with enough intermediate steps that we could regenerate it without the
paper, and to look for gaps or unstated assumptions.

## Implementation

*(Phase 3–4 — to be written.)* This is a structural/correctness claim, not
a performance claim, so verification is by **exhaustive/randomized testing
against a brute-force reference BPE**, not by benchmarking: for many
random dictionaries and strings, confirm that at every prefix length, the
set of suffix tokens satisfying a directly-coded Prefix Last-Token
Condition check is exactly a single root-to-θ(s) path.

## Experiment

*(Phase 4–5 — to be written.)*

## Benchmark

Not applicable — this is a correctness/structural claim, not a performance
claim. No timing benchmark belongs here (see Claims 3–4 for performance).

## Result

*(Phase 6 — to be written. No fabricated numbers.)*

## Discussion

*(Phase 6 — to be written.)*

## Limitations

*(Phase 6 — to be written.)*

## Conclusion

*(Phase 6 — to be written.)*

---

> **Inference X-Ray candidate:** Yes — likely strong. The "Prefix Tree of
> Tokens" / Successor Forest / Suffix-Successor Tree construction is a
> genuinely elegant way to visualize *why* BPE tokenization is prefix-
> consistent, which is a subtle point most tokenizer explainers skip
> entirely. Worth a chapter independent of the incremental-algorithm
> framing: "why can you truncate a BPE tokenization and still get a valid
> tokenization of the prefix?" Flag for a note in Inference X-Ray once
> Phase 2 write-up exists to draw from.
