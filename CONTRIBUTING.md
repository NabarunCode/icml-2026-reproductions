# Contributing

This repository holds honest, scientific reproductions of ML papers. The
bar for contributions is scientific integrity first, engineering polish
second, speed last. Read this page fully before opening a PR.

## Getting set up

Requirements: Python ≥ 3.11 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/NabarunCode/icml-2026-reproductions.git
cd icml-2026-reproductions
uv sync --all-packages     # installs repro-core + every paper package + dev tools
uv run pre-commit install  # ruff + mypy + hygiene checks on every commit
uv run pytest              # everything should pass before you change anything
```

The official reference implementations are git submodules and are **not**
needed to run tests. Fetch them only when studying a reference:

```bash
git submodule update --init
```

## Everyday commands

| Command | What it does |
|---|---|
| `uv run pytest` | All tests: shared infrastructure + every paper. |
| `uv run ruff check .` / `uv run ruff format .` | Lint / format. |
| `uv run mypy .` | Strict type-checking (zero errors is the baseline). |
| `uv run repro-env out.json` | Capture the current environment (used by every benchmark). |
| `uv run pre-commit run --all-files` | Everything CI runs, locally. |

CI (`.github/workflows/ci.yml`) runs ruff, mypy, and pytest on every push
and pull request. A red CI is never merged.

## Non-negotiable rules

These are the repository's reason to exist. PRs that violate them are
rejected regardless of code quality:

1. **Never fabricate.** No invented benchmark numbers, no extrapolated
   results presented as measured, no placeholder data that looks real.
2. **Never claim reproduction without evidence.** A claim's verdict must
   be backed by a runnable experiment committed in this repository.
3. **Never hide failed experiments.** Negative and partial results are
   documented with the same rigor as positive ones.
4. **Never modify an experiment after the fact to match a paper's
   numbers.** If our result diverges, the divergence is the finding.
5. **Never blur independent reproduction and reference code.** Every
   paper directory carries a `PROVENANCE.md` classifying each source
   file; keep it accurate when you touch anything.

## Code style

- Python ≥ 3.11, strongly typed (`mypy --strict` must pass), PEP 8 via
  ruff (config in `pyproject.toml` — line length 100).
- Docstrings on public functions; small, single-purpose functions.
- No speculative abstraction: shared code goes in `src/repro_core/` only
  once a **second** paper actually needs it.
- Correctness claims are backed by tests, not by inspection — prefer
  differential tests against an oracle over example-based assertions
  (see `papers/incremental-bpe-tokenization/experiments/README.md`
  "Verification approach" for the house style).

## Adding a new paper

1. Create `papers/<paper-slug>/` with the standard skeleton (see
   `docs/ARCHITECTURE.md` for the canonical layout).
2. Add the paper's `experiments/` directory as a package with its own
   `pyproject.toml` — the uv workspace (`papers/*/experiments`) picks it
   up automatically; `uv sync --all-packages` and `uv run pytest` will
   include it with no root-config changes.
3. Pin the official implementation (if any) as a git submodule under
   `papers/<paper-slug>/references/`, pinned to a tag, never a branch.
4. Add a `## Paper N` section to `docs/ROADMAP.md` and follow the
   eight-phase workflow in `docs/WORKFLOW.md` — phases are never skipped.
5. Write the paper's `PROVENANCE.md` before Phase 4 code lands.

## Benchmarks

Follow `docs/BENCHMARK_PROTOCOL.md` exactly — warm-up, repetitions,
mean and variance, `environment.json` via `repro_core`, raw samples
committed. Fill in `docs/REPRODUCIBILITY_CHECKLIST.md` for every
published result.

## Pull requests

- One logical change per PR; reference the paper/claim it advances.
- Update the relevant claim `README.md` and `docs/ROADMAP.md` status in
  the same PR as the code that changes them.
- Test fixtures derived from third-party sources (reference test suites,
  datasets) must say so where they are defined, with a pointer to how
  they were obtained.
