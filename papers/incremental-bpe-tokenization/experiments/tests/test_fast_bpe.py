"""Differential tests for the fast dynamic-priority BPE path.

``fast_bpe`` implements SentencePiece/HF-style dynamic priority, which
coincides with the standard fixed-schedule oracle on *proper*
dictionaries (the paper's Appendix A distinction). These tests pin that
down: exact agreement on the known-proper fixture families, and
structural invariants (never full agreement claims) on arbitrary random
dictionaries, where a legitimate semantic difference can exist.
"""

from __future__ import annotations

import itertools
import random
import unittest

from incbpe.dictionary import Dictionary
from incbpe.fast_bpe import normalize_pq, tokenize_pq, tokenize_pq_with_last_rule
from incbpe.fixtures import FIGURE2_VARIANT_RULES, FIGURE2_VARIANT_VOCAB
from incbpe.normalize import normalize
from incbpe.oracle import tokenize_with_last_rule
from incbpe.vocab import TokenId, Vocab


def _atomic_ids(vocab: Vocab, data: bytes) -> list[TokenId]:
    ids = []
    for byte in data:
        tid = vocab.find_token_id(bytes([byte]))
        assert tid is not None
        ids.append(tid)
    return ids


def _is_single_byte(_tid: TokenId, token: bytes) -> bool:
    return len(token) == 1


class FastBpeProperDictionaryTest(unittest.TestCase):
    """On known-proper dictionaries the fast path must equal the oracle."""

    def _assert_equal_everywhere(self, dictionary: Dictionary, strings: list[bytes]) -> None:
        for s in strings:
            ids = _atomic_ids(dictionary.vocab, s)
            with self.subTest(string=s):
                self.assertEqual(
                    tokenize_pq_with_last_rule(dictionary, ids),
                    tokenize_with_last_rule(dictionary, ids),
                )
        self.assertEqual(
            normalize_pq(dictionary, _is_single_byte),
            normalize(dictionary, _is_single_byte),
        )

    def test_figure2_variant(self) -> None:
        vocab = Vocab.new(FIGURE2_VARIANT_VOCAB)
        dictionary = Dictionary.new(vocab, FIGURE2_VARIANT_RULES)
        strings = [b"abcdefg", b"babcdefg", b"cdefg", b"", b"g"]
        rng = random.Random(20260718)
        alphabet = b"abcdefg"
        strings += [
            bytes(rng.choice(alphabet) for _ in range(rng.randint(1, 12))) for _ in range(100)
        ]
        self._assert_equal_everywhere(dictionary, strings)

    def test_repeated_character_family(self) -> None:
        vocab = Vocab.new([""] + ["a" * i for i in range(1, 17)])
        rule_sets = [
            [("a", "a")],
            [("a", "a"), ("aa", "a")],
            [("a", "a"), ("a", "aa")],
            [("a", "a"), ("aa", "a"), ("aa", "aa")],
            [("a", "a"), ("aa", "aa"), ("aa", "a"), ("aaaa", "a")],
        ]
        for rules in rule_sets:
            dictionary = Dictionary.new(vocab, rules)
            strings = [b"a" * n for n in range(0, 40)]
            with self.subTest(rules=rules):
                self._assert_equal_everywhere(dictionary, strings)


class FastBpeInvariantsTest(unittest.TestCase):
    """On arbitrary (possibly non-proper) dictionaries, only invariants."""

    def test_random_dictionaries_structural_invariants(self) -> None:
        rng = random.Random(20260718)
        alphabet = ["a", "b", "c"]
        for trial in range(200):
            vocab_tokens: list[str] = list(alphabet)
            seen = set(alphabet)
            rules: list[tuple[str, str]] = []
            for _ in range(rng.randint(1, 6)):
                left = rng.choice(vocab_tokens)
                right = rng.choice(vocab_tokens)
                merged = left + right
                if merged in seen or len(merged) > 8:
                    continue
                vocab_tokens.append(merged)
                seen.add(merged)
                rules.append((left, right))
            if not rules:
                continue
            vocab = Vocab.new(["", *vocab_tokens])
            dictionary = Dictionary.new(vocab, rules)
            for _ in range(5):
                s = bytes(rng.choice(b"abc") for _ in range(rng.randint(0, 12)))
                ids = _atomic_ids(vocab, s)
                result = tokenize_pq(dictionary, ids)
                with self.subTest(trial=trial, string=s):
                    # Concatenation is preserved, and no adjacent pair in the
                    # output can still be merged (the loop ran to fixpoint).
                    self.assertEqual(b"".join(vocab[t] for t in result), s)
                    for left_tok, right_tok in itertools.pairwise(result):
                        self.assertIsNone(dictionary.find_rule(left_tok, right_tok))


if __name__ == "__main__":
    unittest.main()
