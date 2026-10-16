"""Common translation routing for the public API, toolkit and CLI, above the plain engine."""

from __future__ import annotations

from typing import Sequence

from .claude import DEFAULT_MODEL
from .engine import Result, Translator, default_translator
from .errors import UserError
from .markdown import DocumentResult, translate_document
from .policy import resolve


def run(text: str, *, translator: Translator, level: int | str = 5, seed: int = 0,
        vulgarity: int | str | None = None, variety: int = 0, registers: Sequence[str] | None = None,
        regions: Sequence[str] | None = None, unlock: Sequence[str] | None = None, markdown: bool = False,
        markup: str = "text", english: str | None = None, embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None,
        embedder: str | None = None, rewrite: str | None = None, surface: bool = False,
        model: str = DEFAULT_MODEL) -> Result | DocumentResult:
    if markdown and markup != "text":
        raise UserError("choose markdown=True or markup, rather than both document modes")
    if surface and markup != "text":
        raise UserError("--surface rewrites the whole document; use --rewrite to preserve markup")
    if markdown:
        if rewrite or surface:
            raise UserError("Markdown translation cannot use --rewrite or --surface")
        policy = translator.policy(level=level, seed=seed, vulgarity=vulgarity, variety=variety,
                                   registers=registers, regions=regions, unlock=unlock, embedder=embedder,
                                   english=english, embellishment=embellishment, document_type=document_type, document_config=document_config)
        if policy.embedder not in (None, "", "ngram", "none"):
            raise UserError(f"Markdown translation requires ngram or none fallback, got {policy.embedder!r}; "
                            "use --embedder ngram/none or configure the profile's policy.embedder")
        return translate_document(text, translator, policy, resolve(policy, translator.dictionary))
    rewriter = None
    if rewrite:
        from .llm import ClaudeRewriter

        rewriter = ClaudeRewriter(model=model, translator=translator)
    from .markup import mask

    protected = mask(text, markup)
    result = translator.translate(text, level=level, seed=seed, vulgarity=vulgarity, variety=variety,
                                  registers=registers, regions=regions, unlock=unlock, embedder=embedder,
                                  rewriter=rewriter, rewrite_mode=rewrite or "hard", english=english,
                                  embellishment=embellishment, document_type=document_type, document_config=document_config, _protected=protected)
    if surface:
        from .llm import surface_rewrite

        surface_rewrite(result, model=model, translator=translator)
    return result


def translate(text: str, *, level: int | str = 5, seed: int = 0, vulgarity: int | str | None = None,
              variety: int = 0, registers: Sequence[str] | None = None, regions: Sequence[str] | None = None,
              unlock: Sequence[str] | None = None, markdown: bool = False,
              markup: str = "text", english: str | None = None, embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None,
              translator: Translator | None = None) -> Result | DocumentResult:
    """Translate plain text, or explicitly selected Markdown prose with its markup kept intact."""
    return run(text, translator=translator or default_translator(), level=level, seed=seed, vulgarity=vulgarity,
               variety=variety, registers=registers, regions=regions, unlock=unlock, markdown=markdown, markup=markup, english=english, embellishment=embellishment, document_type=document_type, document_config=document_config)
