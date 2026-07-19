# Benchmarks — Incremental BPE Tokenization

Phase 5 benchmark scripts + raw run output, all following
`docs/BENCHMARK_PROTOCOL.md` (warm-up 3, repeats >=10, raw samples +
`environment.json` committed, clean git tree enforced by the dirty
flag). Curated write-ups live in `../results/`.

| Script | Measures |
|---|---|
| `claim4_pathological.py` | scaling shape on 'a'*n, synthetic dictionary: ours vs restart-per-byte vs batch oracle |
| `claim4_real_vocab.py` | real GPT-2 vocab: ours (flat) vs tiktoken (current), token-for-token cross-checked, to 8 MB |
| `claim4_tiktoken_regression.py` | era-appropriate tiktoken 0.8.0 (run via `uv run --with tiktoken==0.8.0`), version hard-asserted |
| `claim4_tiktoken_cl100k.py` | the claim's named tokenizer (CL100K), both tiktoken eras, encoding hash-verified |
| `claim2_depth_scaling.py` | missing-centroid cost: amortized (flat) + worst single-feed latency (linear in depth) |
| `claim3_throughput_gpt2.py` | paper's English recipe: corpus-scale correctness vs HF tokenizers, eager overhead, baseline throughputs |

`data/` holds hash-pinned vocabulary/encoding files (see
`data/README.md` for provenance); `runs/` holds one directory per
protocol-grade run.

## Pending: HF Jobs corroboration re-run

Every run above carries the caveat "shared multi-tenant VM, idleness
not guaranteed." A one-shot re-run of the full suite on HF Jobs
hardware would corroborate the slopes in a second, quieter environment.
**Blocked on token scope**: submission returns 403 `job.write` — the
configured HF token lacks the Jobs permission. Fix: create a token with
**Jobs write** access (fine-grained token -> enable Jobs; and prefer
`--namespace ICML-2026-agent-repro` so the org credit is billed), then:

```bash
hf jobs run --detach --flavor cpu-upgrade --timeout 2h -s HF_TOKEN \
  --namespace ICML-2026-agent-repro --name icml-repro-corroboration \
  python:3.12 bash -c '
set -ex
pip -q install uv "huggingface_hub[cli]"
git clone --depth 1 -b claude/icml-2026-reproductions-handover-zvye6y https://github.com/NabarunCode/icml-2026-reproductions repo
cd repo && uv sync --all-packages --all-extras && uv run pytest
P=papers/incremental-bpe-tokenization
uv run python $P/benchmarks/claim4_pathological.py
uv run python $P/benchmarks/claim2_depth_scaling.py
uv run python $P/benchmarks/claim4_real_vocab.py
uv run --with tiktoken==0.8.0 python $P/benchmarks/claim4_tiktoken_regression.py
uv run python $P/benchmarks/claim4_tiktoken_cl100k.py
uv run --with tiktoken==0.8.0 python $P/benchmarks/claim4_tiktoken_cl100k.py
uv run python $P/scripts/fetch_wikipedia_sample.py
uv run python $P/benchmarks/claim3_throughput_gpt2.py
tar czf /tmp/runs.tgz -C $P/benchmarks runs
hf upload hinabarun/icml-repro-corroboration-runs /tmp/runs.tgz hfjobs-cpu-upgrade-runs.tgz --repo-type dataset
echo CORROBORATION-JOB-DONE'
```

Results land in the (already-created) dataset repo
`hinabarun/icml-repro-corroboration-runs`; fold them into `../results/`
as a corroboration section when available. Note: the verdicts do not
depend on this — they rest on scaling *shapes*, which are robust to VM
noise; this is belt-and-suspenders.
