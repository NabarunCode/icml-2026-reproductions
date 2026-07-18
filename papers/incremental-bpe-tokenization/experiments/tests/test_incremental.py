"""Correctness tests for the incremental algorithm.

Two independent kinds of evidence:

1. Exact reproduction of the real theta-traces captured from the
   reference implementation's own test suite (Phase 3,
   implementation-notes.md) - this is the strongest test, since it's
   checked against ground truth from the paper authors' own code, not
   just our own oracle.
2. Randomized differential testing against our from-scratch oracle
   (``oracle.py``), across many random small dictionaries and strings -
   this is what actually stress-tests the Monotonic Path Property
   (Theorem 4.2, Claim 1) and the algorithm design (Claim 2), since the
   incremental search's ``verify_monotonic`` flag is turned on, so any
   violation of Theorem 4.2 during the search raises immediately.
"""

from __future__ import annotations

import random
import unittest

from incbpe.dictionary import Dictionary
from incbpe.fixtures import build_figure2_variant
from incbpe.incremental import IncrementalTokenizer
from incbpe.normalize import normalize
from incbpe.oracle import tokenize as oracle_tokenize
from incbpe.successor_forest import build as build_forest
from incbpe.vocab import Vocab


class ReferenceTraceTest(unittest.TestCase):
    """Ground truth captured via `cargo test --lib inc_bpe::tests::test_inc_bpe_demo
    -- --nocapture` against the vendored reference implementation, see
    implementation-notes.md for the full transcript and explanation."""

    def setUp(self) -> None:
        self.normalized, self.forest = build_figure2_variant()
        self.tokenizer = IncrementalTokenizer.build(self.normalized, self.forest)

    def _run(self, s: str) -> list[str]:
        run = self.tokenizer.new_run()
        run.verify_monotonic = True
        for byte in s.encode():
            run.feed(byte)
        vocab = self.normalized.dict.vocab
        return [vocab[t].decode() for t in run.history]

    def test_abcdefg(self) -> None:
        self.assertEqual(
            self._run("abcdefg"),
            ["a", "b", "abc", "d", "abcde", "abcdef", "g"],
        )

    def test_babcdefg(self) -> None:
        self.assertEqual(
            self._run("babcdefg"),
            ["b", "ba", "b", "bc", "d", "de", "bcdef", "g"],
        )

    def test_cdefg(self) -> None:
        self.assertEqual(
            self._run("cdefg"),
            ["c", "cd", "cde", "ef", "cdefg"],
        )

    def test_full_tokenization_matches_backtrack(self) -> None:
        run = self.tokenizer.new_run()
        for byte in b"abcdefg":
            run.feed(byte)
        vocab = self.normalized.dict.vocab
        names = [vocab[t].decode() for t in run.tokens()]
        self.assertEqual(names, ["abcdef", "g"])

        run2 = self.tokenizer.new_run()
        for byte in b"cdefg":
            run2.feed(byte)
        names2 = [vocab[t].decode() for t in run2.tokens()]
        self.assertEqual(names2, ["cdefg"])


class DifferentialTest(unittest.TestCase):
    """Randomized cross-checks against the from-scratch oracle."""

    def _atomic_ids(self, vocab: Vocab, s: bytes) -> list[int]:
        ids = []
        for b in s:
            tid = vocab.find_token_id(bytes([b]))
            assert tid is not None
            ids.append(tid)
        return ids

    def _check_dictionary(
        self, vocab: Vocab, rule_pairs: list[tuple[str, str]], strings: list[bytes]
    ) -> None:
        dictionary = Dictionary.new(vocab, rule_pairs)
        normalized = normalize(dictionary, lambda _tid, token: len(token) == 1)
        forest = build_forest(normalized)
        tokenizer = IncrementalTokenizer.build(normalized, forest)

        for s in strings:
            expected = oracle_tokenize(dictionary, self._atomic_ids(vocab, s))
            run = tokenizer.new_run()
            run.verify_monotonic = True
            for byte in s:
                run.feed(byte)
            self.assertEqual(
                run.tokens(),
                expected,
                f"mismatch on {s!r} with rules {rule_pairs}",
            )

    def test_repeated_character_family(self) -> None:
        """The paper's own pathological-input family (repeated 'a's,
        Section 7.2 / Appendix H.2), across several small rule sets that
        create deep merge chains - exactly the shape that stresses the
        Monotonic Path Property the hardest."""
        vocab = Vocab.new([""] + ["a" * i for i in range(1, 17)])
        rule_sets = [
            [("a", "a")],
            [("a", "a"), ("aa", "a")],
            [("a", "a"), ("a", "aa")],
            [("a", "a"), ("aa", "a"), ("aa", "aa")],
            [("a", "a"), ("aa", "aa"), ("aa", "a"), ("aaaa", "a")],
        ]
        strings = [b"a" * n for n in range(1, 17)]
        for rules in rule_sets:
            self._check_dictionary(vocab, rules, strings)

    def test_random_small_dictionaries(self) -> None:
        """Random dictionaries over a 3-letter alphabet, random merge
        order, random test strings - broad coverage of the structural
        claim without hand-picking favorable cases."""
        rng = random.Random(20260718)
        alphabet = ["a", "b", "c"]

        for trial in range(200):
            vocab_tokens: list[str] = list(alphabet)
            seen = set(alphabet)
            # Build a small random set of merges, always merging two
            # tokens already in vocab_tokens so every rule is well-formed.
            rules: list[tuple[str, str]] = []
            num_rules = rng.randint(1, 6)
            for _ in range(num_rules):
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
            rng.shuffle(rules)

            vocab = Vocab.new(["", *vocab_tokens])
            strings = [
                bytes(rng.choice(alphabet).encode()[0] for _ in range(rng.randint(1, 12)))
                for _ in range(10)
            ]
            with self.subTest(trial=trial, rules=rules):
                self._check_dictionary(vocab, rules, strings)


if __name__ == "__main__":
    unittest.main()
