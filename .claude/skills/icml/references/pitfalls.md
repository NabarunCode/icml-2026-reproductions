# Pitfalls this repo has already hit once

Concrete traps, each with what actually went wrong and the fix — not
hypothetical advice. Read before Phase 4 and Phase 5 especially; most
of these are about quietly fooling yourself with your own tooling
rather than about the paper itself.

## "Local tests pass" is not "CI is green"

A CI quality gate (a stricter mypy config, a different Python version,
a lint rule not enforced locally) can fail on GitHub while every local
check passes, and it can go unnoticed indefinitely if you only ever
check locally. This repo had a real `mypy` job fail on **every push for
a full day** before anyone checked GitHub Actions directly, because the
habit was "run `uv run pytest` locally, call it done." After every
push: check the actual run status on GitHub (the GitHub Actions tools —
`list_workflow_runs` filtered to your branch, `get_job_logs` on any
failure), not just your own sandbox.

Relatedly: a repo's CI status badge can look stale or wrong for two
unrelated reasons — (a) it's genuinely still red, or (b) it's cached
(GitHub's badge SVG sits behind a CDN plus your browser's own image
cache for a few minutes). Don't assume either without checking; the
authoritative signal is the commit-status checkmark next to the actual
commit on GitHub, not the badge image.

## A quietly-introduced strict check can break a benchmark's own record-keeping

Chicken-and-egg example: an `environment.json` capture that checks
`git status` to set a "dirty" flag will report dirty on almost every
re-run once the benchmark's own prior output (`results.json`,
`environment.json`) is already committed from an earlier run — because
the new run overwrites those tracked files *before* the dirty check
fires (if the capture call happens after results are written). This
isn't a bug to "fix" by hiding it; state plainly in the environment
record what caused the dirty flag (the run's own output, not a source
change) so the record stays honest rather than silently wrong or
silently suppressed.

More generally: when a benchmark script or environment-capture helper
is shared across runs, a subtle correctness bug in it corrupts *every*
result that used it, not just one. Treat bugs in shared benchmark
infrastructure (e.g. a "first distribution wins" vs "last wins" bug
when capturing package versions under a version-override like
`uv run --with pkg==X`) as data-integrity incidents: fix the root
cause, and correct affected records with an explicit note rather than
silently editing already-published numbers after the fact.

## Type-checker config can drift out of sync with installed dependencies

A `mypy` config pinned to an old `python_version` floor can start
failing not because of anything in your own code, but because a
third-party dependency's own bundled type stubs adopt newer syntax
(e.g. a PEP-695 `type` statement requiring Python 3.12) that the older
target can't parse. If this happens: check whether the failure is in
*your* code or in a stub file under `site-packages` — if it's the
latter, the fix is usually to bump the type-checker's target version
(the actual *runtime* floor stays enforced by your CI test matrix's
real interpreters, which is a stronger check anyway), not to silence
the error or exclude the dependency.

## A baseline library's behavior can have moved since the paper was written

If a claim's baseline (a specific library version, a specific
tokenizer, a specific dataset) no longer reproduces the paper's
qualitative effect with the *current* release, don't conclude the
paper overclaimed and don't quietly re-run against an old version
without saying so either. Do the version archaeology: measure against
the era-appropriate release (pin it, e.g. via `uv run --with pkg==X`),
confirm the paper's effect *does* reproduce there, and report **both**
findings side by side — the historical reproduction and the
current-environment result. A reproduction that only checks today's
release and calls it a failure would be wrong; a paper's claim about a
specific past baseline is still worth confirming precisely.

## Egress/compute blockers are a request to make, not a reason to approximate

If a benchmark needs a file, dataset, or compute resource the current
sandbox can't reach (blocked egress, no GPU, an expired token scope),
the honest move is either (a) ask the user for the specific unblock —
a hash-pinned file upload, a network allowlist addition, a token with
the right permission scope — or (b) park a fully-specified, ready-to-
run command naming the exact blocker, in the relevant
`benchmarks/README.md`. Don't substitute a synthetic proxy for the real
thing and report it as if it answered the same question — a systems
paper's claim about a *specific* real library or dataset isn't
answered by a stand-in that merely resembles it.

Two specific token/permission traps worth knowing about ahead of time:
- An API token can be valid for normal read/write operations but lack a
  separate, more specific permission scope (e.g. a compute-jobs
  feature) — a 403 naming a specific missing permission is not the
  same failure as a bad/expired token, and needs a differently-scoped
  token, not just a fresh copy of the same kind.
- If a token was ever pasted into chat/a shared channel, treat it as
  compromised regardless of whether it still appears to work — flag it
  for rotation immediately rather than continuing to use it silently.

## Differential testing against an oracle catches your own refactoring bugs

When cleaning up code for lint/type-check compliance, an "obviously
safe" tightening (e.g. adding `strict=True` to a `zip()` call during a
lint pass) can silently break correctness if the underlying data
genuinely has variable-length sequences by design. This repo caught
exactly that during a routine ruff-driven cleanup, because a
differential test suite (comparing output against an independent
oracle across many random cases) failed immediately. The lesson isn't
"avoid `zip(strict=True)`" — it's that a broad, cheap differential
test suite run after every refactor is what catches this class of
mistake, and it's worth having one for any core algorithm before doing
mechanical cleanup passes on it.
