# Functional tests

Domain behaviour and toolkit contracts, including parity across the Python, CLI, MCP and yarn surfaces.

Run from the repository root:

```sh
python -m pytest -q tests/functional
```

| Module | Primary responsibility |
|---|---|
| [test_claude.py](test_claude.py) | Shared SDK request, prompt and cache contracts |
| [test_contracts.py](test_contracts.py) | Agent-consumed result shapes and shared behaviour |
| [test_document_policy.py](test_document_policy.py) | Explicit document presets and behaviour override precedence |
| [test_document_refinement.py](test_document_refinement.py) | Sentence-boundary flavour, casing, contractions and exact technical examples |
| [test_multiline_quotes.py](test_multiline_quotes.py) | Multi-paragraph quote preservation and ordinary dialect checks across surfaces |
| [test_smart_performance.py](test_smart_performance.py) | Semantic fallback eligibility, exact scores and complete-result parity |
| [test_profile_overrides.py](test_profile_overrides.py) | Advanced numeric defaults, isolated behaviour controls and surface parity |
| [test_sense_boundaries.py](test_sense_boundaries.py) | Person/adjective sense guards and clothing agreement |
| [test_lookup_senses.py](test_lookup_senses.py) | Slots, head inflection and conservative negation matching |
| [test_harness_reliability.py](test_harness_reliability.py) | Phrase locality, drawl annotations and reviewed name aliases |
| [test_markdown_composition.py](test_markdown_composition.py) | Shared document state and sentence-safe garnish |
| [test_engine.py](test_engine.py) | Detection, realisation, dials, drawl and garnish |
| [test_everyday_reference.py](test_everyday_reference.py) | Bounded everyday corpus regression checks |
| [test_gaps.py](test_gaps.py) | Gap-finding results |
| [test_guide.py](test_guide.py) | Dial-gated craft and shared workflows |
| [test_harness.py](test_harness.py) | Toolkit operations and yarn orchestration |
| [test_interfaces.py](test_interfaces.py) | Parameter and result parity across surfaces |
| [test_llm.py](test_llm.py) | Optional surface and rewrite behaviour |
| [test_local_reference.py](test_local_reference.py) | Local-only reference properties and the two permitted skips |
| [test_markdown.py](test_markdown.py) | Source protection, inline/block structure, unit offsets and surface parity |
| [test_matching.py](test_matching.py) | Tokenisation, patterns, frames and concept detection |
| [test_reference.py](test_reference.py) | Reference sense accuracy, hit rates and benchmarks |
| [test_schema.py](test_schema.py) | Dictionary data validation and defaults |
| [test_dialect.py](test_dialect.py) | Source-English swaps and typed table validation |
| [test_genre.py](test_genre.py) | Classification, selected configuration and embellishment policies |
| [test_markup.py](test_markup.py) | Extended Markdown/MDX preservation and restoration integrity |
| [test_noun_phrase.py](test_noun_phrase.py) | Nominal matching, sense and subject fit |
| [test_pos.py](test_pos.py) | Bundled tagger and contextual part-of-speech decisions |
| [test_repository_contracts.py](test_repository_contracts.py) | Retained pre-integration API and policy invariants |
| [test_second_pass.py](test_second_pass.py) | Second-pass corpus regressions |
| [test_third_pass.py](test_third_pass.py) | Third-pass corpus regressions |
| [test_verify.py](test_verify.py) | Deterministic fidelity, severity and alignment |
| [test_dinkum_check.py](test_dinkum_check.py) | Dinkum round senses, literal weather subjects and document corpus |
| [test_fourth_pass.py](test_fourth_pass.py) | Fourth round vocabulary, rejected senses and cost-sharing semantics |

Shared fixtures, corpus inputs and helpers live at [tests root](../README.md).
