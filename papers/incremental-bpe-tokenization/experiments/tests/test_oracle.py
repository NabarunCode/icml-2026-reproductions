"""Sanity checks for the standard-BPE oracle against the Phase 2 example."""

import unittest

from incbpe.dictionary import Dictionary
from incbpe.oracle import tokenize
from incbpe.vocab import Vocab


class OracleTest(unittest.TestCase):
    def test_phase2_worked_example(self) -> None:
        """The ab/bb/abb example from notes/theory-notes.md Section 2,
        mechanically verified there with a standalone script; reproduced
        here as a permanent regression test."""
        vocab = Vocab.new(["a", "b", "ab", "bb", "abb"])
        dictionary = Dictionary.new(
            vocab,
            [("a", "b"), ("b", "b"), ("ab", "b")],
        )

        def token_ids_of(s: str) -> list[int]:
            return [vocab.find_token_id(bytes([c])) for c in s.encode()]  # type: ignore[misc]

        def tokenize_str(s: str) -> list[bytes]:
            ids = token_ids_of(s)
            result = tokenize(dictionary, ids)
            return [vocab[i] for i in result]

        self.assertEqual(tokenize_str("a"), [b"a"])
        self.assertEqual(tokenize_str("ab"), [b"ab"])
        self.assertEqual(tokenize_str("abb"), [b"abb"])
        self.assertEqual(tokenize_str("abbb"), [b"ab", b"bb"])
        self.assertEqual(tokenize_str("bb"), [b"bb"])

    def test_appendix_a6_non_properizable_example(self) -> None:
        """Dictionary [(aa,a)->aaa, (a,a)->aa] on "aaaa" (paper Appendix A.6).

        Standard BPE (this oracle's semantics) must give [aa, aa], as
        stated in the paper - the point being that this *differs* from
        SentencePiece semantics ([aaa, a]), which this oracle does not
        implement (properization, Appendix A, is a deferred gap).
        """
        vocab = Vocab.new(["a", "aa", "aaa"])
        dictionary = Dictionary.new(vocab, [("aa", "a"), ("a", "a")])
        ids = [0, 0, 0, 0]  # four atomic 'a's
        result = tokenize(dictionary, ids)
        self.assertEqual([vocab[i] for i in result], [b"aa", b"aa"])


if __name__ == "__main__":
    unittest.main()
