"""Yarn mode: Claude tells the whole text as an Aussie yarn, using the harness as its toolkit.

The rule engine plans: its draft, the phrases it chose, and the sentences it found too formal. Claude
gets that plan, the style guide for the level, and three tools. The embellishment (deadset, dinkum, troppo;
data/genres.yaml; default Dinkum for General, whatever the genre) sets how much liberty it takes: troppo
writes first, without the engine's draft, and treats the planned phrases as vocabulary.

- lookup(query): look up genuine Aussie options for a meaning, or check what a term means
- lint(text):   lint a draft (flagged phrases, swearing over the cap, US spelling, US and British words)
- submit(text):   hand in the final version. It is validated, and rejected with reasons if it
                       fails, so Claude fixes it and submits again.

Validation on submit: no lint issues, most of the planned phrases kept or declined with a reason, below troppo
(a planned phrase can be in the wrong sense: "battlers" for "one people"), each kept one where it replaces what
it was planned for (not worked in somewhere else), and the lint's fidelity and
swearing warnings clear (length within the embellishment's limit, numbers kept, no swear leaned on). If Claude
can't produce a passing version within the turn limit, or the API is unavailable, the deterministic
draft stands. Accepted yarns are cached on disk, so a run is reproducible offline.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from . import claude, harness
from .align import counterparts, sentence_spans
from .claude import DEFAULT_MODEL
from .engine import Translator, default_translator
from .genre import resolve_document, Embellishment
from .policy import DocumentOverrides
from .guide import style_guide_data

from .markup import detect_markup, mask
from .terms import phrase_kept, fold, form_key

YARN_SYSTEM = """You retell English as genuine Australian English using the supplied toolkit and brief.
{rules}

DOCUMENT_CONFIG is the effective behaviour contract and takes precedence over general craft and preset
guidance. Use only the listed garnish placements; offer no talker's openings when openings is false. When
keep_quotes is true, preserve quoted wording exactly. When person_swears is false, do not replace neutral
people with swears. Keep terms protected by term_domains and datelines protected by dateline_context unchanged.
Respect check_length/max_length and keep_share as configured. No optional Custom behaviour is implied by its
embellishment label. Preserve every original fact and the selected markup regardless of the type.

STYLE GUIDE:
{guide}
"""


def tool_definitions() -> list[dict[str, Any]]:
    """Claude API tool definitions for the harness. Any agent built on the Messages API can use these."""
    return [
        {"name": "lookup", "strict": True,
         "description": "Look up genuine Australian slang for a plain-English meaning (e.g. 'very busy', "
                        "'someone', 'too hot'), or what an Aussie term means (e.g. 'goog'). Returns entries with "
                        "gloss, frame, minimum level and vulgarity, filtered to the current level and cap.",
         "input_schema": {"type": "object", "properties": {"query": {"type": "string"}},
                          "required": ["query"], "additionalProperties": False}},
        {"name": "lint", "strict": True,
         "description": "Lint a draft for the current level: flagged or non-Australian phrases, swearing over "
                        "the cap or overused, US spelling and US words, and fidelity to the original (length, "
                        "names, numbers). Also lists optional spots that could be more Aussie, leaving out "
                        "phrases you have already declined.",
         "input_schema": {"type": "object", "properties": {"text": {"type": "string"}},
                          "required": ["text"], "additionalProperties": False}},
        {"name": "submit", "strict": True,
         "description": "Submit the complete final yarn. It's validated; if it fails you get the reasons and "
                        "should fix them and submit again. Keep planned phrases that fit; list in `declined` any "
                        "you left out because they don't (wrong sense, wrong tone), each with a one-line reason.",
         "input_schema": {"type": "object", "properties": {
             "text": {"type": "string"},
             "declined": {"type": "array", "items": {
                 "type": "object", "properties": {"phrase": {"type": "string"}, "reason": {"type": "string"}},
                 "required": ["phrase", "reason"], "additionalProperties": False}}},
             "required": ["text", "declined"], "additionalProperties": False}},
    ]


@dataclass
class YarnResult:
    text: str
    status: str
    draft: str
    plan: dict[str, Any]
    tool_calls: dict[str, int] = field(default_factory=dict)
    model: str = DEFAULT_MODEL
    declined: list[dict] = field(default_factory=list)   # planned phrases the model left out, with its reasons
    outcome: str = "fell_back"   # "applied" (a yarn was accepted, now or from the cache) or "fell_back" (the draft)

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text, "outcome": self.outcome, "status": self.status, "draft": self.draft, "model": self.model,
                "tool_calls": self.tool_calls, "declined": self.declined, "plan": self.plan}


# bumped whenever validate's rules change, so a yarn cached under the old rules is asked for again
VALIDATION_VERSION = 3

# below this many planned phrases a share means nothing: a plan of two is kept whole or declined phrase by phrase
MIN_PLANNED_FOR_SHARE = 4


def _reasons(declined: list[dict] | tuple) -> dict[str, str]:
    """Each declined phrase (the submit tool's {phrase, reason}, as the schema and the CLI give it), by form
    key, with its reason: what validate excuses and what lint stops offering."""
    return {form_key(d["phrase"]): d["reason"].strip() for d in declined}


def validate(session: "YarnSession", text: str, declined: list[dict] | None = None,
             keep_share: float | None = None) -> list[str]:
    """Problems with a submitted yarn (empty: accepted). It lints with the session's own policy, as the lint
    tool does. Each distinct planned phrase counts once. A declined one ({phrase, reason}) is excused, since
    the plan can be wrong ("battlers" for "one people") and the reason is the record of why; of the rest, at
    least keep_share (None: the embellishment's) must be kept, when the plan has enough phrases to make a share
    (declining most of a long plan doesn't let the rest go quietly). At troppo the share is 0: the planned
    phrases are vocabulary."""
    problems = []
    planned = session.planned
    keep_share = session.embellishment.keep_share if keep_share is None else keep_share
    lint = harness.lint(text, level=session.level, vulgarity=session.vulgarity, english=session.english,
                         embellishment=session.embellishment.step, document_type=session.document_type, document_config=session.document_config, original=session.text, markup=session.markup,
                         translator=session.translator, suggest=False)
    for issue in lint["issues"]:
        fix = issue.get("australian")
        problems.append(f"{issue['kind']}: {issue['phrase']}" + (f" (use {fix})" if fix else ""))
    for w in lint["warnings"]:   # the warnings an unharnessed model trips most: one swear leaned on, lost facts
        if w["kind"] in ("swear_overuse", "swear_density", "number_dropped", "tag_in_narration", "tag_overuse",
                         "too_long", "too_short"):
            problems.append(f"{w['kind']}: {w['phrase']}: {w['why']}")
    if planned:
        reasons = _reasons(declined or ())
        unknown = [p for p in reasons if p not in {form_key(x) for x in planned}]
        if unknown:
            problems.append(f"declined phrases that aren't planned: {', '.join(unknown)} (decline a phrase as "
                            f"PLANNED_PHRASES prints it)")
        if any(not r for r in reasons.values()):
            problems.append("every declined phrase needs a reason")
        expected = [p for p in planned if form_key(p) not in reasons]
        missing = [p for p in expected if not phrase_kept(text, p, session.translator.dictionary.phonetic)]
        moved = _moved(session, text, [p for p in expected if p not in missing]) if keep_share else []
        if moved:
            problems.append("planned phrases put somewhere else: " + "; ".join(
                f"{p} is in, but every \"{o}\" it was planned for is still there" for p, o in moved)
                + " (put it where it replaces those words, or decline it)")
        if (keep_share and expected and len(planned) >= MIN_PLANNED_FOR_SHARE
                and 1 - len(missing) / len(expected) < keep_share):
            kept = 1 - len(missing) / len(expected)
            problems.append(f"kept only {kept:.0%} of the planned phrases you didn't decline (need "
                            f"{keep_share:.0%}); bring back, or decline with a reason, some of: "
                            f"{', '.join(sorted(missing)[:10])}")
    return problems


@dataclass
class YarnSession:
    """Everything one yarn run knows before the model speaks: the text, the engine's plan, the level, vulgarity
    and embellishment (resolved), and the brief (system prompt and user payload). Built by brief(); dispatch_tool() answers tool calls
    against it. The API loop in yarn() and the hand-run tools (research/retellings-*/yarn_tools.py) share both."""
    text: str
    level: int
    seed: int
    vulgarity: int
    translator: Translator
    plan: dict[str, Any]
    planned: list[str]
    system: str
    payload: dict[str, Any]
    embellishment: Embellishment   # resolved by brief from the selected dictionary
    document_type: str = "general"
    document_config: DocumentOverrides | None = None
    markup: str = "text"
    english: str | None = None     # the original's English, for the dialect swaps (None: the default)
    declined: set[str] = field(default_factory=set)   # planned phrases declined with a reason (form keys), at any
                                                      # submit so far: lint won't offer them again

    def decline(self, declined: list[dict]) -> None:
        """Remember the phrases declined as validate accepts them (planned, with a reason). Sticky: a later
        submit that declines nothing doesn't bring them back."""
        planned = {form_key(p) for p in self.planned}
        self.declined |= {key for key, reason in _reasons(declined).items() if reason and key in planned}


MARKUP_RULE = ("The original is a {markup} document. Retell only its prose. Keep every code block, inline code "
               "span, tag and component (props included), import, front matter block, heading, link target, URL, "
               "table layout and list marker exactly as it is, character for character.")


def brief(text: str, *, level: int | str = 5, seed: int = 0, vulgarity: int | str | None = None,
          markup: str = "text", english: str | None = None, embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None,
          translator: Translator | None = None) -> YarnSession:
    tr = translator or default_translator()
    document_config = DocumentOverrides.parse(document_config)
    if markup == "auto":
        markup = detect_markup(text)
    the_plan = harness.plan(text, level=level, seed=seed, vulgarity=vulgarity, markup=markup, english=english,
                            embellishment=embellishment, document_type=document_type, document_config=document_config, translator=tr)
    context = resolve_document(None, config=tr.dictionary.genres, document_type=the_plan["genre"],
                               document_config=document_config)
    setting = context.setting(the_plan["embellishment"])
    guide = harness.guide(level=level, vulgarity=vulgarity, embellishment=setting.step, document_type=context.name, document_config=document_config, translator=tr)
    # each phrase once, with what it stands for, so a wrong sense shows at a glance
    phrases: dict[str, dict[str, str]] = {}
    for p in the_plan["planned"]:
        phrases.setdefault(form_key(p["aussie"]), {"phrase": p["aussie"], "replaces": p["original"],
                                                     "means": p["gloss"]})
    planned = [p["phrase"] for p in phrases.values()]
    guide_text = "\n".join([f"Voice: {guide['voice']}", f"Language: {guide['language']}", "Craft:", guide["craft"]])
    payload = {"ORIGINAL": text, "LEVEL": guide["level"], "VULGARITY": guide["vulgarity"],
               "EMBELLISHMENT": {"name": setting.name, "guidance": setting.guidance},
               "GENRE": {"name": the_plan["genre"], "guidance": the_plan["guidance"]["genre"]},
               "DOCUMENT_CONFIG": the_plan["document_config"],
               **({"ENGINE_DRAFT": the_plan["draft"]} if setting.draft else {}),
               "PLANNED_PHRASES": list(phrases.values()), "RIFFS": the_plan["riffs"],
               "OPENINGS": the_plan["openings"], "DIFFICULT_SENTENCES": the_plan["difficult_sentences"]}
    if markup != "text":
        payload["MARKUP"] = MARKUP_RULE.format(markup=markup)
    return YarnSession(text, guide["level"], seed, guide["vulgarity"], tr, the_plan, planned,
                       YARN_SYSTEM.format(guide=guide_text, rules=style_guide_data().yarn_rules), payload, embellishment=setting, document_type=context.name, document_config=document_config, markup=markup, english=english)


def _moved(session: "YarnSession", text: str, kept: list[str]) -> list[tuple[str, str]]:
    """Kept planned phrases that replace nothing: at every spot the phrase was planned for, the yarn's
    counterpart of that sentence still has the words it was planned to replace and not the phrase, so it was
    worked in somewhere else ("lobbed" for "turned up", kept while "turned up" stands; "dosh" pushed into a
    quoted ad). Only the planned spots count: the original's word used again in the writer's own wording
    elsewhere ("a look" for "Examine") is no move."""
    source = mask(session.text, session.markup).prose()
    told = mask(text, session.markup).prose()
    src = sentence_spans(source)   # as verify aligns them
    yarned = [fold(told[a:b]) for a, b in sentence_spans(told)]
    found = counterparts([source[a:b] for a, b in src], yarned)

    def window(at: int) -> str | None:
        i = next((n for n, (a, b) in enumerate(src) if a <= at < b), None)
        c = found[i] if i is not None else None
        return " ".join(yarned[c.start:c.end]) if c is not None else None

    def has(words: str, t: str) -> bool:
        return re.search(rf"(?<!\w){re.escape(words)}(?!\w)", t) is not None

    out = []
    for phrase in kept:
        spots = [(fold(p["original"]), p["span"][0]) for p in session.plan["planned"]
                 if form_key(p["aussie"]) == form_key(phrase)]
        where = [(o, window(at)) for o, at in spots]
        if where and all(w is not None and not has(fold(phrase), w) and has(o, w) for o, w in where):
            out.append((phrase, sorted(o for o, _ in where)[0]))
    return out


TOOL_ARGS = {t["name"]: tuple(t["input_schema"]["required"]) for t in tool_definitions()}


def _without_declined(lint: dict[str, Any], declined: set[str]) -> dict[str, Any]:
    """A lint result with the phrases the model already declined left out of its suggestions and its issues'
    fixes: "punters", turned down as the wrong sense, isn't offered again for the same text."""
    if not declined:
        return lint
    suggestions = []
    for s in lint["suggestions"]:
        options = [o for o in s["options"] if form_key(o) not in declined]
        if options:
            suggestions.append({**s, "options": options})
    issues = [{k: v for k, v in i.items() if not (k == "australian" and form_key(str(v)) in declined)}
              for i in lint["issues"]]
    return {**lint, "issues": issues, "suggestions": suggestions}


def dispatch_tool(session: YarnSession, name: str, args: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Answer one tool call: (result, accepted). accepted is True only for a submit that passes validation.
    An unknown tool or a missing argument comes back as an error result for the model to fix."""
    s = session
    if name not in TOOL_ARGS:
        return {"error": f"unknown tool {name}"}, False
    missing = [a for a in TOOL_ARGS[name] if a not in args]
    if missing:
        return {"error": f"{name}: missing argument {', '.join(missing)}"}, False
    if name == "lookup":
        # short: a writer checking a choice wants the term, its sense and how it fits, not the whole card
        return harness.lookup(args["query"], level=s.level, vulgarity=s.vulgarity, short=True,
                              translator=s.translator), False
    if name == "lint":
        out = harness.lint(args["text"], level=s.level, vulgarity=s.vulgarity, markup=s.markup, english=s.english,
                           embellishment=s.embellishment.step, document_type=s.document_type, document_config=s.document_config, translator=s.translator, original=s.text)
        return _without_declined(out, s.declined), False
    s.decline(args["declined"])
    problems = validate(s, args["text"], args["declined"])
    return {"accepted": not problems, "problems": problems}, not problems


def yarn(text: str, *, level: int | str = 5, seed: int = 0, vulgarity: int | str | None = None,
         markup: str = "text", client: Any = None, model: str = DEFAULT_MODEL, cache: bool = True,
         cache_dir: str | None = None,
         max_turns: int = 12, english: str | None = None, embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None,
         translator: Translator | None = None) -> YarnResult:
    """Run yarn mode: brief the model, answer its tool calls, accept the first submit that validates. Only the
    Anthropic SDK and API calls are guarded (offline, no key, API errors keep the engine's draft); a bug in the
    harness or validation raises. markup (markdown, mdx, auto): the model retells the prose only, and a
    submission that changes any code or markup is sent back. english as for translate; embellishment as for
    translate: General defaults to Dinkum, named types supply presets."""
    session = brief(text, level=level, seed=seed, vulgarity=vulgarity, markup=markup, english=english,
                    embellishment=embellishment, document_type=document_type, document_config=document_config, translator=translator)
    result = YarnResult(session.plan["draft"], "", session.plan["draft"], session.plan, {}, model)

    key_payload = {"BRIEF": session.payload, "PLAN": session.plan, "VALIDATION": VALIDATION_VERSION,
                   "SETTING": {**asdict(session.embellishment), "garnish": sorted(session.embellishment.garnish)}}
    # everything that decides the reply: the brief the model gets (and the plan behind it), the rules its yarn
    # is accepted under (the setting's share and length), and the instructions and tools it works with
    key = claude.Cache.key(model, seed, key_payload, session.system, tool_definitions())
    store = claude.Cache((cache_dir or claude.default_cache_dir("yarn")) if cache else None)
    cached = store.get(key)
    if cached is not None:
        result.text, result.status, result.tool_calls = cached["text"], "yarned (cached)", cached.get("tool_calls", {})
        result.declined, result.outcome = cached.get("declined", []), "applied"
        return result

    messages: list[dict[str, Any]] = [{"role": "user", "content": json.dumps(session.payload, ensure_ascii=False)}]
    for _ in range(max_turns):
        try:
            client = client or claude.client()
            response = claude.create(client, model=model, max_tokens=16000, effort="medium", system=session.system,
                                     tools=tool_definitions(), messages=messages, cache=True)
        except claude.Error as exc:   # no SDK or key, or the API failed: the draft stands
            result.status = f"kept draft: {type(exc).__name__}: {exc}"
            return result
        if response.stop_reason == "refusal":
            result.status = "kept draft: model declined"
            return result
        messages.append({"role": "assistant", "content": response.content})
        uses = [b for b in response.content if b.type == "tool_use"]
        if not uses:
            messages.append({"role": "user", "content": "Please finish by calling submit with the full text."})
            continue
        results = []
        for use in uses:
            result.tool_calls[use.name] = result.tool_calls.get(use.name, 0) + 1
            out, accepted = dispatch_tool(session, use.name, use.input)
            if accepted:
                result.text, result.status, result.outcome = use.input["text"].strip(), "yarned", "applied"
                result.declined = list(use.input.get("declined", []))
                store.put(key, {"text": result.text, "tool_calls": result.tool_calls, "declined": result.declined,
                                "payload": key_payload})
                return result
            results.append(_tool_result(use.id, out, error="error" in out or out.get("accepted") is False))
        messages.append({"role": "user", "content": results})
    result.status = f"kept draft: no accepted yarn within {max_turns} turns"
    return result


def _tool_result(tool_use_id: str, content: Any, error: bool = False) -> dict[str, Any]:
    block = {"type": "tool_result", "tool_use_id": tool_use_id, "content": json.dumps(content, ensure_ascii=False)}
    if error:
        block["is_error"] = True
    return block
