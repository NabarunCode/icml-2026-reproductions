"""Load a real GPT-2-style byte-level BPE vocabulary into incbpe.

GPT-2's ``vocab.json``/``merges.txt`` (identical in content to OpenAI's
``encoder.json``/``vocab.bpe``; see
``papers/incremental-bpe-tokenization/benchmarks/data/README.md`` for
provenance) encode raw bytes through the well-known GPT-2
bytes<->unicode bijection so every token is printable text. This module
inverts that mapping so the incbpe pipeline can work on raw bytes,
which is what it models.

Token ids: incbpe reserves id 0 for the empty-string sentinel, so
``incbpe_id = gpt2_id + 1`` throughout. Cross-implementation
comparisons (tiktoken, HF tokenizers) must convert via
:func:`Gpt2Dictionary.to_gpt2_ids`.
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path

from incbpe.dictionary import Dictionary
from incbpe.fast_bpe import normalize_pq
from incbpe.normalize import NormalizedDict
from incbpe.vocab import TokenId, Vocab


@functools.cache
def bytes_to_unicode() -> dict[int, str]:
    """The standard GPT-2 byte -> printable-unicode-char bijection."""
    bs = (
        list(range(ord("!"), ord("~") + 1))
        + list(range(ord("\xa1"), ord("\xac") + 1))
        + list(range(ord("\xae"), ord("\xff") + 1))
    )
    cs = list(bs)
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return dict(zip(bs, (chr(c) for c in cs), strict=True))


@functools.cache
def unicode_to_bytes() -> dict[str, int]:
    return {c: b for b, c in bytes_to_unicode().items()}


def decode_token(mapped: str) -> bytes:
    """Invert the GPT-2 mapping: printable token text -> raw bytes."""
    table = unicode_to_bytes()
    return bytes(table[ch] for ch in mapped)


@dataclass(frozen=True)
class Gpt2Dictionary:
    """A real vocabulary loaded into incbpe, with the id offset recorded."""

    dictionary: Dictionary
    normalized: NormalizedDict
    id_offset: int  # incbpe_id = gpt2_id + id_offset

    def to_gpt2_ids(self, incbpe_ids: list[TokenId]) -> list[int]:
        return [tid - self.id_offset for tid in incbpe_ids]

    def to_incbpe_ids(self, gpt2_ids: list[int]) -> list[TokenId]:
        return [gid + self.id_offset for gid in gpt2_ids]


def load_gpt2(vocab_path: str | Path, merges_path: str | Path) -> Gpt2Dictionary:
    """Build the incbpe Dictionary + NormalizedDict from GPT-2 files.

    Normalization uses the fast dynamic-priority path
    (:func:`incbpe.fast_bpe.normalize_pq`) — required at 50k scale; its
    equivalence to the oracle on this vocabulary is spot-checked in
    ``tests/test_gpt2_loader.py`` rather than assumed.
    """
    raw_vocab: dict[str, int] = json.loads(Path(vocab_path).read_text(encoding="utf-8"))

    by_id = sorted(raw_vocab.items(), key=lambda kv: kv[1])
    expected_ids = list(range(len(by_id)))
    actual_ids = [gid for _, gid in by_id]
    if actual_ids != expected_ids:
        raise ValueError("vocab.json token ids are not contiguous from 0")

    tokens: list[bytes] = [b""] + [decode_token(text) for text, _ in by_id]
    vocab = Vocab.new(tokens)

    rule_pairs: list[tuple[bytes, bytes]] = []
    for line in Path(merges_path).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#version"):
            continue
        left, _, right = line.partition(" ")
        rule_pairs.append((decode_token(left), decode_token(right)))

    dictionary = Dictionary.new(vocab, rule_pairs)
    normalized = normalize_pq(dictionary, lambda _tid, token: len(token) == 1)
    return Gpt2Dictionary(dictionary=dictionary, normalized=normalized, id_offset=1)
