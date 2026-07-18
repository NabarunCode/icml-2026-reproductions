"""Standard BPE, computed from scratch (paper Section 3.1, Equation 1).

This is the ground-truth *definition* of correctness for everything else
in this package: ``T_D(s) = (T_rm o ... o T_r1)(phi_0)``. It is
deliberately the simplest possible correct implementation - not
optimized, not incremental - so that it can itself be trusted as an
oracle for testing the incremental algorithm in ``incremental.py``.

Matches the reference implementation's own testing strategy: the Rust
crate's tests cross-check the incremental algorithm against
``bpe_with_heap``, a from-scratch baseline internal to that crate.
This module plays the same role for our reproduction.
"""

from __future__ import annotations

from incbpe.dictionary import Dictionary, RuleId
from incbpe.vocab import TokenId


def tokenize(dictionary: Dictionary, token_ids: list[TokenId]) -> list[TokenId]:
    """Apply every rule in priority order, once each, exhaustively.

    ``token_ids`` is the starting sequence (phi_0), one token id per
    atomic unit (e.g. one per byte). Each rule is applied left-to-right,
    replacing every non-overlapping adjacent ``(pre, suc)`` match with
    ``merged``, before moving on to the next rule - matching the paper's
    "standard BPE" semantics exactly (as opposed to SentencePiece's
    dynamic global-max-priority semantics; see the paper's Appendix A,
    not yet implemented here).
    """
    sequence = list(token_ids)
    for rule in dictionary.rules:
        sequence = _apply_rule(sequence, rule.pre, rule.suc, rule.merged)
    return sequence


def tokenize_with_last_rule(
    dictionary: Dictionary, token_ids: list[TokenId]
) -> tuple[list[TokenId], RuleId | None]:
    """Like :func:`tokenize`, but also reports which rule fired last.

    Used by ``normalize.py`` to determine, for a candidate token that
    collapses down to a single token, which specific rule is responsible
    for that final merge (needed when a merged token has multiple
    candidate producing rules in a not-yet-cleaned-up dictionary).
    """
    sequence = list(token_ids)
    last_rule: RuleId | None = None
    for rule_id, rule in enumerate(dictionary.rules):
        new_sequence, changed = _apply_rule_reporting(sequence, rule.pre, rule.suc, rule.merged)
        if changed:
            last_rule = rule_id
        sequence = new_sequence
    return sequence, last_rule


def _apply_rule(sequence: list[TokenId], pre: TokenId, suc: TokenId, merged: TokenId) -> list[TokenId]:
    out, _ = _apply_rule_reporting(sequence, pre, suc, merged)
    return out


def _apply_rule_reporting(
    sequence: list[TokenId], pre: TokenId, suc: TokenId, merged: TokenId
) -> tuple[list[TokenId], bool]:
    out: list[TokenId] = []
    changed = False
    i = 0
    n = len(sequence)
    while i < n:
        if i + 1 < n and sequence[i] == pre and sequence[i + 1] == suc:
            out.append(merged)
            changed = True
            i += 2
        else:
            out.append(sequence[i])
            i += 1
    return out, changed
