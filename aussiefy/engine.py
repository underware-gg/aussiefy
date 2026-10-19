"""The pipeline: parse -> detect -> select -> realise -> garnish."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field, fields
from functools import lru_cache, partial
from typing import Any, Callable, Literal, Protocol, Sequence

from . import pos
from .context import FORMAL_RE, is_chant, sentence_contexts, text_mood
from .detect import (CODE_CONCEPTS, DETERMINERS, Detection, after_determiner, detect, fallback_scorer,
                     resolve_overlaps, owned_degree_modifiers, degree_modifier_spans)
from .embed import Embedder, make_embedder
from .garnish import (Edit, GarnishOffer, GarnishRecord, PhoneticRecord, PhoneticTrace, apply_phonetic, ends_in_list,
                      garnish_offer, pick_riff, place_garnish, tag_in_speech)
from .loader import load_dictionary
from .imagery import image_offers
from .dialect import text_english
from .genre import resolve_document, Embellishment, Genre, form_removes
from .protected import Masked, protected_runs
from .model import Dictionary
from .policy import Effective, Policy, envelope, pick_form, resolve, roll
from .realise import ARTICLES, fit_article, number_problem, phrase_continues, realise, replacement_span
from .select import Candidate, candidates, semantic_rejection, usable_forms, weighted_pick
from .schema import Entry, SchemaError
from .terms import form_key
from .text import (COMMON_STARTERS, DATELINE, MID_SENTENCE_NAME, OPEN_QUOTES, QUOTES, SCRIPT_LINE, Token, capital_is_positional, fix_articles, heading_lines, match_case,
                   document_spans, mentioned_spans, held_spans, sentences, tokenize)


UNTOUCHED_MIN_WORDS = 5


@dataclass
class SubstitutionRecord:
    span: tuple[int, int]
    text: str
    det: Detection
    sentence: int = 0               # index of the sentence it's in
    decision: str = ""
    p: float = 0.0
    roll: float | None = None
    chosen: Candidate | None = None
    output: str | None = None
    out_span: tuple[int, int] | None = None
    stacked: Candidate | None = None
    riff: str | None = None
    term: str | None = None         # the output without its riff: the Aussie phrase itself
    eligible: list[Candidate] = field(default_factory=list)
    rejected: list[tuple[str, str]] = field(default_factory=list)

    @property
    def substituted(self) -> bool:
        return self.output is not None

    def to_dict(self) -> dict[str, Any]:
        total = sum(c.weight for c in self.eligible) or 1.0
        d = self.det
        return {
            "kind": "substitution",
            "span": list(self.span),
            "text": self.text,
            "concepts": list(d.concepts),
            "frame": d.frame,
            "detected_by": d.method,
            "pattern": d.pattern,
            "score": d.score,
            "intensity": d.intensity,
            **({'semantic_degree': dict(d.semantic_degree), 'degree_qualifier': list(d.degree_qualifier),
                'degree_conflicts': sorted(d.degree_conflicts)} if d.semantic_degree or d.degree_conflicts else {}),
            "captures": d.describe_captures(),
            "decision": self.decision,
            "p_substitute": round(self.p, 3),
            "roll": None if self.roll is None else round(self.roll, 4),
            "chosen": None if not self.chosen else {
                "entry": self.chosen.entry.id, "form": self.chosen.entry.form, "why": self.chosen.why,
                "probability": round(self.chosen.weight / total, 3)},
            "stacked": None if not self.stacked else {"entry": self.stacked.entry.id, "why": self.stacked.why},
            "output": self.output,
            "term": self.term,
            "replaced_span": list(self.out_span) if self.out_span else None,
            "candidates": [{"entry": c.entry.id, "probability": round(c.weight / total, 3)} for c in self.eligible],
            "rejected": [{"entry": i, "reason": r} for i, r in self.rejected],
        }


@dataclass
class DifficultSentence:
    """A sentence the dictionary couldn't carry (formal words it left alone): best rewritten whole."""
    sentence: int
    original: str
    draft: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"sentence": self.sentence, "original": self.original, "draft": self.draft, "reason": self.reason}


@dataclass
class RewriteRecord:
    """A whole sentence handed to the LLM rewriter because the dictionary couldn't carry it."""
    sentence: int
    original: str
    draft: str
    output: str | None
    reason: str
    status: str
    model: str

    @property
    def outcome(self) -> str:
        return "applied" if self.output else "fell_back"

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "rewrite", "outcome": self.outcome, "sentence": self.sentence, "original": self.original, "draft": self.draft,
                "output": self.output, "reason": self.reason, "status": self.status, "model": self.model}


@dataclass(frozen=True)
class DialectRecord:
    """An American or British word swapped for the Australian (faucet -> tap)."""
    english: str                  # us, uk or both: the English that uses the word
    before: str
    after: str
    span: tuple[int, int]         # in the source
    sentence: int

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "dialect", "english": self.english, "before": self.before, "after": self.after,
                "span": list(self.span), "sentence": self.sentence}


@dataclass
class Result:
    text: str
    source: str
    level: int
    seed: int
    records: list[SubstitutionRecord]
    garnish: list[GarnishRecord]
    phonetic: list[PhoneticRecord]
    warnings: list[str]
    deterministic_text: str = ""
    surface: dict[str, Any] | None = None
    rewrites: list[RewriteRecord] = field(default_factory=list)
    difficult: list[DifficultSentence] = field(default_factory=list)
    vulgarity: int = 0                                             # the strongest language allowed
    mood: str = "light"                                            # context.text_mood: solemn, dark or light
    genre: Genre | None = None   # genre.text_genre: its form and defaults
    sentences: list[tuple[int, int]] = field(default_factory=list)  # each sentence's span in the source
    dialect: list[DialectRecord] = field(default_factory=list)      # US/UK words swapped for the Australian
    english: str | None = None                                     # the source's English, where known
    embellishment: Embellishment | None = None   # the garnish it took

    variety: int = 0
    profile_config: dict[str, Any] = field(default_factory=dict)
    imagery: list[dict] = field(default_factory=list)

    def envelope(self) -> dict[str, Any]:
        return {**envelope(self.level, self.vulgarity, self.warnings), "profile_config": self.profile_config}

    def sentence_text(self, i: int) -> str:
        return self.source[slice(*self.sentences[i])]

    @property
    def untouched(self) -> list[int]:
        """Sentences of UNTOUCHED_MIN_WORDS or more that nothing was swapped in: where a writer adds most."""
        touched = {r.sentence for r in self.records if r.substituted}
        return [i for i, span in enumerate(self.sentences)
                if i not in touched and sum(t.is_word for t in tokenize(self.sentence_text(i))) >= UNTOUCHED_MIN_WORDS]

    def decisions(self) -> dict[str, Any]:
        """What the engine decided, independent of surface wording (fed to the LLM surface mode)."""
        return {
            "substitutions": [
                {"span": list(r.out_span or r.span), "original": self.source[slice(*(r.out_span or r.span))],
                 "replacement": r.output, "entry": r.chosen.entry.id,
                 "stacked": r.stacked.entry.id if r.stacked else None, "riff": r.riff}
                for r in self.records if r.substituted],
            "garnish": [{"placement": g.placement, "sentence": g.sentence, "entry": g.entry_id, "text": g.text,
                         **({"image_id": g.image_id} if g.image_id else {})}
                        for g in self.garnish if g.text],
            "phonetic": [{"rule": p.rule, "before": p.before, "after": p.after} for p in self.phonetic],
            "dialect": [{"before": d.before, "after": d.after, "english": d.english} for d in self.dialect],
            "rewrites": [{"sentence": w.sentence, "output": w.output} for w in self.rewrites if w.output],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "level": self.level,
            "seed": self.seed,
            **self.envelope(),
            "variety": self.variety,
            "mood": self.mood,
            **self.genre.envelope(self.embellishment.step),
            "embellishment": self.embellishment.step, "embellishment_name": self.embellishment.name,
            "decisions": self.decisions(),
            "explain": [r.to_dict() for r in self.records] + [w.to_dict() for w in self.rewrites]
                       + [g.to_dict() for g in self.garnish] + [p.to_dict() for p in self.phonetic]
                       + [d.to_dict() for d in self.dialect],
            "difficult_sentences": [d.to_dict() for d in self.difficult],
            "warnings": self.warnings,
            **({"deterministic_text": self.deterministic_text, "surface": self.surface} if self.surface else {}),
        }


class Translator:
    def __init__(self, dictionary: Dictionary | None = None, *, lookup_embedder: str | Embedder | None = "configured"):
        """lookup_embedder is the meaning model lookup and gaps use: "configured" (resolved once, on first use,
        from this machine's `aussiefy embedder` settings: an installed model, else the bundled one), "bundled",
        "local", an Embedder, or None for n-grams only."""
        if lookup_embedder == "ngram":
            raise ValueError("lookup_embedder is a meaning model; None means n-grams only")
        self.dictionary = dictionary or load_dictionary()
        self._lookup_embedder = lookup_embedder
        self._embedders: dict[str | None, Embedder | None] = {}
        self._scorers: dict[str | None, Callable[[str], dict[int, float]] | None] = {}
        missing = sorted(CODE_CONCEPTS - set(self.dictionary.concepts))
        if missing:   # the grammar rules name these; a dictionary without them can't be translated with
            raise SchemaError(f"concepts the grammar rules (detect.py) name are missing: {', '.join(missing)}")

    def policy(self, **kwargs) -> Policy:
        """A Policy over the dictionary's defaults; kwargs are Policy fields, and None means "the default"."""
        return Policy.from_mapping(self.dictionary.policy_defaults, **kwargs)

    def effective(self, *, level: int | str = 5, vulgarity: int | str | None = None, **policy) -> Effective:
        """The level and vulgarity as the engine will apply them (numbers; names resolved)."""
        return resolve(self.policy(level=level, vulgarity=vulgarity, **policy), self.dictionary)

    @property
    def lookup_embedder(self) -> Embedder | None:
        spec = self._lookup_embedder
        return self._embedder(spec) if isinstance(spec, str) else spec

    def _fallback_scorer(self, spec: str | None) -> Callable[[str], dict[int, float]] | None:
        """The similarity fallback's scorer over the fallback patterns, built once per embedder."""
        if spec not in self._scorers:
            emb = self._embedder(spec)
            self._scorers[spec] = emb and fallback_scorer(emb, self.dictionary.fallback_patterns)
        return self._scorers[spec]

    def _embedder(self, spec: str | None) -> Embedder | None:
        if spec not in self._embedders:
            self._embedders[spec] = make_embedder(spec)
        return self._embedders[spec]

    def translate(self, text: str, *, level: int | str = 5, seed: int = 0, vulgarity: int | str | None = None,
                  variety: int = 0, registers: Sequence[str] | None = None, english: str | None = None,
                  regions: Sequence[str] | None = None, unlock: Sequence[str] | None = None,
                  embedder: str | None = None, rewriter: Rewriter | None = None,
                  rewrite_mode: Literal["hard", "all"] = "hard",
                  embellishment: int | str | None = None,
                  document_type: str = "general", document_config: dict | None = None,
                  _protected: Masked | None = None, _context: tuple | None = None,
                  _composition: DocumentPart | None = None, _observer: PassObserver | None = None) -> Result:
        """Translate text: the same text, policy and seed always give the same Result.

        level (1-5 or tourist .. swaggie) is how Aussie; vulgarity (0-3 or nan, dad, uncle-bob, tradie; None = the
        level's own) is how vulgar, and wins over the level's in either direction. embellishment (0-2 or deadset,
        dinkum, troppo; None = the selected document type's default) is how much garnish the telling takes. variety N
        picks among the N best-fitting terms (0 weighs every eligible one). registers (current, dated,
        archaic), regions ("qld") and unlock (flags whose gated entries become eligible) narrow or widen what
        the level allows. english (us, uk, auto, none; None = profiles.yaml's) is the English the text is in,
        for the dialect swaps (faucet -> tap, at every level): auto reads American spelling; none turns them
        off. embedder picks the similarity fallback ("ngram", "bundled", "local", "none"; None =
        profiles.yaml's). rewriter (e.g. aussiefy.llm.ClaudeRewriter) rewrites whole sentences the dictionary
        can't carry: the difficult ones (rewrite_mode="hard", thresholds in profiles.yaml `rewrite:`) or every
        one ("all"). Document adapters supply opaque protected spans and whole-text context through the
        internal composition parameters; format selection belongs to the public translation route. _observer
        watches the pass (the changes builder) without changing it."""
        pol = self.policy(level=level, seed=seed, vulgarity=vulgarity,
                          variety=variety, registers=registers, regions=regions, unlock=unlock, embedder=embedder,
                          english=english, embellishment=embellishment,
                          document_type=document_type, document_config=document_config)
        masked = _protected if _protected is not None else Masked(text, text)
        source, text = text, masked.text      # the engine reads the masked text: the same length, same offsets
        tokens = tokenize(text)
        sents = sentences(tokens)
        genre = _context[0] if _context is not None else resolve_document(masked.prose(), masked.source, config=self.dictionary.genres,
                        document_type=pol.document_type, document_config=pol.document_config)
        mood = _composition.mood if _composition is not None and _composition.mood is not None else text_mood(text)
        run = _Run(text, pol, resolve(pol, self.dictionary), mood, is_chant(sents), masked, genre,
                   _context[1] if _context is not None else text_english(pol.english, masked.prose(), self.dictionary.us_spellings),
                   genre.setting(pol.embellishment), composition=_composition, observer=_observer)
        if _composition is not None:
            run.state = _composition.state
        if _observer is not None:
            _observer.begin(run)
        pieces: list[str] = [text[: tokens[0].start] if tokens else text]
        at = len(pieces[0])   # where the next sentence starts in the joined text
        for i, tokens_i in enumerate(sents):
            sent = run.sentence(i, tokens_i, sents)
            recs, splices = self._substitute(sent, run)
            run.records.extend(recs)
            out = _splice(sent, splices)
            hard = self._difficulty(sent.tokens, recs, run.eff)
            if hard:
                run.difficult.append(DifficultSentence(i, masked.restore(sent.text, whole=False),
                                                       masked.restore(out, whole=False), hard))
            if rewriter is not None:
                out = self._rewrite(sent, out, recs, run, rewriter, hard if rewrite_mode == "hard" else
                                    ("rewrite mode: all" if run.eff.level >= run.eff.profile.rewrite.min_level
                                     else None))
            garnished = self._garnish_sentence(out, sent, recs, run)
            if _observer is not None:
                _observer.sentence(SentenceTrace(sent, recs, splices, out, garnished, at))
                at += len(garnished) + sent.next_start - sent.end
            pieces += [garnished, text[sent.end:sent.next_start]]
        # the closer answers the last sentence, so it goes there, not after a code block that follows it
        body, trail = "".join(pieces[:-1]), pieces[-1]
        joined = (self._closer(body, sents, run) + trail) if any(t.is_word for t in tokens) else "".join(pieces)
        keep = partial(_no_drawl, keep_quotes=run.genre.policy.keep_quotes, protected=masked.no_phonetic)
        preserve = partial(document_spans, keep_quotes=run.genre.policy.keep_quotes,
                           datelines=run.genre.policy.dateline_context)
        if owned_degree_modifiers(tokens, self.dictionary.degree_index.find(tokens)):
            document_preserve = preserve
            preserve = lambda current: document_preserve(current) + degree_modifier_spans(current, self.dictionary.degree_index)
        trace = PhoneticTrace(keep, preserve) if _observer is not None else None
        final, phon = apply_phonetic(joined, self.dictionary.phonetic, run.eff, pol.seed,
                                     infixes=run.embellishment.takes("infix"), keep=keep, preserve=preserve,
                                     trace=trace)
        if _observer is not None:
            _observer.phonetic(joined, trace, final)
        final = masked.restore(final)
        warnings = list(run.eff.warnings)
        if pol.vulgarity is not None and run.eff.vulgarity and not run.embellishment.takes("infix"):
            if form_removes(run.genre, "infix", run.embellishment.step):   # the setting does; the form doesn't
                why = f"the {run.genre.name} form takes"
            else:
                whose = "as set" if pol.embellishment is not None else f"the {run.genre.name} text's own"
                why = f"{run.embellishment.name} ({whose}) takes"
            warnings.append(f"{why} no swear infixes, intensifiers or sweary garnish: vulgarity "
                            f"{run.eff.vulgarity} reaches its word swaps only")
        return Result(final, source, pol.level, pol.seed, run.records, run.garnish, phon, warnings,
                      deterministic_text=final, rewrites=run.rewrites, difficult=run.difficult,
                      vulgarity=run.eff.vulgarity, mood=run.mood, genre=run.genre,
                      sentences=[(s[0].start, s[-1].end) for s in sents], dialect=run.dialect,
                      english=run.english, embellishment=run.embellishment, variety=pol.variety,
                      profile_config=run.eff.envelope()["profile_config"], imagery=run.imagery)

    # -- stages -------------------------------------------------------------------------

    def _term_of_art(self, det: Detection, domains: tuple[str, ...]) -> bool:
        """Whether every concept a span was read as is a term of art in this genre (a browser's cookie, a
        struct's field, a build): then the span stays as it is, and no shorter match takes it either."""
        known = [self.dictionary.concepts[c] for c in det.concepts if c in self.dictionary.concepts]
        return bool(known) and all(set(domains) & c.not_in for c in known)

    def _substitute(self, sent: "_Sentence", run: "_Run") -> tuple[list[SubstitutionRecord], list[tuple[int, int, str]]]:
        """Detect the sentence's concepts and swap in Aussie terms: one record per detected span."""
        pol, eff, state, toks = run.pol, run.eff, run.state, sent.tokens
        dets = resolve_overlaps(detect(toks, self.dictionary.index, self._fallback_scorer(pol.embedder),
                                       self.dictionary.fallback_patterns, pol.similarity_threshold, sent.tags,
                                       self.dictionary.adjective_nouns, concepts=self.dictionary.concepts,
                                       complete=sent.complete, degree_index=self.dictionary.degree_index))
        held = run.held(toks)
        dets = [d for d in dets if not self._term_of_art(d, run.genre.policy.term_domains)
                and not held & set(range(d.start, d.end))]
        if pol.english != "none":
            dets = self._yield_to_dialect(dets, toks, run)
        occupied: set[int] = {i for d in dets for i in range(d.start, d.end)}
        records: list[SubstitutionRecord] = []
        splices: list[tuple[int, int, str]] = []
        replaced: set[int] = set()
        said: dict[int, str] = {}   # the swaps made, by the token each ends before
        for det in dets:
            rec = SubstitutionRecord((toks[det.start].start, toks[det.end - 1].end),
                                     run.text[toks[det.start].start: toks[det.end - 1].end], det, sent.index)
            records.append(rec)
            taken = (occupied - set(range(det.start, det.end))) | replaced
            keep, rejected = self.eligible(det, sent, run, eff, state, taken)
            rec.eligible = keep
            rec.rejected = sorted(((e.id, r) for e, r in rejected), key=lambda x: x[0])
            if not keep:
                rec.decision = "kept original: no eligible entry"
                continue
            rec.p = max(eff.profile.substitution[c.entry.substitution_class] for c in keep)
            rec.roll = roll(pol.seed, "substitute", *sent.key, det.start, det.pattern)
            if rec.roll >= rec.p:
                rec.decision = f"kept original: roll {rec.roll:.3f} >= p {rec.p:g}"
                continue
            choice = weighted_pick(keep, roll(pol.seed, "pick", *sent.key, det.start, det.pattern))
            here = Spot(sent, rec, keep, state, replaced, said, taken, len(splices))
            if run.observer is not None:
                choice = run.observer.choose(sent, det, keep, choice)
                run.observer.spot(here.snapshot())
            rec.chosen = choice
            spot = self.render_at_spot(choice, here, run)
            if spot.echo:
                rec.chosen, rec.decision = None, f"kept original: {spot.echo}"
                continue
            rec.stacked, rec.riff = spot.stacked, spot.riff
            s, e = spot.start, spot.end
            rec.output, rec.term, rec.out_span = spot.text, spot.term, (toks[s].start, toks[e - 1].end)
            rec.decision = f"substituted: roll {rec.roll:.3f} < p {rec.p:g}"
            state.entry_uses[choice.entry.id] += 1
            if spot.form in choice.entry.spelling_group:
                state.spellings.setdefault(choice.entry.id, spot.form)
            replaced |= set(range(s, e))
            said[e] = rec.term
            splices.append((toks[s].start, toks[e - 1].end, spot.text))
        self._contextual_imagery(records, splices, sent, run)
        if pol.english != "none":
            splices += self._dialect(sent, run, replaced | held, said)
        return records, splices

    def eligible(self, det: Detection, sent: "_Sentence", run: "_Run", eff: Effective, state: TextState,
                 taken: set[int], entries: list[Entry] | None = None) -> tuple[list[Candidate], list[tuple[Entry, str]]]:
        """The candidates that can fill a detection under eff, and the rest with why not: the policy and grammar
        (select.candidates), the span (taken: the tokens other swaps hold), the genre, then what the text has
        already said and variety. Selection reads it at each spot; the changes builder reads it again with only
        the vulgarity cap raised, for the options a lock holds back (entries: the idioms naming the detection's
        concepts, where it has them to hand; candidates passes over the rest)."""
        eligible, rejected = candidates(det, self.dictionary.idioms if entries is None else entries, eff, state.entry_uses,
                                        self.dictionary.person_concepts, self.dictionary.person_nouns, mood=run.mood)
        keep = []
        for c in eligible:
            reason = (semantic_rejection(c.entry, narrator_opinion=run.embellishment.narrator_opinion)
                      or _span_rejection(c, det, sent.tokens, sent.tags, taken)
                      or _genre_rejection(c, run, self.dictionary.neutral_person_concepts))
            if reason:
                rejected.append((c.entry, reason))
            else:
                keep.append(c)
        return _narrow(keep, rejected, run.pol.variety, state), rejected

    def render_at_spot(self, choice: Candidate, spot: "Spot", run: "_Run") -> "SpotRendering":
        """A candidate rendered at its spot, as the splice puts it in: a form (and the spelling the text keeps), its
        article fitted, the entry's own replacement span, a stacked second idiom, a riff, and a/an and capitals
        fixed against what comes before. It reads run.pol (the seed), run.eff, run.mood, run.embellishment and
        run.composition, and reads and spends from run.state (the stack and the riff use it); the caller applies
        the rest. translate and the changes builder (on a copy of the state at the spot) both render this way."""
        det, toks, sent = spot.rec.det, spot.sent.tokens, spot.sent
        form = self._form(choice.entry, det, run, sent.key)
        out = fit_article(realise(choice.entry, form, det), choice.entry, det, toks)
        s, e = replacement_span(choice.entry, det, toks)
        echo = _gloss_echo(toks, s, e, out, spot.said)
        if echo:
            return SpotRendering(s, e, "", "", form, echo=echo)
        stacked, out = self._stack(out, choice, spot.keep, det, sent, run)
        riff, riff_suffix = self._riff(choice, det, e, sent, run)
        s, out = _fix_article(out + riff_suffix, toks, s, spot.replaced)
        return SpotRendering(s, e, out, out[:-len(riff_suffix)] if riff_suffix else out, form, stacked, riff)

    def _contextual_imagery(self, records, splices, sent, run):
        if sent.quiet or sent.prefix_only:
            return
        for rec in records:
            offers = image_offers(self.dictionary, rec.det, sent.tokens, run.eff.level, run.eff.vulgarity,
                                  run.embellishment)
            if not offers:
                continue
            run.imagery.append({"term": rec.text, "for": rec.text, "riffs": [o.card() for o in offers]})
            automatic = [o for o in offers if o.image.form == "suffix" and o.association == "direct"
                         and o.image.id not in run.state.imagery_used]
            # A dash, slash or opening bracket can continue a phrase rather than close its clause.
            if rec.det.end < len(sent.tokens) and sent.tokens[rec.det.end].is_punct and sent.tokens[rec.det.end].text not in {".", "!", "?", ",", ";", ":"}:
                automatic = []
            if not automatic or not self._riff_room(rec.det.end, rec.det.frame, rec.det.start, sent, run):
                continue
            offer = pick_riff(automatic, run.mood, roll(run.pol.seed, "imagery-pick", *sent.key, rec.det.start))
            run.state.imagery_used.add(offer.image.id)
            self._note_riff(sent, run)
            end = sent.tokens[rec.det.end - 1].end
            following_and = rec.det.end < len(sent.tokens) and sent.tokens[rec.det.end].norm == "and"
            suffix = ", " + offer.text + ("," if following_and else "")
            for index, (start, stop, text) in enumerate(splices):
                if stop == end:
                    splices[index] = (start, stop, text + suffix)
                    break
            else:
                index = len(splices)
                splices.append((end, end, suffix))
            if run.observer is not None:
                run.observer.imagery(sent.index, offer.image.id, index, suffix)
            run.garnish.append(GarnishRecord("riff", sent.index, None, offer.text,
                                            "contextual imagery: direct meaning match", [], offer.image.id))

    def _yield_to_dialect(self, dets: list[Detection], toks: list[Token], run: "_Run") -> list[Detection]:
        """The detections a longer dialect span holds: "cookie jar" is a biscuit tin, not a bickie jar, and
        "petroleum jelly" keeps its jelly. Equal or longer detections keep their words."""
        claimed = self.dictionary.dialect.spans(toks, run.english, run.genre.policy.term_domains)
        return [d for d in dets if not any(a <= d.start and d.end <= b and b - a > d.end - d.start
                                           for a, b in claimed)]

    def _dialect(self, sent: "_Sentence", run: "_Run", replaced: set[int],
                 said: dict[int, str]) -> list[tuple[int, int, str]]:
        """American and British words the dictionary left alone, swapped for the Australian: every one, at
        every level (plain Australian English, like the spelling), unless a bracketed gloss would echo it."""
        toks, splices = sent.tokens, []
        for f in self.dictionary.dialect.find(toks, run.english, run.genre.policy.term_domains, replaced):
            if _gloss_echo(toks, f.start, f.end, f.text, said):
                continue
            said[f.end] = f.text
            s, out = _fix_article(f.text, toks, f.start, replaced)
            replaced |= set(range(s, f.end))
            span = (toks[s].start, toks[f.end - 1].end)
            run.dialect.append(DialectRecord(f.swap.english, run.text[slice(*span)], out, span, sent.index))
            splices.append((*span, out))
        return splices

    def _stack(self, out: str, choice: Candidate, keep: list[Candidate], det: Detection, sent: "_Sentence",
               run: "_Run") -> tuple[Candidate | None, str]:
        """A second descriptive idiom on a predicate slot ("yer a few snags short of a barbie, mad as a cut snake"):
        the one stacked (or None) and the text with it."""
        uses = run.state.entry_uses
        others = [c for c in keep if c.entry.id != choice.entry.id and c.entry.frame == choice.entry.frame
                  and det.frame == "predicate_adj" and choice.entry.frame in ("predicate_adj", "adj")
                  and not uses.get(c.entry.id) and not det.coordinated
                  and len(c.entry.form.split()) <= STACK_MAX_WORDS and len(choice.entry.form.split()) <= STACK_MAX_WORDS
                  and abs(c.entry.intensity - choice.entry.intensity) <= STACK_INTENSITY_SPREAD]
        if det.degree_qualifier or not others or run.eff.profile.stack <= 0 or roll(run.pol.seed, "stack", *sent.key, det.start) >= run.eff.profile.stack:
            return None, out
        extra = weighted_pick(others, roll(run.pol.seed, "stack-pick", *sent.key, det.start))
        uses[extra.entry.id] += 1
        return extra, out + ", " + realise(extra.entry, self._form(extra.entry, det, run, sent.key + ("stack",)), det)

    def _riff(self, choice: Candidate, det: Detection, end: int, sent: "_Sentence",
              run: "_Run") -> tuple[str | None, str]:
        """The image the term calls up ("wheelie bins, overflowin', with the bin chickens fightin' over the
        scraps"), only where the term ends a clause (or is the first of a pair) so the riff can't split a phrase.
        Returns the riff (or None) and the text to append (or "")."""
        if not run.embellishment.entry_riffs or choice.entry.id in run.state.riffed:
            return None, ""
        toks, state, eff = sent.tokens, run.state, run.eff
        riffs = choice.entry.riffs_within(eff.vulgarity)
        if not riffs or not self._riff_room(end, choice.entry.frame, det.start, sent, run):
            return None, ""
        riff = pick_riff(riffs, run.mood, roll(run.pol.seed, "riff-pick", *sent.key, det.start)).text
        state.riffed.add(choice.entry.id)
        self._note_riff(sent, run)
        before_and = end < len(toks) and toks[end].norm == "and"
        return riff, ", " + riff + ("," if before_and else "")

    def _riff_room(self, end, frame, start, sent, run):
        if sent.quiet or sent.prefix_only or not run.embellishment.takes("riff"):
            return False
        toks, state, eff = sent.tokens, run.state, run.eff
        p = eff.profile.garnish.get("riff", 0)
        ends_clause = end >= len(toks) or toks[end].is_punct and toks[end].text not in ("'", "-")
        before_and = frame == "np" and end < len(toks) and toks[end].norm == "and"
        ordinal = sent.index + (run.composition.first_sentence if run.composition is not None else 0)
        last = state.last_placed.get("riff")
        return (p > 0 and (ends_clause or before_and)
                and len(state.riffed) + len(state.imagery_used) < eff.profile.limit("riff")
                and sent.key not in state.riffed_sentences
                and (last is None or ordinal - last > eff.profile.garnish_gap)
                and roll(run.pol.seed, "riff", *sent.key, start) < p)

    def _note_riff(self, sent, run):
        run.state.riffed_sentences.add(sent.key)
        run.state.last_placed["riff"] = sent.index + (run.composition.first_sentence if run.composition is not None else 0)

    def _rewrite(self, sent: "_Sentence", out: str, recs: list[SubstitutionRecord], run: "_Run", rewriter: Rewriter,
                 reason: str | None) -> str:
        """Hand the whole sentence to the rewriter, if there's a reason to; its output replaces the draft."""
        if not reason:
            return out
        planned = [r.output for r in recs if r.substituted]
        new, status = rewriter.rewrite(sent.text, out, planned, level=run.pol.level,
                                       vulgarity=run.eff.vulgarity, seed=run.pol.seed)
        if new and protected_runs(new) != protected_runs(out):
            new, status = None, "rejected: it changed protected markup (code, a link, a tag)"
        put_back = partial(run.masked.restore, whole=False)
        run.rewrites.append(RewriteRecord(sent.index, put_back(sent.text), put_back(out), new and put_back(new),
                                          reason, status, rewriter.model))
        return new or out

    def _closer(self, joined: str, sents: list[list[Token]], run: "_Run") -> str:
        """One closing exclamation for the whole text, answering its last sentence ("that's my two bob's worth"
        only after an opinion): a sweary one at the vulgarity's rate, or else the level's clean one."""
        if (run.composition is not None and (not run.composition.last or not run.composition.ends_sentence
                                             or run.composition.quiet)):
            return joined
        if (not sents or run.masked.quiet_at(sents[-1][0].start) or run.is_held(sents[-1])
                or not run.embellishment.takes("closer") or run.eff.profile.limit("closer") == 0):
            return joined     # a text that ends in a table has nowhere to say it; a notice has no punchline
        contexts = sentence_contexts(sents[-1])
        for swear, p, key in ((True, run.eff.swearing.closer, "swear-closer"),
                             (False, run.eff.profile.garnish.get("closer", 0), "closer")):
            if p <= 0:
                continue
            r = roll(run.pol.seed, key, run.text.lower())
            if r >= p:
                continue
            offer = garnish_offer("closer", self.dictionary.garnish, run.eff, run.pol.seed,
                                  (key, run.text.lower()), run.state.garnish_uses, contexts=contexts,
                                  mood=run.mood, swear=swear, insults=run.embellishment.takes("insult"),
                                  narrator_opinion=run.embellishment.narrator_opinion)
            entry = offer.pick()
            form = entry and offer.words(entry)
            run.garnish.append(GarnishRecord.rolled("closer", len(sents) - 1, entry, form, r, p, offer.rejected))
            if entry:
                run.state.garnish_uses[entry.id] += 1
                return self._place(joined, offer, entry, form, len(sents) - 1, run)
        return joined

    def _tail(self, out: str, sent: "_Sentence", run: "_Run") -> str:
        """Round off a closing list ("their brains and imagination, the whole bloody works?"): the level's clean
        tail, or else a sweary one at the vulgarity's rate. It sits inside the sentence, so it doesn't count
        against the sentence's garnish budget."""
        if sent.prefix_only or not run.embellishment.takes("tail"):
            return out
        state = run.state
        ordinal = sent.index + (run.composition.first_sentence if run.composition is not None else 0)
        last = state.last_placed.get("tail")
        if last is not None and ordinal - last <= run.eff.profile.garnish_gap:
            return out
        for swear, p in ((False, run.eff.profile.garnish.get("tail", 0)), (True, run.eff.swearing.exclaim)):
            key = ("swear" if swear else "") + "tail"
            if p <= 0 or state.placed["tail"] >= run.eff.profile.limit("tail") or not ends_in_list(out):
                continue
            r = roll(run.pol.seed, "garnish", key, *sent.key)
            if r >= p:
                continue
            offer = garnish_offer("tail", self.dictionary.garnish, run.eff, run.pol.seed,
                                  (key,) + sent.key, state.garnish_uses, sentence_contexts(sent.tokens, sent.tags),
                                  swear=swear, insults=run.embellishment.takes("insult"),
                                  narrator_opinion=run.embellishment.narrator_opinion)
            entry = offer.pick()
            form, rej = entry and offer.words(entry), offer.rejected
            if entry:
                out = self._place(out, offer, entry, form, sent.index, run)
                state.garnish_uses[entry.id] += 1
                state.placed["tail"] += 1
                state.last_placed["tail"] = ordinal
            run.garnish.append(GarnishRecord.rolled("tail", sent.index, entry, form, r, p, rej))
            if entry:
                break
        return out

    @staticmethod
    def _place(out: str, offer: GarnishOffer, entry: Entry, form: str, sentence: int, run: "_Run",
               lowerable: frozenset[str] = frozenset(), first_replaced: bool = False) -> str | None:
        """Put a picked garnish in (None where a connective doesn't fit), and tell the observer where it went and
        what it was picked from."""
        placement = offer.placement
        if run.observer is not None:
            form = run.observer.placing(sentence, placement, entry, form)
            if form is None:
                return out   # a test hook: the garnish is decided and counted, but its words left out
        placed = place_garnish(out, placement, form, lowerable, first_replaced)
        if placed is None:
            return None
        if run.observer is not None:
            run.observer.garnish(sentence, entry, form, placed[1], offer)
        return placed[0]

    @staticmethod
    def _case(out: str, sent: list[Token], s: int) -> str:
        """Copy capitals only where they are positional (sentence start) or shouting (ALL CAPS).

        A capital mid-sentence ("conceived in Liberty") marks the original word, not the slang.
        """
        original = sent[s].text
        if capital_is_positional(sent, s) or (original.isupper() and len(original) > 1):
            return match_case(out, original)
        return out

    def _difficulty(self, sent: list[Token], recs: list[SubstitutionRecord], eff: Effective) -> str | None:
        """Why this sentence is too formal for the dictionary, or None. Thresholds live in profiles.yaml."""
        cfg = eff.profile.rewrite
        if eff.level < cfg.min_level or sum(t.is_word for t in sent) < cfg.min_words:
            return None
        done = {i for r in recs if r.substituted and r.out_span for i, t in enumerate(sent)
                if r.out_span[0] <= t.start < r.out_span[1]}
        coverage = len(done) / len(sent)
        formal = [t.text for i, t in enumerate(sent) if i not in done and t.is_word and not t.text[:1].isupper()
                  and len(t.text) >= cfg.formal_length and FORMAL_RE.search(t.text.lower())]
        if len(formal) >= cfg.min_formal_words or (formal and coverage <= cfg.max_coverage):
            return (f"{len(formal)} formal word(s) the dictionary left alone ({', '.join(formal[:4])}); "
                    f"dictionary covered {coverage:.0%}")
        return None

    def _form(self, e: Entry, det: Detection, run: "_Run", skey: tuple) -> str:
        """One of the entry's forms that fits here, picked; where the pick is a spelling of the form (the entry's
        `spellings`), the spelling this text already used, so it keeps one (bikkie, not bikkie then bickie)."""
        forms = usable_forms(e, det)
        form = pick_form(forms, run.pol.seed, e.id, *skey, det.start)
        first = run.state.spellings.get(e.id)
        return first if first in forms and form in e.spelling_group else form

    def _garnish_sentence(self, out: str, sent: "_Sentence", recs: list[SubstitutionRecord], run: "_Run") -> str:
        """Garnish in two channels: the level's (connectives, asides, openers, tags; clean entries, at the
        level's rates) and the swearing (sweary asides, openers and tags, at the vulgarity's rate, whatever the
        level). A sentence takes at most one of each placement. A table cell or list item takes none."""
        if sent.quiet:
            return out
        toks = sent.tokens
        if sum(t.is_word for t in toks) < 2:
            return out
        g = _GarnishSpot(
            starts_with_interjection=any(r.det.start == 0 and r.det.frame == "interjection" for r in recs),
            first_replaced=first_replaced(recs, toks),
            contexts=(sent.source_contexts if sent.source_contexts is not None else sentence_contexts(toks, sent.tags))
                     | ({"paragraph_end"} if sent.para_end else set()))
        # a tag lands at the sentence's end: when that's narration after a closing quote ('"... get the coffins
        # ready,"--and she left him no peace until he consented'), judge it on that narration, not the speech
        quotes = [i for i, t in enumerate(toks) if t.text in QUOTES]
        g.tag_contexts = g.contexts
        out = self._tail(out, sent, run)
        if quotes and any(t.is_word for t in toks[quotes[-1] + 1:]) and not tag_in_speech(out):
            g.tag_contexts = sentence_contexts(toks[quotes[-1] + 1:]) | ({"paragraph_end"} if sent.para_end else set())
        eff = run.eff
        level_rates = {p: eff.profile.garnish.get(p, 0) for p in ("connective", "aside", "opener", "tag")}
        out = self._garnish_channel(out, sent, run, g, level_rates, eff.profile.garnish_per_sentence, swear=False)
        swear_rates = {p: eff.swearing.exclaim for p in ("aside", "opener", "tag")}
        return self._garnish_channel(out, sent, run, g, swear_rates,
                                     max(0, eff.profile.garnish_per_sentence - len(g.placed)), swear=True)

    def replay_garnish(self, out: str, sent: "_Sentence", run: "_Run", ops: Sequence[tuple[str, str]],
                       first_replaced: bool) -> tuple[str, list[Edit | None]]:
        """A sentence's garnish put back, as decided, into another text for it (the changes builder swaps a term
        and keeps the rest): each (placement, words) in the order the engine placed them, the way it placed them,
        with where each went (None where one no longer fits, such as a tail after a swap ends the closing list).
        first_replaced: the sentence's first word is now a swap that starts in lower case."""
        lowerable: frozenset[str] | None = None
        edits: list[Edit | None] = []
        for placement, form in ops:
            if placement in ("opener", "connective") and lowerable is None:
                lowerable = run.opener_lowerable(sent, self.dictionary)
            placed = place_garnish(out, placement, form, lowerable or frozenset(), first_replaced)
            if placed is not None:
                out = placed[0]
            edits.append(placed and placed[1])
        return out, edits

    def _garnish_channel(self, out: str, sent: "_Sentence", run: "_Run", g: "_GarnishSpot",
                         rates: dict[str, float], budget: int, swear: bool) -> str:
        state, eff = run.state, run.eff
        ordinal = sent.index + (run.composition.first_sentence if run.composition is not None else 0)
        channel = "swear" if swear else ""
        spent = 0
        for placement in rates:
            p = rates[placement]
            if sent.prefix_only and placement not in ("opener", "connective"):
                continue
            if p <= 0 or spent >= budget or placement in g.placed or not run.embellishment.takes(placement):
                continue
            if placement in ("opener", "connective") and (g.starts_with_interjection or "opener" in g.placed
                                                          or "connective" in g.placed
                                                          or ordinal == 0 and placement == "connective"):
                continue
            if placement in ("opener", "connective") and SCRIPT_LINE.match(out):
                continue  # a label starts the line: a play's speaker ("HALE:"), or a "NOTE:" or "PS:"
            if placement == "connective" and out.lstrip()[:1] in OPEN_QUOTES:
                continue  # a story connective belongs to the narrator, not inside someone's speech
            if placement == "aside" and (any(q in out for q in QUOTES) or not (sent.para_end or "question" in g.contexts)):
                continue  # a stanza-end punchline, or the narrator answering their own question; never speech
            if placement != "aside" and (run.chant or placement == "opener" and "fragment" in g.contexts):
                continue  # "Jeez Louise, Nightmare of Moloch!": openers and tag-ons break a chant
            lowerable = frozenset()
            if placement in ("opener", "connective"):
                lowerable = run.opener_lowerable(sent, self.dictionary)
                first = re.search(r"[A-Za-z][A-Za-z'’-]*", out)
                if first is not None:
                    word = first.group()
                    # If ordinary-word/name evidence is inconclusive, leave the sentence's case alone.
                    if (word[0].isupper() and word.lower() not in lowerable and not g.first_replaced
                            and word != "I" and not word.startswith(("I'", "I’"))
                            and not any(c.isupper() for c in word[1:])):
                        continue
            key = channel + placement
            if state.placed[placement] >= eff.profile.limit(placement):
                continue
            last = state.last_placed.get(placement)   # spacing is per placement, across both channels
            if last is not None and ordinal - last <= eff.profile.garnish_gap:
                continue
            r = roll(run.pol.seed, "garnish", key, *sent.key)
            if r >= p:
                continue
            recent = {cid for cid, at in state.connectives.items() if ordinal - at <= CONNECTIVE_REPEAT_GAP}
            offer = garnish_offer(placement, self.dictionary.garnish, eff, run.pol.seed, (key,) + sent.key,
                                  state.garnish_uses, g.tag_contexts if placement == "tag" else g.contexts,
                                  exclude=recent, mood=run.mood, swear=swear,
                                  insults=run.embellishment.takes("insult"),
                                  narrator_opinion=run.embellishment.narrator_opinion)
            entry = offer.pick()
            form, rej = entry and offer.words(entry), offer.rejected
            if entry:
                new = self._place(out, offer, entry, form, sent.index, run, lowerable, g.first_replaced)
                if new is None:   # only a connective can refuse
                    entry, form = None, None
                    rej = rej + [("-", "sentence already opens with a connective or quote")]
                else:
                    out = new
            if entry:
                # connectives are plain storytelling words, so the same one can come back later
                if placement != "connective":
                    state.garnish_uses[entry.id] += 1
                else:
                    state.connectives[entry.id] = ordinal
                state.placed[placement] += 1
                state.last_placed[placement] = ordinal
                g.placed.add(placement)
                spent += 1
            run.garnish.append(GarnishRecord.rolled(placement, sent.index, entry, form, r, p, rej))
        return out


@dataclass
class _GarnishSpot:
    """One sentence, as garnish sees it."""
    starts_with_interjection: bool
    first_replaced: bool
    contexts: set[str]
    tag_contexts: set[str] = field(default_factory=set)
    placed: set[str] = field(default_factory=set)   # placements this sentence already carries, from either channel


STACK_MAX_WORDS = 4            # only short idioms stack: two long ones read as a pile-up
STACK_INTENSITY_SPREAD = 1     # ... and only ones of about the same strength
CONNECTIVE_REPEAT_GAP = 4      # a connective may come back after this many sentences


class Rewriter(Protocol):
    """Says a whole sentence the dictionary can't carry (aussiefy.llm.ClaudeRewriter is one)."""
    model: str

    def rewrite(self, original: str, draft: str, planned: list[str], *, level: int, vulgarity: int,
                seed: int = 0) -> tuple[str | None, str]: ...


@dataclass
class TextState:
    """What one translation has done so far, across its sentences: what repeats and spacing rules read."""
    entry_uses: Counter = field(default_factory=Counter)         # idiom entry id -> times used
    garnish_uses: Counter = field(default_factory=Counter)       # garnish entry id -> times used
    riffed: set[str] = field(default_factory=set)                # entries that have brought a riff
    imagery_used: set[str] = field(default_factory=set)
    riffed_sentences: set[tuple] = field(default_factory=set)    # sentences that carry one
    placed: Counter = field(default_factory=Counter)             # garnish placement -> times placed
    last_placed: dict[str, int] = field(default_factory=dict)    # placement -> sentence it was last placed in
    connectives: dict[str, int] = field(default_factory=dict)    # connective id -> sentence it was last used in
    seen_sentences: Counter = field(default_factory=Counter)     # sentence text -> occurrences so far
    spellings: dict[str, str] = field(default_factory=dict)      # entry id -> the spelling it first took


    def copy(self) -> "TextState":
        """A copy to spend from without touching this one (each field's container copied)."""
        return TextState(**{f.name: type(v)(v) for f in fields(self) for v in [getattr(self, f.name)]})


@dataclass(frozen=True)
class SpotRendering:
    """A candidate as render_at_spot puts it in: its token span (after taking in an "a"/"an" before it), its text
    with any riff, the term without the riff, the form picked, the idiom stacked after it and the riff it brought;
    or, with echo, why it can't go in (a bracketed gloss would repeat it)."""
    start: int
    end: int
    text: str
    term: str
    form: str
    stacked: Candidate | None = None
    riff: str | None = None
    echo: str | None = None


@dataclass
class Spot:
    """A detection the engine is about to fill, just before the pick is rendered: the eligible candidates, the state
    and the swaps the sentence has so far (replaced tokens, and what was said before each), the tokens other swaps
    hold (taken), and the index its splice will take in the sentence's splices. render_at_spot reads it; an
    observer gets a snapshot, whose candidates, state, replaced and said, and taken are copies the rest of the pass
    leaves as they were. Its sentence (sent) and record (rec) are shared, and carry the pick's outcome."""
    sent: "_Sentence"
    rec: SubstitutionRecord
    keep: list[Candidate]
    state: TextState
    replaced: set[int]
    said: dict[int, str]
    taken: set[int]
    splice: int

    def snapshot(self) -> "Spot":
        return Spot(self.sent, self.rec, list(self.keep), self.state.copy(), set(self.replaced), dict(self.said),
                    set(self.taken), self.splice)


@dataclass
class SentenceTrace:
    """One sentence once it is spliced and garnished: start is where it begins in the joined text."""
    sent: "_Sentence"
    records: list[SubstitutionRecord]
    splices: list[tuple[int, int, str]]
    spliced: str
    garnished: str
    start: int


class PassObserver:
    """Watches one translate pass (the changes builder does). Every hook does nothing by default, and none may
    change the output, except choose and placing, which exist for tests: a test pins a pick, or another
    garnish's words (None leaves them out), to check what the builder renders against a whole re-render."""

    def begin(self, run: "_Run") -> None:
        pass

    def choose(self, sent: "_Sentence", det: Detection, keep: list[Candidate], choice: Candidate) -> Candidate:
        return choice

    def placing(self, sentence: int, placement: str, entry: Entry, form: str) -> str | None:
        return form

    def spot(self, spot: Spot) -> None:
        pass

    def imagery(self, sentence: int, image_id: str, splice: int, suffix: str) -> None:
        pass

    def garnish(self, sentence: int, entry: Entry, form: str, edit: Edit, offer: GarnishOffer) -> None:
        pass

    def sentence(self, trace: SentenceTrace) -> None:
        pass

    def phonetic(self, joined: str, trace: PhoneticTrace, final: str) -> None:
        pass


@dataclass(frozen=True)
class DocumentPart:
    """A source-preserving adapter's unit: shared document choices, with local result offsets."""
    state: TextState
    first_sentence: int
    starts_sentence: bool
    ends_sentence: bool
    last: bool
    quiet: bool = False
    last_contexts: frozenset[str] = frozenset()
    written: frozenset[str] | None = None
    mood: str | None = None


@dataclass
class _Sentence:
    index: int
    tokens: list[Token]
    text: str
    key: tuple             # (lower-cased text, occurrence): what its rolls are keyed by, so a repeat rolls anew
    next_start: int        # where the next sentence starts (the source between them is kept as it is)
    para_end: bool         # the end of a stanza in a chant (not the last one: that's where the closer goes)
    quiet: bool = False    # a table cell, list item, heading, dateline or held quote: words may be swapped (not
                           # a held quote's), no garnish or riff
    tags: list[str] = field(default_factory=list)   # each token's part of speech (pos.tag), tagged once
    prefix_only: bool = False
    source_contexts: frozenset[str] | None = None
    complete: bool = True

    @property
    def end(self) -> int:
        return self.tokens[-1].end

    def lowerable(self, plain: frozenset[str], commands: frozenset[str] = frozenset(),
                  written: frozenset[str] = frozenset()) -> frozenset[str]:
        """The words safe to lower-case after an opener: the text's plain words, with this sentence's first word
        added where it's an ordinary word or a command ("Well, residents said", "Well, pour the batter") and taken
        out where it reads as a name ("Well, Smith said", "Crikey, Cook sailed in") or starts a run of capitals
        ("New South Wales")."""
        first = self.tokens[0].norm
        if self._starts_capitals():
            return plain - {first}
        command = self._is_command(commands)
        if self._ordinary_first() or command:
            return plain | {first}
        if self._reads_as_name(written) and not command:
            return plain - {first}
        return plain

    def _starts_capitals(self) -> bool:
        """The first word opens a run of capitals ("New South Wales", "Constable Harris"); "The Geebung boys"
        still lowers its "The"."""
        nxt = self.tokens[1] if len(self.tokens) > 1 else None
        return nxt is not None and nxt.text[:1].isupper() and nxt.text != "I" and self.tokens[0].norm not in DETERMINERS

    def _ordinary_first(self) -> bool:
        """Not tagged a name, and in the tagger's own lower-case vocabulary ("Well, residents said")."""
        first = self.tokens[0]
        return first.is_word and self.tags[0] not in pos.NAMES and first.norm in pos.lower_words()

    def _is_command(self, commands: frozenset[str]) -> bool:
        """One of the text's commands (_Run.commands), with no subject: "Cook the beans", but "Cook sailed in"
        is someone doing something."""
        return (self.tokens[0].is_word and self.tokens[0].norm in commands
                and (len(self.tags) < 2 or self.tags[1] not in ("VBD", "VBZ", "VBN", "MD")))

    def _reads_as_name(self, written: frozenset[str]) -> bool:
        """Tagged a name and no common opener ("Up jumped the swagman"), unknown to the tagger in lower case, and
        never written in lower case in this text: keep its capital, even for an ordinary word ("Cook")."""
        first = self.tokens[0]
        return (first.is_word and self.tags[0] in pos.NAMES and first.norm not in COMMON_STARTERS
                and first.norm not in pos.lower_words() and first.norm not in written)


@dataclass
class _Run:
    """One translate() call: its policy, the text's reading, the state across sentences, and the records."""
    text: str
    pol: Policy
    eff: Effective
    mood: str
    chant: bool
    masked: Masked
    genre: Genre
    english: str | None           # the source's English (dialect.text_english), where known
    embellishment: Embellishment  # the caller's setting, or the genre's own: which garnish it takes
    state: TextState = field(default_factory=TextState)
    composition: DocumentPart | None = None
    observer: PassObserver | None = None
    records: list[SubstitutionRecord] = field(default_factory=list)
    garnish: list[GarnishRecord] = field(default_factory=list)
    rewrites: list[RewriteRecord] = field(default_factory=list)
    difficult: list[DifficultSentence] = field(default_factory=list)
    dialect: list[DialectRecord] = field(default_factory=list)
    _plain: frozenset[str] | None = None
    imagery: list[dict] = field(default_factory=list)
    _headings: list[tuple[int, int]] | None = None
    _held: list[tuple[int, int]] | None = None
    _datelines: list[tuple[int, int]] | None = None
    _commands: frozenset[str] | None = None
    _written: frozenset[str] | None = None

    def held(self, tokens: list[Token]) -> set[int]:
        """The tokens no swap may touch: words mentioned rather than used ("the word 'guys'"), and in a genre
        that keeps quotes (news, official prose) the quoted speech and documents."""
        if self._held is None:
            self._held = mentioned_spans(self.text) + document_spans(self.text, keep_quotes=self.genre.policy.keep_quotes,
                                                                   datelines=self.genre.policy.dateline_context)
        return {i for i, t in enumerate(tokens) if any(a <= t.start < b for a, b in self._held)}

    def commands(self) -> frozenset[str]:
        """In instructions, the command verbs a sentence may open on ("Pour the batter"), less any the text
        capitalises mid-sentence (it's a name there: "Captain Cook"). Elsewhere none: "Cook sailed in"."""
        if self._commands is None:
            named = {m.lower() for m in MID_SENTENCE_NAME.findall(self.text)}
            self._commands = (pos.IMPERATIVES - named if self.genre.policy.command_context else frozenset())
        return self._commands

    def opener_lowerable(self, sent: _Sentence, dictionary: Dictionary) -> frozenset[str]:
        """The words safe to lower-case after an opener in this sentence (_Sentence.lowerable, given this text's
        plain words, commands and the words it writes in lower case)."""
        return sent.lowerable(self.plain_words(dictionary), self.commands(), self.written())

    def written(self) -> frozenset[str]:
        """The words this text writes in lower case somewhere."""
        if self._written is None:
            self._written = (self.composition.written if self.composition is not None and self.composition.written is not None
                             else frozenset(re.findall(r"(?<![\w'’])[a-z][a-z'’-]*", self.text)))
        return self._written

    def plain_words(self, dictionary: Dictionary) -> frozenset[str]:
        """Words safe to lower-case after an opener: ordinary English, plus any word this text itself writes in
        lower case, or a stem of one (so it isn't a name here: "Install the CLI" when the text says "installed")."""
        if self._plain is None:
            lower = self.written()
            stems = {w[:-len(end)] for w in lower for end in ("ing", "ed", "es", "s", "d") if w.endswith(end)}
            self._plain = dictionary.plain_words | lower | {w for w in stems if len(w) > 2}
        return self._plain

    def sentence(self, i: int, tokens: list[Token], sents: list[list[Token]]) -> _Sentence:
        text = self.text[tokens[0].start:tokens[-1].end]
        self.state.seen_sentences[text] += 1
        nxt = sents[i + 1][0].start if i + 1 < len(sents) else len(self.text)
        # in a story the engine can't tell whether "What a shocker!" fits what just happened, so only chants
        # get stanza-end asides
        para_end = self.chant and i + 1 < len(sents) and "\n" in self.text[tokens[-1].end:nxt]
        part = self.composition
        starts = part is None or i > 0 or part.starts_sentence
        ends = part is None or i < len(sents) - 1 or part.ends_sentence
        quiet = (not starts or part is not None and part.quiet
                 or self.masked.quiet_at(tokens[0].start) or self.is_heading(tokens) or self.is_held(tokens)
                 or self.in_dateline(tokens))
        return _Sentence(i, tokens, text, (text.lower(), self.state.seen_sentences[text]), nxt, para_end, quiet,
                         pos.tag([t.text for t in tokens]), prefix_only=starts and not ends,
                         source_contexts=part.last_contexts if part is not None and starts and not ends else None,
                         complete=ends)

    def in_dateline(self, tokens: list[Token]) -> bool:
        """A sentence starting in a news story's dateline ("MAMMOTH HOT SPRINGS, Wyo. –", which splits at
        "Wyo.")."""
        if self._datelines is None:
            self._datelines = ([m.span() for m in DATELINE.finditer(self.text)] if self.genre.policy.dateline_context
                               else [])
        return any(a <= tokens[0].start < b for a, b in self._datelines)

    def is_held(self, tokens: list[Token]) -> bool:
        """A sentence that starts or ends inside a held span (held: a quote the genre keeps, a quoted
        statement in the news, or a word mentioned): garnish there would put words in the speaker's mouth."""
        held = self.held(tokens)
        return 0 in held or len(tokens) - 1 in held

    def is_heading(self, tokens: list[Token]) -> bool:
        """A sentence that is a heading in plain text: its words swap, it takes no garnish. (A dateline,
        "WASHINGTON, Dec. 27.—", and a held quote take none either: sentence() checks them.)"""
        if self._headings is None:
            self._headings = heading_lines(self.text)
        return any(a <= tokens[0].start and tokens[-1].end <= b for a, b in self._headings)


def _splice(sent: _Sentence, splices: list[tuple[int, int, str]]) -> str:
    """The sentence with its substitutions spliced in (source offsets, applied right to left)."""
    out, start = sent.text, sent.tokens[0].start
    for a, b, repl in sorted(splices, reverse=True):
        out = out[: a - start] + repl + out[b - start:]
    return out


def _bare(term: str) -> str:
    return re.sub(r"^(?:a|an|the)\s+", "", form_key(term))


def first_replaced(records: Sequence[SubstitutionRecord], tokens: list[Token],
                   swap: tuple[SubstitutionRecord, int, Entry] | None = None) -> bool:
    """Whether a sentence starts with a swap whose term starts in lower case, so an opener lowers it whatever it
    is. swap: (a record, where its swap would start, its entry) in place of that record's own pick, for a telling
    with another option there."""
    for r in records:
        if swap is not None and r is swap[0]:
            start, entry = swap[1], swap[2]
        elif r.substituted and r.out_span:
            start, entry = r.out_span[0], r.chosen.entry
        else:
            continue
        if start == tokens[0].start and entry.form[:1].islower():
            return True
    return False


def _gloss_echo(toks: list[Token], s: int, e: int, term: str, said: dict[int, str]) -> str | None:
    """Why a swap at toks[s:e] would make a bracketed gloss echo its word, if it would. said: the swaps made so
    far in the sentence, by the token they end before."""
    key = _bare(term)
    # the bracket after the span already says it in Australian: "an elevator (lift)" stays, not "lift (lift)"
    if e < len(toks) and toks[e].text == "(":
        close = next((j for j in range(e + 1, min(len(toks), e + 7)) if toks[j].text == ")"), None)
        if close is not None and _bare(" ".join(t.text for t in toks[e + 1:close])) == key:
            return "the bracket after it already says it"
    # the span is a bracketed gloss on a word already swapped: the author's own gloss stays as written ("lunch or
    # dinner (supper)" is "lunch or tea (supper)", not "tea (tea)"; "cookies (biscuits)" is "bickies (biscuits)")
    if s >= 1 and toks[s - 1].text == "(" and e < len(toks) and toks[e].text == ")" and s - 1 in said:
        return "a bracketed gloss on the word before it, which is already swapped"
    return None


def _no_drawl(text: str, keep_quotes: bool, protected=None) -> list[tuple[int, int]]:
    """Where the drawl, contractions and infixes stay out: a heading in plain text ("Minimizing the Risk") and a
    link's text, which name a page or a section rather than say anything; a word mentioned, not used; and in a
    genre that keeps quotes, the quotes (a reporter's "We are going to" isn't "We're gonna")."""
    return heading_lines(text) + (protected(text) if protected is not None else []) + held_spans(text, keep_quotes)


def _genre_rejection(c: Candidate, run: "_Run", neutral_people: frozenset[str]) -> str | None:
    """A swear standing in for someone named neutrally ("some bastard" for someone) needs a genre that takes it:
    not a safety notice, an obituary or a policy. A swear intensifier needs an embellishment that takes infixes,
    and a comic term in solemn prose needs an explicit setting."""
    genre = run.genre
    if c.entry.vulgarity and not genre.policy.person_swears and set(c.entry.concept) & neutral_people:
        return f"a swear for a person, and a {genre.name} text doesn't name people that way"
    if c.entry.vulgarity and c.entry.frame == "adv" and not run.embellishment.takes("infix"):
        return f"a swear as an intensifier (\"bloody stale\"), and {run.embellishment.name} takes none"
    if c.entry.tone == "comic" and run.mood == "solemn" and not run.embellishment.solemn_comic_terms:
        return "a comic term in solemn text; solemn_comic_terms is false"
    return None


def _span_rejection(c: Candidate, det: Detection, toks: list[Token], tags: list[str], taken: set[int]) -> str | None:
    """Why a candidate can't go in this span: it would overlap another swap, a noun phrase goes on past it, it
    brings a determiner the phrase has, or its number doesn't fit."""
    s, e = replacement_span(c.entry, det, toks)
    if set(range(s, e)) & taken:
        return "wider clause span overlaps another substitution"
    if c.entry.frame == "np" and phrase_continues(det, toks, e):
        return "the phrase goes on past the swap (\"the poor old minister\")"
    if c.entry.frame == "np" and c.entry.form.lower().startswith("some ") and toks[det.start].norm not in DETERMINERS \
            and after_determiner(toks, det.start):
        return "brings its own 'some', but the phrase already has a determiner"
    return number_problem(c.entry, det, toks, tags)


def _narrow(keep: list[Candidate], rejected: list, variety: int, state: TextState) -> list[Candidate]:
    """Drop what the text has already said, then (variety N) all but the N best fits."""
    # a multi-word name for a thing reads as a tic the second time ("the Big Smoke ... the Big Smoke"): say it
    # once and let the plain word stand after that. (Letting it back after a gap was tried: a long yarn then
    # leans on "bugger all" and "some bastard" over and over.)
    again = [c for c in keep if c.entry.frame == "np" and len(c.entry.form.split()) > 1 and state.entry_uses.get(c.entry.id)]
    keep = [c for c in keep if c not in again]
    rejected += [(c.entry, "already used in this text; the plain word can stand the second time") for c in again]
    if variety and len(keep) > variety:
        # variety N: pick among the N best fits only (1 = always the best); ties keep dictionary order
        best = set(map(id, sorted(keep, key=lambda c: -c.weight)[:variety]))
        rejected += [(c.entry, f"variety {variety}: not among the {variety} best fits") for c in keep if id(c) not in best]
        keep = [c for c in keep if id(c) in best]
    return keep


def _fix_article(out: str, toks: list[Token], s: int, replaced: set[int]) -> tuple[int, str]:
    """a/an agreement with whatever now follows an article before the swap (taking the article into the span),
    and positional capitals. Returns the swap's new start and text."""
    if s > 0 and toks[s - 1].norm in ("a", "an") and (s - 1) not in replaced:
        if out.split(" ", 1)[0].lower() in ARTICLES:
            return s - 1, Translator._case(out, toks, s - 1)
        return s - 1, fix_articles(toks[s - 1].text + " " + out)
    return s, Translator._case(out, toks, s)


@lru_cache(maxsize=1)
def default_translator() -> Translator:
    """The process-wide Translator over the built-in dictionary (loading it takes most of a second)."""
    return Translator()


def translate(text: str, *, level: int | str = 5, seed: int = 0, vulgarity: int | str | None = None,
              variety: int = 0, registers: Sequence[str] | None = None, regions: Sequence[str] | None = None,
              unlock: Sequence[str] | None = None, english: str | None = None,
              embellishment: int | str | None = None, translator: Translator | None = None) -> Result:
    """The rule engine's translation, as a Result (text, plan, explain records). The toolkit's parameters;
    see Translator.translate for what each does and for the engine-only options (embedder, rewriter)."""
    return (translator or default_translator()).translate(
        text, level=level, seed=seed, vulgarity=vulgarity, variety=variety,
        registers=registers, regions=regions, unlock=unlock, english=english,
        embellishment=embellishment)
