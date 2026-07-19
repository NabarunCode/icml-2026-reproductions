# ICML 2026 Reproductions

[![CI](https://github.com/NabarunCode/icml-2026-reproductions/actions/workflows/ci.yml/badge.svg)](https://github.com/NabarunCode/icml-2026-reproductions/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](pyproject.toml)
[![Typed](https://img.shields.io/badge/mypy-strict-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A research repository for honest, scientific reproductions of accepted
ICML (and eventually NeurIPS / ICLR) papers. This is not a hackathon
project and not a benchmark-chasing exercise — it exists to practice the
full discipline of empirical ML research: read the paper, understand the
theory, understand the reference implementation, reproduce it, benchmark
it rigorously, and report honestly what did and did not hold up.

If a result doesn't reproduce, that is a valid, documented outcome — not
a failure of the repository.

## Principles

- **Correctness over speed.** No claim is reported without evidence.
- **No fabrication.** Numbers are measured, never invented or
  extrapolated without saying so.
- **No hidden failures.** Negative and partial results are documented
  with the same rigor as positive ones.
- **No moving the goalposts.** Experiments are not modified after the
  fact to match a paper's reported numbers.
- **Provenance is explicit.** Every paper carries a `PROVENANCE.md`
  separating independent reproduction from anything influenced by the
  official implementation.

## Quick start

Requires Python ≥ 3.11 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/NabarunCode/icml-2026-reproductions.git
cd icml-2026-reproductions
uv sync --all-packages   # shared infrastructure + every paper package + dev tools
uv run pytest            # run every test in the repository
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full developer workflow
(lint, type-check, pre-commit) and
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the repository is
organized and why.

## Repository layout

Each paper is a **fully self-contained research project**; the root
holds only infrastructure shared by every paper.

| Path | Purpose |
|---|---|
| `papers/<paper-slug>/` | Everything for one paper: PDF, notes, per-claim verification folders, reproduction code (`experiments/`), benchmarks, results, figures, pinned reference implementation, provenance record. |
| `src/repro_core/` | Shared, tested infrastructure: environment capture (`repro-env`), the standard benchmark runner. |
| `docs/` | Project-wide standards: [workflow](docs/WORKFLOW.md), [roadmap](docs/ROADMAP.md), [architecture](docs/ARCHITECTURE.md), [benchmark protocol](docs/BENCHMARK_PROTOCOL.md), [reproducibility checklist](docs/REPRODUCIBILITY_CHECKLIST.md). |
| `tests/` | Tests for `repro_core` (each paper's tests live with that paper). |

## Process

Every paper moves through the same eight phases, in order, never
skipping: read → theory → reference implementation → implement →
benchmark → verify claims → publish logbook → document. The full
process, including the per-claim verdict format, is in
[`docs/WORKFLOW.md`](docs/WORKFLOW.md); per-paper status lives in
[`docs/ROADMAP.md`](docs/ROADMAP.md).

## Current paper

**Incremental BPE Tokenization** — Shenghu Jiang, Ruihao Gong
(ICML 2026). **Status: all 8 phases complete.** Verdicts: 2/4 claims
reproduced, 1 partially, 1 correctness-verified with the speedup
untestable from Python — nothing falsified. Published logbook:
[hinabarun/repro-incremental-bpe-tokenization](https://huggingface.co/spaces/hinabarun/repro-incremental-bpe-tokenization).
Full write-up:
[`papers/incremental-bpe-tokenization/`](papers/incremental-bpe-tokenization/)
(claims, results, runs, [provenance](papers/incremental-bpe-tokenization/PROVENANCE.md)).

## Benchmarking standard

Every benchmark follows
[`docs/BENCHMARK_PROTOCOL.md`](docs/BENCHMARK_PROTOCOL.md): warm-up
runs, ≥10 timed repetitions, mean **and** variance (never a single
number), raw samples committed, and a machine-generated
`environment.json` (git commit, OS, CPU, RAM, GPU/CUDA, Python/Rust
versions, dependency versions) recorded next to every result. Published
results additionally fill in
[`docs/REPRODUCIBILITY_CHECKLIST.md`](docs/REPRODUCIBILITY_CHECKLIST.md).

## Coding style

Python ≥ 3.11 (3.12 targeted), `mypy --strict` clean, ruff-formatted,
docstrings on public functions, small single-purpose functions. No
speculative abstraction — shared code enters `src/repro_core/` only when
a second paper needs it.

## License

MIT ([`LICENSE`](LICENSE)) for first-party code. Reference
implementations are pinned git submodules retaining their own licenses.
Please cite via [`CITATION.cff`](CITATION.cff) — and always cite the
original papers being reproduced.
