# Framework

Reusable research tooling shared across every paper in this repository —
benchmarking harnesses, correctness/differential-testing utilities,
environment-capture helpers, plotting conventions.

Nothing paper-specific belongs here. If a utility is only ever used by one
paper, it stays in that paper's `experiments/` code until a second paper
actually needs it — do not build shared abstractions speculatively.

Empty as of Phase 0 for the Incremental BPE Tokenization paper; expect the
first additions once Phase 4/5 work needs a shared benchmarking harness
(warm-up + multi-iteration timing + environment capture, per the
benchmarking standard in the root `README.md`).
