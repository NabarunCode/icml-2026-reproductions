# Benchmark Protocol

The mandatory methodology for **every** benchmark in this repository,
for every paper. A number produced any other way is not citable in a
claim verdict. The protocol is implemented in code by
`repro_core.timing.run_benchmark` and `repro_core.environment` — use
them rather than re-implementing timing loops per paper.

## 1. Timing methodology

- **Clock:** `time.perf_counter_ns` — monotonic, highest resolution the
  standard library provides. Wall-clock (`time.time`) is never used for
  measurement.
- **Garbage collection:** a full `gc.collect()` runs *before* each timed
  sample, and the collector is disabled *during* each sample (restored
  afterward), so collection pauses land between samples, not inside
  them. `run_benchmark` does this automatically.
- **Too-fast operations:** if a single call is near clock resolution
  (rule of thumb: < 1 µs), use `inner_iterations=N` so each sample times
  a loop of N calls and records the per-call average. State N in the
  write-up.

## 2. Warm-up

At least **3 warm-up executions** are run and discarded before any timed
sample (default `warmup=3`). Warm-up exists to absorb one-time effects:
cold caches, lazy imports, allocator growth, first-call specialization.
If a workload visibly needs more (first timed sample is still an
outlier), increase warm-up and say so — never delete the outlier sample
afterward instead.

## 3. Repetitions

At least **10 timed repetitions** per configuration (default
`repeats=10`); more for noisy or short workloads. Each repetition is an
independent sample of the same operation.

## 4. Statistical reporting

Every reported benchmark states, at minimum:

- **mean** and **standard deviation** (never a single number),
- **median**, **min**, **max**,
- the **raw samples**, committed with the result (they are the data;
  summary statistics can be recomputed, raw samples cannot).

Interpretation rules:

- Prefer the **median** in prose when the distribution is visibly skewed
  (timing distributions usually skew right); the mean and stdev must
  still be reported.
- If `stdev / mean > 5%`, the result is flagged as **noisy** in the
  write-up and either re-run in a quieter environment or reported with
  that caveat prominently — not silently averaged away.
- Speedup ratios (ours vs. baseline) are computed from medians of runs
  taken **on the same machine in the same session**, and reported with
  both sides' dispersion. Never compare numbers captured in different
  environments.

## 5. Environment capture (mandatory)

Every benchmark run writes an `environment.json` produced by
`repro_core.environment.write_environment` (CLI: `uv run repro-env
<path>`) **next to its results**, capturing: git commit + branch + dirty
flag, Python version/implementation, OS, CPU model + core count, total
RAM, GPU devices + CUDA version (None when absent), Rust toolchain
version (None when absent), all installed package versions, and a UTC
timestamp. Undetectable values are recorded as `null`, never omitted.

Additionally, the write-up states what the JSON cannot capture:

- whether the machine was otherwise idle,
- virtualization/container context (bare metal vs. sandbox vs. CI),
- any CPU pinning / frequency-scaling configuration,
- random seeds, for any randomized workload.

## 6. Where results live and what they look like

```
papers/<slug>/benchmarks/   # benchmark scripts + raw run output
papers/<slug>/results/      # curated final numbers + environment.json
```

Expected result format — one JSON file per run:

```json
{
  "protocol_version": 1,
  "description": "what was measured, one sentence",
  "command": "exact command that produced this file",
  "seed": 20260718,
  "environment_file": "environment.json",
  "benchmarks": [
    {
      "name": "incbpe_feed/codellama/english_1MB",
      "warmup": 3,
      "repeats": 10,
      "inner_iterations": 1,
      "mean_ns": 0.0,
      "stdev_ns": 0.0,
      "median_ns": 0.0,
      "min_ns": 0.0,
      "max_ns": 0.0,
      "samples_ns": []
    }
  ]
}
```

(the `benchmarks` entries are exactly
`repro_core.timing.BenchmarkResult.to_dict()` output; zeros above are
placeholders for shape only).

## 7. Comparisons against papers

Our hardware will generally not match a paper's. Therefore:

- Reproduce the paper's *qualitative* claim (relative speedup, scaling
  shape) and report our own absolute numbers honestly alongside the
  paper's — never rescale ours to look comparable.
- State the paper's environment and ours side by side in the claim's
  Result section.
- If the qualitative effect does not reproduce in our environment, that
  is the result. It is written up with the same rigor as a success.

## 8. Integrity rules

- All runs are committed, or a discarded run is recorded with the reason
  (e.g. "laptop unplugged mid-run"). Cherry-picking the best run is
  fabrication.
- Benchmark code is committed at the same commit that produced the
  numbers; the `environment.json` git field proves it.
- Randomized workloads fix and record their seeds.
