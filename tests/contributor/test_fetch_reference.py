import sys
from pathlib import Path

import pytest

pytest.importorskip("bs4")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from aussiefy.scrape.ingest import excerpt, html_to_text  # noqa: E402

PAGE = """<html><head><script>x=1</script></head><body><nav>Menu</nav>
<p>An essay about a poem.</p>
<blockquote><p>First line of the quoted bit!<br>Second line here!</p><p>Last stanza ends here!</p></blockquote>
<p>More essay after the quote.</p></body></html>"""


def test_html_to_text_keeps_stanzas_and_drops_chrome():
    text = html_to_text(PAGE)
    assert "Menu" not in text and "x=1" not in text
    assert "First line of the quoted bit!\nSecond line here!\n\nLast stanza ends here!" in text


def test_excerpt_cuts_between_markers():
    got = excerpt(html_to_text(PAGE), "First line of", "ends here!")
    assert got.startswith("First line of") and got.rstrip().endswith("Last stanza ends here!")
    assert "essay" not in got
    with pytest.raises(ValueError):
        excerpt("nothing here", "First line", "end")
