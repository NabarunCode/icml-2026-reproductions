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
    """Parent *and* children pointers over canonical tokens.

    ``parent[t] = suc(t)`` (``ROOT`` for atomic tokens). ``children[p]``
    lists every token whose ``suc`` is ``p``, sorted from lowest to
    highest priority (largest to smallest rule id) - the paper's own DFS
    visiting order (Section 4.3), kept here for consistency even though
    this module does not (yet) build the DFS timestamps / O(1)
    valid-interval structure the reference implementation uses
    (``suf_suc.rs``) - see ``incremental.py`` for why: the tree-walk
    search added there checks every child directly (there are only ever
    a handful at each node in practice) rather than using the O(1)
    interval trick, deferred along with Centroid Decomposition.
    """

    dict: NormalizedDict
    parent: dict[TokenId, TokenId | None]
    children: dict[TokenId | None, list[TokenId]]

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
    children: dict[TokenId | None, list[TokenId]] = {}
    for token_id in range(len(normalized.dict.vocab)):
        if not normalized.is_canonical(token_id):
            continue
        if normalized.is_atomic(token_id):
            parent[token_id] = ROOT
        else:
            rule = normalized.dict.rules[normalized.priority[token_id]]
            parent[token_id] = rule.suc
        children.setdefault(parent[token_id], []).append(token_id)

    for kids in children.values():
        kids.sort(key=lambda t: -normalized.priority[t])  # lowest priority (largest rule id) first

    return SuccessorForest(normalized, parent, children)
