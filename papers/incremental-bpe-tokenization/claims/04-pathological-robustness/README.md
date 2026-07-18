# Claim 4 — Pathological-Input Robustness vs. `tiktoken`

**Status:** ☐ not started (Phase 0 scaffold only)

## Claim statement

> On pathological inputs, the incremental method maintains stable
> throughput whereas `tiktoken` (CL100K) exhibits characteristic
> quadratic O(n²) performance decay.
>
> — Figure 3, Section 7.2

The pathological input construction is fully specified in the paper
(Appendix H.2): strings of 2^k repetitions of the character `'a'`, for
increasing k. This is the easiest claim in the paper to reproduce exactly
as specified, since the input construction requires no external dataset —
just this one repeated-character generator — and `tiktoken` is a public,
pip-installable package.

## Explanation

*(Phase 1–2 — to be written.)* Why would `tiktoken` be O(n²) here
specifically? Section 2 and Appendix J attribute it to reliance on regex-
based segmentation to bound BPE merge cost — pathological repeated-
character input defeats that bound. Worth an independent explanation of
*why* the regex/BPE interaction degrades quadratically on this specific
input, not just citing the paper's claim.

## Mathematics

The complexity contrast is the whole claim: `tiktoken`'s O(n²) vs. this
paper's O(n log²t) on the same input class. t is small and bounded here
(single-character repeats), so log²t is close to constant — meaning our
reproduction should show near-*linear* throughput for the incremental
method and visibly super-linear (quadratic-looking) decay for `tiktoken`.

## Implementation

*(Phase 3–4 — to be written.)* Shares implementation dependencies with
Claim 3 (needs a working incremental BPE to compare against). This claim
can also be *partially* verified independent of our own implementation:
we can independently confirm the `tiktoken` O(n²) half of the claim today,
using stock `tiktoken`, without needing our reproduction ready yet — worth
doing early as a sanity check that the baseline behavior is real before
we build anything to compare against it.

## Experiment

*(Phase 4–5 — to be written.)* Direct replication of the paper's Figure 3
methodology: throughput (bytes/s) vs. input length on a log–log plot,
filled markers for measured points. Paper notes the O200K tokenizer's
regex stage errors out before reaching the largest lengths (their
"Regex Errors" annotation) — expect to hit the same wall and should
document it rather than route around it.

## Benchmark

Same benchmarking standard as Claim 3. This experiment is cheap enough
(single-character-repeat strings, no dataset download) that it should be
one of the first things run once *any* reproduction code exists, even
before Claim 3's full multi-tokenizer sweep.

## Result

*(Phase 6 — to be written. No fabricated numbers.)*

## Discussion

*(Phase 6 — to be written.)*

## Limitations

*(Phase 6 — to be written.)*

## Conclusion

*(Phase 6 — to be written.)*

---

> **Inference X-Ray candidate:** Yes — algorithmic-complexity attacks
> (the paper's own Impact Statement raises this: "mitigates the risk of
> algorithmic complexity attacks, e.g., Denial-of-Service triggered by
> carefully crafted input sequences") are a good, concrete, demoable
> security-adjacent chapter: a single repeated character causing quadratic
> slowdown in a widely-deployed tokenizer is a vivid, minimal example of
> why worst-case complexity guarantees matter in production inference
> systems, not just average-case speed.
