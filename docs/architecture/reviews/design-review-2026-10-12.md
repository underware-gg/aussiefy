# Design review, 2026-10-12

This review follows the `software-design-review` skill (github.com/Rob-Morris/agent-skills). It covers the whole repository: the engine, dictionary, harness, yarn mode, the MCP server, the CLI, the static model, training, the scrape pipeline and the research tooling (about 7,500 lines of Python).

Six reviewers ran in parallel, each on one concern: premise, structural, code smells, efficiency, defensive coding and completion. Their findings were de-duplicated and their claims re-checked against the code. Several were also confirmed by running them. Convergence (*n*/6) counts the reviewers that raised a finding independently.

The question it answers: where did the system land, and what should be consolidated so it is honest about what it is and cheap to change?

## Findings

### High

| # | where | finding | evidence | fix | conf. |
|---|---|---|---|---|---|
| H1 | `cli.py:351-352`, callers `:101,119,138,149,283` | `--dict` is accepted by every subcommand, but `lookup`, `lint`, `guide`, `plan` and `gaps` ignore it. They call harness functions without a translator, so they fall back to the built-in dictionary without any warning. | 3/6. Premise ran it: `show --dict x` finds the entry, `lookup --dict x` doesn't. | Build one Translator in `main()` from `args.dict` and pass it to every command. | high |
| H2 | `yarn.py:184`, `harness.py:37`, `policy.py:26-65` | **The vulgarity cap is resolved inconsistently.** <br>• With `yarn --uncensored`, lookup gets cap 3 without `uncensored`, so it is clamped back to level 5's cap of 2, while check accepts 3. That breaks "lookup never offers what lint would reject". <br>• `harness._cap` drops resolve's clamp warnings. <br>• An out-of-range cap from MCP or the Python API raises a bare `KeyError`. <br>Root cause: the harness takes loose `(level, max_vulgarity, uncensored)` arguments and re-resolves them, instead of carrying one `Policy`. | 2/6, both runs confirmed. `style_guide(max_vulgarity=9, uncensored=True)` raises `KeyError: 9`. | Validate `vulgarity_cap` (0 to 3) in `Policy.__post_init__`. Have the harness resolve a `Policy` once and return its warnings. Yarn passes the caller's inputs, not the resolved cap. | high |
| H3 | `yarn.py:160-209`; `cli.py:57-95` | **Failures hide as successes.** <br>• Yarn's single `except Exception` wraps the harness, `validate` and the cache write as well as the API. A bug in our own code ends as "kept draft: KeyError" with exit code 0. <br>• If the cache write fails after acceptance, `status` says "kept draft" while `text` holds the yarn. <br>• `--rewrite` failures print nothing at all. <br>• Every fallback exits 0. | 3/6. Completion ran `--rewrite hard` with no SDK installed: the draft printed, nothing on stderr, exit 0. | Narrow the `try` to the SDK import and the API call, as `llm.py` already does. Report rewrite fallbacks on stderr. Use a distinct exit code when a mode falls back to the draft. | high |

### Medium

| # | where | finding | evidence | fix | conf. |
|---|---|---|---|---|---|
| M1 | `cli.py`, `mcp_server.py`, `yarn.py:55-81`, `harness.py`, `SKILL.md` | **One toolkit, four vocabularies.** <br>• Lint is `harness.check`, CLI `lint`, MCP `aussie_check` and yarn `check_draft`, while CLI `check` validates the dictionary. Lookup is `lookup`, `aussie_lookup` and `lookup_slang`. <br>• Parameters drift. MCP has no `uncensored` or `include_gated`. The policy knobs (`registers`, `region`, `unlock`, `embedder`, `variety`) exist only on CLI `translate`. `-s random` works only on `translate`. <br>• The default level is 3 for CLI translate, the engine and `aussiefy.translate`, but 5 everywhere else. <br>• The workflow ("guide, plan, write, lookup, check") is written out four times. | 4/6 | Declare the operations once, in harness: name, function, parameters and defaults. Derive the CLI subparsers, MCP tools and yarn tool definitions from that table. Use one verb per operation everywhere: `lookup`, `lint`, `guide`, `plan`, `translate`, `yarn`. The dictionary check becomes `validate`. One shared parent parser carries level, cap, uncensored and seed. | high |
| M2 | `harness.py` (669 lines) | **harness.py has four reasons to change:** lookup ranking, the lint rules, the style-guide prose (edited every research round) and plan shaping. Its callers use separate subsets. | 1/6 structural, plus code smells on its internals | Split into `lookup.py`, `lint.py` and `guide.py`, and move the CRAFT, LEVEL_GUIDE and OPENINGS content to `data/guide.yaml`. `harness.py` stays a thin facade (see M1). | medium |
| M3 | `engine.py:128-253`, imported by `harness.py:22`, `gaps.py:21` | **Text classification lives in the orchestrator.** `sentence_contexts`, `text_mood`, the mood word lists, the tone tables and `FORMAL_RE` sit in engine.py, and harness and gaps import them from there. The tables saying which tones suit each mood exist twice: `RIFF_TONES_FOR` in the engine and `CLOSING_TONES_FOR` in garnish. Riff picking is inlined in `_substitute`. | 2/6 | Add `context.py` for the contexts, mood and both tone tables. Add `garnish.pick_riff`. Moving the mood lexicons and thresholds to data is a follow-up. | medium |
| M4 | `harness.py:611-660`, `engine.py:305` | **`plan()` gets the engine's difficult sentences through a fake LLM rewriter** (`_Probe`), then zips two lists by position. | 2/6 | Have the engine always record `Result.difficult`. The rewriter becomes a post-pass that fills in outputs, and `plan` reads `difficult` directly. | high |
| M5 | `research/retellings-*/yarn_tools.py:43-66` vs `yarn.py:137-159` | **The yarn brief and tool dispatch are copied field by field**, behind a docstring that says the file "mirrors" yarn. Both reach into the private `harness._default_translator`. | 3/6 | Add `yarn.brief(...)` and `yarn.dispatch_tool(...)`. The API loop and the hand-run tools both call them. | high |
| M6 | `harness.py:52` (`_norm_term`), `scrape/normalise.py:19` (`canonical_key`), both `merge.py`, both `apply.py`, `llm.py:43`, `yarn.py:115` | **"Is this the same term?" is answered at six or more sites, and the answers differ.** Measured: `chuck your wobbly` matches `chuck {poss} wobbly` in three normalisers and not in apply's. So `apply.py` missed duplicates that `merge.py` had flagged. `in'` folds to `in` in one and `ing` in another. | 3/6 | One `terms.py` with `form_key` (plus a loose variant for lookup if needed), used everywhere. | high |
| M7 | `research/{gap-fill,classics}-*/apply.py` | **The apply step is two copies of a 250-line script.** They differ only in the output file and a header. The classics copy also still carries the gap-fill `-gf` id suffix, which contradicts its own docstring. The scrape → tag → review path it was meant to complement has never produced an entry (`scraped.yaml` and `sources.yaml` are empty). | 3/6, the premise reviewer for waiting | **Tension:** extract on the 2nd occurrence, or wait for the 3rd (YAGNI). Resolved by the calibration override: it is the same rule, it already shows drift, and a third round is the stated workflow. Move it into the package as `aussiefy round apply DIR`, built on M6 and `dump.py`. Demote scrape/tag/review to a `dev` group. | medium |
| M8 | `llm.py`, `yarn.py:166`, `scrape/tag.py`, `cli.py:376,389,486` | **The Claude call is open-coded four times:** client, beta flag, fallbacks, refusal check and JSON extraction. The model id appears five times, and the result cache is written twice. | 2/6 | Add `claude.py` with `client()`, `DEFAULT_MODEL`, `call_json(...)` and `cached(...)`. | high |
| M9 | `engine.py:589` (`_default`), `harness.py:28` (`_default_translator`) | **Two process-wide default translators**, each loading the dictionary (0.9 s). Yarn and yarn_tools import the private one. | 4/6 | One public `default_translator()`. | high |
| M10 | `matcher.py:207-226`; `loader.py:68`; `harness.py:111` | **The hot path for every agent tool call:** <br>• `PatternIndex.find` tries every candidate pattern at every token: 135k `match_at` calls per long translate. A prefilter on each pattern's required literal words cut `find` 16× with identical output, `translate` from 0.55 s to 0.22 s, and a long `check` from 0.55 s to 0.19 s. <br>• Each CLI call re-parses about 17 YAML files with pure-Python YAML (0.87 s), against 0.03 s to unpickle the result. <br>• `lookup` builds a new n-gram embedder per call, so its cache never hits: −32% when shared. <br>These make up most of the 4.5-minute test suite and every agent's per-call latency. | 1/6, but measured | Add the prefilter. Use `CSafeLoader` when available, plus a pickled dictionary cache keyed by a hash of the data files. Share one n-gram embedder. | high |
| M11 | `tests/test_cli.py`; `tests/test_harness.py:106` | **Untested interfaces.** 12 of 16 CLI subcommands have no test through the CLI, including the skill's whole lookup, lint, guide and plan workflow. No test ever calls an MCP tool. | 1/6, by running | One smoke test per subcommand through `main([...])`, and one `call_tool` per MCP tool. This comes after M1, which renames them. | high |
| M12 | `tests/test_static.py:96`; `model status` | **The reference-set gate on the shipped model can't fail at the moment.** The model is stale against the grown dictionary, so failures become xfail. It passes today (33/33), but a regression would land without anyone noticing. | 1/6 completion. Premise praised the xfail design. | **Tension:** the xfail is the right behaviour for a truly stale model, but staying stale indefinitely disables the gate. Fix: make the test strict on the required set (it passes now), and keep the xfail only for checks that changed since the model's dictionary. | medium |
| M13 | `cli.py:338`; `research/*/apply.py:248` | **The dictionary is written before it is validated.** `review --apply` and `apply.py --write` write first and call `load_dictionary` afterwards, so a cross-file error leaves a broken dictionary. | 1/6, code read | Validate into a temporary copy before writing. This folds into M7. | medium |
| M14 | `harness.py:41-49,220,274`, `loader.py:182-198`; `harness.py:385-388` | **Lint reads its own copies of the swear and Americanism lists**, always from the package data, while the loader reads `swears.yaml` from the dictionary's own data directory. The swear-strength rule is written three times. Separately, `_form_index` silently skips forms that won't compile (none fail today), while the loader validates `replaces` but not forms. | 3/6 | Put the word lists on `Dictionary` with a `swear_strength()` method. Compile forms in the loader and report failures. | medium |
| M15 | `README.md` | **The docs are out of date:** <br>• the headline example output and the `--explain` sample; <br>• the counts: it says 92 tests, ~120 concepts, ~240 entries and four texts, against 178, 496, 896 and 14; <br>• a contradictory "65% … 60%" figure; <br>• an orphan fragment at :122 and a duplicate sentence at :127; <br>• the "not run live" caveat omits yarn and rewrite. | 1/6, by running | Regenerate the examples from real runs, preferably in the golden test. Drop the hard counts. Do this last, after the interface changes. | high |

### Low

| # | where | finding | fix |
|---|---|---|---|
| L1 | `cli.py:24,357-399,289`; `embed.py:84`; `gaps.py:159` | **CLI edges:** <br>• the `COMMANDS` tuple duplicates the parser, so a missed name is translated as text; <br>• `level_opts` is re-declared by hand; <br>• `--embedder bogus` and a missing SDK give raw tracebacks; <br>• `--draft NAME=PATH` with an unknown NAME is silently dropped, and one without `=` crashes; <br>• `gaps` prints its "~ CONCEPT" marker at a fixed 0.6 instead of the model's own cut-off. | Covered by M1's shared parser. Also validate `--embedder` and `--draft` at parse time, and put `confident` in `Gap.to_dict`. |
| L2 | `harness.py:447` | The tag-on lint uses a hand-written regex (`mate\|ay\|eh\|cobber\|ya …`) and misses the dictionary's own tags ("like a drongo", "ya flamin' mongrel"). Verified. | Build the set from the garnish entries, as the stock-closer check at :465 already does. |
| L3 | `engine.py:284-289,425-442,522-582` | `used` and `count` Counters mix counts with string-prefixed sentinel keys (`"riff:count"`, `f"last_{p}"`, `f"conn:{id}"`), and `_garnish_sentence` takes 13 parameters. | Use a `TextState` dataclass for the per-text state. |
| L4 | `harness.py:120-171,94-98` | About ten magic scores in lookup ranking; `0.62` appears three times with no explanation. `MODEL_THRESHOLD` was calibrated on MiniLM but applies to any installed model. | Name the constants. Record a `lookup_threshold` when a model is installed. |
| L5 | `detect.py:72,207`; `engine.py:134` vs `detect.py:68` | Concept IDs hard-coded in grammar rules (`SPEECH_SENSE = {SCREAM, CRY}`, `"VERY"`). Two diverging lists of irregular past-tense verbs. | Use concept attributes in the data, or check at load time that the IDs exist. Move one `morph.is_past` and one verb set into `morph.py`. |
| L6 | `models.py:47,139`; `scrape/tag.py:174`; `research/gap-fill-*/apply_audit.py:29` | Small defensive slips: <br>• a corrupt config is read as empty and then overwritten; <br>• `from None` drops the cause; <br>• tag's catch takes in programming errors but not API errors; <br>• an audit with an unmatched id is skipped silently. | Catch only `FileNotFoundError`; chain with `from exc`; catch `APIError`; report unmatched ids. |
| L7 | `harness.py:645`; `yarn.py:182,192` | Unreachable guards: a sentence-index bounds check, `json.loads` of SDK input (always a dict), and `.get("declined")` on a field the strict schema requires. | Remove them. |
| L8 | `cli.py:376,452`, `models.py:32` | "model" means both the Claude LLM (`--model`) and the embedder (`aussiefy model install`). `model enable --bundled` switches between two different functions. | Rename the embedder commands to `aussiefy embedder …`, and give it one positional argument for which embedder. |

Not carried forward:
- **Detection memo.** The efficiency reviewer suggested memoising detection across the 100 runs per text in `test_reference`. Detections are mutated downstream, and the prefilter (M10) should remove most of the cost, so re-measure first.
- **Line-number slips.** The structural reviewer cited several `yarn_tools.py` lines (`:292`, `:329`) beyond the file's length; the findings themselves were confirmed at the right lines.

Order of operations:
1. H1–H3, which are small and fix behaviour.
2. M9, then M1 + M2 together (the interface layer). These need H2's Policy-carrying harness.
3. M5 (on M1), then M6 → M7 + M13.
4. M8, M3/M4 and M14.
5. M10, which can go any time and makes everything after it cheaper to test.
6. M11, after M1, because the tests should target the final names.
7. M12, then M15 last.

## What's done well

- **The core pipeline points inward.** `text`, `matcher`, `detect`, `select`, `realise`, `morph` and `schema` import nothing from the loader's I/O, harness, yarn, llm, scrape or cli. The stages are separately testable. Preserve this, and put the new `context.py` in the same layer.
- **`Policy` and `Effective`** are a frozen request/resolved pair. `resolve` returns its warnings instead of printing them, and `roll(seed, *parts)` is the single, context-keyed source of randomness. This is the object H2 and M1 should carry.
- **The loader is a real boundary.** It collects every YAML and schema error with file and id context, raises one `SchemaError`, and the CLI maps that to exit 2. Nothing is half-loaded.
- **The MCP server is a 40-line adapter** with no logic of its own. That is the right weight. M1 generates it from the operation table.
- **`yarn.validate` reuses `harness.check`**, so the acceptance rule has one home. M5 extends the same treatment to the brief.
- **Optional heavy dependencies load lazily** (anthropic, sentence-transformers, torch): import takes 0.08 s, `--help` 0.13 s, and the core runs offline. `llm.py` scopes its `try` to the API call, which is the template for H3.
- **The `Embedder` protocol** has three real implementations, so it earns its abstraction. Its errors name the fix.
- **The tests check behaviour.** The yarn loop is tested against a scripted client at the API boundary. The golden and reference tests check sense and well-formed output across levels and seeds, and the goldens are regenerated deliberately and reviewed as diffs. There are no stubs or TODOs in the code.
- **The static model** loads in 0.15 s without torch or numpy, and its caches are bounded.

## Related follow-ups

| opportunity | benefit | why it's separate |
|---|---|---|
| Run yarn, `--rewrite` and `tag` once against the live API, and commit the transcripts | First observed evidence that the real Messages API loop works (only fakes have been tested; `anthropic` isn't installed here) | It needs an API key; it doesn't block the consolidation |
| Move the mood lexicons, thresholds and openings into data | Each research round would edit data, not code | Bigger once M3 has made the seam; it's content, not structure |
| Release a new model version | Clears the stale flag and re-arms the gate fully | Blocked on the "girl" regression (see training/README); separate from the code changes |
| `pytest-xdist`, fewer seeds for long texts | A faster suite | Re-measure after M10 first |

## Status after the first pass

Done, in the order above: H1–H3; M1, M2 (lookup.py, lint.py, guide.py + data/guide.yaml, harness.py as the
gathering point; `check` → `lint`, `check_draft`/`submit_yarn` → `submit`, CLI `check` → `validate`), M5
(`yarn.brief` / `dispatch_tool`), M6 (`terms.py`), M7 + M13 (`rounds.py`, `aussiefy dev round`), M8
(`claude.py`), M3 (`context.py`, `garnish.pick_riff`), M4 (`Result.difficult`), M9, M10 (matcher prefilter;
libyaml loader, 0.85 → 0.20 s, instead of a pickle cache, which would need invalidating; one n-gram cache),
M11 (`test_cli.py`, `test_interfaces.py`, which checks parity in place of generating the adapters), M12, M14,
M15, and L1, L2, L4–L8. The full suite went from 4:32 to 1:43.

Deferred:
- **L3** (`TextState` for the engine's per-text counters): left for the second review, which looks at the
  engine's internal seams as a whole.
- `rounds.py` writes with `yaml.safe_dump` rather than `dump.py`, so that re-applying the classics round
  reproduces the committed file byte for byte.
