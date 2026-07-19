# Claim 1 — The Monotonic Path Property (Theorem 4.2)

**Status:** ☑ Phase 6 verdict recorded — **Reproduced (empirically),
at the structural level.** The formal Appendix E re-derivation remains
an explicitly open strengthening step (see Limitations).

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
[`../../notes/theory-notes.md`](../../notes/theory-notes.md) (Phase 2).
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

See `../../notes/theory-notes.md` §§4–7 for the worked-example version.
The paper's own proof (Appendix E) proceeds via four claims: upward
closure, uniqueness of the satisfying child, that θ(s) itself satisfies
the condition, and that θ(s) is maximal (no child also satisfies it). Not
yet independently re-derived line-by-line against Appendix E — the theory
notes build intuition and a numerically-checked example, but a full
restatement of the four-claim proof (checking for gaps/unstated
assumptions) is still open, to be done if/when Claim 1's implementation
work (below) surfaces a case the intuition doesn't cleanly cover.

## Implementation

Implemented in
[`../../experiments/incbpe/incremental.py`](../../experiments/incbpe/incremental.py),
which codes Definition 4.1 (Prefix Last-Token Condition) both directly
(Successor Forest ancestor-walk, kept as an oracle) and via the paper's
own O(1) DFS-interval test (`dfs_interval.py`, §4.3), the two checked
against each other exhaustively. Verification is exactly the "exhaustive/randomized
testing against a brute-force reference BPE" approach this section
originally called for: every test in `tests/test_incremental.py` runs
with `verify_monotonic=True`, which — on every single byte fed, not just
the final answer — empirically checks the Upward Closure sub-lemma
(Appendix E, Claim 1) that underlies Theorem 4.2: every forest-ancestor of
the computed θ(s) must itself have satisfied Definition 4.1. This ran
successfully across 200 randomized small dictionaries/strings, the
paper's own repeated-character pathological family, and the real
Figure-2-variant example recovered in Phase 3, with zero violations.

## Experiment

Done for the structural/correctness half (see Implementation above and
`../../experiments/README.md`). Not yet done:
independently re-deriving Appendix E's full four-claim proof line-by-line
to check for gaps the empirical testing wouldn't surface (empirical
testing can show the property holds on tested cases, not prove it holds
universally) — this remains open for Phase 6's final verdict.

## Benchmark

Not applicable — this is a correctness/structural claim, not a performance
claim. No timing benchmark belongs here (see Claims 3–4 for performance).

## Result

Every empirically testable consequence of Theorem 4.2 held with **zero
violations** across every test family in the repository:

- **Upward Closure** (Appendix E Claim 1), checked on *every byte fed*
  (`verify_monotonic=True`): reference-implementation traces, 200
  randomized dictionaries, and the repeated-character pathological
  family — every forest-ancestor of every computed θ(s) satisfied
  Definition 4.1.
- **Uniqueness of the satisfying child** (the theorem's single-path
  half): the "Mutual Exclusion among Siblings" corollary verified
  directly across 200 randomized dictionaries plus the
  Figure-2-variant (`test_sibling_disjointness.py`) — at most one
  child interval ever contains a given query.
- **Equivalence of the O(1) interval test with the definition**: the
  DFS-interval test agrees with the ancestor-walk oracle on the *full
  cross product* of (candidate token × possible history value), not
  just values arising in sampled runs (`test_dfs_interval.py`).
- **Consequence-level check at real scale**: the search built on this
  theorem produced token-for-token identical output to Hugging Face
  `tokenizers` on 500 kB of real Wikipedia text and to `tiktoken` on
  100 kB pathological input, on the real 50 258-token GPT-2 vocabulary.
  Any single-byte failure of the path property anywhere in those runs
  would have produced a divergent token sequence; none occurred.

## Discussion

The theorem is a structural claim, so the right evidence is exhaustive
and adversarial testing of its logical consequences, which is what the
layered test suite does — including one designed-in stress: the primary
search (`_search_binary_walk`) deliberately relies on Appendix E's
Claim 4 holding for *every* forest child (skipping the buffer-suffix
pre-filter the fallback searches use), so hundreds of dictionaries of
per-byte cross-checking directly exercised the theorem's least
intuitive part. Note the complexity *corollary* (O(log²t)/byte) is a
separate matter: our implementation demonstrates the per-level
mechanism but not the centroid-bounded level count (see Claim 2).

## Limitations

- Empirical verification is not proof. The paper's own four-claim proof
  (Appendix E) has **not** been independently re-derived line-by-line;
  this is the one open strengthening step, and it is a reading/writing
  task, not an experimental one.
- Exhaustive coverage applies to the small randomized dictionary space;
  the 50k real vocabulary is covered end-to-end (consequence-level) but
  not exhaustively per-property.
- Byte-level atomicity only; SentencePiece-semantics dictionaries
  (Appendix A) are out of scope of this verdict.

## Conclusion

**Reproduced (empirically).** Every testable consequence of the
Monotonic Path Property held without exception across exhaustive small-
scale spaces, adversarial constructions, and a real 50k-token
vocabulary at corpus scale. We found no case in which the valid
candidates failed to form a single monotonic path. Formal re-derivation
of Appendix E remains open and would upgrade this verdict from
"empirically reproduced" to "independently verified".

---

> **Inference X-Ray candidate:** Yes — likely strong. The "Prefix Tree of
> Tokens" / Successor Forest / Suffix-Successor Tree construction is a
> genuinely elegant way to visualize *why* BPE tokenization is prefix-
> consistent, which is a subtle point most tokenizer explainers skip
> entirely. Worth a chapter independent of the incremental-algorithm
> framing: "why can you truncate a BPE tokenization and still get a valid
> tokenization of the prefix?" Flag for a note in Inference X-Ray once
> Phase 2 write-up exists to draw from.
