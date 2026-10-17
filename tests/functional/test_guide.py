"""The style guide (data/guide.yaml): gated to the level and vulgarity, validated when read, and the one source of
the workflow, the plan's note and yarn mode's rules that every surface shows."""

import importlib
import re

import pytest
import yaml

from aussiefy import harness
from aussiefy.guide import dial_descriptions, read_style_guide, style_guide_data
from aussiefy.policy import DOCUMENT_TYPES, EMBELLISHMENT_NAMES, EMBELLISHMENTS, LEVELS, VULGARITIES
from aussiefy.schema import SchemaError
from aussiefy.loader import DATA_DIR, load_genres


def test_no_guide_carries_language_over_its_vulgarity(translator):
    d = translator.dictionary
    for level in range(1, 6):
        for vulgarity in range(4):
            g = harness.guide(level=level, vulgarity=vulgarity, translator=translator)
            words = re.findall(r"[a-z']+", f"{g['voice']} {g['language']} {g['craft']}".lower())
            rude = sorted({w for w in words if d.swear_strength(w) > vulgarity})
            assert not rude, (level, vulgarity, rude)


def test_a_light_clean_guide_has_no_performing_or_swearing_advice(translator):
    light = harness.guide(level=2, vulgarity="nan", translator=translator)["craft"]
    full = harness.guide(level=5, vulgarity="uncle-bob", embellishment="troppo", translator=translator)["craft"]
    for advice in ("perform it", "present tense", "Swear inside the sentence"):
        assert advice not in light and advice in full, advice
    assert "Australian spelling" in light and "Keep every fact" in light
    assert "2026-10-11" not in full, "provenance belongs in the YAML's comments"


@pytest.mark.parametrize("kind,config,vulgarity,expected", [
    ("general", {}, 1, 1),
    ("general", {"garnish": []}, 1, 0),
    ("custom", {}, 1, 0),
    ("news", {}, 1, 0),
    ("official", {}, 1, 0),
    ("custom", {"garnish": ["infix"]}, 1, 1),
    ("custom", {"garnish": ["infix"], "profile": {"swearing": {"infix": 0}}}, 1, 0),
    ("custom", {"garnish": ["infix"], "profile": {"swearing": {"infix": 0.3}}}, 1, 1),
    ("general", {}, 0, 0),
])
def test_infix_advice_obeys_exact_behaviour_controls(kind, config, vulgarity, expected, translator):
    from aussiefy.yarn import brief

    args = dict(level=5, vulgarity=vulgarity, embellishment="dinkum", document_type=kind,
                document_config=config, translator=translator)
    guide = harness.guide(**args)
    session = brief("The package works.", **args)
    assert guide["voice"].startswith("Full Aussie:")
    assert session.payload["LEVEL"] == 5
    for text in (guide["craft"], session.system):
        assert text.count("Swear inside the sentence") == expected


def test_the_workflow_names_each_surfaces_tools_in_order():
    data = style_guide_data()
    for surface, plan in (("cli", "aussiefy plan"), ("mcp", "aussie_plan"), ("python", "(plan)")):
        steps = data.workflow_for(surface)
        assert plan in steps and "{" not in steps, surface
        order = [steps.index(t) for t in ("guide", "plan", "lookup", "lint", "verify", "Deliver")]
        assert order == sorted(order), surface
    assert "aussie_" not in data.workflow_for("python") and "aussiefy" not in data.workflow_for("mcp")


def test_every_surface_shows_the_one_workflow(capsys):
    from aussiefy.cli import build_parser, main
    from aussiefy.mcp_server import INSTRUCTIONS

    data = style_guide_data()
    assert data.workflow_for("mcp") in INSTRUCTIONS
    flat = lambda s: " ".join(s.split())
    assert flat(data.workflow_for("cli")) in flat(build_parser().format_help())
    assert main(["guide", "-l", "3"]) == 0
    assert flat(data.workflow_for("cli")) in flat(capsys.readouterr().out)
    assert harness.guide()["workflow"] == data.workflow_for("python")
    assert harness.plan("She was very tired.")["note"] == data.plan_note


def test_yarn_mode_gets_its_rules_and_only_its_own_tools(translator):
    yarn = importlib.import_module("aussiefy.yarn")   # the package exports the yarn() function under this name

    data = style_guide_data()
    for level, vulgarity in ((2, 0), (5, None)):
        system = yarn.brief("She was very tired.", level=level, vulgarity=vulgarity, translator=translator).system
        assert data.yarn_rules in system and "{" not in system
        assert "aussie_" not in system and "aussiefy " not in system
        for tool in yarn.TOOL_ARGS:
            assert tool in data.yarn_rules, tool
        for key in re.findall(r"\b[A-Z][A-Z_]{4,}\b", data.yarn_rules):   # the brief's payload keys it names
            assert key in (yarn.brief("x", translator=translator).payload.keys() |
                           yarn.brief("# Title\n\nRun `make`.\n", markup="markdown", translator=translator).payload.keys()), key


def test_a_broken_guide_is_rejected_with_every_problem(tmp_path):
    bad = tmp_path / "guide.yaml"
    bad.write_text("""
levels: {1: a, 2: b, 3: c, 4: d}
language: {0: a, 1: b, 2: c, 3: d}
openings: [{text: So., tone: grumpy}]
craft:
- {rules: '- x', min_level: 7}
- {rules: '- y', min_vulgarity: 1, colour: red}
workflow: ['Plan it ({plna}).']
plan_note: n
yarn_rules: r
""")
    with pytest.raises(SchemaError) as exc:
        read_style_guide(bad)
    message = str(exc.value)
    for problem in ("levels:", "openings:", "min_level must be", "unknown key(s) ['colour']", "placeholder"):
        assert problem in message, problem


@pytest.mark.parametrize("patch,problem", [
    ({"openings": 3}, "openings: want a list"),
    ({"craft": False}, "craft: want a list"),
    ({"workflow": ["Read {plan.no_such_attr}."]}, "unsupported placeholder"),
    ({"workflow": ["Read {plan[0]}."]}, "unsupported placeholder"),
    ({"workflow": ["Read {plan:{unknown}}."]}, "unsupported placeholder"),
    ({"craft": [{"rules": "x", "min_level": True}]}, "min_level must be"),
    ({"craft": [{"rules": "x", "min_vulgarity": False}]}, "min_vulgarity must be"),
    ({"craft": [{"rules": "x", "heading": []}]}, "heading must be text"),
])
def test_malformed_guide_data_is_a_schema_error(tmp_path, patch, problem):
    raw = yaml.safe_load((DATA_DIR / "guide.yaml").read_text())
    raw.update(patch)
    path = tmp_path / "guide.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(SchemaError, match=problem):
        read_style_guide(path)


def test_the_dial_descriptions_cover_every_setting():
    """Every setting of every dial, by name, with its number where it has one and a line describing it."""
    dials = dial_descriptions()
    assert list(dials) == ["level", "vulgarity", "embellishment", "document_type"]
    for dial, settings in (("level", LEVELS), ("vulgarity", VULGARITIES), ("embellishment", EMBELLISHMENTS)):
        assert {name: s["value"] for name, s in dials[dial].items()} == settings, dial
    assert set(dials["document_type"]) == set(DOCUMENT_TYPES)
    assert all(s["description"].strip() for settings in dials.values() for s in settings.values())


def test_a_document_types_line_names_the_default_embellishment_its_genre_sets():
    """genres.yaml owns each document type's default embellishment; the guide's line says the same. Custom takes
    only what its document_config switches on, and auto reads the type from the text, so neither names one."""
    genres = load_genres()
    for name, line in style_guide_data().document_types.items():
        said = re.search(r"; (\w+) unless set\.$", line)
        if name in ("custom", "auto"):
            assert "unless set" not in line, name
        else:
            assert said and said.group(1).lower() == EMBELLISHMENT_NAMES[genres.policies[name].default_embellishment], \
                (name, line)
