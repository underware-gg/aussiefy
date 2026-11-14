# Design review: source-owned wording, selection and near meanings

The current diff after `baf31e0` was reviewed by one independent read-only reviewer against all six
software-design concern areas, with focused follow-through on source grammar, actual edit coordinates,
ED13 replay and hosted adapters. The v4 schema remains a coordinated review draft, not a release freeze.

## Findings

No unresolved findings remain in the reviewed runtime. The following confirmed issues were corrected
and covered by real-emitter regressions before the full repository gate:

| Priority and confidence | Location and concern | Finding, calibration and resolution |
|---|---|---|
| High; high | `personal_terms.py`, `engine.py`; verification | Longest-phrase ownership ran before the vulgarity cap, allowing an ineligible phrase to suppress a shorter eligible one. Filter before ownership. |
| High; high | `engine.py`, `plain_wording.py`; structural and verification | Explicit personal phrases inherited unrelated bound arguments, while English display labels could lose them. Use a separate rendering detection, authored sentence forms and shared capture/degree checks. |
| High; high | `recognition.py`; premise and verification | A lexically first homograph could assert one meaning; an inner station could displace service station. Retain all supported senses and defer to a larger settled source reading. |
| High; high | `literal_spans.py`, `engine.py`, `llm.py`, `changes.py`; structural and verification | Rewriting and replay could lose literal offsets or protect the wrong neighbouring words after garnish changed length. Move owned spans through actual edits and mask them at both optional model boundaries. |
| Medium; high | `engine.py`; verification | The full suite found held spots suppressing existing contextual suffix imagery. Restore imagery outside the exact held marker while retaining inner-edit protection and register filtering; 264 focused integration checks pass. |
| Medium; high | `recognition.py`, `model.py`, `fences.yaml`; verification | Concrete Barbie-doll, qualified-station and literal flat-strap controls were mislabelled; derived dictionaries retained removed form IDs. Rebuild ownership from current entries, use the existing name rule and scoped provisional other-sense data, and retain positive Aussie controls. The independent follow-through found and fixed the plural station family as well. |
| Medium; high | `selection.py`; premise and verification | Target-driven fallback frames offered heaps dogs for many dogs. Establish source grammatical role first; retain supported noun-phrase prepositional complements. |
| Medium; high | `cli.py`; verification | Yarn consumed the personal input without a parser flag. Share one argument parent across translation, Yarn and manual Yarn, and test non-default forwarding through a real offline plan. |
| Medium; high | `mcp_server.py`; boundary verification | The SDK dropped a hidden client list before the wrapper could reject it. Validate raw arguments before field stripping, using public Tool/model registration. |

The root-cause calibration governs these fixes: preserve shared grammatical and coordinate mechanisms,
rather than adding phrase-specific exceptions. Earlier apparent schema date-escape concerns were not
carried forward: inspecting the actual JSON characters showed the existing pattern was correct.

The final independent narrow review passed 109 focused tests without a further finding. Earlier review
passes additionally exercised every one-character selection across seven plain, escaped, Markdown and
Unicode samples, with valid source bounds. These overlapping counts are not added together. Whole pinned
rerenders remain the rendering oracle; generated fixtures are compared with actual emission. Full-suite,
Ruff, generated-doc, provenance/wheel and exact-byte results are recorded separately with the checkpoint.

## What's done well

- Ownership and ordinary replacement share one detection/selection/render/application pass. Caller words
  do not become dictionary evidence, fake cards or tuning terms.
- Near candidates preserve the waiting source reading, cite curated directed relations and retain ordinary
  permissions, genre exclusions, exact-word precedence and their separate graded roll.
- Selection maps through actual edits and escaping; multiple meanings remain separate groups. The fallback
  offers grammatical wording without presenting fuzzy similarity as an inferred meaning.
- Existing replay pins carry explicit alternate readings and preserve both inferred and chosen meanings.
  Fences retain their established priority and cannot acquire a replay identity as a side effect.
- Hosted adapters resolve a personal list once per request and reject a client-owned list at the raw-input
  boundary. The engine has no account or site state.
- Archived review bytes and the r2 bundle remain intact; real fixtures, schema checks and semantic checks
  expose the pending contract change before a site freeze.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent scope |
|---|---|---|
| Coordinate a replay variant for explicit English and request-local personal choices | Share those edits without treating literal keys as dictionary terms | Local rendered editing and existing dictionary/construction/riff replay are complete; this needs a later request-contract agreement. |
| Broaden shared irregular-verb morphology when a witnessed gap appears | Improve arbitrary personal wording beyond the current common inflections | Current capture, tense and article paths are verified; no language-specific special case is needed for this review to converge. |
| Batch meaning-quiz discovery | Reduce the measured question cost | Quiz ranking and safe distractor behaviour are unchanged by this runtime work. |
