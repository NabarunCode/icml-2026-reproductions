"""Priority-queue BPE: the fast path for real-vocabulary scale.

``oracle.tokenize`` applies every rule in priority order, once each —
the paper's Equation 1 *definition*, O(rules x length) per call. That is
the right oracle for small test dictionaries but is infeasible for
normalizing a real 50k-rule vocabulary in Python (canonicity checks
alone would be O(vocab x rules)).

This module implements the classic dynamic-priority merge loop instead:
repeatedly merge the currently-present adjacent pair with the best
(lowest) rule id, ties broken leftmost — O(length x log length) per
call. **Semantics caveat, stated plainly:** this is SentencePiece/HF-
style *dynamic* priority, which the paper (Appendix A) distinguishes
from standard fixed-schedule BPE. On *proper* dictionaries the two
coincide; on non-proper dictionaries they can differ. Uses in this
repository therefore:

- always validate against ``oracle.tokenize`` on the known-proper test
  fixtures (``tests/test_fast_bpe.py``), and
- spot-check real vocabularies (e.g. GPT-2) against the oracle on
  sampled tokens, so a non-proper vocabulary is *detected*, never
  silently mis-normalized (``tests/test_gpt2_loader.py``).
"""

from __future__ import annotations

import heapq
from collections.abc import Callable

from incbpe.dictionary import Dictionary, RuleId
from incbpe.normalize import NormalizedDict, normalize
from incbpe.vocab import TokenId


def tokenize_pq_with_last_rule(
    dictionary: Dictionary, token_ids: list[TokenId]
) -> tuple[list[TokenId], RuleId | None]:
    """Dynamic-priority BPE; returns (sequence, temporally-last rule applied)."""
    n = len(token_ids)
    if n == 0:
        return [], None

    seq = list(token_ids)
    nxt = [*range(1, n), -1]
    prv = [-1, *range(n - 1)]
    alive = [True] * n
    find_rule = dictionary.find_rule
    rules = dictionary.rules

    heap: list[tuple[RuleId, int]] = []
    for i in range(n - 1):
        rule_id = find_rule(seq[i], seq[i + 1])
        if rule_id is not None:
            heap.append((rule_id, i))
    heapq.heapify(heap)

    last_rule: RuleId | None = None
    while heap:
        rule_id, left = heapq.heappop(heap)
        if not alive[left]:
            continue
        right = nxt[left]
        if right == -1:
            continue
        rule = rules[rule_id]
        if seq[left] != rule.pre or seq[right] != rule.suc:
            continue  # stale heap entry; a fresh one exists if still relevant

        seq[left] = rule.merged
        alive[right] = False
        nxt[left] = nxt[right]
        if nxt[right] != -1:
            prv[nxt[right]] = left
        last_rule = rule_id

        before = prv[left]
        if before != -1:
            neighbor_rule = find_rule(seq[before], seq[left])
            if neighbor_rule is not None:
                heapq.heappush(heap, (neighbor_rule, before))
        after = nxt[left]
        if after != -1:
            neighbor_rule = find_rule(seq[left], seq[after])
            if neighbor_rule is not None:
                heapq.heappush(heap, (neighbor_rule, left))

    result = [seq[i] for i in range(n) if alive[i]]
    return result, last_rule


def tokenize_pq(dictionary: Dictionary, token_ids: list[TokenId]) -> list[TokenId]:
    """Dynamic-priority BPE tokenization (see module docstring for semantics)."""
    result, _ = tokenize_pq_with_last_rule(dictionary, token_ids)
    return result


def normalize_pq(
    dictionary: Dictionary, is_atomic: Callable[[TokenId, bytes], bool]
) -> NormalizedDict:
    """:func:`incbpe.normalize.normalize`, but using the fast merge loop.

    Identical output to ``normalize`` whenever the dictionary is proper
    (validated by tests on every fixture family); usable at real-vocab
    scale where the oracle path is infeasible.
    """
    return normalize(dictionary, is_atomic, tokenize_fn=tokenize_pq_with_last_rule)
