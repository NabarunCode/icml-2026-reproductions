"""Incremental BPE: maintaining theta(s) one byte at a time.

Implements the Prefix Last-Token Condition (paper Definition 4.1)
literally, and searches for theta(sc) by checking every canonical token
that is a suffix of the buffer so far, from shortest (length 1, always
an atomic token, always valid) to longest - the Monotonic Path Property
(Theorem 4.2) says the valid ones form a prefix of this list in
increasing-length order, so the last valid one found is theta(sc).

SCOPING NOTE (honest, not a silent shortcut): this is a *correct* but
*not yet asymptotically optimal* implementation. The paper's O(log^2 t)
per-byte bound comes from two speedups this module does not yet
implement:

1. Finding the longest suffix token in O(1) via an Aho-Corasick
   automaton (Section 5.2) - here it's found by scanning candidate
   lengths directly against the vocabulary, O(t) per byte.
2. Finding theta(sc) in O(log t) via Centroid Decomposition + the
   O(1) DFS-interval test (Sections 4.3, 5.3) - here it's found by
   checking every candidate length directly (each check itself is
   O(depth) via an ancestor walk), so worst case O(t * depth) per byte.

Both are deferred to a documented follow-up before Claims 3-4
(performance) can be benchmarked at realistic scale; this module is
scoped to verifying Claims 1-2 (structural correctness and algorithm
design) honestly, at a complexity that is easy to get right and to
verify against the oracle. See ``../README.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from incbpe.normalize import NormalizedDict
from incbpe.successor_forest import SuccessorForest
from incbpe.vocab import TokenId

# Root sentinel for "no last token yet" (the empty prefix, i.e. the
# virtual root of the Prefix Tree of Tokens - not to be confused with
# SuccessorForest.ROOT, which marks a token's forest parent as "none").
EMPTY_PREFIX: TokenId | None = None


@dataclass
class IncrementalTokenizer:
    """Precomputed structures shared across many incremental runs."""

    normalized: NormalizedDict
    forest: SuccessorForest
    max_token_length: int

    @staticmethod
    def build(normalized: NormalizedDict, forest: SuccessorForest) -> IncrementalTokenizer:
        max_len = max((len(t) for t in normalized.dict.vocab.tokens if t), default=1)
        return IncrementalTokenizer(normalized, forest, max_len)

    def new_run(self) -> Run:
        return Run(self, bytearray(), [])


@dataclass
class Run:
    """One incremental tokenization in progress: a growing buffer plus
    the full history of theta values, one per byte fed so far."""

    tokenizer: IncrementalTokenizer
    buffer: bytearray
    history: list[TokenId] = field(default_factory=list)
    verify_monotonic: bool = False

    def feed(self, byte: int) -> TokenId:
        """Append one byte and return the new theta (last token)."""
        self.buffer.append(byte)
        theta = self._search()
        self.history.append(theta)
        return theta

    def feed_all(self, data: bytes) -> TokenId:
        theta = EMPTY_PREFIX  # placeholder for empty input
        for byte in data:
            theta = self.feed(byte)
        if theta is None:
            raise ValueError("cannot feed an empty byte sequence")
        return theta

    def tokens(self) -> list[TokenId]:
        """Reconstruct the full tokenization by backtracking theta chain."""
        vocab = self.tokenizer.normalized.dict.vocab
        result: list[TokenId] = []
        pos = len(self.history)
        while pos > 0:
            theta = self.history[pos - 1]
            result.append(theta)
            pos -= len(vocab[theta])
        result.reverse()
        return result

    def _search(self) -> TokenId:
        """Find theta(sc): the longest canonical suffix of the buffer
        that satisfies the Prefix Last-Token Condition (Definition 4.1).

        Every canonical string-suffix of the buffer is checked
        independently (there is at most one candidate per length, since
        a string has exactly one suffix of each length). Note that a
        *shorter* candidate failing does **not** imply a *longer* one
        must also fail: candidates at different lengths can be siblings
        in the Successor Forest rather than ancestor/descendant (see
        Phase 2/3 notes on "de" having two children, "cde" and "abcde",
        at lengths 3 and 5) - only candidates that are *forest ancestors
        of theta(sc) itself* are guaranteed to pass (Theorem 4.2's
        actual path), which is what ``verify_monotonic`` checks below,
        instead of a same-length-order assumption.
        """
        normalized = self.tokenizer.normalized
        vocab = normalized.dict.vocab
        n = len(self.buffer)
        max_len = min(n, self.tokenizer.max_token_length)

        best: TokenId | None = None
        passed: dict[TokenId, bool] = {}
        for length in range(1, max_len + 1):
            candidate = bytes(self.buffer[n - length : n])
            token_id = vocab.find_token_id(candidate)
            if token_id is None or not normalized.is_canonical(token_id):
                continue
            ok = normalized.is_atomic(token_id) or self._satisfies_condition(token_id, n)
            passed[token_id] = ok
            if ok:
                best = token_id
        assert best is not None, "the atomic (length-1) candidate must always be valid"

        if self.verify_monotonic:
            self._verify_ancestor_path_all_passed(best, passed)
        return best

    def _verify_ancestor_path_all_passed(self, theta: TokenId, passed: dict[TokenId, bool]) -> None:
        """Empirically check Theorem 4.2 / Claim 1 (Upward Closure):
        every forest-ancestor of theta(sc) up to the root must also
        satisfy the condition - i.e. must also be in ``passed`` as True.
        """
        forest = self.tokenizer.forest
        current: TokenId | None = theta
        while current is not None:
            if current != theta:
                assert passed.get(current) is True, (
                    f"Monotonic Path Property violated: token {current} is a forest-ancestor "
                    f"of theta={theta} but did not satisfy the Prefix Last-Token Condition"
                )
            current = forest.parent[current]

    def _theta_of_prefix(self, prefix_len: int) -> TokenId | None:
        if prefix_len == 0:
            return EMPTY_PREFIX
        return self.history[prefix_len - 1]

    def _satisfies_condition(self, token_id: TokenId, n: int) -> bool:
        """Definition 4.1 (Prefix Last-Token Condition), non-atomic case.

        ``n`` is the current buffer length; the prior state to check
        against is theta of the buffer with *just suc(t)'s* suffix
        removed - not the whole candidate token's length, which may be
        much longer than its suc() component (e.g. suc("abc") = "bc",
        length 2, even though "abc" itself has length 3).
        """
        normalized = self.tokenizer.normalized
        forest = self.tokenizer.forest
        rule = normalized.dict.rules[normalized.priority[token_id]]
        pre_t = rule.pre
        suc_len = len(normalized.dict.vocab[rule.suc])
        prev_theta = self._theta_of_prefix(n - suc_len)

        if prev_theta is None:
            return False  # empty prefix can never reach a real token
        if prev_theta == pre_t:
            return True  # reachable with no intermediate child: trivially satisfied
        if not forest.is_ancestor_or_self(pre_t, prev_theta):
            return False  # Reachability fails
        u = forest.child_towards(pre_t, prev_theta)
        return normalized.priority[token_id] < normalized.priority[u]  # Priority dominance
