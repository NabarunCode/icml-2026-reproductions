# Reproducibility checklist — claim2-depth-scaling

Per `docs/REPRODUCIBILITY_CHECKLIST.md`. Auto rows come from
[`../benchmarks/runs/claim2-depth-scaling/environment.json`](../benchmarks/runs/claim2-depth-scaling/environment.json).

| Item | Value | Source |
|---|---|---|
| **System** | | |
| OS + version | Linux 6.18.5 (Ubuntu 24.04 userland) | (auto) |
| CPU model + logical cores | Intel(R) Xeon(R) Processor @ 2.80GHz, 4 logical cores | (auto) |
| RAM (total) | 16 856 244 224 bytes (~15.7 GiB) | (auto) |
| GPU model(s) + driver | null (none present) | (auto) |
| CUDA version | null (none present) | (auto) |
| Bare metal / VM / container / CI | cloud sandbox container (Claude Code remote environment) | manual |
| Machine otherwise idle? | not guaranteed — shared multi-tenant VM, no CPU pinning | manual |
| **Toolchain** | | |
| Python version + implementation | 3.11.15 CPython | (auto) |
| Rust toolchain version | rustc 1.94.1 (present but unused by this benchmark) | (auto) |
| C/C++ compiler | cc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0 (unused — pure Python) | manual |
| uv version | 0.8.17 | manual |
| **Code + dependencies** | | |
| Git commit | e973b1637 (see environment.json for full hash) | (auto) |
| Branch | claude/icml-2026-reproductions-handover-zvye6y | (auto) |
| Working tree clean? | dirty: false | (auto) |
| Dependency versions | environment.json packages + committed uv.lock; benchmark itself is stdlib + incbpe + repro-core only | (auto) |
| Reference submodule commit | N/A — not used by this benchmark (CI-equivalent: not checked out) | manual |
| **Experiment** | | |
| Random seed(s) | N/A — fully deterministic workload (recorded as null in results.json) | manual |
| Exact command(s) executed | `uv run python papers/incremental-bpe-tokenization/benchmarks/claim2_depth_scaling.py` | manual |
| Expected output | flat ~1.5 us/byte amortized; max feed latency linear in depth (slope 0.972); see results.json | manual |
| Warm-up / repeats / inner iterations | 3 / 10 / 1 (in results.json per entry) | manual |
| **Data** | | |
| Dataset name + version | N/A — synthetic input, generated in-script (depth-d successor chain, amortized + max feed latency) | manual |
| Dataset acquisition command | N/A — deterministic construction in the benchmark script | manual |
| Dataset content hash or size check | input sizes recorded in results.json | manual |
| Tokenizer/vocab name + version | synthetic dictionary, fully specified in results.json | manual |
