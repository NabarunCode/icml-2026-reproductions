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

## Done: HF Jobs corroboration re-run (2026-07-19)

Every run above carries the caveat "shared multi-tenant VM, idleness
not guaranteed." The full suite was re-run on dedicated HF Jobs
compute (`cpu-upgrade` flavor, 64-core) to check whether the measured
slopes hold on quieter hardware — see
[`../results/corroboration-hfjobs.md`](../results/corroboration-hfjobs.md)
for the full side-by-side table. Headline: every slope reproduces
within ±0.03 of the sandbox measurement; no verdict changed. Raw data:
`runs/hfjobs-corroboration/<script>/` (committed alongside the
originals) and the job's own upload,
[`hinabarun/icml-repro-corroboration-runs`](https://huggingface.co/datasets/hinabarun/icml-repro-corroboration-runs).

Rerun command (same one the job used):

```bash
hf jobs run --detach --flavor cpu-upgrade --timeout 2h -s HF_TOKEN \
  --name icml-repro-corroboration \
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

(Ran under the personal namespace — the `ICML-2026-agent-repro` org
namespace still returns 403 `job.write` even with the current token;
the personal namespace worked and billed to the account's own credit.)
