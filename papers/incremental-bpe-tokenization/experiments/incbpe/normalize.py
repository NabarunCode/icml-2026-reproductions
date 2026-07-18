"""Normalization: canonical tokens/rules (paper Section 3.3, Appendix C).

A token ``t`` is *canonical* if ``T_D(t) == [t]`` - tokenizing its own
bytes with the full dictionary gives back exactly itself, as one token.
Appendix C proves this has a useful consequence: every canonical
non-atomic token has a unique producing rule, and that rule's ``pre``
and ``suc`` components are themselves canonical. This module computes
that canonical subset directly from the definition (via the oracle in
``oracle.py``), rather than porting the reference implementation's more
elaborate incremental bookkeeping (which exists there purely as a
performance optimization over many tokens, not for a different result).
Byte-level atomicity only (see :func:`normalize` docstring).

Deliberately NOT implemented here: Appendix A's "properization" (the
standard-BPE vs. SentencePiece semantics reconciliation). A dictionary
that is not properizable will simply have some tokens fail the
canonicity check below rather than being repaired - correct, but not
yet compatible with tokenizers trained under SentencePiece semantics.
Flagged in `../README.md` as a known gap to close before Claim 3 (which
needs real tokenizer vocabularies).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from incbpe.dictionary import Dictionary, RuleId
from incbpe.oracle import tokenize_with_last_rule
from incbpe.vocab import TokenId, Vocab

# Sentinel priority for atomic tokens: sorts after every real (non-atomic)
# rule priority, since atomic tokens have no rule and must root the
# Successor Forest below every canonical non-atomic token that uses them.
ATOMIC_PRIORITY_BASE = 1 << 30

NOT_CANONICAL: RuleId = -1


@dataclass(frozen=True)
class NormalizedDict:
    """A dictionary annotated with each token's canonical status."""

    dict: Dictionary
    priority: tuple[RuleId, ...]  # per token id; NOT_CANONICAL if not canonical
    atomic: tuple[bool, ...]  # per token id

    def is_canonical(self, token_id: TokenId) -> bool:
        return self.priority[token_id] != NOT_CANONICAL

    def is_atomic(self, token_id: TokenId) -> bool:
        return self.atomic[token_id]

    def __getitem__(self, token_id: TokenId) -> bytes:
        return self.dict[token_id]

    @property
    def vocab(self) -> Vocab:
        return self.dict.vocab


def normalize(
    dictionary: Dictionary, is_atomic: Callable[[TokenId, bytes], bool]
) -> NormalizedDict:
    """Build a :class:`NormalizedDict` from a raw dictionary.

    ``is_atomic`` decides which tokens are the base alphabet. This
    implementation only supports **byte-level** atomicity (each atomic
    token must be exactly one byte) - the reference implementation's
    UTF-8-codepoint-level mode (``new_in_utf8``) is not yet ported; byte-
    level is what real byte-level BPE tokenizers (GPT-style, CodeLlama,
    tiktoken encodings) actually use, so this covers Claim 3's needs.
    """
    num_tokens = len(dictionary.vocab)
    priority: list[RuleId] = [NOT_CANONICAL] * num_tokens
    atomic: list[bool] = [False] * num_tokens

    for token_id, token in enumerate(dictionary.vocab.tokens):
        if not token:
            continue
        if is_atomic(token_id, token):
            if len(token) != 1:
                raise ValueError(
                    f"token {token_id} ({token!r}) marked atomic but is not a single byte; "
                    "UTF-8-codepoint-level atomicity is not supported yet"
                )
            atomic[token_id] = True
            priority[token_id] = ATOMIC_PRIORITY_BASE + token_id

    byte_to_token: dict[int, TokenId] = {
        token[0]: token_id
        for token_id, token in enumerate(dictionary.vocab.tokens)
        if atomic[token_id]
    }

    merged_to_rules: dict[TokenId, list[RuleId]] = {}
    for rule_id, rule in enumerate(dictionary.rules):
        merged_to_rules.setdefault(rule.merged, []).append(rule_id)

    for token_id, token in enumerate(dictionary.vocab.tokens):
        if not token or atomic[token_id]:
            continue
        candidates = merged_to_rules.get(token_id, [])
        if not candidates:
            continue  # unreachable token: nothing in the dictionary ever produces it
        try:
            atomic_ids = [byte_to_token[b] for b in token]
        except KeyError:
            continue  # some byte in this token has no atomic vocab entry at all
        result, last_rule = tokenize_with_last_rule(dictionary, atomic_ids)
        if result != [token_id] or last_rule is None:
            continue  # not canonical: tokenizing its own bytes doesn't collapse to itself
        assert last_rule in candidates, (
            "the rule that produced the final merge must be one of the rules "
            "whose declared merge target is this token id"
        )
        priority[token_id] = last_rule

    return NormalizedDict(dictionary, tuple(priority), tuple(atomic))
