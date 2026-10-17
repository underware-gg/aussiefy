# The dictionary

All the slang is data: every phrase is an entry in the YAML dictionary under `aussiefy/data/`, and every level is
a profile in `aussiefy/data/profiles.yaml` (see
[DD-002](../../architecture/decisions/dd-002-slang-is-data.md)). This page describes the files, the entry format
and the checks the loader runs. How entries get into the dictionary is in the contributor guide to
[data acquisition](../contributor/data-acquisition.md).

## Files

```
aussiefy/data/
  concepts.yaml        controlled concept vocabulary + plain-English trigger patterns per frame
  grammar.yaml         editable person nouns, adjective/noun sense limits and reviewed name-comparison aliases for the frame checker
  profiles.yaml        level profiles 1-5, the swearing rates per vulgarity, and policy defaults
  phonetic.yaml        drawl: contractions (level 4+), respellings (level 5), swear infixes (by vulgarity),
                       and Australian spelling (kind: spelling)
                       optional unless_before regex excludes grammatical contexts before a rule match
  riffs.yaml           the image a term calls up (wheelie bin: bin chickens fightin' over the scraps)
  guide.yaml           voice, language limits, openings, gated craft, workflow, plan note and yarn rules
  swears.yaml          swear words by strength, for lint and for rating riffs
  dialect.yaml         US/UK patterns, Australian replacements, sense guards and lint-only expressions
  genres.yaml          explicit document presets and embellishment settings
  judge.yaml           blind comparison rubric and report schema
  pos/                 licensed English POS weights and provenance metadata
  source_policy.yaml   sites the scraper must not bulk-extract (reference-only)
  sources.yaml         extra source URLs per entry (written by `dev review --apply`)
  model/               the bundled static embedding model
  entries/
    lexical.yaml       one-word swaps: nouns, adjectives, adverbs
    phrases.yaml       interjections, imperatives, short noun phrases
    idioms.yaml        predicate / verb-phrase / clause idioms
    garnish.yaml       connectives, openers, tag-ons, asides, tails, closers
    swearing.yaml      plain-word swears (fuckin', fuck all, a dickhead, no bastard, some cunt)
    fragments.yaml     slang found inside existing idioms
    gapfill.yaml       the gap-fill research round (research/gap-fill-2026-10-11)
    classics.yaml      the classics research round (research/classics-2026-10-11)
    flagged.yaml       omitted and gated entries (kept so re-scrapes don't reintroduce them)
    scraped.yaml       machine-managed output of the review tool
```

## Entries

An entry is one meaning-shape:

```yaml
- id: roos-top-paddock
  form: "{subj} {have} a kangaroo loose in {poss} top paddock"
  variants: ["{subj} {have} kangaroos loose in {poss} top paddock"]
  concept: [CRAZY]
  frame: clause          # predicate_adj | np | adj | adv | vp | clause | interjection | imperative | tag
  intensity: 4           # 1-5
  vulgarity: 0           # 0 clean, 1 mild (bloody, bastard), 2 impolite (piss, arse, fuck), 3 the c-word
  incoherence: 4         # minimum level at which the entry is eligible
  register: current      # current | dated | archaic
  region: []             # e.g. [qld]
  replaces: []           # plain-English paraphrases (patterns); drive matching
  status: active         # active | gate | omit
  flags: []              # not_aussie | slur | dubious_meaning | archaic | fabricated | untagged
  sources: []
  gloss: Not quite sane; eccentric.   # our own words, never a source's
```

An entry's `incoherence` (its minimum level) says how hard it is to follow, never how rude it is; rudeness is
its `vulgarity`. A `gate` entry is held back until all its flags are unlocked (`--unlock`, or `--unlock all`); an
`omit` entry is never used, and is kept only so that re-scrapes recognise it.

`riffs.yaml` maps entry IDs to optional images, each with `text` and `tone` (`comic`, `grim` or `plain`).
These can include original comparisons as well as familiar imagery; they are not additional meanings or
automatically attested sayings. Lookup offers only riffs within the swear cap, with the first eligible one
marked `best`. Plans apply the effective document/embellishment permissions; translations additionally apply
profile probabilities, spacing and limits. No extra persona setting is required to use a harvested riff.

Further optional fields:

- `slots` are inferred from the placeholders in `form`.
- `plural` handles irregular noun plurals.
- `class` (lexical, phrase or idiom) overrides how the level profile treats an entry.
- `weight` sets an entry's prior.
- `notes` holds review notes.
- `key_sha256` lets an omitted entry (for example a slur) block re-scrapes without storing the text.
- `type: garnish` entries carry `placement` (connective, opener, tag, aside, tail or closer), an optional
  `when` (the sentence contexts they suit) and an optional `stretch` (vowel-stretch the closer, as in
  "Faaaaaark me").

## Slots

Slots are `{subj} {be} {have} {do} {poss} {obj}`, plus `{np}`, which captures a short noun phrase and copies
it across, and `{will}`, which becomes "will" or "would" by tense. For example, `reckon {np} {have} Buckley's`
turns "believing her assertion to be simply impossible" into "reckoning her assertion had Buckley's". When an
entry has no verb of its own to take tense from, it uses the rest of the sentence's tense. Clause forms can
also start with "there" ("it's impossible" → "there's no bloody way").

## Pattern language

`replaces` and concept triggers share a small pattern language:

- literals, and `{slot}`
- `a|an` alternatives
- `word?` for an optional word
- `!war|deal` to block a sense: neither of the next two words may be one of these, so `great !war` skips "a
  great civil war" but still fires on "a great game"
- a trailing `@N` for intensity

In `vp` patterns the head verb matches any inflection, and in `np` patterns the head noun matches its plural.

## Validation

The loader validates everything at load time: field types and ranges, kebab-case ids, known concepts and
slots, clause forms starting with `{subj}`, `slur` forcing `omit`, no duplicate ids, and that every form
compiles as a pattern. It collects every error, with file and id, and raises one `SchemaError` (the CLI exits
2). It also warns about concepts that can never be detected and flagged entries left active.
`aussiefy validate` runs the same checks and prints stats. Required concepts, profiles, phonetic, swears,
genre, riffs and entries files must be present; malformed YAML and missing files are collected
with the other errors. String-list fields require strings, `person` and `stretch` require real booleans,
and profile garnish keys must name known placements. The guide validates its own structure and dial keys.

## Extending it

To extend the dictionary without touching the package, pass `--dict my-entries.yaml` (a file or a directory;
repeatable) to any command, or `load_dictionary(["my-entries.yaml"])` in Python. A step-by-step guide is in
[getting-started.md](../user/getting-started.md#add-your-own-entries).

## Context and source-English data

`genres.yaml` defines every genre policy and all three embellishment settings. Boolean switches must be
YAML booleans; guidance is text, garnish is a list of known placements or `all`, `keep_share` is a finite
number in 0–1 and `max_length` is finite and at least 1. Custom data directories provide their own policies.
The loader collects malformed genre/dialect data with the other dictionary diagnostics.

`dialect.yaml` maps `us`, `uk` and shared expressions to Australian wording. Values are text or a mapping
with `to`, optional `plural`, `frame`, `known_only` and `not_in`. Replacement/plural values are text and
`known_only` is boolean. `lint_only` flags expressions without automatic replacements. Concept
`not_in` and lexical subject-fit/POS rules keep terms of art and noun/verb senses in their own contexts.
See [translation controls](translation-controls.md) and the executable
[dialect](../../../tests/functional/test_dialect.py), [noun phrase](../../../tests/functional/test_noun_phrase.py)
and [schema](../../../tests/functional/test_schema.py) specifications.

## Frame vocabulary

`grammar.yaml` contains `person_nouns` (lower-case noun forms) and `adjective_nouns` (adjective to allowed
following nouns). The same adjective rule applies to attributive matches after a linking verb, so “great
disappointments” cannot evade it through a predicate frame. Multiword person triggers do not make their bare
head a person: “a party animal” does not make an animal a person. Bare person triggers and explicit role nouns
supply the person's vocabulary. Keep genuinely human singular and plural roles in the list.

Plural-only clothing forms remain available where they fit. Where a singular agreeing verb must remain, the
engine selects a compatible singular alternative rather than introducing “is my togs”.

Similarity fallback covers slot-free predicate patterns with a fixed literal shape. Optional-word patterns
remain supported by exact trigger matching; they are not guessed through similarity.

## Drawl comparison

A literal drawl rule may declare `reads_as`, its canonical wording for lint's refrain comparison:

```yaml
- id: want-to-wanna
  match: "(?i)\\bwant to\\b"
  replace: wanna
  reads_as: want to
  prob: 0.6
  min_level: 5
```

Lint reads these annotations from the loaded dictionary, including custom data. This is a comparison spelling,
not a grammatical inverse: ambiguous `yer` is consistently read as `your`. Group-reference replacements and
spelling rules cannot declare `reads_as`. Dropped-g words are also normalised during comparison.

`grammar.yaml` may declare `name_aliases`, a mapping of exact original phrases to accepted comparison wordings.
These only affect lint fidelity, never translation. Keep them narrowly reviewed: a capitalised common phrase
such as `Christmas Trees` can have `Chrissy trees` as an alias without exempting `Christmas Island` or words
inside a person's name. Changed names without an explicit alias retain their warnings.
