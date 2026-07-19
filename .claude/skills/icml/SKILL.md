---
name: icml
description: Use this skill whenever working on a paper reproduction in the icml-2026-reproductions repository — starting a brand-new paper, resuming an in-progress one, or moving a paper forward a phase. Trigger on things like "let's add the next paper", "start reproducing <paper>", "continue phase 5 for <paper>", "verify claim 2", "publish the logbook", or any mention of a paper title / arXiv id / OpenReview id / challenge id in the context of this repo — even if the user doesn't say "phase" or name this skill explicitly. Also consult it right after pushing any commit to this repo, to confirm CI is actually green on GitHub itself, not just locally. Do not use it for unrelated engineering work in this repo (CI config, README styling, general refactors) unless that work is part of moving a specific paper through its phases.
---

# ICML Paper Reproduction

This repo exists to produce reproductions that are actually trustworthy,
not reproductions that merely look finished. That only works if every
paper goes through the same eight phases, in order, with a real
evidence artifact at each step — and if the five rules below are never
bent for the sake of finishing faster.

## The five rules everything else serves

1. **Never fabricate.** No invented numbers, no extrapolated results
   presented as measured, no placeholder data dressed up as real.
2. **Never claim reproduction without evidence.** Every verdict traces
   to a runnable, committed experiment.
3. **Never hide a failure.** A negative or partial result is documented
   with the same rigor as a positive one — it is not a defect in the
   work, it's the work.
4. **Never move the goalposts.** If a result diverges from the paper,
   the divergence *is* the finding. Don't adjust the experiment until it
   agrees.
5. **Provenance stays explicit.** Every paper's `PROVENANCE.md`
   classifies each source file as independent (A) or reference-derived
   (B), kept accurate as code changes.

If a step you're about to take would violate one of these to save time,
stop and do the honest, slower thing instead. This is the entire reason
the repo exists; nothing downstream (a green CI badge, a clean-looking
README, a finished-looking Trackio page) matters if these bend.

## First: figure out where this paper actually is

Before doing anything, check `docs/ROADMAP.md`:

- **Not listed yet** → this is a new paper. Confirm its identity with
  the user if anything is ambiguous (exact title, venue, arXiv id,
  OpenReview id, challenge id, official implementation repo) — don't
  guess these from memory. Start at Phase 0.
- **Already listed** → read its `☑`/`◐`/`☐`/`✗` row and the paper's own
  `papers/<slug>/README.md` to find the *true* current phase. Resume
  there — never restart from Phase 0, and never skip ahead of what the
  roadmap actually shows evidence for. If the roadmap claims a phase is
  done, spot-check that the evidence really exists (a committed run, a
  filled-in claims file) before building on top of it; roadmaps can
  drift from reality if a phase was marked complete prematurely.

## The eight phases

Never skipped, never reordered, and a phase doesn't start until the
previous one has a real artifact — a doc, a folder, a script, a
committed run — that a reviewer could independently check.

| # | Phase | Deliverable |
|---|---|---|
| 0 | Repository setup | `papers/<slug>/` skeleton, official resources identified, `docs/ROADMAP.md` entry |
| 1 | Read paper | `notes/reading-notes.md` — claims in the paper's own words, no interpretation yet |
| 2 | Understand theory | `notes/theory-notes.md` — plain-language + mathematical why, independent of any code |
| 3 | Understand reference implementation | `notes/implementation-notes.md` — paper-section-to-code map; reference pinned as a submodule |
| 4 | Implement | `experiments/` installable package + tests + `PROVENANCE.md` |
| 5 | Benchmark | `benchmarks/` scripts + raw runs, `results/` with `environment.json` per run |
| 6 | Verify claims | `claims/<NN>-slug>/README.md` verdict, per claim, with evidence |
| 7 | Publish Trackio logbook | Published HF Space, validator-green |
| 8 | GitHub documentation | Paper README outcome section, root README row, roadmap updated |

Full per-phase checklists, gating questions, and file templates are in
[`references/phases.md`](references/phases.md) — read the section for
whichever phase you're actually starting. Don't try to hold all eight
phases' detail in your head at once; load the one you need.

## Operating principles that apply across every phase

- **Measure, don't reason, whenever a claim is measurable.** If a claim
  names a specific baseline library or dataset, install/fetch the real
  thing and run it rather than approximating its behavior from memory.
- **Blocked compute is not skipped compute.** If a benchmark can't run
  in the current sandbox (no egress, no GPU, quota), park a
  fully-specified, ready-to-run command with the exact blocker named —
  in the relevant `benchmarks/README.md` — rather than silently omitting
  the measurement or reporting an approximation as if it were real.
- **A conflict with the paper is a finding, not a bug to smooth over.**
  If a baseline's behavior has drifted since the paper was written (a
  library fixed something, hardware moved on), report both the
  era-appropriate reproduction and the current-environment result
  side by side. See `references/pitfalls.md` for a worked example.
- **After every push, verify CI on GitHub itself — not just a local
  test run.** This repo already learned this the hard way once: a real
  failure in the `mypy` quality gate sat unnoticed in GitHub Actions for
  a full day because only `uv run pytest` had been checked locally.
  Local passing tells you your working tree is fine; it tells you
  nothing about whether the CI config, a stricter job, or a different
  Python version agrees. Use the GitHub Actions tools
  (`actions_list` → `list_workflow_runs`, `get_job_logs` on failure) to
  confirm every job on the pushed commit is green before considering
  the push done.
- **Git hygiene:** develop on the branch you've been assigned, commit
  with messages that explain *why*, push with retry-with-backoff on
  transient network errors, and never force-push or rewrite already-
  pushed history unless explicitly asked — even to "clean up" a commit
  message you don't love.

## Reference files

- [`references/phases.md`](references/phases.md) — the detailed
  per-phase playbook: what to produce, what question to ask yourself
  before calling a phase done, and where it lives in the repo.
- [`references/trackio.md`](references/trackio.md) — Phase 7's
  mechanics specifically (the challenge's scaffold/validate scripts,
  mandatory page order and tags, and the handful of sharp edges those
  scripts have).
- [`references/pitfalls.md`](references/pitfalls.md) — concrete traps
  this repo has already fallen into and climbed out of once. Worth a
  read before Phase 4 (implement) and Phase 5 (benchmark) especially —
  they're the phases with the most ways to quietly fool yourself.
