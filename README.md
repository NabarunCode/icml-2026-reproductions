# ICML 2026 Reproductions

A research repository for honest, scientific reproductions of accepted ICML
(and eventually NeurIPS / ICLR) papers. This is not a hackathon project and
not a benchmark-chasing exercise — it exists to practice the full discipline
of empirical ML research: read the paper, understand the theory, understand
the reference implementation, reproduce it, benchmark it rigorously, and
report honestly what did and did not hold up.

If a result doesn't reproduce, that is a valid, documented outcome — not a
failure of the repository.

## Principles

- **Correctness over speed.** No claim is reported without evidence.
- **No fabrication.** Numbers are measured, never invented or extrapolated
  without saying so.
- **No hidden failures.** Negative and partial results are documented with
  the same rigor as positive ones.
- **No moving the goalposts.** Experiments are not modified after the fact
  to match a paper's reported numbers.
- **Reusable infrastructure.** Anything that isn't specific to one paper
  belongs in `framework/`, not copy-pasted into a paper folder.

See [`docs/WORKFLOW.md`](docs/WORKFLOW.md) for the phase-by-phase process
every paper in this repository goes through, and
[`docs/ROADMAP.md`](docs/ROADMAP.md) for the current status of each paper.

## Repository layout

| Path | Purpose |
|---|---|
| `papers/<paper-slug>/` | Everything specific to one paper: the PDF, notes, per-claim verification folders, links to the reference implementation. |
| `framework/` | Reusable research tooling shared across papers (benchmarking harnesses, correctness checkers, plotting utilities). |
| `benchmarks/` | Cross-paper benchmark infrastructure and raw run outputs. |
| `docs/` | Project-wide documentation: workflow, roadmap, conventions. |
| `scripts/` | Small reusable CLI entry points (data download, environment capture, etc.). |
| `experiments/` | Working experiment code, organized per paper/claim. |
| `results/` | Committed, final result tables/summaries (not scratch output). |
| `figures/` | Generated plots and diagrams referenced by documentation. |
| `trackio/` | Trackio logbook configuration and publishing notes. |

## Current paper

**Incremental BPE Tokenization** — Shenghu Jiang, Ruihao Gong (ICML 2026).
See [`papers/incremental-bpe-tokenization/README.md`](papers/incremental-bpe-tokenization/README.md).

## Coding style

Python 3.12, strongly typed, PEP 8, docstrings on public functions, small
single-purpose functions. No speculative abstraction — code is written for
the experiment in front of us, not for hypothetical future papers.

## Benchmarking standard

Every benchmark in this repository (see `framework/benchmarking.md` once
implemented) must: warm up before timing, run multiple iterations, report
mean and variance (not a single number), and record the full environment
(OS, CPU, RAM, Python version, dependency versions, and whether the machine
was otherwise idle).
