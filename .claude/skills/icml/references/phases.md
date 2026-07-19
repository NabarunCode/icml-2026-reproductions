# Phase-by-phase playbook

For each phase: what to produce, the question to ask before calling it
done, and where it lives. The canonical process docs
(`docs/WORKFLOW.md`, `docs/ARCHITECTURE.md`, `docs/BENCHMARK_PROTOCOL.md`,
`docs/REPRODUCIBILITY_CHECKLIST.md`) are the authority on rules; this
file is the operational checklist for actually moving through them.

## Phase 0 — Repository setup

Create `papers/<paper-slug>/` with the standard skeleton (see
`docs/ARCHITECTURE.md` for the canonical layout — copy the shape, not
the content, from `papers/incremental-bpe-tokenization/` as a worked
example):

```
papers/<paper-slug>/
  README.md            # paper overview, authors, venue, links, one-paragraph summary
  PROVENANCE.md         # started now, filled in properly before Phase 4 code lands
  paper/                # the paper PDF
  supplementary/        # supplementary material, if any
  notes/
  claims/
  experiments/          # pyproject.toml added when Phase 4 starts, not before
  benchmarks/
  results/
  figures/
  scripts/
  references/           # official implementation submodule goes here (Phase 3)
  trackio/
```

Also do, before moving on:
- Add a `## Paper N — <title>` section to `docs/ROADMAP.md` with the
  phase table (all `☐` to start), the venue/arXiv/OpenReview/challenge
  ids, and the official implementation's repo link.
- Identify and record the official implementation repo (if one exists)
  — don't pin it as a submodule yet, that's Phase 3.
- Confirm with the user anything about the paper's identity you're not
  certain of (exact venue, ids) rather than guessing.

**Gate to Phase 1:** does `docs/ROADMAP.md` have a real row for this
paper, and does the folder skeleton exist?

## Phase 1 — Read paper

Write `notes/reading-notes.md`: the paper's claims *in the paper's own
words*, before any interpretation or judgment about feasibility. This
phase produces no code and no opinions yet — its job is to prevent the
common failure of jumping straight to "how would I implement this"
before being sure what "this" actually claims.

Also extract the specific, numbered claims the reproduction will
target (a challenge listing, if one exists, usually enumerates them —
cross-check its wording against the paper text itself rather than
trusting the listing blindly).

**Gate to Phase 2:** could someone who has never read the paper
understand its claims from your notes alone, without you being in the
room?

## Phase 2 — Understand theory

Write `notes/theory-notes.md`: a plain-language and mathematical
explanation of *why* the method works, independent of any code. If the
paper has a structural or correctness proof (a theorem, an invariant),
work through it and, where practical, build and mechanically verify a
small example of your own — don't just trust the paper's own worked
example or figure; those are illustrations, not evidence you generated.

**Gate to Phase 3:** if the reference implementation didn't exist,
could you still explain to someone why the method is correct?

## Phase 3 — Understand reference implementation

If an official implementation exists: pin it as a git submodule under
`papers/<paper-slug>/references/<name>/`, at a specific **release tag**
(never a branch — branches move, tags don't). Write
`notes/implementation-notes.md` mapping the paper's sections to the
reference's actual module structure.

Where possible, **run the reference's own test suite** rather than
just reading its source — its own tests are often the best available
ground truth (e.g. a worked example the authors themselves validated),
and capturing their actual output beats re-deriving it by hand.

This phase is read-only with respect to your own reproduction code —
resist the urge to start writing Phase 4 code here just because you're
already looking at working code. Understanding the architecture before
writing your own implementation is fine and expected; transcribing
functions is not (see `PROVENANCE.md`'s classification rules below).

**Gate to Phase 4:** do you have a paper-section → reference-module map,
and (if the reference has tests) their own ground-truth output
captured somewhere you can diff against later?

## Phase 4 — Implement

Build the reproduction under `experiments/` as a proper installable
Python package (src layout, `py.typed` marker, its own `pyproject.toml`
as a `[tool.uv.workspace]` member — the workspace picks it up
automatically, no root config changes needed) with its own test suite.
Python-first by default; fall back to a native/Rust hot path only if
Python is a genuine blocker for demonstrating a specific claim
(document that decision inline where it's made, not just in a commit
message).

**Write `PROVENANCE.md` as code lands, not after.** For every source
file, classify it:
- **A — independent implementation**: written from the paper's own
  definitions (or classic literature), not translated from the
  reference. Deliberate divergences from the reference (a different
  mechanism that's still correct) are *positive* evidence of
  independence — note them explicitly rather than treating them as
  something to minimize.
- **B — reference-derived**: content taken from or shaped by the
  official implementation (code or data), documented explicitly,
  including test fixtures recovered from the reference's own test
  suite.

State the honest global caveat if Phase 3 studied the reference's
architecture before writing code: that's not a strict clean-room
reproduction, and the provenance doc should say so plainly rather than
implying otherwise.

**Gate to Phase 5:** does every source file appear in `PROVENANCE.md`
with an honest classification, and does the test suite pass?

## Phase 5 — Benchmark

Follow `docs/BENCHMARK_PROTOCOL.md` exactly — this is not optional
detail, it's the difference between a number and a citable result:
`perf_counter_ns`, GC disabled per sample, ≥3 warm-up runs discarded,
≥10 timed repetitions, mean **and** stdev (never a single number), raw
samples committed, `environment.json` via `repro_core.environment`
next to every result, clean git tree required for anything published.
Fill in `docs/REPRODUCIBILITY_CHECKLIST.md` per published run.

Two things worth over-investing in here:
- **Measure the actual thing the claim names.** If a claim says
  "vs. tiktoken", install real tiktoken and run it — don't approximate
  its behavior. If real data/vocab files are needed and blocked by
  sandbox egress, ask the user for a hash-pinned upload or an
  allowlist change rather than substituting synthetic data silently.
- **Use log-log slope analysis to characterize scaling shape** (slope
  ≈1 linear, ≈2 quadratic) — it's far more informative for an
  algorithmic-complexity claim than a single absolute number, and it's
  usually the part of a claim that survives hardware differences even
  when absolute numbers don't (see `docs/BENCHMARK_PROTOCOL.md` §7).

If compute is genuinely unavailable here (no GPU, blocked egress, quota
exhausted): park a fully-specified, ready-to-run command in the
relevant `benchmarks/README.md`, naming the exact blocker, rather than
skipping the measurement or reporting a proxy as if it answered the
question.

**Gate to Phase 6:** for every number you want to cite in a verdict, is
there a committed `results.json` + `environment.json` pair, produced on
a clean tree, that a stranger could regenerate from the exact command
recorded?

## Phase 6 — Verify claims

One folder per claim: `claims/<NN>-<claim-slug>/README.md`, with
Explanation, Mathematics, Implementation, Experiment, Benchmark,
**Result, Discussion, Limitations, Conclusion** sections. Every claim
gets an explicit verdict — reproduced / partially reproduced /
reproduced against a stated caveat / not reproduced / inconclusive —
and every number in that verdict links to a Phase 5 run.

A claim that can't be tested with available compute says so explicitly
in Limitations; it is never left silently empty, and it is never
marked verified without a runnable experiment behind it in this repo.

**Gate to Phase 7:** could a skeptical reader click through from each
claim's verdict to the exact committed run that justifies it?

## Phase 7 — Publish Trackio logbook

See [`trackio.md`](trackio.md) in this same directory for the specific
mechanics (scaffold/validate scripts, mandatory page order and tags,
known sharp edges). Only run this phase once Phases 1–6 have produced
real content for every claim page — the scaffold is structure, not
content, and publishing an empty scaffold is worse than not publishing.

**Gate to Phase 8:** does the validator pass, and does the published
page's artifact link resolve to a real bucket URL (not a
`trackio-artifact://` placeholder)?

## Phase 8 — GitHub documentation

Write a "Reproduction outcome" section at the **top** of
`papers/<paper-slug>/README.md`: a verdict table with headline evidence
per claim, the published logbook link, one-command rerun instructions,
and an honest "deliberately not done" list — each item paired with
whatever measured acceptance test would tell someone the gap has been
closed (not just a vague "future work" bullet).

Then:
- Add a new row to the root `README.md`'s Reproductions table — never
  overwrite or replace a finished paper's row with a new one.
- Update `docs/ROADMAP.md`'s phase table to `☑` across the board (or
  `✗`/partial with the specific remaining gap named).
- Re-verify the whole test suite is green and CI is green **on GitHub**
  (see the SKILL.md operating principle on this) before considering the
  paper finished.

**Done, for real:** all eight phases have a linkable artifact, nothing
was fabricated or hidden, and a stranger could clone the repo and
regenerate every cited number.
