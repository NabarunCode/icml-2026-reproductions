# Reproducibility Checklist

Filled in for **every published benchmark result** (Phase 5/6) and
included, completed, in the paper's `results/` directory next to the
numbers it describes. Items marked *(auto)* are captured automatically
by `repro_core.environment` into `environment.json`; the rest must be
recorded by hand. "N/A" is an acceptable answer; a blank is not.

## Template

Copy this table into `papers/<slug>/results/CHECKLIST-<run-name>.md`.

| Item | Value | Source |
|---|---|---|
| **System** | | |
| OS + version | | *(auto)* `os.system/release/version` |
| CPU model + logical cores | | *(auto)* `cpu` |
| RAM (total) | | *(auto)* `memory.total_bytes` |
| GPU model(s) + driver | | *(auto)* `gpu.devices` (null if none) |
| CUDA version | | *(auto)* `gpu.cuda_version` (null if none) |
| Bare metal / VM / container / CI | | manual |
| Machine otherwise idle? | | manual |
| **Toolchain** | | |
| Python version + implementation | | *(auto)* `python` |
| Rust toolchain version | | *(auto)* `rust.rustc_version` (null if none) |
| C/C++ compiler (if any native builds) | | manual (`cc --version`) |
| uv version | | manual (`uv --version`) |
| **Code + dependencies** | | |
| Git commit | | *(auto)* `git.commit` |
| Branch | | *(auto)* `git.branch` |
| Working tree clean? | | *(auto)* `git.dirty` must be `false` for published results |
| Dependency versions | | *(auto)* `packages` + committed `uv.lock` |
| Reference submodule commit (if used) | | manual (`git submodule status`) |
| **Experiment** | | |
| Random seed(s) | | manual — every randomized component |
| Exact command(s) executed | | manual — copy-pasteable from repo root |
| Expected output (what a re-runner should see) | | manual |
| Warm-up / repeats / inner iterations | | in result JSON (protocol §2–3) |
| **Data** | | |
| Dataset name + version/revision | | manual (e.g. HF dataset id + revision hash) |
| Dataset acquisition command | | manual |
| Dataset content hash or size check | | manual |
| Tokenizer/vocab name + version (if applicable) | | manual |

## Rules

1. `git.dirty` must be `false` for any published number — results from
   an uncommitted tree cannot be reproduced by anyone, including us.
2. Datasets are pinned by **revision/hash**, not "latest". If a dataset
   cannot be pinned, snapshot the exact sample used into the paper's
   `benchmarks/` directory (respecting its license) or record why not.
3. The "exact commands" row must be sufficient for a stranger to go from
   `git clone` to the reported numbers with no undocumented steps.
4. If any row cannot be filled truthfully, the result is not published —
   the gap is documented in the claim's Limitations section instead.
