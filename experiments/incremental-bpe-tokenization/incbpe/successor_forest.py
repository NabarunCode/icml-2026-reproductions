"""Successor Forest (paper Section 3.4).

A directed graph over canonical tokens: every non-atomic canonical token
points to its ``suc`` (its forest "parent"). Since ``suc(t)`` is always a
proper suffix of ``t`` (strictly shorter), this graph is acyclic and
forms a forest rooted at the atomic tokens.
"""

from __future__ import annotations

from dataclasses import dataclass

from incbpe.normalize import NormalizedDict
from incbpe.vocab import TokenId

ROOT: TokenId | None = None


@dataclass(frozen=True)
class SuccessorForest:
    """Parent pointers over canonical tokens: ``parent[t] = suc(t)``.

    Atomic tokens (and the implicit virtual root) map to :data:`ROOT`.
    This is deliberately just the parent-pointer graph, not the full
    node/children/DFS-timestamp structure the reference implementation
    builds (``successor.rs``) - see ``incremental.py`` for why: this
    reproduction's first correctness pass walks ancestor chains directly
    instead of using the O(1) DFS-interval trick (paper Section 4.3),
    so the extra bookkeeping isn't needed yet.
    """

    dict: NormalizedDict
    parent: dict[TokenId, TokenId | None]

    def is_ancestor_or_self(self, ancestor: TokenId, node: TokenId) -> bool:
        """Does walking ``node``'s parent chain reach ``ancestor``?"""
        current: TokenId | None = node
        while current is not None:
            if current == ancestor:
                return True
            current = self.parent[current]
        return False

    def child_towards(self, ancestor: TokenId, node: TokenId) -> TokenId:
        """The child of ``ancestor`` on the path from ``node`` up to it.

        Precondition: ``ancestor`` is a strict ancestor of ``node`` (or
        ``node`` itself is that child), checked via
        :meth:`is_ancestor_or_self` by the caller first.
        """
        current = node
        while self.parent[current] != ancestor:
            next_node = self.parent[current]
            if next_node is None:
                raise ValueError(f"{ancestor} is not an ancestor of {node}")
            current = next_node
        return current


def build(normalized: NormalizedDict) -> SuccessorForest:
    parent: dict[TokenId, TokenId | None] = {}
    for token_id in range(len(normalized.dict.vocab)):
        if not normalized.is_canonical(token_id):
            continue
        if normalized.is_atomic(token_id):
            parent[token_id] = ROOT
            continue
        rule = normalized.dict.rules[normalized.priority[token_id]]
        parent[token_id] = rule.suc
    return SuccessorForest(normalized, parent)
