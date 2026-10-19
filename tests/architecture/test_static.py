"""The bundled static model: its pure-Python tokenizer and vectors, and the senses it must keep apart."""

import importlib.util
import re

import pytest

from aussiefy import harness
from aussiefy.static import StaticEmbedder, bundled, dictionary_fingerprint, normalize


@pytest.fixture(scope="module")
def emb():
    return bundled()


def test_bundled_model_ships_and_loads(emb):
    assert emb is not None and emb.name.startswith("bundled:") and emb.dims == len(emb.encode("arvo"))
    assert 0.3 <= emb.lookup_threshold <= 0.8 and 0.3 <= emb.gaps_confident <= 0.8
    assert len(dictionary_fingerprint()) == 64


def test_deterministic_and_unit_length(emb):
    v = emb.encode("Fair dinkum, mate")
    assert v == StaticEmbedder().encode("Fair dinkum, mate")
    assert abs(sum(x * x for x in v) - 1) < 1e-6
    assert emb.encode("") == (0.0,) * emb.dims and emb.similarity("", "arvo") == 0.0


def test_normalizer_and_tokenizer_basics(emb):
    assert normalize("Café\tNAÏVE\x00") == "cafe naive"
    assert emb.tokenize("G'DAY") == emb.tokenize("g'day") == [emb.vocab["g'day"]]   # an added token, whole
    assert emb.tokenize("the bloke's ute")[1] == emb.vocab["bloke's"]
    assert emb.tokenize("arvo") == [emb.vocab["arvo"]]                                 # slang has its own vector


@pytest.mark.skipif(importlib.util.find_spec("tokenizers") is None, reason="needs the tokenizers package")
def test_tokenizer_matches_the_real_one(emb, dictionary):
    import json

    from tokenizers import Tokenizer

    from aussiefy.static import MODEL_DIR

    meta = json.loads((MODEL_DIR / "meta.json").read_text())
    vocab = (MODEL_DIR / "vocab.txt").read_text(encoding="utf-8").split("\n")
    spec = {"version": "1.0", "truncation": None, "padding": None, "decoder": None, "post_processor": None,
            "added_tokens": [{"id": vocab.index(t), "content": t, "single_word": False, "lstrip": True,
                              "rstrip": True, "normalized": True, "special": False} for t in meta["added_tokens"]],
            "normalizer": {"type": "BertNormalizer", "clean_text": True, "handle_chinese_chars": True,
                           "strip_accents": None, "lowercase": True},
            "pre_tokenizer": {"type": "BertPreTokenizer"},
            "model": {"type": "WordPiece", "unk_token": meta["unk_token"], "continuing_subword_prefix": "##",
                      "max_input_chars_per_word": 100, "vocab": {t: i for i, t in enumerate(vocab)}}}
    real = Tokenizer.from_str(json.dumps(spec))
    unk = vocab.index(meta["unk_token"])
    texts = {e.gloss for e in dictionary.entries.values() if e.gloss} | {e.form for e in dictionary.entries.values()}
    texts |= {"“Fair dinkum,” she said — 100%!", "日本語 text", "emoji 🦘 roo", "a" * 150, "it’s Macca's"}
    for t in sorted(texts):
        assert emb.tokenize(t) == [i for i in real.encode(t, add_special_tokens=False).ids if i != unk], t


def test_meaning_not_spelling(emb):
    assert emb.similarity("arvo", "The afternoon.") > emb.lookup_threshold
    assert emb.similarity("knackered", "Exhausted, worn out.") > emb.similarity("knackered", "A barbecue.")


def test_wrong_senses_stay_apart(translator):
    girl = harness.lookup("girl", translator=translator)["results"]
    assert "sheila" not in [r["form"] for r in girl]
    war = harness.lookup("a great war", translator=translator)["results"]
    excellent = {e.form for e in translator.dictionary.entries.values() if "EXCELLENT" in e.concept}
    assert not excellent & {r["form"] for r in war}


@pytest.mark.parametrize(("query", "matches"), [
    ("knackered beyond belief", {"meaning", "meaning (local model)"}),
    ("physically exhausted beyond endurance", {"meaning (local model)"}),
])
def test_lookup_finds_slang_by_meaning(translator, query, matches):
    res = harness.lookup(query, translator=translator)["results"]
    tired = {e.form for e in translator.dictionary.entries.values() if "TIRED" in e.concept}
    assert any(r["form"] in tired and r["match"] in matches for r in res)


def test_shipped_model_meets_the_reference_set(dictionary):
    """training/reference.yaml's required checks, as `scripts/train_embedder.py check` runs them."""
    pytest.importorskip("numpy")
    import sys

    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import train_embedder as t

    t.R = t.load_recipe()
    emb = bundled()
    ref = t.reference(dictionary, t.Bundled(), emb.lookup_threshold)
    failed = [r["query"] for r in ref["checks"] if not r["pass"] and not r["known"]]
    # strict even while the model is stale against the dictionary: a dictionary change that breaks a required
    # check needs a retrain (or the check moved to `known`, with a reason), not a silent xfail
    assert not failed, f"{emb.name} fails reference checks{' (stale: retrain)' if emb.stale() else ''}: {failed}"


def test_meta_records_version_and_provenance(emb):
    assert re.fullmatch(r"\d+\.\d+\.\d+", emb.meta.get("version") or ""), emb.meta.get("version")
    assert emb.name.endswith(emb.meta["version"])
    for key in ("dictionary_sha256", "vectors_sha256", "recipe", "toolchain", "evaluation", "reference"):
        assert key in emb.meta, key


def test_the_fingerprint_covers_every_entry_file_the_loader_reads(tmp_path):
    (tmp_path / "entries").mkdir()
    (tmp_path / "concepts.yaml").write_text("A: {}\n")
    (tmp_path / "entries" / "a.yaml").write_text("- {id: a}\n")
    before = dictionary_fingerprint(tmp_path)
    (tmp_path / "entries" / "b.yml").write_text("- {id: b}\n")
    assert dictionary_fingerprint(tmp_path) != before
