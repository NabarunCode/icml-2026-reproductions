"""Tests for the Aho-Corasick automaton against a brute-force oracle."""

from __future__ import annotations

import random
import unittest

from incbpe.aho_corasick import ROOT_STATE, build
from incbpe.dictionary import Dictionary
from incbpe.normalize import normalize
from incbpe.vocab import Vocab
from tests.fixtures import build_figure2_variant


def brute_force_longest_suffix(normalized, buffer: bytes) -> int | None:
    vocab = normalized.dict.vocab
    for length in range(len(buffer), 0, -1):
        candidate = buffer[len(buffer) - length :]
        tid = vocab.find_token_id(candidate)
        if tid is not None and normalized.is_canonical(tid):
            return tid
    return None


class AhoCorasickTest(unittest.TestCase):
    def test_figure2_variant_matches_brute_force(self) -> None:
        normalized, _forest = build_figure2_variant()
        automaton = build(normalized)

        for s in ["abcdefg", "babcdefg", "cdefg", "a", "gggg", "defcdefg"]:
            state = ROOT_STATE
            buffer = bytearray()
            for byte in s.encode():
                buffer.append(byte)
                state = automaton.step(state, byte)
                expected = brute_force_longest_suffix(normalized, bytes(buffer))
                self.assertEqual(
                    automaton.longest_token[state],
                    expected,
                    f"mismatch at buffer={bytes(buffer)!r}",
                )

    def test_random_dictionaries_match_brute_force(self) -> None:
        rng = random.Random(7)
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

            vocab = Vocab.new([""] + vocab_tokens)
            dictionary = Dictionary.new(vocab, rules)
            normalized = normalize(dictionary, lambda _tid, token: len(token) == 1)
            automaton = build(normalized)

            with self.subTest(trial=trial, rules=rules):
                state = ROOT_STATE
                buffer = bytearray()
                s = bytes(rng.choice(alphabet).encode()[0] for _ in range(rng.randint(1, 15)))
                for byte in s:
                    buffer.append(byte)
                    state = automaton.step(state, byte)
                    expected = brute_force_longest_suffix(normalized, bytes(buffer))
                    self.assertEqual(automaton.longest_token[state], expected)


if __name__ == "__main__":
    unittest.main()
