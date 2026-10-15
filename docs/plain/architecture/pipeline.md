# The translation pipeline

Idioms replace **meanings**, not words, and each one brings its own grammar. The engine
(`aussiefy/engine.py`) runs each text through five stages. Everything a level does is read from
`aussiefy/data/profiles.yaml`, and every phrase from the [dictionary](../functional/dictionary.md): the engine
has no slang or level logic of its own.

1. **Parse** (`text.py`, `detect.py`). Tokenise with character offsets and split contractions
   (`you're` → `you` + `are`). A frame checker then decides whether each candidate span is in a position its
   frame allows. A predicate adjective needs a linking verb ("he's ___"), and the checker absorbs
   intensifiers ("extremely busy" scores intensity 4 and is replaced whole). It also sees through
   coordination ("stupid and all talk") and question inversion ("are you crazy"), and rejects negation
   ("not tired") and "so X that" result clauses. Interjections and imperatives must stand at the start of a
   clause. The checker records the subject and verb so that clause idioms can bind `{subj}`.
2. **Detect concepts** (`matcher.py`, `detect.py`). Trigger patterns come from the concept vocabulary and
   from every entry's `replaces`. A match on an entry's own paraphrase earns that entry a bonus. A fallback
   compares predicate spans the triggers missed against those paraphrases by similarity (`embed.py`;
   character trigrams by default).
3. **Select** (`select.py`). Filter candidates by concept, frame compatibility, level, vulgarity,
   register, region, status and slot availability. A clause idiom needs a subject, and a person idiom needs
   a person ("the plan is crazy" never gets a kangaroo loose in its top paddock). Each surviving candidate is
   weighted by intensity fit, direct match, source count, repeat penalty and the level's probability for
   its class, with a lean towards rude candidates set by the vulgarity. One seeded roll decides whether to
   substitute and another picks the candidate.
4. **Realise** (`realise.py`, `morph.py`). Fill slots and fix agreement: "are you crazy" becomes "do you
   have a kangaroo loose in your top paddock", "was" becomes "had", "lost his temper" becomes "spat the
   dummy" and "overreacting" becomes "carrying on like a pork chop". This step also handles plurals
   ("mosquitoes" becomes "mozzies"), a/an, capitalisation, and keeps contractions ("it's bucketing down").
5. **Garnish** (`garnish.py`). Each sentence gets at most one item, chosen to suit it:
   - **Connectives** ("Anyway,", "Well,", "Now,") go on narration, to move a yarn along.
   - **Openers** are exclamations.
   - **Tag-ons** (", mate") go only where someone is being addressed: dialogue (inside the quote),
     questions, exclamations, or "you".
   - **The pub aside** ("no matter what some drongo reckons") goes only after an opinion.
   - **Asides** ("What a dog's breakfast!", "Gawd help us.") close a stanza of a chant, and rhetorical
     follow-ups ("Search me.") answer the narrator's own question. In a story the engine can't judge
     whether "What a shocker!" fits what just happened, so asides stay out of story narration.
   - **Riffs** (`aussiefy/data/riffs.yaml`): at level 5 a swapped term may bring its image along where it ends a
     clause, once per sentence and twice per text: "Wheelie bins, overflowin', bin chickens fightin' over
     the scraps, and unobtainable quid!" Riffs are rated for swearing word by word, so the cap applies,
     and each has a tone (comic, grim or plain). The text's mood pulls the choice like gravity rather than a
     fence: a comic riff in a solemn text (Gettysburg) or a grim one in a light text (Goldilocks) is a
     quarter as likely, never banned. `lookup` and `plan` offer riffs to agents too.
   - **Tails** round off a closing list: "their brains and imagination, the whole kit 'n caboodle?"
   - **Chants** (mostly short exclamations, like a litany) get no openers, connectives or tag-ons, which
     would break the rhythm; only the stanza-end asides and the closer.
   - **Closers** end the text, vowel-stretched when the entry says `stretch: true` ("Faaaaaark me").

   The swear channel adds sweary openers, asides, tags, tails and closers at the vulgarity's own rate, apart
   from the level's clean garnish (see [the dials](../functional/dials.md#how-swearing-comes)). Repeats and
   synonym pile-ups are held back. The step also stacks idioms on predicate slots and applies the drawl rules
   in `aussiefy/data/phonetic.yaml`, including the swear infixes and Australian spelling. What kind of sentence
   each one is (dialogue, a question, narration ending on a deed) and the text's mood (solemn, dark or light)
   come from `context.py`.

With `--rewrite`, a sentence the dictionary couldn't carry goes to an optional rewriter after its
substitutions and before its garnish; with `--surface`, the finished text goes to Claude as a final pass (see
[LLM modes](../functional/llm-modes.md)).

Every random choice in these stages is a seeded roll keyed by its context: see
[determinism](determinism.md).

Document behaviour and source English are resolved before those stages. `genre.py` selects General by default,
a named preset directly, or classifies eligible prose and layout only when Auto is requested. It then applies
explicit dials and exact behaviour overrides. `dialect.py` reserves and realises US/UK word swaps alongside
slang. `pos.py` tags each sentence once, supplying noun/verb and subject checks. Consumers read the resolved
controls for garnish, quotes and terminology domains. Strict Markdown shares one document context, vocabulary
choices and garnish state across its prose units, retains source sentence positions for spacing and suppresses
garnish on incomplete fragments. Extended markup sends one masked document through the pipeline with opaque
protected spans. See [translation controls](../functional/translation-controls.md).
