"""Aho-Corasick automaton (paper Section 5.2).

Standard multi-pattern-matching automaton (Aho & Corasick, 1975) over
the canonical vocabulary, used here to identify tau(sc) - the longest
canonical token that is a suffix of the string fed so far - in O(1)
amortized per byte. This is a well-known technique the paper applies,
not its novel contribution (the paper's own Appendix J compares against
prior work, `rust-gems`, that already uses Aho-Corasick this way).

Simplification vs. the reference implementation: transitions are
resolved lazily by walking failure links at query time (the classic
"failure function" approach), giving amortized O(1) per byte over a
whole run, rather than the reference's eagerly-precomputed full
256-wide transition table (its square-root-tiled Appendix F structure).
That table is a memory/practical optimization for Rust production use,
not a correctness or complexity-class requirement for this
reproduction's purposes.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from incbpe.normalize import NormalizedDict
from incbpe.vocab import TokenId

State = int
ROOT_STATE: State = 0


@dataclass(frozen=True)
class AhoCorasick:
    goto: tuple[dict[int, State], ...]  # real trie edges only, per state
    fail: tuple[State, ...]
    longest_token: tuple[TokenId | None, ...]  # per state
    depth: tuple[int, ...]  # trie depth per state = length of the matched suffix

    def step(self, state: State, byte: int) -> State:
        while state != ROOT_STATE and byte not in self.goto[state]:
            state = self.fail[state]
        return self.goto[state].get(byte, ROOT_STATE)

    def feed(self, state: State, data: bytes) -> State:
        for byte in data:
            state = self.step(state, byte)
        return state


def build(normalized: NormalizedDict) -> AhoCorasick:
    vocab = normalized.dict.vocab

    # 1. Build the trie over every canonical token's bytes.
    goto: list[dict[int, State]] = [{}]
    end_of_token: list[TokenId | None] = [None]
    depth: list[int] = [0]
    for token_id, token in enumerate(vocab.tokens):
        if not token or not normalized.is_canonical(token_id):
            continue
        state = ROOT_STATE
        for byte in token:
            nxt = goto[state].get(byte)
            if nxt is None:
                goto.append({})
                end_of_token.append(None)
                depth.append(depth[state] + 1)
                nxt = len(goto) - 1
                goto[state][byte] = nxt
            state = nxt
        end_of_token[state] = token_id

    # 2. Compute failure links via BFS (classic Aho-Corasick construction).
    num_states = len(goto)
    fail = [ROOT_STATE] * num_states
    order: list[State] = [ROOT_STATE]
    queue: deque[State] = deque()
    for _byte, nxt in goto[ROOT_STATE].items():
        fail[nxt] = ROOT_STATE
        queue.append(nxt)
        order.append(nxt)
    while queue:
        state = queue.popleft()
        for byte, nxt in goto[state].items():
            f = fail[state]
            while f != ROOT_STATE and byte not in goto[f]:
                f = fail[f]
            fail[nxt] = goto[f].get(byte, ROOT_STATE)
            queue.append(nxt)
            order.append(nxt)

    # 3. longest_token[s] = the token ending exactly at s, or (by suffix
    #    link inheritance) the longest token ending at some suffix of s.
    #    Processed in BFS order so fail[s] is always resolved first.
    longest_token: list[TokenId | None] = [None] * num_states
    for state in order:
        if end_of_token[state] is not None:
            longest_token[state] = end_of_token[state]
        elif state != ROOT_STATE:
            longest_token[state] = longest_token[fail[state]]

    return AhoCorasick(tuple(goto), tuple(fail), tuple(longest_token), tuple(depth))
