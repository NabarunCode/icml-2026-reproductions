"""Dictionary: an ordered list of merge rules D = [r1, ..., rm] (paper Section 3.1)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from incbpe.vocab import TokenId, Vocab

RuleId = int

# A token may be referred to by id, by text, or by raw bytes.
TokenRef = TokenId | str | bytes


@dataclass(frozen=True)
class Rule:
    """A single merge rule ``(pre, suc) -> merged``.

    Field names match the paper's ``pre(t)`` / ``suc(t)`` terminology
    (Section 3.3) directly, rather than the more common "left"/"right".
    """

    pre: TokenId
    suc: TokenId
    merged: TokenId


@dataclass(frozen=True)
class Dictionary:
    """Vocabulary plus an ordered rule list; rule index IS its priority.

    Rule 0 is the highest priority (applied first), matching the
    paper's convention: "r1 represents the highest priority rule".
    """

    vocab: Vocab
    rules: tuple[Rule, ...]
    _pair_to_rule: dict[tuple[TokenId, TokenId], RuleId]

    @staticmethod
    def new(vocab: Vocab, rule_pairs: Sequence[tuple[TokenRef, TokenRef]]) -> Dictionary:
        rules: list[Rule] = []
        pair_to_rule: dict[tuple[TokenId, TokenId], RuleId] = {}
        for rule_id, (left, right) in enumerate(rule_pairs):
            pre = _resolve(vocab, left)
            suc = _resolve(vocab, right)
            merged_bytes = vocab[pre] + vocab[suc]
            merged = vocab.find_token_id(merged_bytes)
            if merged is None:
                raise ValueError(
                    f"rule {rule_id} ({left!r}, {right!r}) -> {merged_bytes!r} "
                    "produces a token not present in the vocabulary"
                )
            rules.append(Rule(pre=pre, suc=suc, merged=merged))
            # First occurrence wins: for a duplicated (pre, suc) pair the
            # highest-priority (lowest-id) rule is the one lookups must see.
            pair_to_rule.setdefault((pre, suc), rule_id)
        return Dictionary(vocab, tuple(rules), pair_to_rule)

    def find_rule(self, pre: TokenId, suc: TokenId) -> RuleId | None:
        return self._pair_to_rule.get((pre, suc))

    def __getitem__(self, token_id: TokenId) -> bytes:
        return self.vocab[token_id]


def _resolve(vocab: Vocab, token: TokenRef) -> TokenId:
    if isinstance(token, int):
        return token
    raw = token.encode("utf-8") if isinstance(token, str) else token
    token_id = vocab.find_token_id(raw)
    if token_id is None:
        raise ValueError(f"token {token!r} not present in vocabulary")
    return token_id
