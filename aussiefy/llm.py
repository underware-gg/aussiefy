"""Optional fluent-surface mode: the engine plans, an LLM smooths only the joins.

The deterministic plan stays authoritative. The model receives the draft and the
list of planned phrases, and returns a rewrite that must keep every planned
phrase and add no other slang. If the rewrite drops a planned phrase, or the
call fails, we keep the deterministic text and record why in `result.surface`.
"""

from __future__ import annotations

from .themes import ThemePermissions, ThemePolicy

import json
from pathlib import Path
from typing import Any

from . import claude
from .claude import DEFAULT_MODEL
from .engine import Result, Translator, default_translator
from .errors import UserError
from .guide import style_guide_data
from .terms import phrase_kept
from .text import sentences, tokenize
from .policy import theme_permissions
from .semantic_checks import theme_issues


SURFACE_SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string"}},
    "required": ["text"],
    "additionalProperties": False,
}

SYSTEM = """You polish machine-generated Australian slang so it reads like natural speech.
You get the ORIGINAL plain-English text, a DRAFT produced by a rule-based engine and a list
of PLANNED phrases the engine chose. Rewrite the DRAFT so the joins sound natural: fix
grammar around the inserted phrases, punctuation, capitalisation and rhythm.

Rules:
- Keep every PLANNED phrase. You may adjust its inflection, phonetic spelling or capitalisation,
  but keep its words.
- Do not add slang, idioms, openers, tag-ons or swears that are not in the plan.
- Keep the meaning of the ORIGINAL. Do not add or remove claims.
- Respect THEME_RULES (allowed_through is the maximum tag tier; -1 forbids all, 3 allows all), with THEME_PERMISSIONS showing only defaults. Reviewed tag tiers can differ from those defaults; retain the original's own subject matter.
- Return only the rewritten text."""



def missing_phrases(text: str, planned: list[str]) -> list[str]:
    """Planned forms absent from a draft, using the shared inflection-aware term rule."""
    return [phrase for phrase in planned if not phrase_kept(text, phrase, default_translator().dictionary.phonetic)]

def surface_rewrite(result: Result, client: Any = None, model: str = DEFAULT_MODEL,
                    translator: Translator | None = None) -> Result:
    """Polish the joins of result's text in place; translator is the one that made it (its phonetic rules say
    which respellings of a planned phrase still count as keeping it)."""
    dictionary = (translator or default_translator()).dictionary
    phonetic = dictionary.phonetic
    plan = result.decisions()
    planned = [s["replacement"] for s in plan["substitutions"]] + [g["text"] for g in plan["garnish"]]
    surface: dict[str, Any] = {"model": model, "planned": planned}
    result.deterministic_text = result.text
    result.surface = surface
    if not planned:
        surface.update(outcome="skipped", status="skipped: nothing planned")
        return result
    try:
        text = claude.call_json(client or claude.client(), model=model, system=SYSTEM, max_tokens=8000,
                                schema=SURFACE_SCHEMA, prompt=json.dumps(
                                    {"ORIGINAL": result.source, "DRAFT": result.text, "PLANNED": planned,
                                     "THEME_PERMISSIONS": theme_permissions(result.theme_policy), "THEME_RULES": result.theme_policy.rules()},
                                    ensure_ascii=False))["text"].strip()
    except claude.Error as exc:  # offline, no key, declined, a bad reply: the deterministic output stands
        surface.update(outcome="fell_back", status=f"kept deterministic: {type(exc).__name__}: {exc}")
        return result
    missing = [p for p in planned if not phrase_kept(text, p, phonetic)]
    if missing:
        surface.update(outcome="fell_back", rejected_text=text,
                       status=f"kept deterministic: rewrite dropped planned phrase(s) {missing}")
        return result
    if theme_issues(text, result.source, dictionary, result.theme_policy):
        surface.update(outcome="fell_back", rejected_text=text,
                       status="kept deterministic: rewrite introduced known wording with forbidden themes")
        return result
    surface.update(outcome="applied", status="applied")
    result.text = text
    return result


# --- whole-sentence rewriter for sentences the dictionary can't carry ---------------

def _voice(level: int, vulgarity: int) -> str:
    data = style_guide_data()
    return f"Level {level}/5: {data.levels[level]} {data.language[vulgarity]}"


REWRITE_SCHEMA = SURFACE_SCHEMA

REWRITE_SYSTEM = """You translate one English sentence into Australian slang, the way an Australian would
actually say it. Use genuine Australian usage only: words and idioms Australians really say (they need
not be exclusively Australian), nothing American and no invented slang. Swap whole ideas for the way an
Aussie would put them, not word for word. Keep every fact, name, number and claim of the original, and
its sentence type (question, statement, exclamation).

Translate the register, not the speech. Keep the original's structure, rhythm and famous turns of
phrase where they still work ("of the people, by the people, for the people"), and change the words
around them. At higher levels, an Aussie speaker leans on swear infixes within the vulgarity limit
("a bloody great effort", "can't bloody well") and the odd short pub aside, but don't overdo either.
Use Australian spelling (honoured, colour, organise).

You are also given a DRAFT in which a rule-based engine has already inserted some PLANNED phrases. Keep
every planned phrase (inflection may change). Don't add openers, tag-ons or swears at the start or
end of the sentence (no "Strewth," no ", mate"), because the engine adds those separately.
Respect THEME_RULES (allowed_through is the maximum tag tier; -1 forbids all, 3 allows all), with THEME_PERMISSIONS showing only defaults. Reviewed tag tiers can differ from those defaults; retain the original's own subject matter. Return one
sentence only."""


class ClaudeRewriter:
    """Says a difficult sentence in Aussie drawl. Accepted rewrites are cached on disk (default: cache/rewrite under
    the aussiefy home, $AUSSIEFY_HOME or ~/.aussiefy), so a given (sentence, draft, level, vulgarity, seed, model)
    always gives the same output; cache=False neither reads nor writes it. translator is the one whose drafts it
    rewrites (its phonetic rules say which respellings of a planned phrase still count as keeping it)."""

    def __init__(self, client: Any = None, model: str = DEFAULT_MODEL, cache: bool = True,
                 cache_dir: str | Path | None = None, translator: Translator | None = None):
        self.client = client
        self.model = model
        self.cache = claude.Cache((cache_dir or claude.default_cache_dir("rewrite")) if cache else None)
        self.translator = translator or default_translator()
        self.phonetic = self.translator.dictionary.phonetic

    def rewrite(self, original: str, draft: str, planned: list[str], *, level: int, vulgarity: int,
                seed: int = 0, permitted_themes: frozenset[str] | None = None, theme_policy: ThemePolicy | None = None) -> tuple[str | None, str]:
        if theme_policy is None:
            theme_policy = self.translator.effective(level=level, vulgarity=vulgarity).theme_policy
            if permitted_themes is not None:
                from dataclasses import replace
                theme_policy = replace(theme_policy, overrides=tuple((name, name in permitted_themes) for name, _ in theme_policy.starts))
        payload = {"ORIGINAL": original, "DRAFT": draft, "PLANNED": planned,
                   "VOICE": _voice(level, vulgarity), "THEME_PERMISSIONS": theme_permissions(theme_policy), "THEME_RULES": theme_policy.rules()}
        key = claude.Cache.key(self.model, seed, payload, REWRITE_SYSTEM)
        cached = self.cache.get(key)
        if cached is not None:
            if (not isinstance(cached, dict) or not isinstance(cached.get("text"), str)
                    or not isinstance(cached.get("status"), str)):
                raise UserError(f"{self.cache.directory / (key + '.json')}: invalid rewrite cache entry; delete it")
            if self._problem(cached["text"], original, planned, theme_policy) is None:
                return cached["text"], f"{cached['status']} (cached)"
        try:
            self.client = self.client or claude.client()
            text = claude.call_json(self.client, model=self.model, system=REWRITE_SYSTEM, schema=REWRITE_SCHEMA,
                                    prompt=json.dumps(payload, ensure_ascii=False))["text"].strip()
        except claude.Error as exc:  # offline, no key, declined, a bad reply: the dictionary's draft stands
            return None, f"kept draft: {type(exc).__name__}: {exc}"

        problem = self._problem(text, original, planned, theme_policy)
        if problem:
            return None, f"kept draft: rewrite {problem}"
        self.cache.put(key, {"text": text, "status": "rewritten", "payload": payload})
        return text, "rewritten"

    def _problem(self, text: str, original: str, planned: list[str],
                 permitted_themes: ThemePermissions | None = None) -> str | None:
        """The acceptance rule for both fresh and cached replies, including older cache entries."""
        missing = [p for p in planned if not phrase_kept(text, p, self.phonetic)]
        if not text or "\n" in text or len(sentences(tokenize(text))) != 1:
            return "not a single sentence"
        if len(text.split()) > 3 * len(original.split()) + 10:
            return "far longer than the original"
        if missing:
            return f"dropped planned phrase(s) {missing}"
        if permitted_themes is not None and theme_issues(text, original, self.translator.dictionary, permitted_themes):
            return "introduced known wording with forbidden themes"
        return None
