# DD-001: No NLP dependency in the core

- **Status:** Accepted
- **Date:** during the initial build; in place by v0.1.0 (2026-10-12, per `CHANGELOG.md`). Recorded
  retrospectively on 2026-10-13 from the old manual's "Decisions on the brief's open questions".

## Context

The project brief left the stack open. Idioms need some syntax: whether a span is a predicate adjective after a
linking verb, intensifiers, coordination, question inversion, negation, clause boundaries, and the subject and
verb a clause idiom binds to. A full NLP library such as spaCy covers all of that, but brings a model of about
800 MB and parses that change with the library version, which would make pinned golden outputs brittle.

## Decision

Write the engine in Python, with no NLP dependency in the core. Parsing is a deliberately small, deterministic
frame checker (`aussiefy/detect.py`) that covers only what the idioms need. A spaCy-backed checker can be added
behind `detect.check_frame` later if the dictionary outgrows it.

## Consequences

- The core installs with PyYAML alone, runs offline, and gives identical output across machines and versions,
  so golden tests can pin exact text.
- The checker is heuristic and misfires on unusual syntax. Each misfire is visible in explain mode, and most
  are fixed by tightening a trigger pattern in the data rather than the code.
- Every new grammatical construction the idioms need has to be added to the checker by hand.
