"""Bounded plain-text regression coverage for the licensed everyday corpus.

Document syntax protection belongs to the planned Markdown adapter, not the plain-text engine.
"""

from pathlib import Path

import pytest
import yaml

CORPUS = Path(__file__).parents[1] / "corpus" / "everyday"
GROUPS = ("instructions", "news", "conversational", "workplace")


def sources():
    for group in GROUPS:
        directory = CORPUS / group if group in ("conversational", "workplace") else CORPUS
        for row in yaml.safe_load((CORPUS / f"{group}.yaml").read_text(encoding="utf-8")):
            if row["file"] is not None:
                yield directory / row["file"]


@pytest.mark.parametrize("path", list(sources()), ids=lambda p: p.name)
def test_everyday_translation_retains_source_and_is_repeatable(translator, path):
    source = path.read_text(encoding="utf-8")
    assert source.strip()
    for level, seed in ((1, 0), (3, 7), (5, 19)):
        first = translator.translate(source, level=level, vulgarity=0, seed=seed, embedder="none")
        again = translator.translate(source, level=level, vulgarity=0, seed=seed, embedder="none")
        assert first.to_dict() == again.to_dict()
        assert first.source == source
        assert first.text.strip()
        if path.suffix == ".txt":
            assert first.text.count("\n") == source.count("\n")
        for record in first.records:
            start, end = record.span
            assert source[start:end] == record.text


def test_everyday_manifests_cover_exactly_the_committed_input_files():
    declared = list(sources())
    actual = {p for group in GROUPS for p in (CORPUS / group).iterdir() if p.suffix in (".txt", ".md")}
    assert len(declared) == len(set(declared))
    assert set(declared) == actual
