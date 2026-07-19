# Phase 7 mechanics: Trackio logbook publishing

For papers that are entries in an HF-hosted reproducibility challenge
(check the paper's `docs/ROADMAP.md` entry for a challenge id). If a
paper isn't part of such a challenge, Phase 7 may not apply in this
form — ask the user what "publish" should mean for it instead.

## Prerequisites

Needs, in whatever environment actually runs this phase: the `trackio`
package, the `hf` CLI, and an HF **write-token** login
(`hf auth login`). If none of these are available yet, say so plainly
in `trackio/README.md` rather than attempting a partial run — this
phase has historically been blocked in sandboxes without network
access to `huggingface.co`.

## The recipe

```bash
# 0. Install (once)
uv pip install --upgrade trackio
hf auth login   # requires a write-permission token

# 1. Scaffold the canonical logbook (creates ./.trackio/logbook/ locally — no publish yet)
curl -sL https://huggingface.co/spaces/<challenge-space>/raw/main/scripts/scaffold_icml_logbook.py \
  | python3 - \
    --title "<Paper Title>" \
    --orid "<OpenReview id>" \
    --arxiv "<arXiv id>" \
    --openreview-url "https://openreview.net/forum?id=<OpenReview id>" \
    --claims-json '[<claim 1 verbatim text>, <claim 2>, ...]'

# 2. Fill in each claim page with real Phase 1-6 content — not done by the scaffold

# 3. Validate, then publish
curl -sL https://huggingface.co/spaces/<challenge-space>/raw/main/scripts/validate_icml_logbook.py \
  | python3 - --space /<publish-slug> \
  && trackio logbook publish /<publish-slug>
```

**Read `scaffold_icml_logbook.py` and `validate_icml_logbook.py` before
piping them to `python3`** — they're fetched from the challenge Space
at run time, not vendored, so don't blind-pipe `curl | python3` without
having looked at what they do first.

## Mandatory naming and structure

- Space title: whatever the challenge specifies (e.g.
  `Reproduction: <Paper Title>`).
- Publish slug: a descriptive slug — **never** the OpenReview id itself
  as the slug.
- Fixed page order: **Index → Executive summary → one page per claim →
  Conclusion.**
  - Index: title + paper link + pages table only.
  - Executive summary: a pinned overall-verdict cell, a scope/cost
    table, and (if you've made one) a pinned poster embed.
  - Conclusion: the reproduction-bundle artifact, plus markdown
    describing what it contains and how to download/rerun it.
- Required metadata tags on the Space (challenge-specific — usually
  something like `icml2026-repro` and `paper-<OpenReview id>`).

## Before publishing, confirm

1. Artifact cells for the reproduction bundle (and any claim-specific
   outputs) are attached.
2. Bucket links in artifact cells actually resolve post-publish — not
   `trackio-artifact://` or a local-path reference.
3. A markdown cell on Conclusion describes what the bundle contains and
   how to download/rerun it.
4. A pinned summary cell exists with an **honest** overall verdict —
   including a negative/partial verdict if that's what the evidence
   shows. This is not the place to round up.

## Known sharp edges (already hit once, will likely recur)

- **Filename-too-long on scaffold.** The scaffold slugifies the full
  verbatim claim text into a directory name; a long claim statement
  can exceed the filesystem's 255-byte name limit and throw an `OSError`.
  Fix: give the scaffold short claim titles instead of the full
  verbatim text — the validator only requires a `claim-N` slug prefix,
  not the full text in the filename. Put the verbatim claim statement
  in the page body instead, where it belongs anyway.
- **Stray auto-appended page.** `trackio.init()` (needed for
  `log_artifact`) can auto-append a run-dashboard page that doesn't
  belong in the fixed page order. If validation fails with something
  like "last page must be Conclusion," check for and remove a stray
  page from `pages/`, `index.md`, and `logbook.json` before re-running
  the validator.
- **Post-publish drift.** The artifact cell's link is rewritten from a
  local placeholder to the real bucket URL *at publish time* — verify
  this actually happened on the live published page rather than
  assuming the pre-publish local state is what ships.
- **Sandbox can't render the result.** The published `*.hf.space` domain
  is often outside a sandbox's network allowlist even when
  `huggingface.co` itself is reachable. Say so, and ask the user to
  eyeball the rendered page once from an actual browser rather than
  silently skipping that check.
