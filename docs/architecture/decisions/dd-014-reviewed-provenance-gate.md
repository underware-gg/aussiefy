# DD-014: Reviewed provenance enforced against tracked files and built wheels

Status: Accepted

Date: 2026-10-13

Extends: [DD-011](dd-011-copyrighted-texts-stay-local.md), [DD-012](dd-012-reference-dictionaries-are-reference-only.md)

## Context

The repository bundles derived model artefacts and keeps public-domain, own and explicitly audited research
texts. The import added attribution, but no automated check held it to the artefacts or prevented a new
tracked corpus file from losing its provenance. Ignored local copyrighted texts must not affect a release.

## Decision

A small Python maintainer script reads a reviewed registry and existing corpus manifests. It generates the
committed notices and checks metadata bindings, canonical licence bytes, packaging declarations, exactly
one claim per tracked packaged/reference text and exact remote-excerpt exceptions. Scraped entry URLs use
the existing reference-source policy. Enumeration uses Git's tracked paths, never a local corpus walk.

Fast pytest exercises those rules and fixture wheel archives. Promotion additionally builds a wheel from
an isolated tracked-file copy and compares its actual contents and licence metadata with reviewed inputs.
Build tools are maintainer dependencies; the core runtime still requires only PyYAML.

## Consequences

Model/provenance changes require reviewing declarations and regenerating notices. New files must be staged
before the working-tree check; promotion judges the exact committed checkout. Name checks and declarations
are enforcement mechanisms, not evidence of legal permission or proof that all embedded text is original.
Installed Python dependencies are not vendored and do not need a dependency licence crawler.
