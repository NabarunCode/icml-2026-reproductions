"""Tests for canonicity/normalization against the Figure-2-variant fixture."""

import unittest

from tests.fixtures import FIGURE2_VARIANT_RULES, build_figure2_variant, token_id


class NormalizeTest(unittest.TestCase):
    def test_all_figure2_rules_are_canonical(self) -> None:
        """The reference implementation's own test
        (`normalize.rs::test_normalized_dict`) asserts all 13 rules in
        this fixture are canonical; we should get the same result."""
        normalized, _forest = build_figure2_variant()
        for pre_name, suc_name in FIGURE2_VARIANT_RULES:
            merged_name = pre_name + suc_name
            merged_id = token_id(normalized, merged_name)
            self.assertTrue(
                normalized.is_canonical(merged_id),
                f"expected {merged_name!r} to be canonical",
            )
            self.assertFalse(normalized.is_atomic(merged_id))

    def test_atomic_tokens(self) -> None:
        normalized, _forest = build_figure2_variant()
        for letter in "abcdefg":
            tid = token_id(normalized, letter)
            self.assertTrue(normalized.is_atomic(tid))
            self.assertTrue(normalized.is_canonical(tid))


if __name__ == "__main__":
    unittest.main()
