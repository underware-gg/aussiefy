"""Well-formedness checks on copyrighted texts kept locally in tests/corpus/local/ (gitignored).

Drop any .txt file there (e.g. Ginsberg's "Meditations on Moloch") and these run on it; with the folder
empty they skip, so the shared repo never needs the text.
"""

import re
from pathlib import Path

import pytest

from aussiefy.context import sentence_contexts
from aussiefy.text import tokenize

LOCAL = Path(__file__).resolve().parents[1] / "corpus" / "local"
FILES = sorted(LOCAL.glob("*.txt"))


@pytest.mark.skipif(not FILES, reason="no local reference texts; run aussiefy dev ingest tests/corpus/remote.yaml")
@pytest.mark.parametrize("path", FILES, ids=[p.stem for p in FILES])
def test_local_text_well_formed(translator, path):
    src = path.read_text(encoding="utf-8")
    for level in range(1, 6):
        for seed in range(10):
            r = translator.translate(src, level=level, seed=seed)
            out, where = r.text, f"{path.stem} L{level} s{seed}"
            assert out.count("\n") == src.count("\n"), f"{where}: line structure changed"
            assert not re.search(r"[.!?,]\s*[.,]|,\s*[!?]|\.\"\.|\s,", out), f"{where}: broken punctuation"
            for g in r.garnish:   # tags only where someone is addressed
                if g.placement == "tag" and g.text:
                    a, b = r.sentences[g.sentence]
                    said = sentence_contexts(tokenize(src[a:b]))
                    assert said & {"dialogue", "question", "second_person"}, f"{where}: tag on {src[a:b]!r}"
            if level >= 3:
                assert sum(x.substituted for x in r.records) >= 1, f"{where}: nothing Aussified"


@pytest.mark.skipif(not (LOCAL / "moloch.txt").exists(),
                    reason="moloch.txt not present; run aussiefy dev ingest tests/corpus/remote.yaml")
def test_moloch_specifics(translator):
    src = (LOCAL / "moloch.txt").read_text(encoding="utf-8")
    outs = [translator.translate(src, level=5, seed=s).text for s in range(10)]
    assert all("screams blue murder" not in o for o in outs), "'animal screams' is a noun"
    assert all(", mate!" not in o and ", ay!" not in o and ", cobber!" not in o for o in outs), \
        "no tag-ons on lines nobody is addressed in"
    assert any("Ankle biters" in o or "Littlies" in o for o in outs)
    assert any("bulldust" in o for o in outs)
