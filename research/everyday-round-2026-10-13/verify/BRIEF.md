# Verifier brief (everyday round 2026-10-13)

You are verifying candidate Australian English terms before they go into a curated slang dictionary for an
English-to-Australian translator (repo: /workspace/aussiefy). **Precision matters more than coverage.** A wrong
entry makes the translator produce nonsense, and a missing one just leaves plain English. The last evaluation
found the translator's worst failures were *wrong senses*: "battlers" for any "people", "mob" for "nation",
"yakka" for a computing "task", "paddock" for a struct's "fields", "tucker" in "food colouring". So for every
entry you add, think hard about which plain-English uses it must **not** catch.

## Inputs

- **Your slice:** a YAML list of candidates (path given in your task). They were harvested from Aussie
  retellings of everyday texts by two kinds of agent: `yarn` (writing with the dictionary's help) and
  `unharnessed` (from instinct). Each candidate has these fields:
  - `term`;
  - `texts`: how many texts used it;
  - `by`: which kinds of agent used it;
  - `meanings`: `replaces: X` is the plain English the term stood for; `added` means it had no counterpart;
  - `examples`: a word-level diff context, so it may read choppy;
  - `from_texts`.

  Much of the slice is noise: retold fragments, plain English, spans that merged two edits. Reject those
  quickly.
- **`/workspace/aussiefy/research/everyday-round-2026-10-13/existing_forms.txt`:** every concept ID with its
  description, its plain-English triggers and its existing Aussie forms. Use existing concept IDs wherever the
  meaning fits, and don't duplicate an existing form.
- **The texts themselves,** if you need context: `/workspace/aussiefy/research/everyday-pass-2026-10-12/texts/NAME/`
  (`yarn.txt`, `unharnessed.txt`, and the source in `tests/corpus/everyday/`).

**Web access:** you may use search to confirm a term, and should for anything you're not certain of. Use the
User-Agent "aussiefy-research/0.1" and no email address. Write glosses in your own words; never copy a
dictionary's definition. Macquarie, the Australian National Dictionary and the OED are for checking only:
cite them, never copy them.

## Decide, for every candidate

- **`add_entry`:** a reusable, genuinely Australian expression, or general English that is distinctly the
  Australian choice. It needs evidence: a source you found, or (for very common items such as "arvo",
  "servo", "uni") your own certainty plus use in the harvest, marked `evidence: agents_only`.
- **`gate`:** probably genuine but doubtful in sense, currency, region or offensiveness. Include it as an entry
  with `status: gate` and flags (`dubious_meaning`, `archaic`, `not_aussie`).
- **`add_trigger`:** no new Aussie form is needed; a plain-English word should become a trigger of an existing
  concept, so existing slang fires for it. Give `triggers_to_add`: {CONCEPT: {frame: [phrases]}}. Use `!a|b`
  after a word to exclude what follows it ("food !colouring|safety"). Mark a trigger said only of people with
  ` ^person` before any `@level` ("drained ^person@3").
- **`americanism`:** a US word or phrase an Australian wouldn't use, with the Australian equivalent ("fall" to
  "autumn", "refrigerator" to "fridge", "gas station" to "servo"). Give `us:` and `australian:`. Only
  unambiguous ones: "fall" is also a verb, so don't list it alone; "fall season" or "in the fall" are fine.
- **`style_guide`:** a discourse habit the engine can't place as a word swap (quotative "goes", the "ADJ as"
  pattern, "a bit" understatement). Describe it in one line.
- **`reject`,** with a reason:
  - `not_lexical`: a one-off phrasing, plain English, a fragment, or a merged diff span;
  - `not_aussie`: American or British only;
  - `unattested`;
  - `wrong_sense`;
  - `offensive`: a slur, or a term demeaning a group;
  - `fabricated`: a tourist stereotype;
  - `duplicate`: an existing form.

## For add_entry and gate, give a dictionary-ready entry

```yaml
- decision: add_entry
  candidate: the candidate's term
  entry:
    id: kebab-case-id            # unique, short
    form: "the form"             # slots allowed: {subj} {be} {have} {do} {poss} {obj} {np}
    variants: []                 # spelling or article variants only (never a plural: the engine pluralises)
    concept: [EXISTING_ID]       # or NEW:SUGGESTED_ID, with `new_concept`
    frame: np                    # predicate_adj | np | adj | adv | vp | clause | interjection | imperative
    intensity: 3                 # 1-5, how strong the meaning is
    vulgarity: 0                 # 0 clean; 1 bloody, bugger, bastard; 2 piss, arse, shit, fuck; 3 the c-word
    incoherence: 2               # the minimum level, 1-5: 1 understood by anyone (arvo), 3 clear slang, 5 obscure
    register: current            # current | dated | archaic
    replaces: []                 # plain-English phrases it should replace, if the concept's triggers don't cover them
    gloss: Our own short wording.
    sources: [urls]
  new_concept: null              # or {id, description, triggers: {np: [...]}}
  triggers_to_add: {}
  evidence: web | search_summary | agents_only
  confidence: high | medium | low
  why: one line, including which senses it must not catch
```

**Notes on the fields:**
- `incoherence` is how hard the term is to follow, not how rude it is. Everyday words such as "arvo",
  "servo", "brekkie" and "uni" are 1-2.
- A noun's `form` is singular ("a servo", or "servo" for a mass noun). Give `plural:` only if it's irregular.
- An entry that only fits people, or only one sense, needs triggers that say so.

## Output

Write YAML to the output path in your task: a list with one item per candidate, and every candidate must get a
decision. A `reject`, `americanism`, `style_guide` or `add_trigger` item needs only `decision`, `candidate`,
the relevant field (`reason`, `us`/`australian`, `guidance`, `triggers_to_add`) and `why`. Check that the file
parses with `python3 -c "import yaml; yaml.safe_load(open(PATH))"`. Don't modify any other file, and don't
commit.
