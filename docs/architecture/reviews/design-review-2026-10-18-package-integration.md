# Design review: installed-package integration, 18 October 2026

Surface: W10/W3 installed-wheel probes, Unicode offset contract clarification and regressions, retained
transport/browser/performance evidence, publication and provenance. One independent reviewer assessed all
six software-design concerns.

## Findings

No remaining findings.

The package already reports Unicode code-point offsets. The schema and current guide only said “character
offsets”, leaving JavaScript consumers to guess the unit. Clarify it for change/alternative spans and mask
positions, give a code-point slicing example and pin the existing behaviour across plain text, markup and
strict Markdown with emoji, combining marks and joined emoji. A separate mask regression pins local
rendering coordinates. Contract version 1, runtime algorithms, fixtures and translations remain unchanged.

Independent verification exactly reproduced the complete installed-wheel probe report, the actual Node
alternative swap and its UTF-16 mismatch. All 94 imported package-file hashes match the wheel and checkout,
including the schema clarification. All 48 focused changes/masks tests passed. Complete pre-commit results
are recorded in the maintenance continuation.

The initial timing captures changed `Translator.lookup_embedder`, which does not choose translation's
matching mode. Both were Basic; the retained evidence now says so explicitly. A new driver requests each
translation mode through the existing `translation.run` seam. Review caught two concrete harness errors:
the public convenience wrappers reject `embedder`, and Basic's resolved scorer key is `ngram`, not `None`.
Both were corrected without changing the runtime API. An independent small wheel-backed driver run
confirmed actual scorer activation, resolved policies, text parity and package import precedence.

The explicit capture retains a failed performance criterion: Basic/Swaggie's median changes/translate is
1.606, above 1.5. Other cases have inversions and outliers; no speedup, stable Smart/Basic cost or regression
cause is inferred. The report separates observed local timings from performance acceptance and records the
controlled recheck as follow-up work.

Final independent review reproduced all 36 plain/changes outputs, parity checks and rendering counts against
the wheel without taking new timings. Driver/helper hashes, all runtime hashes, input/settings/resolved modes
and both families of timing summaries match. No findings remain for this documentation/integration slice;
the failed performance criterion remains unresolved and does not become performance acceptance.

The complete pre-commit suite passed: **2,212 tests, two expected local-corpus skips, 1,768.57 seconds**.
Ruff, whitespace and generated-publication checks also pass.

## What's done well

- The harness remains the owner of tool behaviour; real stdio and HTTP/ASGI calls compare against it rather
  than duplicating expected result construction.
- Wheel payload identity and outside-checkout imports are verified, so editable imports cannot silently
  stand in for packaged code or omit the shipped JSON schema.
- Browser interoperability is checked using an actual alternative, with no new Node dependency in the
  Python package or its test suite.
- Performance evidence retains every case and separates the median criterion from slower individual
  requests. Neither local ASGI nor engine timings are presented as deployed-site verification.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Controlled changes-overhead timing | Resolve the Basic/Swaggie median budget miss and separate scheduling from engine work | This slice clarifies the existing contract without changing translation algorithms; performance acceptance is withheld |
| Website release pin, service/editor and live client checks | Verify the actual service and consumer rather than just package boundaries | Those surfaces are owned by the website/integration work |
| Meaning-specific training and refreshed unknown-word benchmark | Test the next model against an agreed quality contract | Requires shaping before another training experiment |
