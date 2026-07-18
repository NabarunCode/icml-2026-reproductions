"""Verifies the paper's own 'Mutual Exclusion among Siblings' corollary
(Section 4.3) directly: for every forest node with 2+ children, their
precomputed valid_range intervals must be pairwise disjoint. This is
exactly the property that makes a binary-search-based centroid search
(Section 5.3) sound - checked here as a property test in its own right,
not just assumed."""

from __future__ import annotations

import random
import unittest

from incbpe.dfs_interval import build as build_intervals
from incbpe.dictionary import Dictionary
from incbpe.normalize import normalize
from incbpe.successor_forest import build as build_forest
from incbpe.vocab import Vocab
from tests.fixtures import build_figure2_variant


def _assert_siblings_disjoint(test: unittest.TestCase, forest, intervals) -> None:
    normalized = forest.dict
    for parent, children in forest.children.items():
        # valid_range is only defined for non-atomic canonical tokens
        # (atomic tokens - e.g. the root's own children - always
        # trivially satisfy Definition 4.1, no interval to compare).
        non_atomic_children = [c for c in children if not normalized.is_atomic(c)]
        ranges = [intervals.valid_range[c] for c in non_atomic_children]
        ranges.sort()
        for (l1, r1), (l2, r2) in zip(ranges, ranges[1:]):
            test.assertLessEqual(
                r1,
                l2,
                f"sibling ranges overlap under parent {parent}: ({l1},{r1}) vs ({l2},{r2})",
            )


class SiblingDisjointnessTest(unittest.TestCase):
    def test_figure2_variant(self) -> None:
        normalized, forest = build_figure2_variant()
        intervals = build_intervals(normalized, forest)
        _assert_siblings_disjoint(self, forest, intervals)

    def test_random_small_dictionaries(self) -> None:
        rng = random.Random(1234)
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
            intervals = build_intervals(normalized, forest)
            with self.subTest(trial=trial, rules=rules):
                _assert_siblings_disjoint(self, forest, intervals)


if __name__ == "__main__":
    unittest.main()
