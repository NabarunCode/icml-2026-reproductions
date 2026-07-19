# Claim 4 — Pathological-Input Robustness vs. `tiktoken`

**Status:** ☑ Phase 6 verdict recorded — **Reproduced against the
era-appropriate baseline, with a documented environment-drift finding**
(current tiktoken no longer exhibits the quadratic decay; the claim's
mechanism contrast survives).

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

*(Phase 3–4 — to be written.)* Python-first per `docs/ROADMAP.md`; shares
implementation dependencies with Claim 3 (needs a working incremental BPE
to compare against). This claim is arguably the safest one for a Python
reproduction to hold up cleanly: it's about *shape* (linear-looking vs.
quadratic-looking growth), which should survive constant-factor overhead
much better than an absolute "3.13×"-style number would. It can also be
*partially* verified independent of our own implementation: we can
independently confirm the `tiktoken` O(n²) half of the claim today, using
stock `tiktoken`, without needing our reproduction ready yet — worth doing
early as a sanity check that the baseline behavior is real before we build
anything to compare against it.

## Experiment

*(Phase 4–5 — to be written.)* Direct replication of the paper's Figure 3
methodology: throughput (bytes/s) vs. input length on a log–log plot,
filled markers for measured points. Paper notes the O200K tokenizer's
regex stage errors out before reaching the largest lengths (their
"Regex Errors" annotation) — expect to hit the same wall and should
document it rather than route around it.

## Benchmark

**Run (Phase 5, 2026-07-18):**
[`../../results/claim4-pathological.md`](../../results/claim4-pathological.md)
— script [`../../benchmarks/claim4_pathological.py`](../../benchmarks/claim4_pathological.py),
raw data + environment under `../../benchmarks/runs/claim4-pathological/`,
per `docs/BENCHMARK_PROTOCOL.md` (clean tree, warm-up 3, repeats 10,
raw samples committed).

Headline measurements (details and caveats in the results doc):

- our incremental implementation: **flat ~1.9 µs/byte from n=1 000 to
  n=100 000** — log-log slope of total time vs n = **0.995** (linear);
- restart-per-byte from-scratch baseline: slope **1.901** (quadratic),
  per-byte cost doubling as n doubles;
- correctness cross-checked against the oracle at every size before
  timing.

**Run 2 (Phase 5, 2026-07-18) — real vocabulary, real tiktoken:**
[`../../results/claim4-real-vocab.md`](../../results/claim4-real-vocab.md).
The tiktoken egress blocker was resolved by owner-uploaded, hash-pinned
vocabulary files (`../../benchmarks/data/`); tiktoken's GPT-2 encoding
is constructed fully offline from them, and our implementation is
asserted token-for-token identical to tiktoken before any timing.
Headlines, all protocol-grade on clean trees:

- ours on the real GPT-2/R50K vocabulary: flat ~19.7 µs/byte,
  slope **0.987** (linear);
- tiktoken **0.8.0** (era-appropriate baseline): slope **2.084**
  (quadratic — the paper's reported O(n²) behavior, reproduced), with a
  measured crossover: our pure-Python implementation overtakes it
  beyond ~60-100 kB of pathological input despite the Rust-vs-Python
  handicap;
- tiktoken **0.13.0** (current): slope **1.159** up to 8 MB — the
  quadratic blow-up has been optimized away upstream since the paper's
  measurements. Reported as environment drift, not hidden: against
  today's baseline the dramatic contrast narrows to "flat vs. mildly
  superlinear."

**Run 3 (Phase 5, 2026-07-19) — the claim's exact named tokenizer:**
after the environment's network allowlist was opened, `cl100k_base`
was fetched from OpenAI's CDN (SHA256 matches tiktoken's own pinned
checksum) and the same two-era measurement ran on **CL100K** — the
tokenizer the claim statement names: tiktoken 0.8.0 slope **2.041**
(quadratic), tiktoken 0.13.0 slope **1.141** (mild) up to 8 MB. The
finding is vocabulary-robust. Remaining: O200K (encoding documented,
not yet measured).

## Result

(Three protocol-grade run families; details in
[`../../results/claim4-pathological.md`](../../results/claim4-pathological.md)
and [`../../results/claim4-real-vocab.md`](../../results/claim4-real-vocab.md).)

- **Our incremental implementation holds stable throughput** on 'a'*n:
  log-log slope 0.995 (synthetic dictionary, n to 100k) and 0.987 (real
  GPT-2 vocabulary) — flat per-byte cost across a 100× size range, with
  output asserted token-identical to tiktoken before timing.
- **tiktoken's O(n²) decay reproduces on the era-appropriate version
  (0.8.0)**: slope 2.084 on R50K and **2.041 on CL100K — the tokenizer
  the claim statement names**. Per-byte cost doubles with every input
  doubling, exactly the paper's Figure 3 behavior.
- **Measured crossover**: our pure-Python implementation overtakes
  0.8.0-era Rust tiktoken beyond ~60–100 kB of pathological input
  (5.7× faster at 200 kB) — right asymptotics beating a compiled
  implementation with wrong asymptotics.
- **Environment drift**: current tiktoken (0.13.0) no longer shows the
  blow-up (slopes 1.14–1.16 up to 8 MB, consistent with an upstream
  algorithmic fix between 0.8.0 and 0.13.0). Against today's baseline
  the contrast narrows to "flat vs. mildly superlinear."

## Discussion

The claim has two parts and they fared differently. The part about *the
incremental method* — stable throughput on adversarial input — is
cleanly reproduced, twice over (synthetic and real vocabulary). The
part about *the baseline* was true when the paper measured it and is no
longer true of the current release: baselines are moving targets, and
this reproduction caught the movement precisely because it version-
pinned everything. Note the paper's underlying point survives the
drift: the incremental method's worst-case guarantee is structural,
while tiktoken's improvement is an implementation optimization that
had to be discovered and shipped — the DoS-hardening argument in the
paper's Impact Statement favors guarantees over patches.

## Limitations

- O200K not yet measured (encoding documented, file exceeds the
  large-file cap). The paper's "Regex Errors" observation at extreme
  lengths is untested.
- tiktoken 0.5.2 could not be probed (packaging quirk); the exact
  version range where upstream fixed the merge loop is not pinned down.
- Absolute numbers are Python-vs-Rust and carry no magnitude
  information (protocol §7); the verdict rests entirely on shape.

## Conclusion

**Reproduced — against the baseline as it existed in the paper's era —
with the added finding that the baseline has since fixed the quadratic
behavior upstream.** Both halves are evidence-backed: slopes 2.04–2.08
(old tiktoken, quadratic, including on CL100K specifically) vs. 0.99
(ours, flat), and slopes 1.14–1.16 for today's tiktoken. A reproduction
that simply ran today's tiktoken would have wrongly concluded the paper
overclaimed; version archaeology shows it didn't.

---

> **Inference X-Ray candidate:** Yes — algorithmic-complexity attacks
> (the paper's own Impact Statement raises this: "mitigates the risk of
> algorithmic complexity attacks, e.g., Denial-of-Service triggered by
> carefully crafted input sequences") are a good, concrete, demoable
> security-adjacent chapter: a single repeated character causing quadratic
> slowdown in a widely-deployed tokenizer is a vivid, minimal example of
> why worst-case complexity guarantees matter in production inference
> systems, not just average-case speed.
