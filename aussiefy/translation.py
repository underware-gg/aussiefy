"""Common translation routing for the public API, toolkit and CLI, above the plain engine."""

from __future__ import annotations

from .engine import resolve_request

from typing import Sequence

from .claude import DEFAULT_MODEL
from .engine import Result, Translator, default_translator
from .errors import UserError
from .changes import ChangeSet, build
from .markdown import DocumentResult, document_changes, translate_document
from .markup import mask
from .policy import Effective, Policy, resolve


def _check_modes(markdown: bool, markup: str, rewrite: str | None, surface: bool) -> None:
    if markdown and markup != "text":
        raise UserError("choose markdown=True or markup, rather than both document modes")
    if surface and markup != "text":
        raise UserError("--surface rewrites the whole document; use --rewrite to preserve markup")
    if markdown and (rewrite or surface):
        raise UserError("Markdown translation cannot use --rewrite or --surface")


def _document_policy(translator: Translator, **dials) -> tuple[Policy, Effective]:
    """A Markdown document's policy, resolved; its similarity fallback must be one the strict units can take."""
    policy = translator.policy(**dials)
    if policy.embedder not in (None, "", "ngram", "none"):
        raise UserError(f"Markdown translation requires ngram or none fallback, got {policy.embedder!r}; "
                        "use --embedder ngram/none or configure the profile's policy.embedder")
    return policy, resolve(policy, translator.dictionary)


def run(text: str, *, translator: Translator, level: int | str = 5, seed: int = 0,
        vulgarity: int | str | None = None, variety: int = 0, registers: Sequence[str] | None = None,
        regions: Sequence[str] | None = None, unlock: Sequence[str] | None = None, markdown: bool = False,
        markup: str = "text", english: str | None = None, embellishment: int | str | None = None, dial_mode: str = "cap",
        document_type: str = "general", document_config: dict | None = None,
        themes: dict[str, bool] | None = None, invention: bool | None = None,
        popularity: bool = False, preferences: list[dict] | None = None, pins: dict | None = None,
        personal_terms: list[dict] | None = None, _personal_terms_hook=None,
        _preferences_hook=None,
        embedder: str | None = None, rewrite: str | None = None, surface: bool = False,
        model: str = DEFAULT_MODEL) -> Result | DocumentResult:
    translator, document_config = resolve_request(translator, document_config, themes=themes, invention=invention)
    _check_modes(markdown, markup, rewrite, surface)
    dials = dict(level=level, seed=seed, vulgarity=vulgarity, variety=variety, registers=registers, regions=regions,
                 unlock=unlock, embedder=embedder, english=english, embellishment=embellishment, dial_mode=dial_mode,
                 document_type=document_type, document_config=document_config)
    if markdown:
        return translate_document(text, translator, *_document_policy(translator, **dials), _tuning={'popularity': popularity, 'preferences': preferences}, _preferences_hook=_preferences_hook, pins=pins, personal_terms=personal_terms, _personal_terms_hook=_personal_terms_hook)
    rewriter = None
    if rewrite:
        from .llm import ClaudeRewriter

        rewriter = ClaudeRewriter(model=model, translator=translator)
    result = translator.translate(text, **dials, rewriter=rewriter, rewrite_mode=rewrite or "hard",
                                  _protected=mask(text, markup), popularity=popularity, preferences=preferences, pins=pins, _preferences_hook=_preferences_hook, personal_terms=personal_terms, _personal_terms_hook=_personal_terms_hook)
    if surface:
        from .llm import surface_rewrite

        surface_rewrite(result, model=model, translator=translator)
    return result


def translate(text: str, *, level: int | str = 5, seed: int = 0, vulgarity: int | str | None = None,
              variety: int = 0, registers: Sequence[str] | None = None, regions: Sequence[str] | None = None,
              unlock: Sequence[str] | None = None, markdown: bool = False,
              markup: str = "text", english: str | None = None, embellishment: int | str | None = None, dial_mode: str = "cap",
              document_type: str = "general", document_config: dict | None = None,
              themes: dict[str, bool] | None = None, invention: bool | None = None,
              popularity: bool = False, preferences: list[dict] | None = None, pins: dict | None = None,
        personal_terms: list[dict] | None = None, _personal_terms_hook=None,
              _preferences_hook=None,
              translator: Translator | None = None) -> Result | DocumentResult:
    """Translate plain text, or explicitly selected Markdown prose with its markup kept intact."""
    translator, document_config = resolve_request(translator, document_config, themes=themes, invention=invention)
    return run(text, dial_mode=dial_mode, translator=translator or default_translator(), level=level, seed=seed, vulgarity=vulgarity,
               variety=variety, registers=registers, regions=regions, unlock=unlock, markdown=markdown, markup=markup, english=english, embellishment=embellishment, document_type=document_type, document_config=document_config, popularity=popularity, preferences=preferences, pins=pins, _preferences_hook=_preferences_hook, personal_terms=personal_terms, _personal_terms_hook=_personal_terms_hook)


def translate_changes(text: str, *, level: int | str = 5, seed: int = 0, vulgarity: int | str | None = None,
                      variety: int = 0, registers: Sequence[str] | None = None, regions: Sequence[str] | None = None,
                      unlock: Sequence[str] | None = None, markdown: bool = False,
                      markup: str = "text", english: str | None = None, embellishment: int | str | None = None, dial_mode: str = "cap",
                      document_type: str = "general", document_config: dict | None = None,
                      themes: dict[str, bool] | None = None, invention: bool | None = None,
                      popularity: bool = False, preferences: list[dict] | None = None, pins: dict | None = None,
        personal_terms: list[dict] | None = None, _personal_terms_hook=None,
                      _preferences_hook=None,
                      embedder: str | None = None, translator: Translator | None = None, _watch=None) -> ChangeSet:
    """translate's translation, with every change it made (the `changes` contract, aussiefy.changes.VERSION): each
    swap, garnish, drawl, swear infix and US/UK swap placed in the output, and each swap's alternatives, and those a
    vulgarity lock holds back, rendered where they stand. Takes translate's parameters, and embedder: the
    similarity fallback ("ngram", "bundled", "local", "none"; None = profiles.yaml's), which a host sets
    explicitly. The CLI, MCP tools and yarn mode don't offer it (DD-029)."""
    translator, document_config = resolve_request(translator, document_config, themes=themes, invention=invention)
    tr = translator or default_translator()
    _check_modes(markdown, markup, None, False)
    dials = dict(level=level, seed=seed, vulgarity=vulgarity, variety=variety, registers=registers, regions=regions,
                 unlock=unlock, embedder=embedder, english=english, embellishment=embellishment, dial_mode=dial_mode,
                 document_type=document_type, document_config=document_config)
    if markdown:
        return document_changes(text, tr, *_document_policy(tr, **dials), _watch=_watch, _tuning={'popularity': popularity, 'preferences': preferences}, _preferences_hook=_preferences_hook, pins=pins, personal_terms=personal_terms, _personal_terms_hook=_personal_terms_hook)
    return build(tr, text, **dials, _observer=_watch(0) if _watch else None, _protected=mask(text, markup), popularity=popularity, preferences=preferences, pins=pins, _preferences_hook=_preferences_hook, personal_terms=personal_terms, _personal_terms_hook=_personal_terms_hook)
