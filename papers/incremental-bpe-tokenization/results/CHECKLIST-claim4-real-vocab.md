# Reproducibility checklist — claim4-real-vocab (+ tiktoken-0.8.0 regression)

Per `docs/REPRODUCIBILITY_CHECKLIST.md`. Auto rows from
[`../benchmarks/runs/claim4-real-vocab/environment.json`](../benchmarks/runs/claim4-real-vocab/environment.json)
and
[`../benchmarks/runs/claim4-tiktoken-0.8.0/environment.json`](../benchmarks/runs/claim4-tiktoken-0.8.0/environment.json).

| Item | Value | Source |
|---|---|---|
| **System** | | |
| OS + version | Linux 6.18.5 (Ubuntu 24.04 userland) | (auto) |
| CPU model + logical cores | Intel(R) Xeon(R) Processor @ 2.80GHz, 4 logical cores | (auto) |
| RAM (total) | ~15.7 GiB | (auto) |
| GPU / CUDA | null (none present) | (auto) |
| Bare metal / VM / container / CI | cloud sandbox container (Claude Code remote environment) | manual |
| Machine otherwise idle? | not guaranteed — shared multi-tenant VM, no CPU pinning | manual |
| **Toolchain** | | |
| Python | 3.11.15 CPython | (auto) |
| Rust | rustc 1.94.1 present, unused (tiktoken installed as prebuilt wheel) | (auto) |
| C/C++ compiler | cc 13.3.0, unused (no source builds) | manual |
| uv version | 0.8.17 | manual |
| **Code + dependencies** | | |
| Git commit | claim4-real-vocab: 674b0a1b · tiktoken-0.8.0 run: see its environment.json | (auto) |
| Branch | claude/icml-2026-reproductions-handover-zvye6y | (auto) |
| Working tree clean? | dirty: false (both runs) | (auto) |
| Dependency versions | committed uv.lock; tiktoken 0.13.0 (main run) / 0.8.0 (regression run, layered via `uv run --with tiktoken==0.8.0`, hard-asserted in-script) | (auto + script assert) |
| Reference submodule commit | N/A — not used | manual |
| **Experiment** | | |
| Random seed(s) | N/A — fully deterministic workload | manual |
| Exact command(s) | `uv run python papers/incremental-bpe-tokenization/benchmarks/claim4_real_vocab.py` · `uv run --with tiktoken==0.8.0 python papers/incremental-bpe-tokenization/benchmarks/claim4_tiktoken_regression.py` | manual |
| Expected output | ours flat ~19.7 µs/byte (slope 0.987); tiktoken 0.13.0 slope ~1.16 to 8 MB; tiktoken 0.8.0 quadratic (per-byte ~×10 per ×10 n); token-for-token cross-check passes before timing | manual |
| Warm-up / repeats / inner iterations | 3 / 10 / 1 | in results.json |
| **Data** | | |
| Dataset | synthetic `'a'*n`, generated in-script; sizes in results.json | manual |
| Tokenizer/vocab | GPT-2/R50K from committed files, SHA256 in `../benchmarks/data/README.md` and in each results.json | manual |
