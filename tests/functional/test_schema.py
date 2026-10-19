import pytest

from aussiefy.loader import load_dictionary
from aussiefy.schema import SchemaError, parse_entry

BASE = {"id": "x", "form": "x", "concept": ["BUSY"], "frame": "np"}


def entry(**kw):
    return parse_entry({**BASE, **kw})


def test_minimal_entry_defaults():
    e = entry()
    assert e.status == "active" and e.vulgarity == 0 and e.incoherence == 1
    assert e.substitution_class == "lexical"


@pytest.mark.parametrize("kw, msg", [
    ({"frame": "noun"}, "frame must be one of"),
    ({"status": "maybe"}, "status must be one of"),
    ({"intensity": 9}, "intensity"),
    ({"vulgarity": -1}, "vulgarity"),
    ({"form": "{who} reckons"}, "unknown slot"),
    ({"flags": ["slur"]}, "must have status omit"),
    ({"flags": ["spicy"]}, "unknown flag"),
    ({"frame": "clause", "form": "a {subj} thing"}, "must start with {subj}"),
    ({"form": "{subj} {be} off"}, "only clause frames"),
    ({"concept": []}, "at least one concept"),
    ({"colour": "red"}, "unknown field"),
    ({"id": "Not Kebab"}, "kebab-case"),
    ({"placement": "opener"}, "only valid on garnish"),
    ({"type": "garnish"}, "garnish entries need placement"),
    ({"flags": ["untagged"], "concept": []}, "untagged entries cannot be active"),
    ({"variants": ["ok", 3]}, "'variants' must be a list of strings"),
    ({"concept": [["BUSY"]]}, "'concept' must be a list of strings"),
    ({"type": "garnish", "placement": "closer", "stretch": "no"}, "'stretch' must be true or false"),
])
def test_validation_errors(kw, msg):
    with pytest.raises(SchemaError, match=msg.replace("{", r"\{").replace("}", r"\}")):
        entry(**kw)


def test_slots_inferred_from_form():
    e = entry(frame="clause", form="{subj} {have} a roo loose in {poss} paddock")
    assert e.slots == {"subj": "pronoun", "have": "verb_agree", "poss": "possessive"}


def test_slot_inference_does_not_mutate_the_input():
    raw = {**BASE, "form": "{poss} thing", "slots": {"obj": "object_pronoun"}}
    parsed = parse_entry(raw)
    assert parsed.slots == {"obj": "object_pronoun", "poss": "possessive"}
    assert raw["slots"] == {"obj": "object_pronoun"}


def test_substitution_class():
    assert entry(form="no worries", frame="interjection").substitution_class == "phrase"
    assert entry(form="flat chat", frame="predicate_adj").substitution_class == "idiom"
    assert entry(form="flat chat", frame="predicate_adj", **{"class": "phrase"}).substitution_class == "phrase"


def test_builtin_dictionary_loads_cleanly(dictionary):
    assert len(dictionary.entries) > 200
    assert not dictionary.warnings, dictionary.warnings
    assert sorted(dictionary.profiles) == [1, 2, 3, 4, 5]


def test_builtin_dictionary_is_identical_without_libyaml(monkeypatch, dictionary):
    import yaml
    from aussiefy import loader

    monkeypatch.setattr(loader, '_YAML_LOADER', yaml.SafeLoader)
    fallback = loader.load_dictionary()
    assert fallback.entries == dictionary.entries
    assert fallback.concepts == dictionary.concepts
    assert fallback.profiles == dictionary.profiles
    assert fallback.imagery == dictionary.imagery
    assert fallback.warnings == dictionary.warnings


def test_loader_rejects_unknown_concept_and_duplicates(tmp_path):
    f = tmp_path / "extra.yaml"
    f.write_text("- {id: mate, form: cobba, concept: [FRIEND], frame: np}\n"
                 "- {id: new-one, form: thing, concept: [NOT_A_CONCEPT], frame: np}\n")
    with pytest.raises(SchemaError) as exc:
        load_dictionary([f])
    assert "duplicate id 'mate'" in str(exc.value)
    assert "unknown concept 'NOT_A_CONCEPT'" in str(exc.value)


def test_extra_dictionary_file_extends(tmp_path, dictionary):
    f = tmp_path / "extra.yaml"
    f.write_text("- {id: bonzer-test, form: bonzer-test, concept: [BREAKFAST], frame: np, weight: 50}\n")
    d = load_dictionary([f])
    assert "bonzer-test" in d.entries and len(d.entries) == len(dictionary.entries) + 1


def test_to_dict_round_trips(dictionary):
    for e in dictionary.entries.values():
        again = parse_entry(e.to_dict(), origin=e.origin_file)
        assert again.to_dict() == e.to_dict()


def test_a_form_lint_cannot_match_is_a_load_error(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- {id: zzslot, form: '!zz thing', concept: [TIRED], frame: predicate_adj}\n")
    with pytest.raises(SchemaError, match="zzslot: form"):
        load_dictionary([bad])


def test_swear_strength_reads_swears_yaml():
    d = load_dictionary()
    assert d.swear_strength("bloody") >= 1 and d.swear_strength("Bloody") == d.swear_strength("bloody")
    assert d.swear_strength("tired") == 0 and d.dialect.swaps


def test_a_dictionary_without_the_grammar_rules_concepts_is_refused():
    from aussiefy.engine import Translator

    d = load_dictionary()
    del d.concepts["VERY"]
    with pytest.raises(SchemaError, match="VERY"):
        Translator(d)


def test_to_dict_lists_keys_in_entry_keys_order(dictionary):
    from aussiefy.schema import ENTRY_KEYS

    for e in dictionary.entries.values():
        keys = list(e.to_dict())
        assert keys == [k for k in ENTRY_KEYS if k in keys], e.id


def test_a_bad_list_item_is_collected_with_the_other_errors(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- {id: zzone, form: x, concept: [TIRED], frame: np, variants: [1]}\n"
                   "- {id: zztwo, form: y, concept: [NOPE], frame: np}\n")
    with pytest.raises(SchemaError) as exc:
        load_dictionary([bad])
    assert "zzone: 'variants' must be a list of strings" in str(exc.value) and "unknown concept 'NOPE'" in str(exc.value)


def test_a_data_dir_missing_a_lint_file_fails_closed(tmp_path):
    """Lint's swearing, US words and spelling come from these files: a missing one is an error, not no checks."""
    import shutil

    from aussiefy.loader import DATA_DIR

    data = tmp_path / "data"
    shutil.copytree(DATA_DIR, data)
    (data / "swears.yaml").unlink()
    (data / "riffs.yaml").write_text("bad: [unclosed\n")
    profiles = data / "profiles.yaml"
    profiles.write_text(profiles.read_text().replace("riff: 0.5,", "rifff: 0.5,"))
    with pytest.raises(SchemaError) as exc:
        load_dictionary(data_dir=data)
    message = str(exc.value)
    assert "swears.yaml: missing" in message and "riffs.yaml: invalid YAML" in message
    assert "unknown garnish key(s) ['rifff']" in message


def test_entry_files_are_the_data_dirs_entries():
    from aussiefy.loader import DATA_DIR, entry_files

    assert entry_files() == sorted((DATA_DIR / "entries").glob("*.yaml")) and entry_files(DATA_DIR)
