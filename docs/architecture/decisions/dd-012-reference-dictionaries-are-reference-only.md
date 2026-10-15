# DD-012: Reference dictionaries are reference-only; glosses are our own words

- **Status:** Accepted
- **Date:** during the initial build; in place by v0.1.0 (2026-10-12, per `CHANGELOG.md`). Recorded
  retrospectively on 2026-10-13.

## Context

The Macquarie Dictionary (with its Australian Word Map of regional words), the Australian National Dictionary
and the OED are the best checks on whether a word is genuinely Australian, where it is used and what it means.
They are copyrighted, and the Word Map sits behind a subscription; no reuse licence was found. The scraper can
bulk-extract phrase lists from web pages, and the tagger can see source meanings.

## Decision

- `aussiefy/data/source_policy.yaml` lists reference-only sources, and `dev scrape` refuses them (exit 3)
  unless `--permitted` is passed for a source you have permission to extract from. They are used by hand: look
  a word up, set its `region` and `register`, and cite the page in `sources`.
- Every gloss is written in our own words, never a source's. The tagger sees source meanings as context only,
  and a proposed gloss too similar to a source description is blanked and flagged for a rewrite.

## Consequences

- The dictionary can be published under the project's own licence.
- Regional and register tags from those dictionaries are added slowly, by hand.
