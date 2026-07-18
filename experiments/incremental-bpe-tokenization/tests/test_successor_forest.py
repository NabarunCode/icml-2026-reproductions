"""Successor Forest structure, checked against the real reference-implementation
output captured in implementation-notes.md (from `cargo test
successor::tests::test_suc_forest -- --nocapture`)."""

import unittest

from incbpe.successor_forest import ROOT
from tests.fixtures import build_figure2_variant, token_id


class SuccessorForestTest(unittest.TestCase):
    def test_parent_pointers_match_reference_run(self) -> None:
        normalized, forest = build_figure2_variant()

        def tid(name: str) -> int:
            return token_id(normalized, name)

        expected_parent = {
            "a": ROOT,
            "b": ROOT,
            "c": ROOT,
            "d": ROOT,
            "e": ROOT,
            "f": ROOT,
            "g": ROOT,
            "ba": "a",
            "bc": "c",
            "abc": "bc",
            "cd": "d",
            "de": "e",
            "cde": "de",
            "abcde": "de",
            "ef": "f",
            "def": "ef",
            "bcdef": "def",
            "abcdef": "def",
            "efg": "g",
            "cdefg": "efg",
        }
        for name, expected in expected_parent.items():
            actual = forest.parent[tid(name)]
            expected_id = expected if expected is ROOT else tid(expected)  # type: ignore[arg-type]
            self.assertEqual(
                actual,
                expected_id,
                f"parent of {name!r} should be {expected!r}, got token id {actual}",
            )

    def test_de_has_two_children_sharing_a_forest_parent(self) -> None:
        """The genuine sibling-branching case from Phase 2/3: 'cde' and
        'abcde' both have forest-parent 'de', even though 'cde' is also
        a literal string-suffix of 'abcde' - the tree-parent relation
        is not the same as string-suffix nesting."""
        normalized, forest = build_figure2_variant()

        def tid(name: str) -> int:
            return token_id(normalized, name)

        self.assertEqual(forest.parent[tid("cde")], tid("de"))
        self.assertEqual(forest.parent[tid("abcde")], tid("de"))
        self.assertEqual(forest.parent[tid("bcdef")], tid("def"))
        self.assertEqual(forest.parent[tid("abcdef")], tid("def"))


if __name__ == "__main__":
    unittest.main()
