# Corroboration run — HF Jobs, dedicated CPU (2026-07-19)

**Purpose:** every run above this one carries the caveat "shared
multi-tenant sandbox VM, idleness not guaranteed." This is a one-shot
re-run of the *entire* Phase 5 benchmark suite on dedicated HF Jobs
compute (`cpu-upgrade` flavor), to check whether the measured shapes
(the log-log slopes the verdicts rest on) hold on different, quieter
hardware. **They do — every slope reproduces to within ~0.03 of the
original sandbox measurement.** This section does not change any
verdict; it corroborates the ones already recorded in Phase 6.

- **Job:** `hinabarun/6a5cdd75d216bd6f3a201568` — 64-core AMD EPYC 7R13,
  512 GB RAM, `python:3.12` image, fresh clone, `19m 16s` wall time.
- **Code under test:** commit `bbac0df` on
  `claude/icml-2026-reproductions-handover-zvye6y` — the exact commit
  already pushed as this repository's Phase-8-final state.
- **Raw data:** `../benchmarks/runs/hfjobs-corroboration/<run>/` (one
  `results.json` + `environment.json` pair per script, committed
  alongside the originals) and the job's own upload,
  [`hinabarun/icml-repro-corroboration-runs`](https://huggingface.co/datasets/hinabarun/icml-repro-corroboration-runs)
  (dataset repo, tarball of the same files).
- **Command:** the full pinned script parked in
  [`../benchmarks/README.md`](../benchmarks/README.md) — clone, `uv
  sync --all-packages --all-extras`, `uv run pytest`, then all eight
  benchmark invocations in sequence, tar the `runs/` output, upload.
- **`environment.json` note:** every file in this run reports
  `git.dirty: true`. This is expected, not a regression: the job
  writes its `results.json`/`environment.json` output into paths this
  repo already tracks (from the original local runs), and
  `write_environment()` runs *after* those files are overwritten —
  so the working tree is (correctly) reported dirty by the time it's
  captured, from the run's own output alone. No source file changed;
  `git.commit` in every file confirms the checkout was `bbac0df`
  throughout.

## Side-by-side: sandbox vs. dedicated HF Jobs hardware

| Series | Sandbox slope | HF Jobs slope | Shape (both) |
|---|---|---|---|
| `incremental` / `'a'*n`, synthetic dict (Claim 4) | 0.995 | **0.997** | linear |
| `restart_per_byte` baseline (Claim 4) | 1.901 | **1.984** | quadratic |
| `batch_oracle` (Claim 4, sanity check) | 0.960 | **1.015** | linear |
| `chain_amortized` per-byte (Claim 2) | flat (0.961 vs input len) | flat (**0.994** vs depth $\times$ input len) | linear |
| `feed_max_latency` (Claim 2, missing-centroid cost) | 0.972 | **1.016** | linear in depth |
| `ours_gpt2` real vocab, `'a'*n` (Claim 4) | 0.987 | **0.997** | linear |
| tiktoken **0.13.0**, R50K/GPT-2 (Claim 4) | 1.159 | **1.138** | mildly superlinear |
| tiktoken **0.8.0**, R50K/GPT-2 (Claim 4) | 2.084 | **2.036** | quadratic |
| tiktoken **0.13.0**, CL100K (Claim 4) | 1.141 | **1.131** | mildly superlinear |
| tiktoken **0.8.0**, CL100K (Claim 4) | 2.041 | **2.033** | quadratic |

Every slope lands within **±0.03** of the sandbox measurement, and
every linear/quadratic/mild-superlinear classification is unchanged.
The two hardest-to-trust numbers — the missing-centroid tail latency
(1.016 vs. 0.972) and the restart-per-byte baseline (1.984 vs. 1.901,
both ≈2.0) — corroborate on dedicated hardware just as cleanly as the
flat ones.

## Claim 3 (English corpus, GPT-2) — single-point corroboration

Same dataset (Wikipedia 20231101, stride-42, revision `b04c8d1c`,
re-fetched fresh, byte-identical: `3709` docs / `16502234` bytes —
matches the sandbox run exactly), same slice size (500 kB, eager 10 kB):

| series | sandbox | HF Jobs | ratio |
|---|---|---|---|
| `ours_feed` | 28.0 µs/byte | **32.3 µs/byte** | 1.15× |
| `ours_eager` | 964.5 µs/byte | **1161.5 µs/byte** | 1.20× (still ≈34× over non-eager: 36.0×) |
| `hf_bpe_word` | 536 ns/byte | **389 ns/byte** | 0.73× |
| `tiktoken_r50k` | 85 ns/byte | **67 ns/byte** | 0.79× |
| correctness vs HF `tokenizers` | 114 399 tokens, 0 divergences | **114 399 tokens, 0 divergences** | identical |
| whole-string vs regex-pretok token count | 114 399 vs 115 391 | **114 399 vs 115 391** | identical |

The 64-core dedicated box is a faster machine overall (Rust baselines
dropped 20-27%), but the *ratios that matter to the claim* — our
eager-vs-non-eager overhead (36.0× here vs. 34× sandbox) and the
correctness/token-count results — are unchanged to the byte.

## Conclusion

No verdict in `docs/ROADMAP.md` or any `claims/*/README.md` changes as
a result of this run. Its only job was to answer "is the shared
sandbox hiding something?", and the answer is no: same shapes, same
correctness, same qualitative eager-overhead ratio, on completely
different, dedicated hardware. Filed as corroborating evidence per
`docs/BENCHMARK_PROTOCOL.md`'s recommendation to re-run on a second
environment when one is available.
