---
name: aussiefy
description: Rewrite English as genuine Australian English (slang, idiom, drawl) at a chosen level from 1 (light) to 5 (full pub yarn). Use when asked to "aussify", "say it like an Aussie", "translate into Australian slang", or to tell something as an Aussie yarn. Gives you a curated slang dictionary, a draft from a rule engine, a lint for non-Aussie phrases and US spelling, and the craft rules that make it read naturally.
---

# Aussify

You're good at Australian English. This skill gives you quality source material and a check, so the
result is genuinely Australian rather than a caricature. All commands come from the `aussiefy` CLI
(`pip install -e .` in the aussiefy repo). Every toolkit command takes two independent dials, by number or name: `-l/--level` 1-5 (`tourist`,
`blow-in`, `local`, `larrikin`, `swaggie`) and `--vulgarity` 0-3 (`nan`, `dad`, `uncle-bob`, `tradie`;
default: the level's own, `nan` at 1-2, `dad` at 3-4, `uncle-bob` at 5). Commands that read a text, and `guide`, also
take `-e/--embellishment` 0-2: how much liberty the telling takes (`deadset` straight, `dinkum` in a genuine voice,
`troppo` a performed yarn). General is the default document type, with `dinkum` embellishment. Use `--document-type auto` to opt into
detection, or select a named preset. `custom` enables only explicitly configured optional behaviours.
All document operations accept `document_config` (`--document-config` JSON): exact overrides after presets and
dials, with false and empty lists preserved. See [translation controls](../../docs/functional/translation-controls.md).
Its nested `profile` object tunes substitution, frames, garnish rates/limits/spacing, drawl, stacking,
swearing and rewrite thresholds. Omitted keys inherit the level/vulgarity defaults for every type, including
Custom. Enable Custom's optional document behaviours separately. Inspect JSON `profile_config` for the full
resolved numeric configuration, and pass it back as `document_config.profile` to reuse it.

## Workflow

1. **Know the brief.** Ask, or assume, the level (default 5, `swaggie`) and how vulgar it can be (default: the
   level's own). The vulgarity tiers are calibrated to Australian ears:
   - 0 `nan`: no swearing (strewth and crikey are fine)
   - 1 `dad`: bloody, bugger, bastard, donger
   - 2 `uncle-bob`: piss, arse, fuck
   - 3 `tradie`: the c-word too (only when asked for: no level defaults to it)

2. **Read the guide:** `aussiefy guide -l 5`
   It covers the voice, the language limits and the craft rules: swear inside sentences (where swearing is
   allowed), tag-ons only where someone is addressed, connectives in narration, no synonym pile-ups,
   Australian spelling. It gives
   `dinkum`'s note; add `-e deadset|troppo` for another setting's; at `troppo` it also says to perform the text, not
   transcribe it: unpack images into concrete Aussie ones, react like a talker (rhetorical follow-ups, stanza
   punchlines), and let terms call up their riffs. The level still decides how thick the slang is: a
   `deadset` text at level 5 is broad Aussie in its words, told straight.

3. **Get the plan:** `aussiefy plan -l 5 < input.txt` (for a Markdown or MDX document, add `--markup auto`:
   only the prose is planned, and `aussiefy lint --markup auto --original input.md` checks that your version
   kept every piece of code and markup exactly)
   This gives you the engine's draft, the slang it chose (`planned`), the `difficult_sentences` it
   couldn't carry, and `guidance` for the text's genre and embellishment. At `troppo`, write your own
   version from the original first and treat `planned` as vocabulary. The planned phrases are vetted, so keep them where they fit. The difficult sentences
   are where you add the most.

   The planned phrases are vetted candidates, not obligations. Drop any pile-ups ("buggered, rooted"),
   anything that doesn't flow, and any the engine took in the wrong sense ("battlers" for "one people",
   "ripper" for "fantastic terrors"). Also look at `untouched_sentences`: the dictionary found nothing in
   them, so they need your writing most.

   `riffs` lists the images the text's Aussie terms call up for an Australian: wheelie bins bring
   "bin chickens fightin' over the scraps", the pollies "standin' about like stunned mullets". They're
   colour that hangs off a word already there, not new content. Use one or two where they land; `lookup`
   shows riffs too. The riff marked `best` is the term's signature image (wheelie bins: the bin chickens).

   `openings` suggests three ways to start this particular text. "Right, so" is the opener every model
   reaches for, so don't default to it; pick a suggestion, or start straight in with the action. Each riff has a tone (comic, grim or plain), and `mood` says what the text is:
   solemn (a eulogy), dark (a rant or lament) or light (a fairy tale). `suits_mood` marks the riffs that
   match it. Lean towards those, but it's a lean, not a rule: a riff that fits its line and flows can
   cut against the mood, and a dark text can take a laugh.

4. **Write it.** Retell the text yourself, keeping every event, fact and character. When you're unsure
   whether something is genuinely Australian, or you want options, look it up:
   `aussiefy lookup -l 5 "very busy"`, `aussiefy lookup -l 5 someone`, `aussiefy lookup goog`.
   `lookup` uses the same vulgarity as `lint`, so it never offers what lint would
   reject. Partial terms work ("kip", "witch's tit"). If `lookup` finds nothing and you're sure
   Australians say it (lounge room, plonk), use it. If you're not sure, rephrase.

5. **Lint and fix:** `aussiefy lint -l 5 --original source.txt < draft.txt`. Exit code 1 means there are
   issues. `--original` adds the fidelity checks; always pass it when you have the source.
   - `!` issues must be fixed:
     - phrases the dictionary has flagged as non-Australian
     - swearing over the cap
     - US spelling
     - US words (y'all → youse, sidewalk → footpath)
   - `?` warnings are the guide's style rules: synonym pile-ups, slang used 3+ times, tag-ons in a story's
     narration (`tag_in_narration`; in a monologue or poem the odd "mate" to the listener is fine, but
     not on every other line: `tag_overuse`), one swear leaned on (`swear_overuse`) or too many overall
     (`swear_density`). Swear words that are in the original itself don't count against you. Fix them unless the
     repetition is a deliberate pattern in the original. With `--original`: `too_long`/`too_short`,
     `number_dropped`, `name_dropped` (fine if you localised it on purpose) and `name_added` (invented?).
   - `~` suggestions are optional extra Aussie.

   Lint does not catch invented slang, British-only or American words it doesn't list, or invented
   lines that add no names or length. A clean lint is necessary, not sufficient: reread for those yourself.

6. **Verify it:** `aussiefy verify -l 5 --original source.txt draft.txt`. It lists what you may have lost,
   worst first: `critical` (a number, a piece of markup), `major` (the brief: swearing over the cap, US
   words), `minor` (craft, and `unmatched`: an original sentence nothing in yours says again; check you
   meant to drop or rework it). Exit code 1 means a critical or major problem to fix.

7. **Deliver it.** Give the yarn. Mention the level, and anything you deliberately left formal.

## Shortcuts

- `aussiefy "text" -l 3`: the plain deterministic translation. The same text, level and seed always give
  the same output.
- `aussiefy yarn -l 5 < input.txt`: hands the whole job to Claude via the API, using this same toolkit.
  It needs `pip install -e '.[llm]'` and an API key.
- MCP: `claude mcp add aussiefy -- aussiefy-mcp` exposes the tools `aussie_lookup`, `aussie_lint`,
  `aussie_guide`, `aussie_plan`, `aussie_translate` and `aussie_verify`.

## Quality bar

- **Flow:** it reads like a person telling it, not a word swap. Vary the slang and link the sentences.
- **Fidelity:** facts and famous lines are kept. Translate the register, not the content.
- **Authenticity:** every slang term is one Australians actually use. `lint` passes.


## Markdown documents

For deterministic Markdown prose translation, use `aussiefy translate --markdown FILE`, or MCP
`aussie_translate` with `markdown: true`. It retains code/output blocks, links/images, tables, frontmatter,
HTML, markers and all heading text/IDs. JSON and explain report per-unit results and document character
ranges. Link labels and ambiguous regions are deliberately retained. General MDX/JSX prose extraction is
outside this dialect. Do not use plain-text `plan` to infer document-mode decisions.

Use the offline ngram/disabled fallback. CLI `--embedder ngram` or `--embedder none` can override a profile;
MCP/toolkit use profile defaults. Markdown rejects `--surface`, `--rewrite` and model fallbacks before work.
