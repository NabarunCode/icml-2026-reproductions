"""Fetch the paper's English dataset sample (Appendix H.2, Table 2).

The paper samples English Wikipedia from the 20231101 dump by taking
every 42nd document until ~16.5 MB. This script reproduces that
recipe against the ``wikimedia/wikipedia`` dataset on the Hugging Face
Hub, **pinned by revision** so the sample is reproducible:

    revision b04c8d1ceb2f5cd4588862100d08de323dccfbaa (2024-01-09)

Output: ``benchmarks/data/datasets/wikipedia_en_20231101_stride42.jsonl``
(one JSON object per document: ``{"id", "title", "bytes", "text"}``)
plus a ``.provenance.json`` sidecar recording revision, stride, document
count, total bytes, and the output file's SHA256. The sample itself is
NOT committed (16.5 MB); anyone can regenerate it with this script and
verify the hash against the committed sidecar.

Requires network access to huggingface.co and the ``datasets`` package
(bench extra). Run from the repository root:

    uv run python papers/incremental-bpe-tokenization/scripts/fetch_wikipedia_sample.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DATASET = "wikimedia/wikipedia"
CONFIG = "20231101.en"
REVISION = "b04c8d1ceb2f5cd4588862100d08de323dccfbaa"
STRIDE = 42  # paper: every 42nd English document
TARGET_BYTES = 16_500_000  # paper: ~16.5M bytes

OUT_DIR = Path(__file__).resolve().parents[1] / "benchmarks" / "data" / "datasets"
OUT_FILE = OUT_DIR / "wikipedia_en_20231101_stride42.jsonl"


def main() -> None:
    from datasets import load_dataset  # bench extra; imported late for a clear error

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stream = load_dataset(DATASET, CONFIG, revision=REVISION, streaming=True, split="train")

    total_bytes = 0
    num_docs = 0
    with OUT_FILE.open("w", encoding="utf-8") as out:
        for i, doc in enumerate(stream):
            if i % STRIDE != 0:
                continue
            text = doc["text"]
            record = {
                "id": doc["id"],
                "title": doc["title"],
                "bytes": len(text.encode("utf-8")),
                "text": text,
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            total_bytes += record["bytes"]
            num_docs += 1
            if total_bytes >= TARGET_BYTES:
                break

    digest = hashlib.sha256(OUT_FILE.read_bytes()).hexdigest()
    provenance = {
        "dataset": DATASET,
        "config": CONFIG,
        "revision": REVISION,
        "stride": STRIDE,
        "target_bytes": TARGET_BYTES,
        "documents": num_docs,
        "text_bytes_total": total_bytes,
        "output_file": OUT_FILE.name,
        "output_sha256": digest,
    }
    sidecar = OUT_FILE.with_suffix(".provenance.json")
    sidecar.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
