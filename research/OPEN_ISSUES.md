# Open issues, 2026-10-14

What's known and not yet done, as of the end of the third everyday pass and its rounds. The evidence for each item
is in the file named after it. The backlog was reconciled after the Underware integration on 2026-10-15. Historical genre findings below assume explicit Auto or the named type now that General is the default.

## Wrong senses the engine still produces (engine code needed)

The data can't fix these without losing the right sense:

- **"great" before a noun, read as a predicate:** "These are great disappointments" → "ripper disappointments"; "great
  fun" and "great dearth" take a predicate form. (fairdinkum-round DECISIONS)
- **"good" and "nice" need a list of the nouns they praise**, like "great"'s GREAT_GOOD_NOUNS (better in data: a
  concept-level `only_before:`). Until then GOOD has no bare "good" trigger, so "a good feed" doesn't become a beaut
  one. (third-pass-round DECISIONS)
- **No "not a person" marker (`^thing`):** "she is feasible" can still become "a goer"; the same marker would suit
  Yanks and the punters. `^person` also does nothing on an `adv` trigger ("dedicated to"). (third-pass-round)
- **"An American football coach"** at the start of a sentence gets "footy": the capitalised determiner hides the
  guard. (second-pass-round)
- **`^person` counts "dog" as a person** ("the dog is loyal" → "true blue"), and doesn't know many real person
  nouns ("the apprentice was keen" is missed). (fairdinkum and second-pass rounds)

## Matching gaps (safe, but narrow)

- An exclusion can't look past a comma, and none looks back ("much ^adj" → heaps can't be written safely).
- A noun-phrase match right after a pronoun or "to" is refused, so guards must carry the pronoun.
- The tagger reads a comparative before a noun as a noun ("a cooler airmass").
- "The kids misbehaved all day" and "The public loved it" never swap; clause triggers need a pronoun subject ("the
  council is completely incompetent" doesn't reach its idiom).
- A plural-only term after a singular verb keeps the verb: "Where is my swimsuit?" becomes "Where is my togs?".
- The dialect table skips every capitalised word as a name ("American football").
- Intensity fit is soft: an intensity-5 entry still wins about a quarter of the time on an intensity-3 trigger.

## Harness

- **The moved-phrase check** (yarn.py `_moved`) aligns each planned spot with up to three nearby sentences, so a
  retelling that reuses the original's word next door can still be sent back. A tighter alignment (the one
  counterpart sentence) would close it. (third-pass design review)
- **Lookup's meaning model** still returns weak cross-sense matches ("harmless" → "a bit red hot"); the negation
  filter catches only opposites with a negation in them. Inflection matching gives an Aussie term in its other sense
  where one exists ("shouted" → a shout, buying a round).

## The bundled embedder

`aussiefy embedder status` reports aussie-static 1.2.0 as stale. It was trained before the fairdinkum, second-pass
and third-pass rounds; their entries work through the engine and lookup triggers without it, but meaning-based lookup
doesn't know them. Two 1.3.0 trials have stopped at the reference gate: "girl" ranked WOMAN after the classics round,
and after the third pass "a top bloke" reached *a mongrel bastard* (0.52 against 0.50), with no clear gain elsewhere
(`training/README.md`). 1.2.0 still passes all 33 checks. Each release adds about 14 MB to git history, so the new
repository may want `vectors.f16` in Git LFS or as a release asset first.

## Tooling

- A dictionary round can't write `not_in`, `person` or guard concepts, can't add a second sense with an existing
  form, and rewrites its own section of `concepts.yaml` when re-applied (losing hand edits there). Every recent
  round needed hand edits for these.
- Dialect-table candidate left over: "yield sign" → "give way sign".

## From the design review of the work since 5b385b4 (2026-10-14)

The review's findings were fixed; these are its follow-ups, each independent of the reviewed work:

| opportunity | benefit | why it's separate |
|---|---|---|
| Pass the toolkit one request value (a `Policy` plus `markup`) instead of threading each dial | `markup`, `english` and `embellishment` each had to be added to every signature, `YarnSession` and every MCP tool (`embellishment` alone appears 15 times in 8 modules) | An interface change across every surface |
| One `read_text(text, markup, policy, dictionary)` for the engine and lint (mask, genre, English) | Lint can't drift from how the engine read the original; it would also tidy lint's rebound parameters | Touches the engine's and lint's entry points together |
| `terms.dropped_g` for the six local copies of "Xin' is Xing" (`model.swear_strength`, `lint._phrase_words`, `lint._DROPPED_G`, lookup, gaps, llm) | One rule, one apostrophe handling | Older sites outside this change share it |
| Generate lint's `DRAWL` reverse map from `phonetic.yaml` | It has fallen behind: wanna, gotta, 'ave, dunno, 'cause, prob'ly and others aren't read back | A data-format decision (a `reads_as` field, or derived) |
| Move `model.PERSON_ROLES` into the dictionary data | Dictionary rounds can grow the person nouns `^person` knows ("the apprentice") | A data migration |
| Move the engine's reading heuristics (when to lower a first word, commands, datelines, held spans) out of `engine.py` into `context.py` or a `reading.py` | `engine.py` grew from 635 to about 900 lines, mostly text reading rather than pipeline | A refactor with no behaviour change |
| File `tests/test_second_pass.py`, `test_third_pass.py` and `test_third_pass_harness.py` by behaviour (`test_text`, `test_lint`, `test_dialect` ...) | A change's tests sit in one place | A move of about 1,000 lines of tests |
| Shared plural-inflection constants (`det.is_plural`) for `realise.number_problem`, `fit_article` and `realise` | Three sites match "plural"/"written_plural" by hand | Older sites outside this change share it |
| `heading_lines` is quadratic in the number of lines | Long plain-text documents | Pre-existing; measured as minor beside the fixed mention scan |

## From the fourth everyday pass

Measured in `research/fourth-pass-2026-10-14/FINDINGS.md`. Its recommendations are done: openings follow the form
at every setting, strict genres take no swear infixes, dinkum's guidance puts the voice into strict forms'
connecting prose, and the docs offer troppo for levels 4-5. The fourth-pass round
(`research/fourth-pass-round-2026-10-14/DECISIONS.md`) took its vocabulary and fixed its wrong senses in data. What's
left:

| issue | benefit | why it's separate |
|---|---|---|
| Re-measure dinkum after the dinkum check's fixes (`research/dinkum-check-2026-10-14/FINDINGS.md`: register came back, 3.60 to 4.00, but meaning fell 4.90 to 4.65 and dinkum-3 still leads, 4.57 against 4.46) | Whether "a verb keeps its weight" and no riffs on real things win back fidelity without losing the voice | Needs a yarn and judge pass, with dinkum-3 as the anchor |
| Thin plans in news and official prose: most texts get no planned phrases, and at level 2 the draft is the original | The engine's draft carries some of the voice, as dinkum-3's did | Dictionary coverage of formal words, or a level-aware plan |
| Lint misses American forms ("outta", "oughta", "wanna", "folks") and some US spellings in capitalised headings | The drawl's American forms are caught | Data (`dialect.yaml` lint_only) and the spelling rules |
| `name_dropped` fires when a comma sits between a title and a name ("President, George Washington"), or when a capitalised common noun is respelt ("Christmas Trees" to "Chrissy trees") | Fewer false warnings | Lint's name reading |
| A form that leaves a captured slot unused drops it (stuff up needed two entries); a trigger's lookahead stops at punctuation | Simpler entries | Engine changes (`research/dinkum-check-round-2026-10-14/DECISIONS.md`) |
| A person swear can't tell a warm referent from any other ("every bastard" for refugees, "some bugger" for a hoped-for husband) | The worst remaining wrong senses in retellings | Needs a sentiment or referent signal the engine doesn't have |
| No negative-polarity marker in triggers, so "didn't care about" can't reach give a stuff about | Restores a swap the round had to cut | A pattern-language change |
| The embedding fallback's shape check counts a trigger's `!` exclusions ("felt terrible about" slipped through one) | Exclusions hold in the fallback too | Matcher and model change |
| `^person` does nothing on a verb phrase; a guard can't end on a finite verb or hold part of a multi-word name; a noun-phrase trigger can't keep "a"; "three lots" isn't read as a count; a capital after "No" reads as a vocative | Each narrows a wrong sense the round could only part-fix (see DECISIONS) | Engine changes, one each |
| Lookup doesn't match a slot to a pronoun ("give them a bell" misses give {obj} a bell) | Agents find the variants they reach for | Lookup change |
| The round tool can't write `not_in` or a concept carrying existing entries | Rounds stop needing hand edits to concepts.yaml | Tooling |
| Troppo's binding rules (a letter stays a letter, a hazard is never the joke) live in guidance prose, not data | They could be checked, not only asked for | Design call: without boxing troppo in |
| Unit tests for lint's name fidelity (`_derived_from`, the exact forms set) beside the pass tests | The demonym rules are pinned where they live | Small |
| A regression check over every strict genre that the engine draft has no infix, not only the lightning notice | Catches a garnish list growing `infix` again | Small |
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
