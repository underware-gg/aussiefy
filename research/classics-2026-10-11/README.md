# Classics round, 2026-10-11

This round took Australianisms from classic Australian texts (Paterson, Lawson, Dennis and his glossary,
O'Brien, Rudd, Mackellar) and from three other sources: the project owner's seed terms from Waltzing Matilda,
and the phrases the unharnessed retellings used (`../retellings-2026-10-11/new_phrases.yaml`). Everything was
verified and applied to the dictionary. Every step's output is stored here, so the round can be audited or
repeated.

## Steps and files

| step | who | output |
|---|---|---|
| 1. Texts | a subagent; each text proofed against a scan of an early printing where one exists | `tests/corpus/classics/` (with `manifest.yaml`); My Country is listed in `tests/corpus/remote.yaml` and fetched locally |
| 2. Extraction | two subagents, kept from reading the dictionary. **X** took Paterson, O'Brien, Rudd and Mackellar; **Y** took Lawson, Dennis and his glossary | `extract/{X,Y}/terms.yaml`: 135 and 261 terms, each with its verbatim line, sense, proposed triggers, register and currency. `NOTES.md` covers voice habits and doubtful items |
| 3. Merge | `merge.py` | `merged.yaml`: 624 candidates (34 already in the dictionary, which were checked rather than duplicated). `dropped.yaml` lists the 11 offensive terms. `verify/candidates-{1,2,3}.yaml` are the three slices |
| 4. Verification | three subagents under `verify/BRIEF.md`, with page fetches allowed this time | `verify/verdicts-{1,2,3}.yaml` |
| 5. Apply | `aussiefy dev round research/classics-2026-10-11` (configured by `round.yaml`), plus the hand review in `concept_aliases.yaml`, `trigger_fixes.yaml`, `entry_fixes.yaml` and `extra_entries.yaml` | `aussiefy/data/entries/classics.yaml` and a new section in `concepts.yaml` |

## Outcome

Of 624 candidates:
- 182 accepted and 29 gated;
- 62 merged into existing entries and 3 became triggers only;
- 50 became style-guide notes;
- 298 rejected: 153 not Australian, 121 not reusable expressions, 13 wrong sense, 6 duplicates, 3 offensive and 2 unattested.

After the hand review this came to **210 entries (30 gated) under 139 new concepts**, plus triggers on 7
existing concepts.

| where a candidate came from | verified as useful (accepted, gated, merged or trigger) |
|---|---|
| the project owner's seed terms | 12/12 |
| both extractors | 14/16 (88%) |
| one extractor | 180/341 (53%; 39 more became style-guide notes) |
| an unharnessed retelling only | 68/252 (27%) |

The retelling-only rate (27%) matches the gap-fill round's rephraser-only rate (31%). An LLM writing freely in
Aussie mostly reaches for general informal English. The extractors scored lower than last round's web research
(91%) because they recorded everything Australian in a text, including plant and animal names with no
plain-English trigger and Dennis's British slang. The verifiers rejected those as `not_lexical` and
`not_aussie`.

## What the verifiers caught

- **Senses that read differently now:**
  - *chuck up* (now vomit), *knocks her up* (now pregnant), *top off* (now fill up);
  - *native* (now reads as Aboriginal people), *tuppy* (a vulgar homonym), *get wet*;
  - *chew the rag*, gated because readers know the US "chat" sense;
  - *tart*, *bit of fluff* and *bit of skirt*, rejected as offensive.
- **Audits of existing entries, applied by hand:**
  - *crook* gains AWFUL and DODGY ("things are looking crook", "a crook deal");
  - *pulling a swifty* moves from TEASE to TRICK;
  - *flamin'* drops to intensity 3;
  - *work back* is ungated;
  - over-broad triggers come out: FOOTBALL "soccer", FOOD "grub" (slang itself), SHOWY "flash" (slang
    itself), DORK "square" (a town square);
  - FIELD and STREAM are narrowed with lookaheads ("field of study", "field trip", "a stream of data").
- **Your seed terms:**
  - *squatter* (both senses in the gloss, dated);
  - *swagman* and *sundowner* (SWAGMAN, triggered by hobo, vagrant and drifter, but not "a tramp", which has
    other senses);
  - *billy* (only "camp kettle", never a bare "kettle");
  - *jumbuck* (only "a sheep", so "black sheep" can't fire);
  - *go waltzing Matilda*, *tucker bag*, *swag* (bedroll) and *billabong* (waterhole);
  - *coolibah tree* (a narrow trigger: "a eucalyptus by the water");
  - *gone walkabout* (the "gone missing" sense, with a sensitivity note);
  - *tucker* was already in the dictionary.

## Hand review

- **`concept_aliases.yaml`:** six concepts were proposed twice under different names (TRAMP → SWAGMAN,
  ON_THE_TRACK → TRAMP_ROADS, TAUNT → MOCK and others).
- **`trigger_fixes.yaml`:**
  - triggers with another sense come out ("a tramp");
  - possessive triggers come out: "his horse" → *prad* would drop the "his", so a bare noun is used;
  - plural literals are replaced. "cowards" isn't recognised as plural, so it gave "make a gutless wonder of us
    all". A bare singular noun matches both numbers, and the entry inflects. Bare nouns with another sense
    (steer, wildfire, corral) just lose the plural;
  - the three lookup-only concepts get narrow triggers.
- **`entry_fixes.yaml`:** *tell ya what* had a trailing comma, which the engine doubled.
- **`the good oil`:** added by hand in `phrases.yaml`. It's the current form of *the dinkum oil*.

## Engine changes this round

- **Dated and archaic words weigh 0.25** where a level allows them (level 5). They're colour, not the default:
  *bloke* keeps about three in four choices over *cove*.
- **`pluralise` drops a leading article and handles -man:** "a gutless wonder" → "gutless wonders",
  "a stockman" → "stockmen".
- **The article check looks back across the whole noun phrase,** so "the two old statesmen" no longer becomes
  "the two old the pollies".
- **No detection inside a hyphenated word** ("good-bye" was becoming "good-catch ya later"), and the "bloody"
  infix no longer splits one ("bloody good-bye").
- **Yarn mode's planned phrases leave out riffs.** The keep-60% check demanded "bush, miles from the nearest
  servo" when the yarn had *the bush*.

## Golden review

The goldens were regenerated and every changed line reviewed. The changes are:
- new genuine slang: *nan*, *clobber*, *strides*, *quick smart*, *in strife*, *thick as two planks*, *have a lash*,
  *gutless wonders*, *crook!* for "terrible!";
- re-rolls among existing slang;
- the fixes above.

One loss is accepted: "a field of turnips" no longer becomes a paddock, because "field of" is excluded to
protect "field of study".

## Style-guide notes

The 50 style-guide items are printed by `aussiefy dev round`. The useful ones are folded into the yarn-mode craft guide
(`harness.CRAFT`):
- "fair" as an intensifier before verbs ("it fair knocked me flat");
- the right-dislocated tag ("He's a good bloke, is Davo");
- "who does she run into but X";
- the reversed tag ("Never get done, do they.");
- deadpan undercutting;
- avoiding Cockney eye-dialect (wiv, orf, 'ere), which reads British today.

## Repeating the round

1. Add texts to `tests/corpus/classics/`.
2. Re-run the extractor prompts on them.
3. Run `python3 merge.py`.
4. Run the verifiers.
5. Run `aussiefy dev round research/classics-2026-10-11`. It plans against the dictionary as it was
   before the round (it sets aside `entries/classics.yaml` and the round's section of `concepts.yaml`) and
   prints what it would add and drop. Hand entries that use the round's concepts belong in
   `extra_entries.yaml`.
6. Review the dry run, add fixes here, then run it with `--write`. It validates the result in a scratch
   copy before touching the dictionary.
7. Regenerate and review the goldens.
8. Release a new model version.
