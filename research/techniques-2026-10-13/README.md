# Techniques round, 2026-10-13: making the deterministic engine translate better

**The question.** What best-practice techniques and libraries could fix the engine's weaknesses from the
everyday pass (`research/everyday-pass-2026-10-12/FINDINGS.md`)? The engine scored 2.35 against yarn's 4.68,
was never ranked first, and was weakest on authenticity, variety, register and sense. The constraint is no LLM
at run time, with deterministic, seeded output; pure Python with small dependencies is preferred.

The weaknesses, labelled for reference below:
- **W1. Wrong-sense swaps:** the wrong sense, the wrong part of speech, or a word inside a name or technical
  term.
- **W2. Low coverage** of everyday vocabulary: 34% of longer sentences are left untouched.
- **W3. Garnish and swearing that ignore genre and tone.**
- **W4. Rough grammar** around substitutions.
- **W5. No notion of genre or register.**

**How it was done.**
- Versions, licences and sizes come from PyPI's JSON API, model cards and the papers (fetched 2026-10-13,
  User-Agent `aussiefy-research/0.1`).
- Four small experiments ran in a scratch virtualenv, outside the repo: POS tagging of the findings'
  wrong-sense sentences; WordNet supersenses and the inflection libraries; genre features over
  `tests/corpus/everyday/`; and VADER on tone-sensitive sentences. Their results are quoted where they bear on a
  verdict.
- Nothing in the package was changed.

**One caveat up front.** The repo has no LICENSE file. Whether CC BY-SA data (Wiktionary, wordfreq's lists) can
be bundled depends on the licence chosen for the package. Decide it before importing share-alike data.

---

## 1. POS tagging, lemmatisation and dependency parsing

**What the engine has.** A regex frame checker (`detect.check_frame`) and the morphology heuristics in
`morph.py`. The README's decision against spaCy cites "an 800 MB model". That is the transformer pipeline with
torch. `en_core_web_sm` is 12 MB, although spaCy's own dependency tree (thinc, numpy, blis, pydantic and the
rest) is still around 100 MB installed.

| Option | Version | Licence | Size | Accuracy (published) | Determinism | Verdict |
|---|---|---|---|---|---|---|
| NLTK averaged perceptron (`averaged_perceptron_tagger_eng`) | nltk 3.10.3; data JSON | MIT (data, per nltk_data index); code Apache-2.0 | 1.5 MB zipped, 5.7 MB JSON weights | about 97% on WSJ in domain (Honnibal's reference implementation: 96.8-97.1%) | Fully: greedy, pure-Python inference | **Adopt by vendoring.** The inference is about 100 lines, needs no numpy, and measured 0.16 ms a sentence |
| spaCy + `en_core_web_sm` | spacy 3.8.16, model 3.8.0 | MIT (model trained on OntoNotes, licensed to Explosion) | 12 MB model; 36 MB spaCy wheel plus dependencies | TAG 97.29, UAS 91.77, LAS 89.92, NER F 84.33, sentences F 90.68 | Deterministic on CPU for a pinned version; parses change between model versions | **Optional extra** (`[parse]`) behind `check_frame`. Measured 0.74 ms a sentence, identical across repeat runs |
| Stanza | 1.15.0 | Apache-2.0 | torch plus 100 MB+ models | EWT from raw text: UPOS 96.20, lemma 96.63, UAS 88.90, LAS 86.77 | Deterministic on CPU in practice; torch-bound | Overkill: lower English accuracy than spaCy small, at torch cost |
| Flair | 0.15.1 (Feb 2025) | MIT | `pos-english-fast` 75 MB, `upos-english` 244 MB, plus torch | OntoNotes POS F1 98.10 (fast), 98.6 (upos) | Deterministic on CPU; slow | Overkill: tags only, no parser |
| UDPipe 1 (`ufal.udpipe`) | 1.4.0.1 | MPL-2.0 code; the UD models are CC BY-NC-SA | about 16 MB models | Near Stanza | Deterministic | **Avoid:** the non-commercial model licence |
| LemmInflect | 0.2.3 (2022) | MIT; data from NLM's SPECIALIST Lexicon | 0.8 MB; needs numpy | Lemmatiser 95.6% against AGID (self-reported; spaCy 84.7%, NLTK 52.6%) | Deterministic | **Adopt its tables** for lemmas and irregular inflection (see §7) |
| simplemma | 2.0.0 | MIT | 19 MB (many languages) | Dictionary lookup, no POS | Deterministic | Not needed: without POS it can't settle *figure* (noun or verb) |

**Experiment: would POS alone have stopped the findings' wrong swaps?** Twenty sentences rebuilt from
FINDINGS.md were tagged by both NLTK and spaCy small:
- **Blocked by POS** (6 of 19 wrong swaps):
  - *taste* as a noun (NN) against a verb idiom;
  - *figure* as a noun ("a picturesque figure") against *reckon*;
  - *relative* as an adjective against *rello*;
  - *zero* as a number modifier (CD or nummod) against *bugger-all*;
  - *live* as an adverb or adjective against a verb;
  - *Nations* as a proper noun, tagged ORG by spaCy.
- **Not blocked** (13): *fields*, *full*, *drained*, *loads*, *dedicated*, *building*, *Expect*, *pay
  attention* and the rest. The part of speech is right in each and the sense is wrong, so they need §2's
  selectional preferences and sense scoring.
- **spaCy slipped** on "drops of food colouring": it made *food* the object of *of* rather than a compound
  modifier, so even a parser needs a noun-noun backstop rule.
- Both taggers agree on all twenty, so the cheap one buys nearly everything here.

**What to adopt, ranked by value against cost:**
1. **Vendor the averaged-perceptron tagger** as `aussiefy/pos.py`, with weights in `data/pos/`. Tag each
   sentence once, in `engine.py`, after tokenising.
   - **POS constraints in the pattern language** (`matcher.py`): something like `figure/V` or `taste/N`, with
     defaults by frame. In `vp` and `predicate_adj` patterns, the head must carry a verb or adjective tag.
   - **A modifier rule in `detect.py`:** a noun followed by another noun, as in "food colouring", "dollar bill"
     or "water jackets", is a modifier and is not swapped as a head noun. This retires a family of
     hand-written exclusions.
   - **Licence caution:** the NLTK weights were trained on WSJ (Penn Treebank, an LDC corpus) and are
     distributed as MIT. If that provenance worries you, retrain the same 100-line perceptron on UD English EWT
     (CC BY-SA 4.0) or GUM, and ship the weights file under share-alike.
   - **Domain shift:** taggers lose a point or more out of domain (Honnibal says so explicitly), and the corpus
     includes 1890s recipes and MDX. Use the tags as vetoes on swaps, never as a requirement for detection.
2. **Optional spaCy small behind `detect.check_frame`**, for subject and object heads (feeding §2) and clause
   boundaries. Pin the model version in an extra, keep the goldens on the default path, and run a parity test
   for spaCy on and off. This only becomes worth it once selectional preferences are in and the heuristic head
   finder is the bottleneck.
3. Don't adopt Stanza, Flair or UDPipe.

**Modules:** `text.py` (tags on Token), new `pos.py`, `matcher.py`, `detect.py`, `engine.py`.

Sources:
- https://pypi.org/project/nltk/
- https://www.nltk.org/_modules/nltk/tag/perceptron.html
- https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/index.xml
- https://explosion.ai/blog/part-of-speech-pos-tagger-in-python
- https://raw.githubusercontent.com/explosion/spacy-models/master/meta/en_core_web_sm-3.8.0.json
- https://pypi.org/project/spacy/
- https://stanfordnlp.github.io/stanza/performance.html
- https://huggingface.co/flair/pos-english-fast
- https://huggingface.co/flair/upos-english
- https://pypi.org/project/ufal.udpipe/
- https://github.com/bjascob/LemmInflect
- https://pypi.org/project/simplemma/

---

## 2. Word sense disambiguation, cheap and deterministic

**The key point.** Classic WSD (picking a WordNet synset) is the wrong task here, and it barely beats a baseline
anyway. On Raganato et al.'s unified benchmark (F1, all parts of speech):
- extended Lesk: 48.7;
- Lesk with embeddings: 63.7;
- UKB with glosses: 57.5;
- Babelfy: 65.5;
- WordNet's first sense: 65.2;
- supervised IMS and context2vec: about 69.

Verbs sit below 58% for every system. aussiefy's real question is coarser, and binary: does this occurrence of
the trigger carry the meaning this entry glosses? The same paper notes that knowledge-based systems weigh every
context word equally and miss local cues. Local collocations are exactly what aussiefy's `!exclusions` already
capture.

| Option | Version | Licence | Size | Determinism | Verdict |
|---|---|---|---|---|---|
| pywsd (Lesk variants over NLTK WordNet) | 1.3.0 | MIT | 1.5 MB plus WordNet | Deterministic | No: fine-grained synsets at about first-sense accuracy |
| `wn` with Open English WordNet 2025 | wn 1.1.1, OEWN 2025 edition | MIT code; OEWN CC BY 4.0 | about 30 MB LMF, used offline only | Deterministic | **Use offline** to build a compact supersense table |
| NLTK WordNet 3.0 | in nltk_data | WordNet licence (permissive) | 10.8 MB zip | Deterministic | Equivalent to OEWN; the bundled model was already trained against WN 3.0 |
| Yarowsky decision lists; one sense per collocation and per discourse | papers | n/a | tiny | Deterministic | **Adopt:** it generalises `!war\|deal` |
| Embedding similarity over a context window (Lesk-with-embeddings or Melamud-style) | bundled static model | repo's own | already shipped (15 MB) | Deterministic, stdlib | **Adopt:** score each swap against sense exemplars |
| Selectional preferences on subject and object supersenses | own code plus WordNet table | CC BY 4.0 attribution | about 1-2 MB table | Deterministic | **Adopt:** it generalises the `person` subject check |

**Experiment: WordNet lexicographer classes (supersenses) of the heads in the findings:**
- *jackets* and *tank* are `noun.artifact`, so person predicates ("stuffed", "rooted") are refused.
- *software* is `noun.communication`, so *knock together* (which wants a physical artefact) is refused, while
  "building a shed" (`noun.artifact`) is allowed.
- *children* and *hikers* are `noun.person`.
- *task* is `noun.act`, which identifies a countable act and flags uncountable *yakka* for a rewrite.
- **The pitfall:** `wn.morphy("fields")` returns *fields* itself (W. C. Fields), whose first sense is
  `noun.person`. Lemmatise with the POS tag first (LemmInflect), and drop synsets whose lemma is capitalised.

**What to adopt, ranked:**
1. **Selectional preferences in entries.** Add optional `subj:` and `obj:` fields to the schema (`person`,
   `animate`, `artifact`, `physical`, `abstract`, `event`, ...). Map them to sets of WordNet supersenses
   through a table precomputed offline by a `scripts/` builder: each lemma's most frequent and second
   supersense, as a dict of about 80,000 nouns, a few hundred KB gzipped. `select.fit_rejection` checks the
   captured head. This generalises the `person` check that fixed "the water jackets are full". Value is high,
   cost medium, and it touches `schema.py`, `loader.py`, `detect.py` (head capture) and `select.py`.
2. **Sense exemplars scored with the bundled model.** Store a few positive and negative context sentences per
   entry or trigger. Score `cos(window, positive centroid) − cos(window, negative centroid)` with the static
   model, using a window of ±5 content words. Apply it as a weight factor, with a hard floor, in
   `select.candidates`, and show it in explain mode.
   - **Data you already have:** the 748 wrong-sense training pairs, every `!exclusion`, and the judges' 284
     quoted engine problems in `research/everyday-pass-2026-10-12/texts/*/verdict.json`. Each has the quote,
     the original and the reason.
   - **How cheap it is:** this is Lesk-with-embeddings, which closed most of Lesk's gap to the first-sense
     baseline above, but with in-domain exemplars instead of WordNet glosses. It costs one mean-of-vectors per
     detection.
3. **Decision lists** (Yarowsky 1994). Turn `!word|word` into ranked rules of the form: collocate within ±k,
   neighbour POS, captured head's supersense, then genre (§4), then accept or reject. Learn candidate rules
   from labelled swaps, ranked by log-likelihood ratio, and have a person curate them into
   `concepts.yaml`. They stay readable in explain mode.
4. **One sense per discourse** (Gale, Church and Yarowsky 1992). Once a trigger lemma is rejected in a text,
   such as *field* in a document with struct fields, reject it for the rest of that text. Likewise once a
   technical register is detected (§3, §4). Cheap, and it is engine-level state in `engine.py`.

Sources:
- https://aclanthology.org/E17-1010.pdf
- https://aclanthology.org/P94-1013.pdf
- https://aclanthology.org/H92-1045.pdf
- https://pypi.org/project/pywsd/
- https://pypi.org/project/wn/
- https://en-word.net/
- https://github.com/globalwordnet/english-wordnet
- https://aclanthology.org/W15-1501.pdf

---

## 3. Named entities and technical terms

**What the engine has.** `detect._in_a_name` (a capital next to a capital), `matcher._is_name` and the
Markdown/MDX masks in `markup.py`, which already protect identifiers, paths, flags and calls, but only in
markup modes.

| Option | Version | Licence | Size | Determinism | Verdict |
|---|---|---|---|---|---|
| Heuristics: capitals, ALL-CAPS acronyms, CamelCase or snake_case, dotted names, digits with units, `code` | own | n/a | 0 | Deterministic | **Adopt:** extend `markup.py`'s identifier masks to plain text |
| Termhood by frequency (a word rare in general English but repeated in this document) | wordfreq 3.1.1 (frozen since 2024) | Apache-2.0 code; CC BY-SA 4.0 data | 57 MB wheel; an extracted top-50k list is about 600 KB | Deterministic | **Adopt a derived list** (subject to the licence decision above) |
| C-value / NC-value multiword term extraction (Frantzi et al. 2000) | pyate 0.5.5 | MIT | small, but needs spaCy | Deterministic | Implement C-value yourself (about 50 lines over §1's tags); pyate drags in spaCy |
| spaCy small NER | 3.8.0 model | MIT | 12 MB plus spaCy | Deterministic, pinned | Optional, with the `[parse]` extra. F 84.3 in domain; caught "The United Nations" (ORG) |
| GLiNER (zero-shot NER) | 0.2.29 | Apache-2.0 | `gliner_small-v2.1` is 611 MB, plus torch | Deterministic on CPU | Overkill |
| YAKE / RAKE keyword extraction | yake 0.7.3 (LGPL/GPL), rake-nltk 1.0.6 (MIT) | mixed | small | Deterministic | No: keywords aren't terms, and YAKE's licence is copyleft |
| Gazetteers: Open English Namenet (2025, Wikidata-derived), Geoscience Australia place names | OEWN 2025 | CC BY 4.0 (OEWN) | large; filter to Australian and global organisations | Deterministic | Try a small filtered list, for "Broken Hill", "Snowy Mountains" and agencies |

**What to adopt, ranked:**
1. **Plain-text protection masks.** Run `markup.py`'s identifier, path, URL, flag and call masks in `text` mode
   too, plus ALL-CAPS acronyms and number-with-unit spans ("3 L", "375 °F"). The machinery exists and is
   offset-safe. Value is high, cost small, and it touches `markup.py` and `engine.py`.
2. **Recurring noun compounds count as terms.** A noun-noun or adjective-noun sequence (from §1's tags) that
   occurs twice or more in a document, or whose words are rare in general English (below about Zipf 3.5) and
   recurring, is a term ("water jackets", "food safety", "liquidity pool", "struct fields"). Its words are not
   swappable. This is C-value lite, it touches `detect.py`, and it adds the frequency list as data.
3. **One technical-register switch** feeding §4. Code-token density above about 1 per 100 words (the Interfold
   docs measure 5.5, every other group under 1) turns off rural, person and body senses for nouns.

Sources:
- https://pypi.org/project/wordfreq/
- https://raw.githubusercontent.com/rspeer/wordfreq/master/SUNSET.md
- https://pypi.org/project/pyate/
- https://pypi.org/project/gliner/
- https://huggingface.co/urchade/gliner_small-v2.1
- https://pypi.org/project/yake/
- https://github.com/globalwordnet/english-wordnet
- C-value: Frantzi, Ananiadou and Mima 2000, *Int. J. on Digital Libraries* 3(2), https://doi.org/10.1007/s007999900023

---

## 4. Tone, sentiment, formality, and genre or register classification

**What the engine has.** `context.text_mood` (solemn, dark or light, from word lists) and per-sentence
contexts. It has no genre, no formality and no safety or legal detection, so garnish runs at the same rate on a
lightning-safety notice and a yarn.

| Option | Version | Licence | Size | Determinism | Verdict |
|---|---|---|---|---|---|
| VADER | vaderSentiment 3.3.2 (2020) | MIT | 434 KB lexicon (7,506 entries) | Deterministic | **Not a tone gate** (see the experiment below). At most a weak feature |
| NRC Emotion, VAD and Intensity lexicons; NRCLex | NRCLex 4.1.0 | NRCLex code is MIT, but the NRC lexicons are **non-commercial only** | small | Deterministic | **Avoid bundling:** a licence trap |
| LIWC | commercial | proprietary | n/a | Deterministic | No |
| Heylighen-Dewaele F-score (formality from POS frequencies) | formula | n/a | 0 (needs §1's tags) | Deterministic | **Adopt** |
| Lexical formality lexicons: Brooke, Wang and Hirst 2010; Pavlick and Nenkova 2015 (PPDB formality and complexity scores) | papers, data | research release (PPDB is CC BY 3.0; check the scores' terms) | small | Deterministic | Try: a per-word formality prior, and a source of formal-to-casual paraphrase pairs |
| GYAFC formality corpus | Rao and Tetreault 2018 | requires the Yahoo L6 licence | n/a | n/a | No: can't redistribute; reference only |
| textstat | 0.7.13 | MIT; needs pyphen (tri-licensed) and nltk | small | **Not offline:** on first use it calls `nltk.download("cmudict")` (observed here) | **Don't depend on it.** Compute Flesch and average word length in a few lines |
| Biber's multidimensional features; CORE register categories | papers | n/a | 0 | Deterministic | **Adopt as the feature design** |
| Small classifier on static embeddings (nearest centroid or logistic regression over the bundled vectors plus the features) | own | n/a | KBs | Deterministic given fixed weights | Later: only once the rules plateau, and with more labelled texts than the 72 there are now |

**Experiment: VADER compound scores.**

| Sentence | Score |
|---|---|
| "You are a bloody legend, mate." | −0.44 |
| "You are a useless mongrel." | −0.42 (*mongrel* isn't in the lexicon) |
| "He died peacefully at home, surrounded by family." | −0.05 |
| "Do not feed the bears." | 0.00 |
| "The tank may be drained in spring." | −0.36 |

It reads Australian affection as hostility, and it reads a death notice and a safety order as neutral.
Sentiment isn't register.

**Experiment: cheap genre features over the everyday corpus** (spaCy tags as a stand-in for §1's tagger;
group means, rates per 100 words except `imper`, which is the percentage of sentences):

| group | imperative sentences | you | I/we | past tense | proper nouns | code tokens | F-score | n |
|---|---|---|---|---|---|---|---|---|
| conversational | 3.5 | 2.1 | 3.8 | 3.8 | 4.7 | 0.3 | **49.8** | 14 |
| instructions | **24.6** | 2.0 | 0.1 | 0.5 | 3.5 | 0.0 | 61.7 | 14 |
| interfold (docs) | 9.1 | 0.5 | 0.1 | 1.1 | 9.3 | **5.5** | **69.2** | 15 |
| news | 2.6 | 0.0 | 0.2 | 3.2 | **15.3** | 0.0 | 66.1 | 12 |
| workplace | 8.7 | 3.2 | 1.1 | 0.7 | 6.5 | 0.8 | 62.6 | 15 |

Individual texts:
- The safety texts (bear safety, lightning) have 27-37% imperative sentences and 2.3-2.9 safety cues per 100
  words. Every other text has 0.7 or fewer.
- The two obituaries have no imperatives and no *you*, 6-7% past-tense verbs, a high proper-noun rate, and
  obituary formula hits.
- The GitHub terms are the only text with legal cues above 1.

A handful of transparent features already separates the groups. Instructions and safety notices are the
easiest, because of their imperative rate.

**Features that distinguish the genres to handle.** All are deterministic, and most are cue lists plus POS
rates:

| Genre | Strongest cues |
|---|---|
| Instructions or recipe | Sentence-initial bare verbs (VB with no subject), numbered steps, quantities with units, *until*, *then* |
| Safety notice | Imperatives plus deontic modals (*must*, *should*, *do not*, *never*), signal words (DANGER, WARNING, CAUTION, NOTICE: ANSI Z535, and Australia's AS 1319), hazard nouns (*injury*, *burn*, *lightning*), emergency numbers (000, 911), "If you ... , call" |
| News | Datelines, third person, past tense, *said* or *according to* attributions, high proper-noun and number density, no *you* |
| Legal or terms | *shall*, *hereby*, *herein*, *thereof*, *pursuant*, *liable*, defined terms in capitals, numbered clauses, long sentences |
| Technical docs | Code and identifier density, *install*, *run*, *returns*, *parameter*, *configure*, imperatives, second person, headings |
| Narrative | Past tense, third person, names, dialogue quotes, time adverbials |
| Dialogue or script | Quote density, `NAME:` turn markers, first and second person, questions, interjections |
| Letter | *Dear* ... salutation, *Sincerely*, *Yours*, *Regards*, first and second person, a date line |
| Obituary or eulogy | *died*, *passed away*, *survived by*, *predeceased*, *funeral*, *memorial*, *in lieu of flowers*, ages and years, past tense, many family nouns |
| FAQ | Question headings followed by answers, second person |

**What to adopt, ranked:**
1. **A `Register` profile per text and per section**, in `context.py`, replacing and extending `text_mood`:
   - `genre`: one of the genres above, or `mixed`;
   - `formality`: the F-score plus the Latinate share that `FORMAL_RE` already measures;
   - `gravity`: solemn or grave, from the existing lists plus the obituary and safety cues;
   - `technical`: a boolean, from §3.

   Use transparent weighted rules, with every feature and the decision shown in explain mode. Tune the weights
   on the 72 labelled everyday texts, and add a held-out set before trusting them. This is the root fix for
   W3 and W5. Value is high, cost medium.
2. **A genre budget table in `profiles.yaml`.** For each genre, multipliers on the substitution probability by
   class, plus the garnish placements allowed, the riff and closer rates, sweary garnish, and the swear
   function and stance allowed (§5). For example:
   - safety and legal: lexical swaps only, no openers, closers, riffs or swears;
   - obituary: warm terms only, nothing comic or contemptuous;
   - technical: no swaps in identifier-bearing sentences, no tag-ons, no closer after code;
   - news: no tag-ons, a dry closer at most.

   `garnish.py` and `select.py` read the table. It is data, so tuning it doesn't touch code.
3. **A formality prior on substitution:** the more formal the sentence, the less likely a level-3+ idiom. A
   gentle slope, not a fence, in `select.py`.
4. Defer the embedding classifier. With 72 texts it would overfit. Revisit with a few hundred labelled texts;
   your own ingest manifests could label them by source.

Sources:
- https://github.com/cjhutto/vaderSentiment
- https://pypi.org/project/vaderSentiment/
- https://saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm
- https://pypi.org/project/NRCLex/
- https://pypi.org/project/textstat/
- https://aclanthology.org/C10-2011.pdf
- https://aclanthology.org/N15-1023.pdf
- https://aclanthology.org/Q16-1005.pdf
- https://aclanthology.org/N18-1012.pdf
- Heylighen and Dewaele 2002, "Variation in the contextuality of language", *Foundations of Science* 7,
  https://doi.org/10.1023/A:1019661126744
- Biber 1988, *Variation across Speech and Writing*, https://doi.org/10.1017/CBO9780511621024
- Egbert, Biber and Davies 2015, CORE register taxonomy, https://doi.org/10.1002/asi.23308

---

## 5. Profanity and offensiveness: detection, grading and gating

**What the engine has.** `data/swears.yaml` grades words 1-3 on an Australian scale, entries carry
`vulgarity`, and `profiles.yaml` sets swearing rates by vulgarity. Swearing is calibrated for *how rude*, but not
for *at whom* or *in what text*. The findings' failures are all of that kind:
- "If some mongrel is struck by lightning": a generic referent who is a victim;
- "every bastard": a universal quantifier;
- "little buggers" for millions of children.

| Option | Version | Licence | Size | Graded? | Determinism | Verdict |
|---|---|---|---|---|---|---|
| better-profanity | 0.7.0 (2020; its own README warns of a performance regression and recommends 0.6.1) | MIT | 50 KB | No: yes or no, with leetspeak variants | Deterministic | No: binary, US-centric, unmaintained |
| alt-profanity-check | 1.9.1 | MIT | 0.8 MB, scikit-learn linear SVM | No | Deterministic for pinned sklearn | No: binary, trained on US toxicity data, and would flag "bloody legend" |
| profanity-filter | 1.3.3 | GPL-3.0+ | small plus spaCy | No | Deterministic | No: licence and weight |
| Detoxify (`toxic-bert`) | 0.5.2 | Apache-2.0 | 438 MB plus torch | Scores for toxicity and identity attack | Deterministic on CPU | Overkill at run time. Possibly an offline audit of riffs and swears for identity attacks |
| Ofcom 2021 offensive-language research (186 words, rated mild, medium, strong or strongest) | report | Ofcom copyright | n/a | **Yes** | n/a | **Use as a calibration reference** for `swears.yaml` grades (UK ears; the c-word differs, as the README notes) |
| HurtLex (offensive lexicon by category, including target types) | dataset | CC BY-SA 4.0 per its GitHub repo (not in the paper; verify) | small | Categories | Deterministic | Try for flagging identity and slur categories, the `slur` flag's guard |
| McEnery's swearing function scheme | papers | n/a | 0 | Function, not strength | n/a | **Adopt as an entry field** |

**The technique worth stealing is function-based annotation.** McEnery and Xiao's categories for *fuck* in the
BNC are: general expletive, personal insult (a defined referent), cursing, destinational ("piss off"), literal,
emphatic intensifier ("fucking marvellous"), pronominal, and idiomatic set phrase. Insult risk lives almost
entirely in *personal insult* and *cursing*. *Emphatic intensifier* and *general expletive* carry no target.
That is why "a bloody great stoush" is fine on a news story where "some mongrel" is not.

**What to adopt, ranked:**
1. **Tag every swearing entry with `function`, `stance` and `target`.**
   - `function`: intensifier, expletive, insult, destinational, idiom or descriptive.
   - `stance`: affectionate, neutral or contemptuous. "A good cunt" is affectionate, "a dog cunt"
     contemptuous, and "little buggers" fond only when the target is small and present.
   - `target`: what a person-word may land on.

   This needs a schema field and a one-off curation pass over about 150 entries. It touches `schema.py`,
   `loader.py`, `entries/swearing.yaml` and `phrases.yaml`.
2. **Target gating in `select.fit_rejection`.** A person insult, or any contemptuous stance, needs a referent
   that is a specific adult. It must be either addressed (second person or dialogue) or the subject of an
   opinion. Refuse it when:
   - the referent is generic or quantified (*some*, *every*, *any*, *anyone*, *millions of*, plural with no
     determiner);
   - the referent is a victim (the subject of a passive harm verb: *struck*, *killed*, *injured*, *bitten*,
     *drowned*);
   - the referent is a child (`noun.person` plus a child lexicon);
   - the referent is deceased (an obituary genre, or *the late*).

   This uses §1's tags and §2's supersense table.
3. **Genre gating** through §4's budget table: safety and legal allow no swears; obituaries allow affectionate
   swears only (and only at `uncle-bob`+ when the source is itself a eulogy in a casual voice); news and
   technical allow intensifiers only. `vulgarity` stays the ceiling, and genre sets what is allowed under it.
4. **Recalibrate grades with Ofcom's tiers as a cross-check.** Don't copy their list; note disagreements in
   `swears.yaml` comments. Add HurtLex's identity categories to `flagged.yaml` checks, so a scrape can't bring
   in a slur.
5. Lint (`lint.py`) gets the same gate as warnings, for yarn mode: "contemptuous swear on a generic referent".

Sources:
- https://pypi.org/project/better-profanity/
- https://github.com/snguyenthanh/better_profanity
- https://pypi.org/project/alt-profanity-check/
- https://github.com/dimitrismistriotis/alt-profanity-check
- https://pypi.org/project/profanity-filter/
- https://pypi.org/project/detoxify/
- https://huggingface.co/unitary/toxic-bert
- https://www.ofcom.org.uk/research-and-data/tv-radio-and-on-demand/tv-research/offensive-language
- https://www.ofcom.org.uk/__data/assets/pdf_file/0018/225432/Note-to-Broadcasters-Offensive-Language-Research.pdf
- https://eprints.lancs.ac.uk/id/eprint/52/
- https://research.aston.ac.uk/files/117719442/love_swearing_symposium.pdf
- HurtLex: Bassignana, Basile and Patti 2018, https://ceur-ws.org/Vol-2253/paper49.pdf

---

## 6. Rule- and lexicon-based style transfer, dialect translation and lexical substitution

**Dialect rewriting by rule.** Multi-VALUE (Ziems et al., ACL 2023) is the closest academic analogue to
aussiefy:
- **What it is:** a controllable rule-based translator from Standard American English to 50 English dialects,
  implementing 189 morphosyntactic features from eWAVE (the electronic World Atlas of Varieties of English).
  Native speakers validated its perturbations: 74 of 92 rules were more than 95% accurate.
- **Dialects:** it includes "Australian English" (60 attested features) and "Australian Vernacular English"
  (56), weighted by eWAVE's attestation (1.0 pervasive, 0.6 neither, 0.3 rare).
- **Package:** `value-nlp` 0.3, Apache-2.0, pins spaCy 3.7.4, Stanza 1.8.2, NLTK 3.5 and transformers.
- **Its features are grammar, not slang.** Examples for Australian Vernacular English:
  - *me* for *my* ("me mum", 1.0);
  - *yous* (the `yall` feature, 1.0);
  - *them* for *those* ("them boots", 1.0);
  - flat adverbs ("real good", 1.0);
  - existential *there's* with a plural ("there's heaps of them", 1.0);
  - negative concord (1.0);
  - *never* as a past negator ("I never took it" for "didn't", 0.6);
  - *she* or *he* for inanimate things ("she'll be right", 0.6);
  - clause-final *but* (0.6).

  These are exactly what the drawl rules lack.
- **Verdict:** don't import the package. Its dependencies are heavy and old, and it's built to stress-test
  models, not to read naturally. Port six to eight eWAVE features as level-4/5 rules with frame checks. eWAVE is
  CC BY 3.0.

**Retrieval-style style transfer.** "Delete, Retrieve, Generate" (Li et al. 2018) finds attribute markers by
salience: n-grams far more frequent in one style's corpus than the other's. Its deterministic *delete* step is a
good ranking for `aussiefy dev harvest`. Rank the 2,125 staged phrasings by salience (frequency in the yarn and
unharnessed retellings against the originals) before human review.

**Contextual lexical substitution.**
- **The benchmarks:** LS07 (SemEval-2007 task 10), CoInCo (Kremer et al. 2014) and SWORDS (Lee et al. 2021).
  SWORDS's main lesson suits aussiefy: separate *candidate generation* from *acceptability in context*, and
  judge acceptability as a classification. In aussiefy the dictionary generates and select ranks.
- **The cheapest strong unsupervised ranker:** Melamud, Levy and Dagan's (2015) add/balAdd/mult measures score
  a substitute *s* for target *t* in context *C* as

  `BalAdd = (|C|·cos(s,t) + Σ_c cos(s,c)) / (2|C|)`

  This keeps the target similarity and the context fit in equal balance. Arefyev et al. (2020) show that
  injecting the target's own information, not just the context, is what makes neural substitution work. That
  is the same balance.
- **What aussiefy can do:** compute BalAdd with the bundled static model. *s* is the entry's gloss and forms, *t*
  the trigger span, *C* the ±5 content words. Use it as a multiplicative weight and a floor in
  `select.candidates`. Melamud's measure assumes separate word and context embeddings (from skip-gram). The
  bundled model has one space, so treat it as a heuristic and calibrate the floor on labelled swaps.

**What to adopt, ranked:**
1. **A labelled swap set ("aussiefy-LS").** Take every engine swap in the 59 everyday texts (from `--explain`),
   joined to the judges' 284 quoted engine problems. Label each acceptable or wrong-sense, with the context.
   Use it to tune §2's exemplar floor and the BalAdd floor for precision at fixed coverage, and keep it as a
   regression test. Value is high, cost low to medium, and it needs no dependency.
2. **The BalAdd context score in `select.py`**, next to the existing weights, shown in explain mode.
3. **eWAVE grammar features** as level-4/5 rules in `phonetic.yaml` and `realise.py`, each behind a frame check
   (*me* for *my* only before a kin or possession noun, not in "my God"; *she'll be right* only for an inanimate
   subject with *will be fine/okay*). This mainly helps variety and authenticity (W2).
4. **Salience ranking in harvest** (`scrape/harvest`), to feed the coverage round.

Sources:
- https://aclanthology.org/2023.acl-long.44.pdf
- https://aclanthology.org/2022.acl-long.258.pdf
- https://pypi.org/project/value-nlp/
- https://raw.githubusercontent.com/SALT-NLP/multi-value/main/README.md
- https://ewave-atlas.org/
- https://aclanthology.org/N18-1169.pdf
- https://aclanthology.org/W15-1501.pdf
- https://aclanthology.org/2020.coling-main.107.pdf
- https://aclanthology.org/2021.naacl-main.345.pdf
- LS07: https://aclanthology.org/S07-1009/
- CoInCo: https://aclanthology.org/E14-1057/

---

## 7. Grammar repair after substitution

| Option | Version | Licence | Size | Determinism | Verdict |
|---|---|---|---|---|---|
| LemmInflect | 0.2.3 | MIT (data from the SPECIALIST Lexicon) | 0.8 MB; numpy for the out-of-vocabulary net | Deterministic | **Adopt its lookup tables** (vendor them; skip the numpy fallback) |
| pyinflect | 0.5.1 (2020) | MIT | 0.7 MB | Deterministic | No: superseded by LemmInflect |
| inflect | 7.5.0 | MIT; needs more_itertools and typeguard | 70 KB | Deterministic | **Port its a/an rules**, or depend on it optionally. Its plurals handle multiword heads ("cups of tea") |
| LanguageTool | core LGPL-2.1 (Java 17+); `language_tool_python` 3.4.0 is **GPL-3.0** | 0.06 MB wrapper plus a 200 MB+ Java server | Deterministic only with a pinned local server; the public API is rate-limited and changes | **Dev or tuning loop only:** count errors the translation introduces. Never import it from the package (GPL wrapper) or run it at run time |
| Neural GEC (GECToR, Gramformer) | various | various | GBs | Not reliably deterministic | No |

**Experiment: a/an on Australian words**:

| Phrase | `text.fix_articles` today | inflect 7.5.0 | Correct |
|---|---|---|---|
| ute | "an ute" | "a ute" | a |
| U-turn | "an U-turn" | "a U-turn" | a |
| FBI agent | "a FBI agent" | "an FBI agent" | an |
| NSW bloke | "a NSW bloke" | "an NSW bloke" | an |
| RSL | "a RSL" | "an RSL" | an |
| SUV | "a SUV" | "a SUV" | an |
| uni | "a uni" | "an uni" | a |
| hour, esky, arvo, one-off | right | right | |

`fix_articles` gets 6 of 14 wrong, and inflect gets 2. The best is inflect's letter-name rule for acronyms
combined with aussiefy's own exceptions (uni, ute, u-ey, Uluru). It's a small, concrete fix.

**Experiment: inflection.**
- LemmInflect gives *lobbed* and *spat*, but `getInflection("darts", "NNS")` gives **"dartses"**. That is the
  same bug FINDINGS fixed by hand. Always lemmatise first, then inflect.

**What to adopt, ranked:**
1. **Fix `text.fix_articles`.** Use the letter-name rule for all-caps tokens: *an* before F, H, L, M, N, R, S
   and X and before vowel letters except U; *a* otherwise. Use a `yoo`-sound prefix list (uni-, ute, use-, eu-,
   u-ey, union) and a silent-h list. Test with the table above. Cost is an hour, and it touches `text.py`.
2. **Replace the irregular paths in `morph.py`** with a vendored LemmInflect table (lemma ↔ VBD, VBN, VBG, VBZ,
   NNS), keeping the consonant-doubling rule as the fallback. Always lemmatise the entry's head before
   inflecting it.
3. **Countability on entries:** `count: mass | count | plural_only`. *Yakka* and *tucker* are mass, *thongs*
   and *heaps* plural-only, *a sickie* count. `realise.py` repairs the determiner and the verb agreement after a
   swap ("a task" → "a bit of yakka", not "a yakka"; "heaps is" → "heaps are"). Multi-VALUE ships a list of
   1,495 mass nouns (Apache-2.0) to seed source-side countability.
4. **Fluency in the tuning loop.** Run a pinned local LanguageTool (en-AU) over the original and the
   translation, and count only the *new* matches near substituted spans. Dev-only, behind a script, never a
   package import.

Sources:
- https://github.com/bjascob/LemmInflect
- https://pypi.org/project/lemminflect/
- https://pypi.org/project/pyinflect/
- https://pypi.org/project/inflect/
- https://pypi.org/project/language-tool-python/
- https://github.com/languagetool-org/languagetool
- https://lhncbc.nlm.nih.gov/LSG/Projects/lexicon/current/web/index.html

---

## 8. Evaluation for style transfer and dialect translation

**What the literature recommends:**
- **Mir et al. (2019)** evaluate style transfer on three axes: style intensity (a direction-corrected Earth
  Mover's Distance over a style classifier's outputs), content preservation (Word Mover's Distance on
  *style-masked* texts) and naturalness (adversarial classifiers).
- **Briakou et al. (2021)** compared metrics against human judgments for formality transfer in four
  languages. They recommend:
  - **chrF** for meaning preservation (over BLEU, which correlates poorly);
  - **regression** models over binary classifiers for style strength;
  - pseudo-likelihood from XLM-R for fluency, which is the heavy one.

| Metric | Library | Version | Licence | Cost | Determinism | Verdict for the tuning loop |
|---|---|---|---|---|---|---|
| chrF / chrF++ | sacrebleu | 2.6.0 | Apache-2.0 | ms per document, pure Python | Deterministic, with a signature string | **Adopt (dev extra)**, computed on style-masked text (mask the dictionary's spans in both texts, after Mir et al.) |
| BERTScore | bert-score | 0.3.13 (2023) | MIT | roberta-large (1.4 GB) plus torch | Deterministic on CPU if pinned | Too heavy for thousands of runs. **Write a "static BERTScore" instead:** greedy cosine alignment using the bundled vectors |
| Perplexity or pseudo-likelihood (GPT-2, XLM-R) | transformers | n/a | various | GPU-ish | Deterministic on CPU, slow | No, for the inner loop. Spot-check a held-out set at most |
| n-gram LM join score | KenLM (LGPL-2.1, C++ build) or a pure-Python trigram LM | n/a | n/a | ms | Deterministic | **Try:** score only the ±3-token windows around each substitution against the same window in the original. This catches broken joins (W4) cheaply. Train on the yarn outputs and public-domain Australian prose |
| Style strength | own | n/a | n/a | ms | Deterministic | Slang density per 100 words (already countable), with a level target band, plus a regression on static vectors (yarn against originals). **Goodhart warning:** without the band it rewards stacking |
| Garnish and genre violations | own (`verify.py`) | n/a | n/a | ms | Deterministic | **Adopt:** count garnish a genre doesn't allow (§4 table) and gated swears (§5) |
| LLM judge | `judge.py` | n/a | n/a | $ | Non-deterministic | Keep as the outer gate on a fixed held-out set, not every iteration |

**Calibration data you already have.** 177 judged candidates: 59 texts, each with engine, yarn and unharnessed
versions, scored on eight criteria (`texts/*/verdict.json`). Before trusting any cheap metric, compute Kendall's
τ between each metric and the judge's corresponding criterion, per text across the three candidates and pooled:
- masked chrF against *meaning*;
- the join score and the LanguageTool delta against *flow*;
- slang density in band against *authenticity* and *register*;
- violations against *tone* and *register*.

Keep a metric only if τ is clearly positive. The three candidates differ so much that the correlation will be
inflated, so also check it within the engine's own seed variants.

**What to adopt, ranked:**
1. Style-masked chrF, static BERTScore, slang-density band and genre violations, all added to `verify.py`
   metrics. sacrebleu is a dev extra.
2. The swap-level precision on aussiefy-LS (§6), the most direct measure of W1.
3. The join score from a small n-gram LM, in `scripts/`.
4. A `scripts/tune.py` that runs a seeded random search over the `profiles.yaml` weights and the §4 budget
   table, optimising the calibrated composite on a training split and reporting on a held-out split. It ends
   with one judge pass over the held-out split.

Sources:
- https://aclanthology.org/N19-1049.pdf
- https://aclanthology.org/2021.emnlp-main.100.pdf
- https://pypi.org/project/sacrebleu/
- https://pypi.org/project/bert-score/
- https://arxiv.org/abs/1904.09675
- https://pypi.org/project/kenlm/
- https://github.com/kpu/kenlm

---

## 9. Australian English resources

| Resource | What it gives | Licence or access | Verdict |
|---|---|---|---|
| Wiktionary, Category:Australian English | 3,734 pages, plus 17 subcategories (Australian Aboriginal English 55, Australian slang 10, rhyming slang, state categories). Most slang is marked by sense-level labels (*Australia*, *slang*, *colloquial*, *vulgar*, *derogatory*, *dated*), not by category | CC BY-SA 4.0 plus GFDL | **Best open source for terms, register and region labels.** Extract with Wiktextract (kaikki.org JSON) and filter on sense tags. Glosses are share-alike, so keep writing glosses in your own words (current policy); terms and labels are facts |
| Wiktextract / kaikki.org | Machine-readable Wiktionary, with sense tags and examples | follows Wiktionary's licence | Use offline in a `research/` round |
| eWAVE (and Multi-VALUE's `ewave.csv` and attestation vectors) | Grammar features of Australian English, Australian Vernacular English and Aboriginal English, with pervasiveness | CC BY 3.0 (eWAVE); Apache-2.0 (Multi-VALUE code) | **Use** for §6's grammar rules |
| Macquarie Dictionary and Australian Word Map | Authoritative meanings, regions, currency | Copyright, subscription | Reference-only by hand, as `source_policy.yaml` already says |
| Australian National Dictionary (ANDC and OUP; online at australianwords.au) | Historical citations: is a word dated or current? | Copyright; free to read | Reference-only; cite pages in `sources` |
| ANDC *Ozwords*, Word of the Month | Usage notes on new and old words | ANU copyright | Reference-only |
| COOEE (Corpus of Oz Early English, 1788-1900, four registers) | Historical Australian text | **Conflicting statements:** LDaCA lists CC BY 4.0, while Alveo and CoRD say rights are reserved or academic use only | Verify on the LDaCA record before any use; only for `register: dated` decisions |
| Australian Corpus of English (ACE, 1986 written) | Australian written-register frequencies | AusNC Terms of Use: per session, a limited licence, research and study | Internal frequency checks only; don't commit derived text |
| ICE-Australia | Spoken and written Australian English, 1990s | Restricted licence | Low priority |
| AusTalk (about 3,000 hours of audio-visual speech, via Alveo or LDaCA) | Mostly read and task speech; the transcripts aren't vernacular-rich | Per-collection licence agreement | **Skip:** audio-centric, little slang |
| Federal Hansard | Parliamentary register, interjections | CC BY-NC-ND 3.0 AU (2010 decision; verify the current notice) | Low value; NoDerivs rules out redistributing derived texts |
| Trove (NLA) digitised newspapers | Attestations for dated slang; much of it pre-1955 public domain | API key; per-item rights | Use by hand for attestation, not bulk |
| Australian Government Style Manual | Australian spelling, dates and numbers for lint and the spelling pass | Commonwealth copyright; government material is usually CC BY 4.0 (not confirmed for the Style Manual) | Reference for `americanisms.yaml` and date rules |
| Geoscience Australia place names | Protecting place names (§3) | CC BY 4.0 (check) | Try a filtered list |
| Slang listicles (tourism sites, blogs) | Candidate terms | Copyright (descriptions); terms are facts | As now: scrape politely, flag, rewrite glosses |

**A note on Aboriginal English.** eWAVE and Wiktionary both cover it. Its features aren't slang and shouldn't
become comic garnish or "drawl". Keep them out of the engine, or behind an explicit, separately reviewed region
flag.

Sources:
- https://en.wiktionary.org/wiki/Category:Australian_English
- https://kaikki.org/dictionary/English/index.html
- https://aclanthology.org/2022.lrec-1.140.pdf
- https://ewave-atlas.org/
- https://australianwords.au/
- https://slll.cass.anu.edu.au/centres/andc/australian-national-dictionary
- https://ldaca.edu.au/resources/ldaca-resources/licenses
- https://bridges.monash.edu/articles/dataset/Corpus_of_Oz_Early_English_COOEE_/23961609
- https://varieng.helsinki.fi/CoRD/corpora/COOEE/
- https://app.alveo.edu.au/catalog/cooee
- https://docs.ldaca.edu.au/licenses/ace/all/v1/
- https://alveo.edu.au/tutorials/accessing-austalk-in-alveo
- https://researchers.mq.edu.au/en/publications/austalk-an-audio-visual-corpus-of-australian-english/
- https://lists.ibiblio.org/sympa/arc/cc-au/2010-06/msg00002.html
- https://trove.nla.gov.au/
- https://www.stylemanual.gov.au/

---

## Top 8 improvements, prioritised

The order is by expected value for cost. Effort: S is under a day, M two to four days, L a week or more.

| # | Improvement | Fixes | Expected impact | Effort | Dependency added | Modules |
|---|---|---|---|---|---|---|
| 1 | **Register profile and genre budget table.** Rule-based genre (instructions, safety, news, legal, technical, narrative, dialogue, letter, obituary, FAQ), formality (F-score) and gravity; `profiles.yaml` gets per-genre multipliers for swaps, garnish placements, riffs, closers and swears | W3, W5 | Removes pub openers on safety notices, closers on press releases and tag-ons in news. Should lift the judge's *register* and *tone* most on the instructions, workplace and news groups | M | None (stdlib; better with #3's tags) | `context.py`, `garnish.py`, `select.py`, `profiles.yaml`, `explain.py` |
| 2 | **Swearing function, stance and target gating.** Entries tagged after McEnery's scheme; no contemptuous or insult swears on generic, quantified, victim, child or deceased referents; genre caps from #1 | W3 | Eliminates the findings' "some mongrel struck by lightning", "every bastard" and "little buggers" class of errors outright | S-M (curating about 150 entries) | None | `schema.py`, `loader.py`, `entries/swearing.yaml`, `select.py`, `lint.py` |
| 3 | **Vendored averaged-perceptron POS tagger** with POS constraints in patterns and a noun-noun modifier veto | W1, W4 | Would have stopped about a third of the findings' wrong swaps (6 of 19 tested: *taste*, *figure*, *relative*, *zero*, *live*, *Nations*), and the "food colouring" and "dollar bill" family. Prerequisite for #4, #5 and the F-score | M | None at run time: NLTK's MIT weights (5.7 MB JSON; trim or quantise) and about 100 lines of inference. Optional `[parse]` extra with spaCy 3.8 small later | new `pos.py`, `text.py`, `matcher.py`, `detect.py` |
| 4 | **Plain-text protection of names and terms.** `markup.py`'s identifier masks in text mode, plus acronyms, units and recurring noun compounds (C-value lite); one sense per discourse once a technical register is detected | W1 | Stops swaps inside technical terms ("struct fields" → paddocks, "zero ciphertext") and multiword names beyond the capital-next-to-capital rule | S-M | Optional: a 600 KB frequency list derived from wordfreq (CC BY-SA 4.0; settle the repo licence first) | `markup.py`, `detect.py`, `engine.py` |
| 5 | **Sense scoring:** selectional preferences (`subj:` and `obj:` supersense constraints from a precomputed WordNet table), exemplar-centroid and BalAdd context scores from the bundled static model, Yarowsky-style decision lists replacing `!exclusions` | W1 | The main lever on *sense* (2.20): addresses the two thirds of wrong swaps that POS can't, such as *knock together* on software, person predicates on tanks, and *yakka* for countable tasks | M-L | A supersense table built offline from OEWN 2025 (CC BY 4.0) with `wn`; no run-time dependency | `schema.py`, `loader.py`, `detect.py`, `select.py`, `concepts.yaml`, `scripts/` |
| 6 | **A cheap, calibrated metric suite and labelled swap set.** "aussiefy-LS" from the 59 texts' swaps and 284 judge problems; style-masked chrF, static BERTScore, slang-density band, genre violations and an n-gram join score, each kept only if Kendall's τ against the 177 judged candidates is positive; a seeded tuning script | All, indirectly | Makes #1-#5 tunable without paying for judges each iteration, and turns the everyday pass into a regression suite | M | sacrebleu 2.6.0 (Apache-2.0) as a dev extra | `verify.py`, `scripts/tune.py`, `tests/` |
| 7 | **Coverage round from Wiktionary (Wiktextract) senses tagged Australia and slang, plus eWAVE grammar features** (*me* for *my*, *yous*, *them* for *those*, flat adverbs, *she'll be right*, clause-final *but*, *never* as past negator) as level-4/5 rules; harvest ranked by salience | W2 | Raises the share of sentences touched (34% untouched now) and *authenticity* and *variety* (1.34 and 1.56). Grammar features add Aussie colour to sentences with no slang concept at all | M-L (mostly curation) | None at run time; CC BY-SA and CC BY 3.0 attribution for the research round's sources | `research/` round, `entries/*.yaml`, `phonetic.yaml`, `realise.py`, `scrape/harvest` |
| 8 | **Grammar repair:** a/an letter-name rules (6 of 14 probe cases wrong today: "an ute", "a NSW bloke", "a RSL"), vendored LemmInflect irregular tables with lemmatise-before-inflect, `count:` mass or plural on entries, and determiner and agreement repair | W4 | Fixes visible errors on every level; small but certain gains in *flow* | S-M | None (vendored MIT tables; inflect 7.5.0 optional) | `text.py`, `morph.py`, `realise.py`, `schema.py` |

**What not to do:**
- No Stanza, Flair, GLiNER, Detoxify or BERTScore at run time. Each brings torch, hundreds of MB to GBs, and
  version-sensitive outputs, for gains a seeded rule engine can't use well.
- No NRC lexicons or `language_tool_python` imported in the package (licences).
- No textstat (it downloads data on first use).
- No WordNet synset-level WSD (it barely beats the first-sense baseline, and aussiefy needs entry-level sense
  decisions, not synsets).
