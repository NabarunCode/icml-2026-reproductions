"""Real-vocabulary tests: GPT-2 (50k tokens) loaded into incbpe.

The data files are committed with provenance (see
``papers/incremental-bpe-tokenization/benchmarks/data/README.md``), so
these tests run in CI too — the reproduction is exercised at real scale
on every push, not just on toy fixtures.

The load is cached at module level: ~2 s once, shared by all tests.
"""

from __future__ import annotations

import functools
import random
import unittest
from pathlib import Path

from incbpe.fast_bpe import tokenize_pq
from incbpe.gpt2 import Gpt2Dictionary, bytes_to_unicode, load_gpt2
from incbpe.incremental import IncrementalTokenizer
from incbpe.oracle import tokenize_with_last_rule
from incbpe.successor_forest import build as build_forest
from incbpe.vocab import TokenId

DATA = Path(__file__).resolve().parents[2] / "benchmarks" / "data" / "gpt2"

SAMPLE_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "Incremental BPE tokenization holds stable throughput on streaming input. "
    "def tokenize(s: str) -> list[int]:\n    return [ord(c) for c in s]\n"
    "Ünïcödé bytes müssen auch funktionieren — 日本語too. \t 12345!!\n"
)


@functools.cache
def _gpt2() -> Gpt2Dictionary:
    return load_gpt2(DATA / "vocab.json", DATA / "merges.txt")


@functools.cache
def _tokenizer() -> IncrementalTokenizer:
    g = _gpt2()
    return IncrementalTokenizer.build(g.normalized, build_forest(g.normalized))


def _atomic_ids(data: bytes) -> list[TokenId]:
    vocab = _gpt2().normalized.dict.vocab
    ids = []
    for byte in data:
        tid = vocab.find_token_id(bytes([byte]))
        assert tid is not None
        ids.append(tid)
    return ids


class Gpt2LoaderTest(unittest.TestCase):
    def test_byte_unicode_bijection(self) -> None:
        table = bytes_to_unicode()
        self.assertEqual(len(table), 256)
        self.assertEqual(len(set(table.values())), 256)

    def test_vocabulary_statistics(self) -> None:
        n = _gpt2().normalized
        total = len(n.dict.vocab)
        self.assertEqual(total, 50258)  # 50257 GPT-2 tokens + empty-string sentinel
        atomic = [t for t in range(total) if n.is_atomic(t)]
        self.assertEqual(len(atomic), 256)  # full byte alphabet present
        non_canonical = [t for t in range(total) if not n.is_canonical(t)]
        # Exactly the sentinel and the special token no merge produces.
        self.assertEqual([n.dict.vocab[t] for t in non_canonical], [b"", b"<|endoftext|>"])

    def test_fast_path_agrees_with_oracle_on_sampled_tokens(self) -> None:
        """The proper-dictionary assumption for GPT-2 is checked, not assumed.

        The full oracle over all 50k tokens is infeasible in a unit test
        (O(vocab x rules)); a seeded sample keeps the check honest and
        CI-fast. A failure here would mean GPT-2 is not proper and the
        whole fast-normalization path is invalid for it - loudly.
        """
        g = _gpt2()
        n = g.normalized
        rng = random.Random(20260718)
        candidates = [t for t in range(len(n.dict.vocab)) if n.dict.vocab[t] and not n.is_atomic(t)]
        for token_id in rng.sample(candidates, 12):
            ids = _atomic_ids(n.dict.vocab[token_id])
            with self.subTest(token=n.dict.vocab[token_id]):
                result, last_rule = tokenize_with_last_rule(g.dictionary, ids)
                is_canonical_oracle = result == [token_id]
                self.assertEqual(is_canonical_oracle, n.is_canonical(token_id))
                if is_canonical_oracle:
                    self.assertEqual(last_rule, n.priority[token_id])

    def test_incremental_matches_fast_bpe_on_real_text(self) -> None:
        g = _gpt2()
        data = SAMPLE_TEXT.encode()
        run = _tokenizer().new_run()
        run.feed_all(data)
        self.assertEqual(run.tokens(), tokenize_pq(g.dictionary, _atomic_ids(data)))

    def test_against_hf_tokenizers_if_available(self) -> None:
        """External differential: our whole pipeline vs HF `tokenizers`.

        Uses the HF BPE model directly with no pre-tokenizer, feeding
        text through the GPT-2 byte->unicode mapping, so both sides
        solve the identical whole-string BPE problem.
        """
        try:
            from tokenizers import Tokenizer
            from tokenizers.models import BPE
        except ImportError:
            self.skipTest("tokenizers (bench extra) not installed")

        hf = Tokenizer(BPE.from_file(str(DATA / "vocab.json"), str(DATA / "merges.txt")))
        table = bytes_to_unicode()
        g = _gpt2()
        for text in (SAMPLE_TEXT, "hello world", "  \n\t", "aaaaaaaaaaaaaaaaaaaaaaaa"):
            data = text.encode()
            mapped = "".join(table[b] for b in data)
            hf_ids = hf.encode(mapped, add_special_tokens=False).ids
            run = _tokenizer().new_run()
            run.feed_all(data)
            with self.subTest(text=text[:30]):
                self.assertEqual(g.to_gpt2_ids(run.tokens()), hf_ids)


if __name__ == "__main__":
    unittest.main()
