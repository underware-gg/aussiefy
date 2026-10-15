"""The one place aussiefy talks to Claude: the client, the request shape, JSON replies and the on-disk cache.

The surface rewrite, the sentence rewriter, yarn mode and dev tag all go through here. The SDK is optional
(pip install aussiefy[llm]). Every way Claude can fail to give a usable reply raises a claude.Error, and callers
catch that alone, so a bug in aussiefy still raises:
    Unavailable  no SDK, no credentials, or the API failed (network, auth, rate limits, server errors)
    Refused      the model declined
    BadReply     the reply isn't what was asked for (no text, truncated at max_tokens, not the JSON asked for)
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import UserError

DEFAULT_MODEL = "claude-opus-5-5"
BETAS = ["server-side-fallback-2026-07-01"]


class Error(Exception):
    """Claude gave no usable reply; the caller keeps what it had (the engine's draft)."""


class Unavailable(Error):
    """No SDK, no credentials, or the API call failed."""


class Refused(Error):
    """The model declined the request."""


class BadReply(Error):
    """The reply isn't the one asked for."""


def client() -> Any:
    try:
        import anthropic  # optional dependency: pip install aussiefy[llm]
    except ImportError as exc:
        raise Unavailable("the anthropic SDK isn't installed: "
                          "pip install \"aussiefy[llm] @ git+https://github.com/underware-gg/aussiefy\"") from exc
    return anthropic.Anthropic()


def _cached(text: str) -> dict[str, Any]:
    """A text block with a prompt-caching breakpoint after it."""
    return {"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}


def create(cl: Any, *, model: str, system: str | list[dict], messages: list[dict], max_tokens: int,
           effort: str = "low", schema: dict | None = None, tools: list[dict] | None = None,
           cache: bool = False) -> Any:
    """One Messages API call with server-side fallback; schema asks for a JSON reply, tools for tool use, and
    cache caches the conversation for the turns of a loop: the stable prefix (tools, system prompt, the first
    message) and, through automatic caching, everything up to the latest turn."""
    output: dict[str, Any] = {"effort": effort}
    if schema is not None:
        output["format"] = {"type": "json_schema", "schema": schema}
    kwargs: dict[str, Any] = {"tools": tools} if tools else {}
    sys_param: Any = system
    if cache:
        # three of the four breakpoints a request may carry, all at the default TTL: after the system prompt (tools
        # come before it), after the first message (the brief: a read point that holds however much one turn
        # adds, where the automatic one looks back only 20 blocks), and the automatic one on the last block,
        # which moves forward as the conversation grows
        sys_param = [_cached(system)]
        first = messages[0]
        if isinstance(first.get("content"), str):
            messages = [{**first, "content": [_cached(first["content"])]}, *messages[1:]]
        kwargs["cache_control"] = {"type": "ephemeral"}
    try:
        return cl.beta.messages.create(model=model, max_tokens=max_tokens, betas=BETAS, fallbacks="default",
                                       system=sys_param, messages=messages, output_config=output, **kwargs)
    except Exception as exc:
        if _is_api_failure(exc):
            raise Unavailable(f"{type(exc).__name__}: {exc}") from exc
        raise


def _is_api_failure(exc: Exception) -> bool:
    """The SDK's own failures: anthropic.APIError (network, auth, rate limits, server errors), and the TypeError it
    raises when it finds no credentials at request time. Anything else from the call is a bug of ours."""
    try:
        import anthropic
    except ImportError:
        return False
    return isinstance(exc, anthropic.APIError) or (isinstance(exc, TypeError) and "authentication" in str(exc))


def json_reply(response: Any, required: tuple[str, ...] = ()) -> dict:
    """The JSON object a schema-constrained reply carries, with the keys it must have."""
    if response.stop_reason == "refusal":
        raise Refused("model declined")
    if response.stop_reason == "max_tokens":
        raise BadReply("reply truncated at max_tokens")
    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise BadReply("reply has no text")
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BadReply(f"reply isn't JSON: {exc}") from exc
    missing = [k for k in required if not isinstance(obj, dict) or k not in obj]
    if missing:
        raise BadReply(f"reply lacks {', '.join(missing)}")
    return obj


def call_json(cl: Any, *, model: str, system: str, prompt: str, schema: dict, max_tokens: int = 4000,
              effort: str = "low", cache: bool = False) -> dict:
    """Send one user message and return the reply's JSON object (with the schema's required keys). cache marks
    the system prompt for prompt caching, for many calls that share it: only the system prompt, since a
    breakpoint after a prompt that differs every call would write a cache entry no call reads."""
    return json_reply(create(cl, model=model, system=[_cached(system)] if cache else system,
                             messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens, effort=effort,
                             schema=schema), tuple(schema.get("required", ())))


def default_cache_dir(kind: str) -> Path:
    """Where one kind of cached data (accepted replies, fetched pages) is kept unless the caller says otherwise:
    the aussiefy home's cache."""
    from .models import home

    return home() / "cache" / kind


class Cache:
    """Accepted replies on disk, keyed by everything that decides them, so a run is reproducible offline.
    directory=None turns caching off."""

    def __init__(self, directory: str | Path | None):
        self.directory = Path(directory) if directory else None

    @staticmethod
    def key(*parts: Any) -> str:
        return hashlib.sha256(json.dumps(list(parts), sort_keys=True, default=str).encode()).hexdigest()[:24]

    def get(self, key: str) -> dict | None:
        path = self.directory / f"{key}.json" if self.directory else None
        if not (path and path.exists()):
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:   # not a miss: say which file, so it can be deleted
            raise UserError(f"{path}: corrupt cache entry ({exc}); delete it") from exc

    def put(self, key: str, value: dict) -> None:
        """Write atomically, so an interrupted run never leaves a half-written entry."""
        if self.directory:
            self.directory.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self.directory, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(value, fh, ensure_ascii=False, indent=1, default=str)
            os.replace(tmp, self.directory / f"{key}.json")
