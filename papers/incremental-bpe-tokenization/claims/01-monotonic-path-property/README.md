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

Full write-up in
[`../../paper/theory-notes.md`](../../paper/theory-notes.md) (Phase 2).
Summary: because a merge rule can only glue together tokens that are
*already adjacent*, and can never reach back across a boundary that's
already settled (boundary elimination), truncating a valid tokenization
at any token boundary always gives you the valid tokenization of the
shorter string (Lemma 3.1). That fact is what lets the algorithm track
just one moving "last token" instead of a whole tokenization, and
Theorem 4.2 is the guarantee that as that last token moves (byte by
byte), the set of things it could possibly be forms one single connected
path in the Suffix-Successor Tree — never two live branches at once. The
theory notes include a small, mechanically-verified 3-rule example
(`ab`/`bb`/`abb` over alphabet `{a,b}`) showing the last token jumping
between sibling branches of the tree as the string grows
(`θ(a)=a → θ(ab)=ab → θ(abb)=abb → θ(abbb)=bb`), including the concrete
DFS-interval arithmetic that predicts the jump.

## Mathematics

See `../../paper/theory-notes.md` §§4–7 for the worked-example version.
The paper's own proof (Appendix E) proceeds via four claims: upward
closure, uniqueness of the satisfying child, that θ(s) itself satisfies
the condition, and that θ(s) is maximal (no child also satisfies it). Not
yet independently re-derived line-by-line against Appendix E — the theory
notes build intuition and a numerically-checked example, but a full
restatement of the four-claim proof (checking for gaps/unstated
assumptions) is still open, to be done if/when Claim 1's implementation
work (below) surfaces a case the intuition doesn't cleanly cover.

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
