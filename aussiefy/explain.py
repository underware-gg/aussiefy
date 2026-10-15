"""Human-readable explain report."""

from __future__ import annotations

from .engine import Result
from .markdown import DocumentResult
from .select import Gated


def _reason(reason: str) -> str:
    """A rejection as the CLI says it: a gate names the --unlock that lifts it."""
    if isinstance(reason, Gated):
        return f"{reason}; unlock with --unlock {','.join(reason.locked) or 'all'}"
    return reason


def format_explain(result: Result | DocumentResult, show_rejected: bool = True, max_rejected: int = 12) -> str:
    if isinstance(result, DocumentResult):
        lines = [f"Markdown: level {result.level}, seed {result.seed}",
                 "Source spans use document character offsets; decisions are relative to each prose unit."]
        for unit in result.units:
            lines += ["", f"prose [{unit.source_span[0]}:{unit.source_span[1]}] -> "
                      f"output [{unit.output_span[0]}:{unit.output_span[1]}]", "rendered: " + unit.text,
                      format_explain(unit.result, show_rejected, max_rejected)]
        return "\n".join(lines)
    g = result.genre
    scores = ", ".join(f"{k} {v:g}" for k, v in sorted(g.scores.items(), key=lambda kv: -kv[1]))
    lines = [f"level {result.level}, seed {result.seed}, mood {result.mood}",
             f"genre {g.name} ({scores}); embellishment {result.embellishment.name}: garnish "
             f"{', '.join(sorted(result.embellishment.garnish)) or 'none'}"
             + ("" if g.policy.person_swears else "; no swears for people"), ""]
    if result.surface:
        lines += [f"deterministic: {result.deterministic_text}",
                  f"surface ({result.surface.get('model')}): {result.surface.get('status')}", ""]
    lines.append("substitutions:")
    if not result.records:
        lines.append("  (no concepts detected)")
    for r in result.records:
        d = r.det
        how = f'{d.method} "{d.pattern}"' + (f" (similarity {d.score:.2f})" if d.method == "embedding" else "")
        head = f'  [{r.span[0]}:{r.span[1]}] "{r.text}"'
        if r.substituted:
            head += f' -> "{r.output}"'
        lines.append(head)
        caps = ", ".join(f"{k}={v}" for k, v in d.describe_captures().items())
        lines.append(f"      concept {'/'.join(d.concepts)}, frame {d.frame}, intensity {d.intensity}, via {how}"
                     + (f"; captures {caps}" if caps else ""))
        lines.append(f"      {r.decision}")
        total = sum(c.weight for c in r.eligible) or 1.0
        if r.chosen:
            lines.append(f"      chosen {r.chosen.entry.id} (p={r.chosen.weight / total:.2f}): {r.chosen.why}")
        if r.stacked:
            lines.append(f"      stacked {r.stacked.entry.id}")
        others = [f"{c.entry.id} {c.weight / total:.2f}" for c in r.eligible if c is not r.chosen]
        if others:
            lines.append(f"      other candidates: {', '.join(others)}")
        if show_rejected and r.rejected:
            shown = r.rejected[:max_rejected]
            lines.append("      rejected:")
            lines += [f"        - {i}: {_reason(reason)}" for i, reason in shown]
            if len(r.rejected) > len(shown):
                lines.append(f"        ... and {len(r.rejected) - len(shown)} more")
    if result.rewrites:
        lines += ["", "whole-sentence rewrites:"]
        for w in result.rewrites:
            lines.append(f"  sentence {w.sentence} ({w.model}): {w.status}; {w.reason}")
            if w.output:
                lines.append(f'      "{w.output}"')
    if result.garnish:
        lines += ["", "garnish:"]
        for g in result.garnish:
            what = f'"{g.text}" ({g.entry_id})' if g.text else "(none)"
            lines.append(f"  {g.placement:<6} sentence {g.sentence}: {what}; {g.decision}")
    if result.dialect:
        lines += ["", f"dialect ({result.english or 'English not known'}):"]
        lines += [f'  "{d.before}" -> "{d.after}" ({d.english}), sentence {d.sentence}' for d in result.dialect]
    if result.phonetic:
        lines += ["", "phonetic:"]
        for p in result.phonetic:
            lines.append(f'  {p.rule}: "{p.before}" -> "{p.after}" at {p.offset}')
    return "\n".join(lines)
