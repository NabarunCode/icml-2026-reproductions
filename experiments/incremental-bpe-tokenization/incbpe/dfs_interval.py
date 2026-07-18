"""DFS linearization and the O(1) valid-interval test (paper Section 4.3).

A single pre-order DFS over the whole Successor Forest, visiting each
node's children from lowest to highest priority (largest to smallest
rule id - the paper's own convention, "children with lower priorities
are mapped to earlier timestamps"), gives every node a contiguous
``[dfs_in, dfs_out)`` timestamp range for its subtree. That turns
"is x a descendant of u" into one integer-range comparison.

For a non-atomic canonical token t, the *valid interval* is the range of
``dfs_in`` values that a history token ``theta_prev`` must fall in for t
to satisfy the Prefix Last-Token Condition (Definition 4.1) - folding
both Reachability and Priority Dominance into a single O(1) check
against pre(t)'s *other* children (t itself is generally not one of
them - see the module docstring in ``incremental.py`` for why this
tripped up an earlier, wrong intuition during development).
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass

from incbpe.normalize import NormalizedDict
from incbpe.successor_forest import ROOT, SuccessorForest
from incbpe.vocab import TokenId

Timestamp = int


@dataclass(frozen=True)
class DFSIntervals:
    dfs_in: dict[TokenId | None, Timestamp]
    dfs_out: dict[TokenId | None, Timestamp]
    valid_range: dict[TokenId, tuple[Timestamp, Timestamp]]  # non-atomic canonical tokens only
    # Per forest-parent, non-atomic children sorted by their own
    # valid_range start - the "Mutual Exclusion among Siblings" corollary
    # (proven in the paper, empirically re-checked in
    # tests/test_sibling_disjointness.py) guarantees these ranges are
    # pairwise disjoint, which is what makes searching this list with
    # bisect (rather than a linear scan) sound: at most one entry can
    # ever contain a given query timestamp.
    children_by_range_start: dict[TokenId | None, list[TokenId]]

    def contains(self, token_id: TokenId, query: TokenId | None) -> bool:
        """Is ``query`` (a theta_prev value, possibly the empty-prefix
        sentinel None) within token_id's precomputed valid interval?"""
        low, high = self.valid_range[token_id]
        return low <= self.dfs_in[query] < high

    def find_valid_child(self, parent: TokenId | None, query: TokenId | None) -> TokenId | None:
        """O(log branching factor): which (at most one) non-atomic
        child of ``parent`` has ``query`` inside its own valid_range,
        via binary search over pre-sorted, pairwise-disjoint sibling
        ranges - the same lookup Section 5.3 performs at each Centroid
        Search Tree node, just not yet on a centroid-balanced tree (see
        ``incremental.py``'s module docstring for that remaining gap).
        """
        siblings = self.children_by_range_start.get(parent, [])
        if not siblings:
            return None
        query_ts = self.dfs_in[query]
        starts = [self.valid_range[c][0] for c in siblings]
        idx = bisect.bisect_right(starts, query_ts) - 1
        if idx < 0:
            return None
        candidate = siblings[idx]
        low, high = self.valid_range[candidate]
        return candidate if low <= query_ts < high else None


def build(normalized: NormalizedDict, forest: SuccessorForest) -> DFSIntervals:
    dfs_in: dict[TokenId | None, Timestamp] = {}
    dfs_out: dict[TokenId | None, Timestamp] = {}
    counter = 0

    # Iterative pre-order DFS (avoids Python's recursion limit on deep chains).
    stack: list[tuple[TokenId | None, int]] = [(ROOT, 0)]
    while stack:
        node, child_idx = stack[-1]
        if child_idx == 0:
            dfs_in[node] = counter
            counter += 1
        kids = forest.children.get(node, [])
        if child_idx < len(kids):
            stack[-1] = (node, child_idx + 1)
            stack.append((kids[child_idx], 0))
        else:
            dfs_out[node] = counter
            stack.pop()

    valid_range: dict[TokenId, tuple[Timestamp, Timestamp]] = {}
    for token_id in range(len(normalized.dict.vocab)):
        if not normalized.is_canonical(token_id) or normalized.is_atomic(token_id):
            continue
        rule = normalized.dict.rules[normalized.priority[token_id]]
        pre_t = rule.pre
        low = dfs_in[pre_t]
        siblings = forest.children.get(pre_t, [])  # sorted lowest-to-highest priority
        t_priority = normalized.priority[token_id]

        if not siblings or t_priority >= normalized.priority[siblings[0]]:
            high = low + 1  # t has priority no better than the weakest sibling: nothing beats it
        elif t_priority < normalized.priority[siblings[-1]]:
            high = dfs_out[pre_t]  # t dominates every sibling: the whole subtree is reachable
        else:
            # siblings' rule ids are strictly descending (priority ascending);
            # find the first sibling (from the start) whose rule id is <= t's.
            descending_rule_ids = [normalized.priority[s] for s in siblings]
            ascending_negated = [-r for r in descending_rule_ids]
            idx = bisect.bisect_left(ascending_negated, -t_priority)
            assert 0 <= idx < len(siblings)
            high = dfs_in[siblings[idx]]

        valid_range[token_id] = (low, high)

    children_by_range_start: dict[TokenId | None, list[TokenId]] = {}
    for parent, kids in forest.children.items():
        non_atomic = [c for c in kids if c in valid_range]
        non_atomic.sort(key=lambda c: valid_range[c][0])
        children_by_range_start[parent] = non_atomic

    return DFSIntervals(dfs_in, dfs_out, valid_range, children_by_range_start)
