"""Shared test fixtures, notably the recovered Figure-2-variant example.

See ``papers/incremental-bpe-tokenization/paper/implementation-notes.md``
for how this exact vocabulary and rule list was recovered (verbatim, in
this priority order) from the reference implementation's own test suite,
and how it was cross-checked against the paper's Figure 2 (13 of its 14
rules - missing only rule 13, "cef").
"""

from __future__ import annotations

from incbpe.dictionary import Dictionary
from incbpe.normalize import NormalizedDict, normalize
from incbpe.successor_forest import SuccessorForest, build as build_forest
from incbpe.vocab import Vocab

FIGURE2_VARIANT_VOCAB = [
    "",
    "a",
    "abc",
    "abcde",
    "abcdef",
    "b",
    "ba",
    "bc",
    "bcdef",
    "c",
    "cd",
    "cde",
    "cdefg",
    "d",
    "de",
    "def",
    "e",
    "ef",
    "efg",
    "f",
    "g",
]

FIGURE2_VARIANT_RULES = [
    ("b", "c"),
    ("e", "f"),
    ("d", "e"),
    ("c", "d"),
    ("d", "ef"),
    ("b", "a"),
    ("a", "bc"),
    ("abc", "de"),
    ("abc", "def"),
    ("bc", "def"),
    ("c", "de"),
    ("ef", "g"),
    ("cd", "efg"),
]


def build_figure2_variant() -> tuple[NormalizedDict, SuccessorForest]:
    vocab = Vocab.new(FIGURE2_VARIANT_VOCAB)
    dictionary = Dictionary.new(vocab, FIGURE2_VARIANT_RULES)
    normalized = normalize(dictionary, lambda _tid, token: len(token) == 1)
    forest = build_forest(normalized)
    return normalized, forest


def token_id(normalized: NormalizedDict, name: str) -> int:
    tid = normalized.dict.vocab.find_token_id(name.encode())
    assert tid is not None, f"token {name!r} not in vocab"
    return tid
