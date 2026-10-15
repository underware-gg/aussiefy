# Verifier brief (gap-fill round 2026-10-11)

You are verifying candidate Australian English terms before they go into a curated slang dictionary for an
English-to-Australian translator (repo: /workspace/aussiefy). Precision matters more than coverage: a wrong
or fake entry makes the translator produce nonsense, and a missing one just leaves plain English.

## Inputs

- Your slice: a YAML list of candidates (path given in your task). Each has `term`, `gaps` (the plain-English
  gaps it was proposed for), `agents` (which of three independent Aussie rephrasers used it: A everyday, B broad
  pub yarn, C dialect coach), `web` (the web researcher's record, with `sources`, `confidence`, `notes`, or
  null), `meanings`, `examples`, `frames`, `vulgarity_guesses`.
- `/workspace/aussiefy/research/gap-fill-2026-10-11/existing_forms.txt`: every concept ID with its description,
  plain-English triggers and existing Aussie forms. Use existing concept IDs wherever the meaning fits.
- Rephrasings and the agents' notes, if you want context: `rephrasings/{A,B,C}/uses.yaml` (C's `note` fields are
  a skeptic's: dated, wrong-sense, not Aussie-specific).
- Web research notes: `web/NOTES.md` (including rejected terms).

Web access: the search tool works; fetching pages directly is blocked by the network policy, so judge a page by
the search result's summary, and say so (`seen_via: search_summary`). Never copy any source's definition text;
write glosses in your own words. Macquarie (macquariedictionary.com.au), the Australian National Dictionary and
oed.com are verify-only: cite them, never copy them.

## Decide, for every candidate

- `add_entry`: a reusable, genuinely Australian expression (or general English strongly current in Australia,
  noted as such), with the sense the gaps need. Needs evidence: the web record with high/medium confidence, or a
  source you find, or (for very common items) agreement of at least two agents plus your own certainty — mark
  that `evidence: agents_only` and lower confidence.
- `add_trigger`: no new Aussie form needed; the plain-English word should become a trigger of an existing concept
  so existing slang fires for it (e.g. `weary` -> TIRED). Give the concept and frame.
- `merge`: the same term as another candidate or an existing form (spelling or article variant); name it.
- `gate`: probably genuine but doubtful (sense, currency, region, offensiveness): include as an entry with
  `status: gate` and flags (`dubious_meaning`, `archaic`, `not_aussie`).
- `style_guide`: a discourse habit the engine can't place as a word swap (e.g. quotative "goes", the "ADJ as"
  pattern, "reckon" as a hedge): describe it in one line for the yarn-mode style guide.
- `reject`, with a reason: `not_lexical` (one-off phrasing, plain English with a word changed, sentence
  fragments like "let herself in"), `not_aussie` (American/British-only), `unattested`, `wrong_sense` (genuine
  term, wrong meaning for the gap, e.g. sheila for girl, stickybeak for gossip, furphy for a lie), `offensive`
  (slurs, terms demeaning groups), `fabricated` (tourist stereotype or invented), `duplicate`.

## For add_entry / gate, give a dictionary-ready entry

```yaml
- decision: add_entry
  candidate: the candidate's term
  entry:
    id: kebab-case-id            # unique, short
    form: "the form"             # slots allowed: {subj} {be} {have} {do} {poss} {obj} {np}; e.g. "chuck a {np}" no
    variants: []                 # spelling/article variants only
    concept: [EXISTING_ID]       # or NEW:SUGGESTED_ID with a one-line description in `new_concept`
    frame: predicate_adj         # predicate_adj | np | adj | adv | vp | clause | interjection | imperative | tag
    intensity: 3                 # 1-5, how strong the meaning is (default 3)
    vulgarity: 0                 # 0 clean, 1 mild (bloody, bugger, bastard), 2 impolite (piss, arse, shit, fuck), 3 c-word
    incoherence: 3               # minimum level 1-5: 1 widely understood (arvo), 3 clear Aussie slang, 5 broad/obscure
    register: current            # current | dated | archaic
    region: []                   # e.g. [qld]
    replaces: []                 # plain-English phrases this should replace if the concept's triggers don't cover them
    gloss: Our own short wording.
    sources: [urls]
  new_concept: null              # or {id, description, triggers: {predicate_adj: [...]} }
  triggers_to_add: {}            # e.g. {TIRED: {predicate_adj: [weary, fatigued]}}: plain words that should fire
  evidence: web | search_summary | agents_only
  confidence: high | medium | low
  why: one line
```

Garnish (fillers): use `type: garnish`, `placement` (opener | tag | connective | aside | tail | closer), `frame:
interjection`, and optionally `when` (narration | dialogue | question | exclamation | second_person | opinion |
fragment | paragraph_end | any). Hedges and fillers that aren't a placement (e.g. "a bit", "pretty much",
"I reckon") are `style_guide` unless they swap for a plain-English phrase (then a normal entry with `replaces`).

Avoid duplicates of existing forms (check existing_forms.txt); prefer one good entry per meaning over near-copies.
Keep ids unique within your slice (prefix nothing; the integrator dedupes across slices).

## Output

Write YAML to the output path in your task: a list, one item per candidate (every candidate must get a
decision), in the formats above (`reject`/`merge`/`style_guide`/`add_trigger` items need only `decision`,
`candidate`, the relevant field — `reason` / `into` / `guidance` / `triggers_to_add` — and `why`). Check it
parses with `python3 -c "import yaml; yaml.safe_load(open(PATH))"`. Don't modify other files.
