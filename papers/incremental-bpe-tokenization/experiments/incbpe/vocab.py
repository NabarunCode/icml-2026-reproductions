"""Vocabulary: the finite set V of tokens (paper Section 3.1)."""

from __future__ import annotations

from dataclasses import dataclass, field

TokenId = int
Token = bytes


@dataclass(frozen=True)
class Vocab:
    """A fixed, ordered set of byte-string tokens, indexed by position.

    Mirrors the paper's ``V`` (Section 3.1): a finite set of atomic and
    non-atomic tokens. Token identity is by position in ``tokens``, not
    by content, matching how real tokenizer vocab files work (a vocab
    file is a list; the index is the token id).
    """

    tokens: tuple[Token, ...]
    _token_to_id: dict[Token, TokenId] = field(repr=False, compare=False)

    @staticmethod
    def new(tokens: list[Token] | list[str]) -> Vocab:
        encoded = tuple(t.encode("utf-8") if isinstance(t, str) else bytes(t) for t in tokens)
        token_to_id: dict[Token, TokenId] = {}
        for token_id, token in enumerate(encoded):
            if token in token_to_id:
                raise ValueError(
                    f"duplicated token {token!r} at ids {token_to_id[token]} and {token_id}"
                )
            token_to_id[token] = token_id
        return Vocab(encoded, token_to_id)

    def __len__(self) -> int:
        return len(self.tokens)

    def find_token_id(self, token: Token) -> TokenId | None:
        return self._token_to_id.get(token)

    def __getitem__(self, token_id: TokenId) -> Token:
        return self.tokens[token_id]
