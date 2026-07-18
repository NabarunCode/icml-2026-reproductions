# Workflow

Every paper in this repository moves through the same eight phases, in
order. Phases are not skipped, and a phase is not started until the
previous one has a written artifact to show for it (a doc, a folder, a
script — something a reviewer could read).

| Phase | Name | Deliverable |
|---|---|---|
| 0 | Repository setup | Directory structure, docs scaffold, official resources downloaded/linked, reference implementation identified, roadmap drafted, Trackio prepared. |
| 1 | Read paper | Notes on the paper's claims, in the paper's own words, before any interpretation. |
| 2 | Understand theory | Plain-language + mathematical explanation of *why* the method works, independent of any code. |
| 3 | Understand implementation | Mapping from the paper's theory to the reference implementation's actual code structure. |
| 4 | Implement | Our own reproduction code (not a copy of the reference implementation), with the paper's `PROVENANCE.md` classifying every source file's independence. |
| 5 | Benchmark | Rigorous, reproducible measurement per `docs/BENCHMARK_PROTOCOL.md`, with `environment.json` and a completed `docs/REPRODUCIBILITY_CHECKLIST.md` per published result. |
| 6 | Verify claims | Each claim from Phase 1 gets a verdict: reproduced, partially reproduced, or not reproduced — with evidence either way. |
| 7 | Trackio | Publish the reproduction as a Trackio logbook per the paper's challenge rules (see `papers/<paper-slug>/trackio/README.md`). |
| 8 | GitHub documentation | Final write-up suitable for public consumption: what we found, how, and what's missing. |

## Why this order

Phase 0 exists so that repository structure and sourcing decisions aren't
made ad hoc mid-implementation. Phases 1–3 are read-only and produce no
code — they exist to prevent the common failure mode of translating code
into more code without understanding *why* it's correct. Phase 4
(implementation) is deliberately *after* theory and reference-implementation
understanding, not before, so implementation choices can be justified by
Phase 2/3 notes rather than reverse-engineered from mismatched benchmark
numbers later.

## Claim verification (Phase 6)

Every claim gets its own folder under `papers/<paper-slug>/claims/`, with a
consistent structure so results are comparable and auditable:

```
claims/<NN>-<claim-slug>/
  README.md         # Explanation, Mathematics, Implementation, Experiment,
                     # Benchmark, Result, Discussion, Limitations, Conclusion
```

A claim is never marked "verified" without a runnable experiment behind it
in this repository. If a claim cannot be tested with available compute, the
folder says so explicitly rather than being left silently empty.

## Inference X-Ray hook

This repository feeds a separate educational project, **Inference X-Ray**.
Whenever implementation or theory work surfaces a tokenizer concept that
would make a good standalone teaching chapter (e.g., a data structure, an
algorithmic idea, a subtle correctness property), we flag it explicitly in
the relevant claim's `README.md` under a `> Inference X-Ray candidate` note,
rather than writing the chapter here. This repository's job is to decide
*whether* something is teachable, not to author the teaching material.
