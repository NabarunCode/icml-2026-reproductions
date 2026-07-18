"""Differential tests: the O(1) DFS-interval test (Section 4.3) must
agree with the already-validated O(depth) ancestor-walk check
(``definition_4_1_ancestor_walk``) on every non-atomic canonical token,
against every possible history value - not just values that arise in
one specific run, but the full cross product, since the interval test
is a *static*, per-dictionary precomputation that has to be right for
every possible query, not just the ones we happen to exercise."""

from __future__ import annotations

import random
import unittest

from incbpe.dfs_interval import build as build_intervals
from incbpe.dictionary import Dictionary
from incbpe.incremental import definition_4_1_ancestor_walk
from incbpe.normalize import normalize
from incbpe.successor_forest import build as build_forest
from incbpe.vocab import Vocab
from tests.fixtures import build_figure2_variant


def _all_possible_theta_values(normalized) -> list[int | None]:
    values: list[int | None] = [None]
    for token_id in range(len(normalized.dict.vocab)):
        if normalized.is_canonical(token_id):
            values.append(token_id)
    return values


class DFSIntervalTest(unittest.TestCase):
    def _check(self, normalized, forest) -> None:
        intervals = build_intervals(normalized, forest)
        candidates = [
            t
            for t in range(len(normalized.dict.vocab))
            if normalized.is_canonical(t) and not normalized.is_atomic(t)
        ]
        queries = _all_possible_theta_values(normalized)
        for token_id in candidates:
            for prev_theta in queries:
                expected = definition_4_1_ancestor_walk(normalized, forest, token_id, prev_theta)
                actual = intervals.contains(token_id, prev_theta)
                self.assertEqual(
                    actual,
                    expected,
                    f"token {token_id}, prev_theta={prev_theta}: "
                    f"interval said {actual}, ancestor-walk said {expected}",
                )

        # find_valid_child (binary search) must agree with a plain linear
        # scan over the same children, using contains() (already checked
        # above against the ancestor-walk oracle).
        for parent, kids in forest.children.items():
            non_atomic_kids = [c for c in kids if not normalized.is_atomic(c)]
            for prev_theta in queries:
                expected_matches = [c for c in non_atomic_kids if intervals.contains(c, prev_theta)]
                assert len(expected_matches) <= 1, (
                    "Mutual Exclusion among Siblings violated: multiple children "
                    f"of {parent} match prev_theta={prev_theta}: {expected_matches}"
                )
                expected_child = expected_matches[0] if expected_matches else None
                actual_child = intervals.find_valid_child(parent, prev_theta)
                self.assertEqual(
                    actual_child,
                    expected_child,
                    f"parent {parent}, prev_theta={prev_theta}: "
                    f"binary search found {actual_child}, linear scan found {expected_child}",
                )

    def test_figure2_variant(self) -> None:
        normalized, forest = build_figure2_variant()
        self._check(normalized, forest)

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
            normalized = normalize(dictionary, lambda _tid, token: len(token) == 1)
            forest = build_forest(normalized)
            self._check(normalized, forest)

    def test_random_small_dictionaries(self) -> None:
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

            vocab = Vocab.new([""] + vocab_tokens)
            dictionary = Dictionary.new(vocab, rules)
            normalized = normalize(dictionary, lambda _tid, token: len(token) == 1)
            forest = build_forest(normalized)
            with self.subTest(trial=trial, rules=rules):
                self._check(normalized, forest)


if __name__ == "__main__":
    unittest.main()
