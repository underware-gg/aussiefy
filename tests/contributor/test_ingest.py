"""aussiefy dev ingest: a manifest of sources in, local files out; conversion is pure, the network injected."""

from pathlib import Path

import pytest
import yaml

from aussiefy.errors import UserError
from aussiefy.scrape.fetch import FetchError
from aussiefy.scrape.ingest import Manifest, Source, convert, excerpt, ingest

CORPUS = Path(__file__).resolve().parents[1] / "corpus"
PAGE = """<html><head><script>x=1</script></head><body><nav>Menu</nav>
<p>An essay about a poem.</p>
<blockquote><p>First line of the quoted bit!<br>Second line here!</p><p>Last stanza ends here!</p></blockquote>
<p>More essay after the quote.</p></body></html>"""


def test_a_page_becomes_its_readable_text_cut_at_the_markers():
    pytest.importorskip("bs4")
    page = Source("poem", "https://example.org/essay", raw=False, suffix=".txt",
                  start="First line of", end="ends here!")
    text = convert(page, PAGE)
    assert text == "First line of the quoted bit!\nSecond line here!\n\nLast stanza ends here!\n"
    whole = convert(Source("essay", "https://example.org/essay", raw=False, suffix=".txt"), PAGE)
    assert "Menu" not in whole and "x=1" not in whole and whole.startswith("An essay")


def test_a_raw_file_is_kept_verbatim():
    doc = "---\ntitle: A\n---\r\n\r\n# Hi\r\n\r\n```sh\nmake\n```\n"
    src = Source.from_item({"name": "a", "path": "docs/a.mdx"}, {"repo": "o/r", "ref": "abc"})
    assert src.url == "https://raw.githubusercontent.com/o/r/abc/docs/a.mdx" and src.filename == "a.mdx"
    assert convert(src, doc) == doc


def test_excerpt_needs_both_markers():
    with pytest.raises(ValueError):
        excerpt("nothing here", "First line", "end")
    with pytest.raises(UserError, match="both start and end"):   # a manifest problem, caught before fetching
        Source.from_item({"name": "x", "url": "https://e.org/x.txt", "start": "a"}, {})


def test_items_need_a_name_and_a_source():
    with pytest.raises(UserError):
        Source.from_item({"url": "https://e.org"}, {})
    with pytest.raises(UserError):
        Source.from_item({"name": "x"}, {})
    with pytest.raises(UserError):
        Source.from_item({"name": "x", "path": "a.md"}, {"repo": "o/r"})     # no ref


def test_ingest_saves_skips_and_reports_failures(tmp_path):
    (tmp_path / "m.yaml").write_text(yaml.safe_dump({"out": "out", "defaults": {"repo": "o/r", "ref": "v1"}, "items": [
        {"name": "good", "path": "good.md"}, {"name": "gone", "path": "gone.md"}]}))
    pages = {"https://raw.githubusercontent.com/o/r/v1/good.md": "# Good\n"}

    def fetch(url):
        if url not in pages:
            raise FetchError(f"{url}: 404")
        return pages[url]

    m = Manifest.load(tmp_path / "m.yaml")
    first = {o.source.name: o for o in ingest(m, fetch)}
    assert first["good"].status == "saved" and (tmp_path / "out" / "good.md").read_text() == "# Good\n"
    assert first["gone"].status == "failed" and "404" in first["gone"].error
    pages["https://raw.githubusercontent.com/o/r/v1/good.md"] = "# Changed\n"
    assert {o.source.name: o.status for o in ingest(m, fetch)}["good"] == "present"
    assert ingest(m, fetch, force=True)[0].status == "saved"
    assert (tmp_path / "out" / "good.md").read_text() == "# Changed\n"
    assert Manifest.load(tmp_path / "m.yaml", ref="main").sources[0].url.endswith("/o/r/main/good.md")


@pytest.mark.parametrize("manifest", sorted(CORPUS.rglob("*remote.yaml")) + [CORPUS / "everyday" / "interfold.yaml"],
                         ids=lambda p: p.name)
def test_the_corpus_manifests_load(manifest):
    m = Manifest.load(manifest)
    assert m.sources and all(s.url.startswith("https://") for s in m.sources)
    assert len({s.filename for s in m.sources}) == len(m.sources)


@pytest.mark.parametrize('name', ['', '.', '..', '/outside', '../outside', 'nested/name', 'nested\\name'])
def test_source_names_cannot_escape_the_output_directory(name):
    with pytest.raises(UserError, match='filename stem'):
        Source.from_item({'name': name, 'url': 'https://example.org/page'}, {})


def test_ref_override_wins_over_item_pin_and_duplicate_outputs_fail(tmp_path):
    path = tmp_path / 'manifest.yaml'
    data = {'out': 'out', 'defaults': {'repo': 'owner/repo', 'ref': 'old'},
            'items': [{'name': 'page', 'path': 'page.md', 'ref': 'item-old'}]}
    path.write_text(yaml.safe_dump(data))
    manifest = Manifest.load(path, ref='chosen')
    assert '/chosen/page.md' in manifest.sources[0].url
    data['items'].append(dict(data['items'][0]))
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(UserError, match='duplicate output'):
        Manifest.load(path)


@pytest.mark.parametrize("fields", [
    {"start": 1, "end": 2}, {"start": "", "end": ""}, {"start": None, "end": None},
    {"url": "https://[bad/"},
])
def test_manifest_source_rejects_bad_markers_and_urls_before_fetch(fields):
    with pytest.raises(UserError):
        Source.from_item({"name": "fixture", "url": "https://example.org/page", **fields}, {})
