# Claim 4 — Real vocabulary + real tiktoken (measured, with a finding)

**Runs:**
[`../benchmarks/runs/claim4-real-vocab/`](../benchmarks/runs/claim4-real-vocab/)
(commit `674b0a1b`, clean tree) and
[`../benchmarks/runs/claim4-tiktoken-0.8.0/`](../benchmarks/runs/claim4-tiktoken-0.8.0/)
(same script family, old baseline) ·
**Scripts:** [`../benchmarks/claim4_real_vocab.py`](../benchmarks/claim4_real_vocab.py),
[`../benchmarks/claim4_tiktoken_regression.py`](../benchmarks/claim4_tiktoken_regression.py) ·
**Checklist:** [`CHECKLIST-claim4-real-vocab.md`](CHECKLIST-claim4-real-vocab.md) ·
Tables via `scripts/analyze_run.py`.

## What was measured

The paper's actual Claim 4 setting: the real GPT-2/R50K vocabulary
(committed with provenance, `../benchmarks/data/README.md`) and the
real `tiktoken` library, built fully offline from those same files.
Input `"a" * n` — a single regex word, so the BPE merge phase bears the
full cost. **Before any timing, our incremental implementation and
tiktoken were asserted to agree token-for-token on every size** — an
external correctness check against a production tokenizer.

## Results

| series | per-byte cost (median) | log-log slope | shape |
|---|---|---|---|
| ours (incremental, Python, GPT-2 vocab) | ~19.7 µs/byte, flat n=5k → 100k | **0.987** | linear |
| tiktoken **0.13.0** (current) | 139 → 412 ns/byte, n=10k → 8M | **1.159** | mildly superlinear (~n log n-like) |
| tiktoken **0.8.0** (2024-era) | 4.1 → 111.5 µs/byte, n=10k → 200k (roughly ×2 per size doubling) | **2.084** | **quadratic — the paper's reported behavior** |

(Full per-size tables with dispersion: regenerate via
`uv run python papers/incremental-bpe-tokenization/scripts/analyze_run.py <run>/results.json`.
All three series are protocol-grade runs on clean trees; the 0.8.0 run's
CVs are 0.8-3.2%.)

**A measured crossover.** Because the old baseline is quadratic and ours
is flat, they cross inside the measured range: at n=100 kB tiktoken
0.8.0 needs ~43.4 µs/byte vs. our ~19.7 µs/byte (ours 2.2× faster), and
at 200 kB ~111.5 vs. ~19.7 µs/byte (ours 5.7× faster) — a pure-Python
implementation with the paper's asymptotics overtaking a Rust
implementation without them, on identical input, vocabulary, and
(asserted) identical token output. Against *current* tiktoken (0.13.0)
no crossover occurs in the measured range: it stays ~50-100× faster
than our Python in absolute terms. Both facts reported.

## The finding

The paper attributes O(n²) pathological-input decay to tiktoken
(Figure 3 / Figure 7), and **that was true of tiktoken as of ~0.8.0** —
we measure clear quadratic growth there. But **current tiktoken
(0.13.0) no longer shows it**: growth up to 8 MB is ~n^1.16, consistent
with an upstream algorithmic improvement to the merge phase between
those releases. Meanwhile our incremental implementation is flat
(slope 0.987) on the same real vocabulary, as the paper's method
predicts.

So Claim 4's honest status on our evidence:

- **Reproduced** against the era-appropriate baseline (tiktoken ≈0.8.0):
  stable incremental throughput vs. quadratic tiktoken decay.
- **Environment drift documented**: against today's tiktoken, the
  *dramatic* contrast has narrowed to "flat vs. mildly superlinear";
  the asymptotic advantage claim survives, the headline blow-up does
  not (at ≤8 MB, R50K vocabulary, this hardware).

Neither half of that is hidden. This is exactly the kind of result the
repository exists to record.

## Noise and limitations

- The 8 MB tiktoken point has CV 35% (one slow outlier sample; median
  reported, raw samples committed). All other points CV ≤ 3.6%.
- Absolute Python-vs-Rust numbers carry no speedup information
  (protocol §7): ours is ~19.7 µs/byte in pure Python; the contrast
  under test is *shape*, not magnitude.
- One vocabulary (R50K) and one pathological family (`'a'*n`); the
  paper's Figure 3 also uses larger tokenizers (CL100K/O200K), whose
  files we don't yet have locally.
- tiktoken 0.5.2 could not be probed (its module lacks
  `__version__`; probe script failed before measuring — not evidence
  about its behavior either way).
- In the 0.8.0 run, `environment.json`'s package list shows the base
  venv's tiktoken (0.13.0) — the `uv run --with` overlay's 0.8.0 shadows
  it on `sys.path` and is hard-asserted in-script and recorded as
  `tiktoken_version` in `results.json`. The capture bug (last duplicate
  distribution winning instead of the first/effective one) is fixed in
  `repro_core.environment` for future runs; this run's record is
  corrected by this note rather than edited after the fact.
