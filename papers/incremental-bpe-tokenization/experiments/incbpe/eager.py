"""Eager output (paper Section 6): streaming emission of stable tokens.

Even once theta(s) is known, it might still change as more characters
arrive - Section 6 defines exactly how far back a future change could
reach (the Active Frontier, Section 6.1: bounded by the automaton's
current match depth d(s)) and shows tokens outside that reach can be
emitted immediately and permanently.

SCOPING NOTE: this is a *definition-first*, not yet efficient,
implementation. The paper's own algorithm (Section 6.2, Appendix G)
maintains the Active Frontier incrementally with a two-pointer sweep for
amortized O(1) overhead per byte. Here, after every fed byte, the
"common ancestral path shared by every candidate in the window" is
recomputed directly from Section 6.1's definition: gather the full
backtrack chain (root to tip) of every prefix in the window, and take
their longest common prefix as sequences. This is O(window size x
average chain length) per byte - correct by direct construction from
the definition, but not the paper's O(1)-amortized mechanism. Closing
this gap is future work, same as the Centroid Decomposition gap in
``incremental.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from incbpe.incremental import Run
from incbpe.vocab import TokenId


@dataclass
class EagerRun:
    inner: Run
    emitted: list[TokenId] = field(default_factory=list)

    def feed(self, byte: int) -> list[TokenId]:
        """Feed one byte; return newly-stable tokens (possibly empty)."""
        self.inner.feed(byte)
        return self._drain(finalize=False)

    def finish(self) -> list[TokenId]:
        """Flush every remaining token once no more input is coming."""
        return self._drain(finalize=True)

    def _drain(self, finalize: bool) -> list[TokenId]:
        n = len(self.inner.buffer)
        if finalize:
            # No more input can arrive to invalidate anything further - the
            # window logic below no longer applies; commit to the whole
            # remaining tokenization of the buffer as fed so far.
            common = self._backtrack_chain(n)
        else:
            automaton = self.inner.tokenizer.automaton
            depth = automaton.depth[self.inner.ac_state]
            window_start = max(0, n - depth)
            chains = [self._backtrack_chain(i) for i in range(window_start, n + 1)]
            common = _longest_common_prefix(chains)

        already = len(self.emitted)
        assert common[:already] == self.emitted, (
            "the common ancestral path must never retroactively change an "
            "already-emitted token - Section 6.1's window is only supposed "
            "to shrink from the back, never invalidate a stable prefix"
        )
        new_tokens = common[already:]
        self.emitted = common
        return new_tokens

    def _backtrack_chain(self, prefix_len: int) -> list[TokenId]:
        if prefix_len == 0:
            return []
        vocab = self.inner.tokenizer.normalized.dict.vocab
        history = self.inner.history
        result: list[TokenId] = []
        pos = prefix_len
        while pos > 0:
            theta = history[pos - 1]
            result.append(theta)
            pos -= len(vocab[theta])
        result.reverse()
        return result


def _longest_common_prefix(chains: list[list[TokenId]]) -> list[TokenId]:
    if not chains:
        return []
    common: list[TokenId] = []
    # Chains legitimately differ in length; zip truncating to the shortest
    # is exactly the longest-common-prefix semantics wanted here.
    for tokens_at_depth in zip(*chains, strict=False):
        first = tokens_at_depth[0]
        if all(t == first for t in tokens_at_depth):
            common.append(first)
        else:
            break
    return common


def new_eager_run(inner: Run) -> EagerRun:
    return EagerRun(inner)


__all__ = ["EagerRun", "new_eager_run"]
