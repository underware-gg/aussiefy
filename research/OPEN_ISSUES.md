# Open issues, 2026-10-14

What's known and not yet done, as of the end of the third everyday pass and its rounds. The evidence for each item
is in the file named after it. The backlog was reconciled after the Underware integration on 2026-10-15. Historical genre findings below assume explicit Auto or the named type now that General is the default.

## Wrong senses the engine still produces (engine code needed)

The data can't fix these without losing the right sense:

- **"good" and "nice" need a list of the nouns they praise**, like "great"'s GREAT_GOOD_NOUNS (better in data: a
  concept-level `only_before:`). Until then GOOD has no bare "good" trigger, so "a good feed" doesn't become a beaut
  one. (third-pass-round DECISIONS)
- **No "not a person" marker (`^thing`):** "she is feasible" can still become "a goer"; the same marker would suit
  Yanks and the punters. `^person` also does nothing on an `adv` trigger ("dedicated to"). (third-pass-round)

## Matching gaps (safe, but narrow)

- An exclusion can't look past a comma, and none looks back ("much ^adj" → heaps can't be written safely).
- A noun-phrase match right after a pronoun or "to" is refused, so guards must carry the pronoun.
- The tagger reads a comparative before a noun as a noun ("a cooler airmass").
- "The kids misbehaved all day" and "The public loved it" never swap; clause triggers need a pronoun subject ("the
  council is completely incompetent" doesn't reach its idiom).
- The dialect table skips every capitalised word as a name ("American football").
- Intensity fit is soft: an intensity-5 entry still wins about a quarter of the time on an intensity-3 trigger.

## Harness

- The reproduced moved-phrase false warning is fixed: yarn uses one counterpart sentence with positional
  tie-breaking; verification retains broader split/merge windows. Heavy paraphrases remain heuristic.
- **Lookup's model still has semantic limitations.** Slot parsing, head-only inflection and conservative
  negation anchors fix the reproduced bell/shouted/harmless toolkit errors. The underlying model remains
  unchanged; see training references for remaining wrong-sense similarities.

## The bundled embedder

The [2026-10-15 maintenance measurement](maintenance-check-2026-10-15/README.md) passes 33/33 required raw
references with all 16 known failures retained. It separately captures real toolkit lookups and pins a fresh
20-text Dinkum comparison. No new weights were produced. The subsequent
[fresh retelling study](document-refinement-2026-10-15/FINDINGS.md) scored meaning 4.95/5 but register 2.00/5;
all 20 deterministic checks passed. The following writer revision and contract-aware evaluation scored
meaning 4.95/5 and register 4.65/5, again passing all mechanical checks. Raw results from both protocols
remain; cross-protocol scores do not establish a causal engine improvement. Remaining high-level voice
weaknesses, one minor forecast narrowing, repeat judges and held-out sources are explicit follow-ups.

`aussiefy embedder status` reports aussie-static 1.2.0 as stale. It was trained before the fairdinkum, second-pass
and third-pass rounds; their entries work through the engine and lookup triggers without it, but meaning-based lookup
doesn't know them. Two 1.3.0 trials have stopped at the reference gate: "girl" ranked WOMAN after the classics round,
and after the third pass "a top bloke" reached *a mongrel bastard* (0.52 against 0.50), with no clear gain elsewhere
(`training/README.md`). 1.2.0 still passes all 33 checks. Each release adds about 14 MB to git history, so the new
repository may want `vectors.f16` in Git LFS or as a release asset first.

## Tooling

- Dictionary rounds now retain metadata and existing concept records, support explicit `concept_fixes.yaml`
  (including entryless guards), and accept a reviewed second sense with `allow_existing_form: true` plus an
  additional concept. Explicit trigger fixes still apply on reapplication; dry runs show concept-fix intent.
- Dialect-table candidate left over: "yield sign" → "give way sign".

## From the design review of the work since 5b385b4 (2026-10-14)

The review's findings were fixed; these are its follow-ups, each independent of the reviewed work:

| opportunity | benefit | why it's separate |
|---|---|---|
| Pass the toolkit one request value (a `Policy` plus `markup`) instead of threading each dial | `markup`, `english` and `embellishment` each had to be added to every signature, `YarnSession` and every MCP tool (`embellishment` alone appears 15 times in 8 modules) | An interface change across every surface |
| One `read_text(text, markup, policy, dictionary)` for the engine and lint (mask, genre, English) | Lint can't drift from how the engine read the original; it would also tidy lint's rebound parameters | Touches the engine's and lint's entry points together |
| `terms.dropped_g` for the six local copies of "Xin' is Xing" (`model.swear_strength`, `lint._phrase_words`, `lint._DROPPED_G`, lookup, gaps, llm) | One rule, one apostrophe handling | Older sites outside this change share it |
| Move the engine's reading heuristics (when to lower a first word, commands, datelines, held spans) out of `engine.py` into `context.py` or a `reading.py` | `engine.py` grew from 635 to about 900 lines, mostly text reading rather than pipeline | A refactor with no behaviour change |
| File `tests/test_second_pass.py`, `test_third_pass.py` and `test_third_pass_harness.py` by behaviour (`test_text`, `test_lint`, `test_dialect` ...) | A change's tests sit in one place | A move of about 1,000 lines of tests |
| Shared plural-inflection constants (`det.is_plural`) for `realise.number_problem`, `fit_article` and `realise` | Three sites match "plural"/"written_plural" by hand | Older sites outside this change share it |
| `heading_lines` is quadratic in the number of lines | Long plain-text documents | Pre-existing; measured as minor beside the fixed mention scan |

## From the fourth everyday pass

Measured in `research/fourth-pass-2026-10-14/FINDINGS.md`. Its recommendations are done: openings follow the form
at every setting, strict genres take no swear infixes, dinkum's guidance puts the voice into strict forms'
connecting prose, and the historical docs offered troppo for levels 4-5. Current repository publication explicitly uses Swaggie/Dinkum/Dad. The fourth-pass round
(`research/fourth-pass-round-2026-10-14/DECISIONS.md`) took its vocabulary and fixed its wrong senses in data. What's
left:

| issue | benefit | why it's separate |
|---|---|---|
| Repeat the completed controlled comparison on held-out sources and with repeat judges | Test whether the high fidelity/register balance generalises beyond these 20 familiar sources | The completed refinement retains the weak first result and later contract-aware comparison; a fresh dataset is independent evidence |
| Carry the full effective document/profile/markup contract through the production judge API | Public judging can apply the same restrictions as writing, as research protocol 2 now does | A public interface change across judge surfaces; the research run already has the context |
| Thin plans in news and official prose: most texts get no planned phrases, and at level 2 the draft is the original | The engine's draft carries some of the voice, as dinkum-3's did | Dictionary coverage of formal words, or a level-aware plan |
| Some US spellings in capitalised headings escape lint | Catch heading spellings without changing names or the Australian Labor Party | Spelling-context work; outta/oughta/wanna are intentionally emitted by our drawl and must not be banned wholesale |
| A form that leaves a captured slot unused drops it (stuff up needed two entries); a trigger's lookahead stops at punctuation | Simpler entries | Engine changes (`research/dinkum-check-round-2026-10-14/DECISIONS.md`) |
| A person swear can't tell a warm referent from any other ("every bastard" for refugees, "some bugger" for a hoped-for husband) | The worst remaining wrong senses in retellings | Needs a sentiment or referent signal the engine doesn't have |
| No negative-polarity marker in triggers, so "didn't care about" can't reach give a stuff about | Restores a swap the round had to cut | A pattern-language change |
| `^person` does nothing on a verb phrase; a guard can't end on a finite verb or hold part of a multi-word name; a noun-phrase trigger can't keep "a"; "three lots" isn't read as a count; a capital after "No" reads as a vocative | Each narrows a wrong sense the round could only part-fix (see DECISIONS) | Engine changes, one each |
| Troppo's binding rules (a letter stays a letter, a hazard is never the joke) live in guidance prose, not data | They could be checked, not only asked for | Design call: without boxing troppo in |
| Narrowed senses are cloned triggers: REPLY_TO_THANKS copies NO_PROBLEM's, EMPHATIC_REFUSAL DISAGREE's, ONE_CIGARETTE, INSIDE_WORD and FAIR_AMOUNT theirs, and some entries' `replaces` repeat their concept's trigger with its exclusions (tea, quid, chuck, the oldies) | One place to fix a sense: a loader warning when a `replaces` or a concept repeats another's trigger with different exclusions, or a way for an entry to take a subset of a concept | A schema and loader change; found by the round's design review |
| "It's fine" in answer to a question ("Is the weather nice? It's fine.") reaches NO_PROBLEM's and REPLY_TO_THANKS's reassurances | One wrong sense | Needs the previous sentence's speech act |
| A first-class `lookup_only` flag instead of placeholder triggers no sentence matches | Lookup-only concepts said outright | A schema and loader change |

## Reconciled integration items, 2026-10-15

Genre loading and validation already live on Dictionary. POS vocabulary is injected into the model without
I/O imports. The complete be-form table is shared with the matcher. Tests occupy functional/contributor layers,
and judge-tally error paths have CLI coverage. The trainer's --dest path bypasses immutable release-report
collisions and writes its report beside the dry-run model. These are resolved, not new implementation tasks.

The two whole-repository design reviews are historical records with their principal findings already fixed.
Remaining structural opportunities above should accompany relevant behaviour changes, rather than reopening
those reviews wholesale. Renaming research-pass test files by behaviour remains optional housekeeping.

Engine follow-up: the four reproduced sense/agreement defects and zero-width fallback exclusions are fixed,
with behaviour regressions. Person classification remains a conservative heuristic; grow explicit roles in
`grammar.yaml` rather than relying on ambiguous compound heads.

Harness follow-up: adjacent phrase reuse, drawl comparison from `reads_as`, dictionary-backed capitalised
phrases, bounded demonym derivation and all four strict presets now have focused regressions. The title/comma
case already passed and is pinned. Strict presets suppress infixes at Deadset/Dinkum; Troppo or explicit
behaviour overrides retain their documented freedom.

Round follow-up: metadata/guard/second-sense and reapplication preservation are implemented and regression-tested.
General comment-preserving YAML editing and a stricter variant-collision policy remain separate work; existing
variant semantics were retained after comparing all eight historical round plans.

Documentation follow-up: current sources and generated outputs are reconciled across all four layers; the
publication notice is uniform and links to each plain counterpart. Markdown fragments now share document
choices/limits. The subsequent sentence-safe refinement permits only leading garnish at a known source
sentence start in an incomplete unit; tags/tails/riffs still require complete units. Quoted examples, neutral
people and technical sense guards are pinned alongside conservative contraction/POS-context refinements.
Gettysburg wording is verified
against the linked primary transcription; Waltzing Matilda still needs an accessible exact-edition check.

Semantic fallback performance: measured dense comparisons dominated the opt-in bundled backend. Eligibility
indexing and an arithmetic-equivalent dot product now reduce warmed core translation time by about 3x on
the long measured inputs, with 92 exact full-result parity comparisons. Weights and thresholds remain.
See [the refinement report](document-refinement-2026-10-15/README.md) for reproducible evidence and limits;
website routing/end-to-end latency was not measured.

## Whole-repository review, 2026-10-16

Six concern reviews found yarn cache acceptance bypass, partial lookup `-ing` drift, a missing verification
step in the canonical agent workflow and inaccurate current documentation. The fixes retain one portable
skill and a shared `retelling.py` contract for agents, with API-specific integration at the edge. Claude
Code and Codex setup is explicit. Existing Python imports remain available.

Independent opportunities remain: optional real-SDK request serialization tests with an HTTP mock,
Python 3.10 compatibility CI, and consolidation of older duplicate contract tests. Live model execution
and website routing remain unverified. The current readiness assessment passed an installed-wheel smoke
check outside the checkout, including its CLI, shared session and installed MCP stdio wrapper; that is
separate from live model execution.

The review withdrew a proposed known-trigger gaps shortcut: custom embedder similarities are not bounded
by one, and even bundled floating-point dot products may slightly exceed it. Preserve current scores until
their public semantics are deliberately changed. Small request-local lookup caching also remains deferred;
measured savings did not justify another cache.
