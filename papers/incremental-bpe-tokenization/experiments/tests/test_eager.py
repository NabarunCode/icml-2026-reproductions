"""Tests for eager output: emitted tokens must exactly reassemble the
same tokenization the non-eager incremental search produces."""

from __future__ import annotations

import random
import unittest

from incbpe.dictionary import Dictionary
from incbpe.eager import new_eager_run
from incbpe.fixtures import build_figure2_variant
from incbpe.incremental import IncrementalTokenizer
from incbpe.normalize import normalize
from incbpe.successor_forest import build as build_forest
from incbpe.vocab import Vocab


class EagerOutputTest(unittest.TestCase):
    def _run_eager(self, tokenizer: IncrementalTokenizer, s: bytes) -> tuple[list[int], list[int]]:
        run = tokenizer.new_run()
        run.verify_monotonic = True
        eager = new_eager_run(run)
        emitted: list[int] = []
        for byte in s:
            emitted.extend(eager.feed(byte))
        emitted.extend(eager.finish())

        expected_run = tokenizer.new_run()
        for byte in s:
            expected_run.feed(byte)
        return emitted, expected_run.tokens()

    def test_figure2_variant_traces(self) -> None:
        normalized, forest = build_figure2_variant()
        tokenizer = IncrementalTokenizer.build(normalized, forest)
        for s in ["abcdefg", "babcdefg", "cdefg"]:
            emitted, expected = self._run_eager(tokenizer, s.encode())
            self.assertEqual(emitted, expected, f"mismatch on {s!r}")

    def test_random_small_dictionaries(self) -> None:
        rng = random.Random(9)
        alphabet = ["a", "b", "c"]
        for trial in range(100):
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
            normalized = normalize(dictionary, lambda _tid, token: len(token) == 1)
            forest = build_forest(normalized)
            tokenizer = IncrementalTokenizer.build(normalized, forest)

            s = bytes(rng.choice(alphabet).encode()[0] for _ in range(rng.randint(1, 12)))
            with self.subTest(trial=trial, rules=rules, s=s):
                emitted, expected = self._run_eager(tokenizer, s)
                self.assertEqual(emitted, expected)

    def test_repeated_character_family(self) -> None:
        vocab = Vocab.new([""] + ["a" * i for i in range(1, 17)])
        rule_sets = [
            [("a", "a")],
            [("a", "a"), ("aa", "a")],
            [("a", "a"), ("a", "aa")],
            [("a", "a"), ("aa", "a"), ("aa", "aa")],
        ]
        strings = [b"a" * n for n in range(1, 17)]
        for rules in rule_sets:
            dictionary = Dictionary.new(vocab, rules)
            normalized = normalize(dictionary, lambda _tid, token: len(token) == 1)
            forest = build_forest(normalized)
            tokenizer = IncrementalTokenizer.build(normalized, forest)
            for s in strings:
                emitted, expected = self._run_eager(tokenizer, s)
                self.assertEqual(emitted, expected, f"mismatch on {s!r} with rules {rules}")


if __name__ == "__main__":
    unittest.main()
