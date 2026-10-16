"""Optional Anthropic API client for the agent-neutral retelling harness.

Shared briefs, tool contracts, validation and dispatch live in retelling.py. The legacy imports below
remain available for existing CLI, Python and research callers.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from . import claude
from .claude import DEFAULT_MODEL
from .engine import Translator
from .errors import UserError
from .retelling import (
    YarnSession as YarnSession, YARN_SYSTEM as YARN_SYSTEM, TOOL_ARGS as TOOL_ARGS,
    VALIDATION_VERSION, brief as brief, dispatch_tool as dispatch_tool,
    validate as validate, tool_contracts, _moved as _moved,
)


def tool_definitions() -> list[dict[str, Any]]:
    """Adapt the shared retelling contracts to Anthropic Messages API tool definitions."""
    return [{"name": tool["name"], "description": tool["description"], "strict": True,
             "input_schema": tool["schema"]} for tool in tool_contracts()]

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
        invalid_cache = f"{store.directory / (key + '.json')}: invalid yarn cache entry; delete it"
        if not isinstance(cached, dict):
            raise UserError(invalid_cache)
        declined, calls = cached.get("declined", []), cached.get("tool_calls", {})
        if (not isinstance(cached.get("text"), str)
                or not isinstance(declined, list)
                or any(not isinstance(d, dict) or not isinstance(d.get("phrase"), str)
                       or not isinstance(d.get("reason"), str) for d in declined)
                or not isinstance(calls, dict)
                or any(not isinstance(name, str) or type(count) is not int or count < 0
                       for name, count in calls.items())):
            raise UserError(invalid_cache)
        if not validate(session, cached["text"], declined):
            result.text, result.status, result.tool_calls = cached["text"], "yarned (cached)", calls
            result.declined, result.outcome = declined, "applied"
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
