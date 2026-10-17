"""The style guide: what each level sounds like, what language each vulgarity allows, ways to open a yarn, the
craft rules that make a retelling read naturally, the toolkit workflow, what plan's result is for and yarn mode's
rules. The content is data (data/guide.yaml), read and validated here; this module serves it resolved to a level
and vulgarity, and with each surface's tool names."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from string import Formatter
from typing import Any

from .engine import Translator, default_translator
from .loader import DATA_DIR, _read
from .genre import resolve_document
from .policy import DOCUMENT_TYPES, EMBELLISHMENTS, LEVELS, VULGARITIES, roll
from .schema import SchemaError

# The toolkit's operations, and each surface's name for them: the workflow's {plan} is `aussiefy plan` on the
# command line, `aussie_plan` over MCP and `plan` in Python.
TOOLS = ("guide", "plan", "lookup", "lint", "verify", "translate")
SURFACES = {"cli": "aussiefy {}", "mcp": "aussie_{}", "python": "{}"}
TONES = ("plain", "chirpy")   # chirpy openings are left out for dark and solemn texts


@dataclass(frozen=True)
class CraftSection:
    """Craft rules that apply from min_level, when the vulgarity is at least min_vulgarity."""
    rules: str
    heading: str = ""
    min_level: int = 1
    min_vulgarity: int = 0
    requires_performance: bool = False
    requires_infix: bool = False


@dataclass(frozen=True)
class StyleGuide:
    levels: dict[int, str]          # level 1-5 -> what it sounds like
    language: dict[int, str]        # vulgarity 0-3 -> what language it allows
    embellishments: dict[int, str]  # embellishment 0-2 -> what it adds, in a line
    document_types: dict[str, str]  # document type -> what it keeps and how, in a line
    openings: tuple[tuple[str, str], ...]   # (text, tone)
    craft: tuple[CraftSection, ...]
    workflow: tuple[str, ...]       # steps, with {tool} placeholders
    plan_note: str
    yarn_rules: str

    def craft_for(self, level: int, vulgarity: int, *, perform: bool = False, infix: bool = True) -> str:
        """The craft rules for a level and vulgarity: a clean or light guide carries no swearing or level-5 advice."""
        return "\n\n".join(f"{s.heading}\n{s.rules}" if s.heading else s.rules for s in self.craft
                           if level >= s.min_level and vulgarity >= s.min_vulgarity and (perform or not s.requires_performance) and (infix or not s.requires_infix))

    def workflow_for(self, surface: str) -> str:
        """The workflow as numbered steps, with a surface's tool names ("cli", "mcp" or "python")."""
        names = {t: SURFACES[surface].format(t) for t in TOOLS}
        return "\n".join(f"{i}. {step.format(**names)}" for i, step in enumerate(self.workflow, 1))


def read_style_guide(path: Path = DATA_DIR / "guide.yaml") -> StyleGuide:
    """guide.yaml, validated: every level and vulgarity described, sections gated by real ones, and every
    workflow step renderable on every surface. All problems are reported at once."""
    errors: list[str] = []
    raw = _read(path, errors, {})

    def texts(key: str, expected: set) -> dict:
        got = raw.get(key)
        if (not isinstance(got, dict) or set(got) != expected
                or any(type(k) is not type(next(iter(expected))) for k in got)
                or not all(isinstance(v, str) and "\n" not in v.strip() for v in got.values())):
            errors.append(f"{key}: want a description for each of {sorted(expected)}")
            return {}
        return got

    def text(key: str) -> str:
        if not isinstance(raw.get(key), str):
            errors.append(f"{key}: want text")
            return ""
        return raw[key]

    levels, language = texts("levels", set(LEVELS.values())), texts("language", set(VULGARITIES.values()))
    embellishments = texts("embellishments", set(EMBELLISHMENTS.values()))
    document_types = texts("document_types", set(DOCUMENT_TYPES))

    def items(key: str) -> list:
        value = raw.get(key, [])
        if not isinstance(value, list):
            errors.append(f"{key}: want a list")
            return []
        return value

    openings = []
    for o in items("openings"):
        if not isinstance(o, dict) or not isinstance(o.get("text"), str) or o.get("tone", "plain") not in TONES:
            errors.append(f"openings: {o!r}: want text and a tone ({', '.join(TONES)})")
        else:
            openings.append((o["text"], o.get("tone", "plain")))
    craft = []
    for i, s in enumerate(items("craft")):
        where = f"craft section {i + 1}"
        if not isinstance(s, dict) or not isinstance(s.get("rules"), str):
            errors.append(f"{where}: want a mapping with rules")
            continue
        unknown = set(s) - set(CraftSection.__dataclass_fields__)
        if unknown:
            errors.append(f"{where}: unknown key(s) {sorted(map(str, unknown))}")
        if not isinstance(s.get("heading", ""), str):
            errors.append(f"{where}: heading must be text")
        if type(s.get("min_level", 1)) is not int or s.get("min_level", 1) not in LEVELS.values():
            errors.append(f"{where}: min_level must be a level 1-5, not {s['min_level']!r}")
        if type(s.get("min_vulgarity", 0)) is not int or s.get("min_vulgarity", 0) not in VULGARITIES.values():
            errors.append(f"{where}: min_vulgarity must be a vulgarity 0-3, not {s['min_vulgarity']!r}")
        craft.append(CraftSection(**{k: v for k, v in s.items() if k in CraftSection.__dataclass_fields__}))
    workflow = raw.get("workflow")
    if not isinstance(workflow, list) or not workflow or not all(isinstance(w, str) for w in workflow):
        errors.append("workflow: want a list of steps")
        workflow = []
    guide = StyleGuide(levels, language, embellishments, document_types, tuple(openings), tuple(craft), tuple(workflow), text("plan_note"),
                       text("yarn_rules"))
    for step in workflow:
        try:
            for _, name, spec, conversion in Formatter().parse(step):
                if name is not None and (name not in TOOLS or spec or conversion):
                    raise ValueError(f"unsupported placeholder {name!r}")
        except ValueError as exc:
            errors.append(f"workflow: a placeholder isn't one of {', '.join(TOOLS)}: {exc}")
    if errors:
        raise SchemaError(f"{path} failed validation:\n  " + "\n  ".join(errors))
    return guide


@lru_cache(maxsize=1)
def style_guide_data() -> StyleGuide:
    return read_style_guide()


def dial_descriptions() -> dict[str, dict[str, dict[str, Any]]]:
    """Every dial's settings by name, each with its number (where it has one) and a description: level, vulgarity
    and embellishment, and the document types. What a page or a host lists as the settings (guide.yaml)."""
    g = style_guide_data()
    return {"level": {name: {"value": n, "description": g.levels[n]} for name, n in LEVELS.items()},
            "vulgarity": {name: {"value": n, "description": g.language[n]} for name, n in VULGARITIES.items()},
            "embellishment": {name: {"value": n, "description": g.embellishments[n]}
                              for name, n in EMBELLISHMENTS.items()},
            "document_type": {name: {"description": text} for name, text in g.document_types.items()}}


def openings(text: str, seed: int = 0, mood: str = "light", n: int = 3) -> list[str]:
    """Three ways to open this text, picked by seed and text so different pieces start differently ("Right, so"
    opened 16 of 18 retellings when nothing steered it); chirpy ones only for light texts."""
    pool = [t for t, tone in style_guide_data().openings if mood == "light" or tone != "chirpy"]
    return sorted(pool, key=lambda o: roll(seed, "opening", text[:300], o))[:n]


def guide(*, level: int | str = 5, vulgarity: int | str | None = None, embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None,
          translator: Translator | None = None) -> dict[str, Any]:
    """The voice, language limits and craft rules for a level and vulgarity, and the toolkit workflow."""
    tr = translator or default_translator()
    eff = tr.effective(level=level, vulgarity=vulgarity, document_config=document_config)
    data = style_guide_data()
    pol = tr.policy(embellishment=embellishment, document_type=document_type, document_config=document_config)
    context = resolve_document(None, config=tr.dictionary.genres, document_type=pol.document_type,
                               document_config=pol.document_config)
    e = context.setting(pol.embellishment)
    return {**eff.envelope(), **context.envelope(pol.embellishment),
            "embellishment": e.step, "embellishment_name": e.name, "embellishment_guidance": e.guidance,
            "voice": data.levels[eff.level], "language": data.language[eff.vulgarity],
            "craft": data.craft_for(eff.level, eff.vulgarity, perform=e.perform,
                                     infix=e.takes("infix") and eff.swearing.infix > 0),
            "workflow": data.workflow_for("python")}
