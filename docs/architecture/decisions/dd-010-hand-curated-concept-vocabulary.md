# DD-010: A hand-curated concept vocabulary

- **Status:** Accepted
- **Date:** during the initial build; in place by v0.1.0 (2026-10-12, per `CHANGELOG.md`). Recorded
  retrospectively on 2026-10-13 from the old manual's "Decisions on the brief's open questions".

## Context

Entries are matched to text through concepts (CRAZY, BUSY, NOTHING), each with plain-English trigger patterns.
The concept set decides what the engine can detect and how entries compete. An automatically derived set would
drift and fragment as scraping and research rounds add entries.

## Decision

The concept vocabulary (`aussiefy/data/concepts.yaml`) is hand-curated. The tagger (`dev tag`) and research
rounds may propose new concept IDs; a proposal from the tagger leaves the entry gated as `untagged`, with the
proposal in its review notes, until a human consolidates it into the vocabulary.

## Consequences

- Concepts stay few, distinct and consistent, which keeps selection and agreement predictable.
- Growing the vocabulary takes human review, which slows large imports.
- The loader can reject entries with unknown concepts, and warn about concepts that can never be detected.
