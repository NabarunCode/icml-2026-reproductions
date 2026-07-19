# Benchmark data — real tokenizer files

Provenance record for every data file used by this paper's benchmarks.
All files below were uploaded by the project owner on 2026-07-18
(sandbox egress blocks direct download; the checklist's "acquisition
command" rows therefore document the original source URLs).

## `gpt2/` (committed — MIT license, OpenAI)

The GPT-2 / R50K byte-level BPE tokenizer definition. **Cross-source
verified:** the copy fetched from the Hugging Face Hub is byte-identical
to the copy served by OpenAI's own CDN (same SHA256), so either source
reproduces these exact files.

| File | SHA256 | Sources |
|---|---|---|
| `vocab.json` (50 257 entries) | `196139668be63f3b5d6574427317ae82f612a97c5d1cdaf36ed2256dbf636783` | `https://huggingface.co/openai-community/gpt2/resolve/main/vocab.json` ≡ `https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/encoder.json` |
| `merges.txt` (50 000 merges) | `1ce1664773c50f3e0cc8842619a93edc4624525b728b188a9e0be33b7726adc5` | `https://huggingface.co/openai-community/gpt2/resolve/main/merges.txt` ≡ `https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/vocab.bpe` |

## `codellama/` (NOT committed — Meta Llama license)

`tokenizer.json` (BPE, 32 016 tokens, 61 260 merges) from
`https://huggingface.co/codellama/CodeLlama-7b-hf/resolve/main/tokenizer.json`
(requires accepting Meta's license on the model page). Kept out of git
deliberately; to reproduce, download it to
`benchmarks/data/codellama/tokenizer.json` and verify:

    SHA256 dcb4337ba92f948b322e080f8b59a2a21cfe65dc2aa7ecf7df080ae8aa63c157

Not yet used by any benchmark: CodeLlama is SentencePiece-semantics and
needs the Appendix A properization work first (see experiments README,
Limitations).

## `tiktoken/` (encoding files, downloaded 2026-07-19 after network-policy change)

Fetched directly from OpenAI's CDN once the environment's network
allowlist was updated (no upload needed):

| File | SHA256 | Committed? | Source |
|---|---|---|---|
| `cl100k_base.tiktoken` (1.68 MB) | `223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7` | yes | `https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken` |
| `o200k_base.tiktoken` (3.6 MB) | `446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d` | no (exceeds 2 MB large-file cap; re-download + verify) | `https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken` |

These SHA256 values match the checksums tiktoken itself pins for these
encodings, cross-confirming integrity.
