"""Incremental BPE: maintaining theta(s) one byte at a time.

Implements the Prefix Last-Token Condition (paper Definition 4.1)
literally. Two search strategies are provided, kept side by side
deliberately so the newer one can be continuously cross-checked against
the older, already-oracle-validated one:

- ``_search_by_length`` (the original Phase 4 pass): checks every
  canonical string-suffix of the buffer independently, longest passing
  one wins. Simple, clearly correct, but O(t) candidates per byte.
- ``_search_tree_walk`` (this pass): walks the Successor Forest
  top-down via real parent/child edges, starting from the atomic token
  for the newly-fed byte and descending into whichever child (there is
  at most one, per the Monotonic Path Property's mutual-exclusion
  corollary) still satisfies Definition 4.1, stopping when none does.
  This only ever visits nodes that are actual forest descendants of the
  root, typically O(depth) of them rather than O(t) - a real complexity
  improvement, verified against the length-based search on every run.

SCOPING NOTE (honest, not a silent shortcut): this is still not the
paper's full O(log^2 t)-per-byte algorithm. What's implemented:

- Finding the longest suffix token, tau(sc), via a real Aho-Corasick
  automaton (Section 5.2, see ``aho_corasick.py``) in O(1) amortized -
  used here as a cross-check (theta(sc) can never be longer than
  tau(sc)), not yet as the search's own starting point.

What's still deferred:

- The O(1) DFS-interval test and Centroid Decomposition (Sections 4.3,
  5.3): ``_search_tree_walk`` finds the right child at each tree level
  by checking every child directly (a handful in practice) rather than
  via interval arithmetic over a centroid-decomposed search tree, so it
  is not yet O(log t) *per level* in the worst case, only in typical
  cases where branching factor is small. Needed before Claims 3-4
  (performance) can be benchmarked at adversarial scale (e.g. the deep,
  wide dictionaries Appendix J constructs).

See ``../README.md`` for the full status table.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from incbpe.aho_corasick import ROOT_STATE, AhoCorasick
from incbpe.aho_corasick import build as build_automaton
from incbpe.normalize import NormalizedDict
from incbpe.successor_forest import ROOT as FOREST_ROOT
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
    automaton: AhoCorasick
    max_token_length: int

    @staticmethod
    def build(normalized: NormalizedDict, forest: SuccessorForest) -> IncrementalTokenizer:
        max_len = max((len(t) for t in normalized.dict.vocab.tokens if t), default=1)
        automaton = build_automaton(normalized)
        return IncrementalTokenizer(normalized, forest, automaton, max_len)

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
    ac_state: int = ROOT_STATE

    def feed(self, byte: int) -> TokenId:
        """Append one byte and return the new theta (last token)."""
        self.buffer.append(byte)
        self.ac_state = self.tokenizer.automaton.step(self.ac_state, byte)
        theta = self._search_tree_walk()

        if self.verify_monotonic:
            reference = self._search_by_length()
            assert theta == reference, (
                f"tree-walk search ({theta}) disagrees with the length-based "
                f"search ({reference}) on buffer {bytes(self.buffer)!r}"
            )
            tau = self.tokenizer.automaton.longest_token[self.ac_state]
            assert tau is not None
            vocab = self.tokenizer.normalized.dict.vocab
            assert len(vocab[theta]) <= len(vocab[tau]), (
                "theta(sc) must never be longer than tau(sc), the longest "
                "recognized suffix token"
            )

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

    def _search_tree_walk(self) -> TokenId:
        """Find theta(sc) by walking the Successor Forest top-down.

        Starts at the atomic token for the just-fed byte (always valid,
        trivially) and descends into whichever child currently satisfies
        Definition 4.1 - there is at most one, per the Monotonic Path
        Property's mutual-exclusion corollary (Section 4.3) - stopping
        once no child qualifies. Only visits actual forest descendants
        of the root, not every possible string length.
        """
        normalized = self.tokenizer.normalized
        forest = self.tokenizer.forest
        n = len(self.buffer)
        last_byte = bytes([self.buffer[-1]])
        current = normalized.dict.vocab.find_token_id(last_byte)
        assert current is not None and normalized.is_atomic(current), (
            f"byte {last_byte!r} has no atomic vocabulary entry - "
            "out-of-vocabulary bytes are not yet supported"
        )

        while True:
            candidates = forest.children.get(current, [])
            next_node: TokenId | None = None
            matches = 0
            for child in candidates:
                token = normalized.dict.vocab[child]
                if not self.buffer.endswith(token):
                    continue  # not even a string-suffix of the buffer, skip
                if self._satisfies_condition(child, n):
                    matches += 1
                    next_node = child
                    if not self.verify_monotonic:
                        break
            if self.verify_monotonic:
                assert matches <= 1, (
                    f"Monotonic Path Property violated: {matches} children of "
                    f"{current} simultaneously satisfy Definition 4.1"
                )
            if next_node is None:
                return current
            current = next_node

    def _search_by_length(self) -> TokenId:
        """Reference implementation from the first Phase 4 pass: checks
        every canonical string-suffix of the buffer independently,
        longest passing one wins. Kept as a cross-check oracle for
        ``_search_tree_walk`` - see the module docstring.

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
