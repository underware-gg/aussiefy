"""Plain/public placement, source-preserving publication and the promotion freshness boundary."""

from pathlib import Path
import sys

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import publish_docs as p  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def put(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def repo(tmp_path):
    rows = [{"source": "docs/plain/root/README.md", "output": "README.md"},
            {"source": "docs/plain/user/guide.md", "output": "docs/user/guide.md"}]
    put(tmp_path, p.CONFIG, yaml.safe_dump({"translation": p.SETTINGS, "documents": rows}))
    put(tmp_path, "docs/plain/root/README.md", '# Intro\n\nI\'m extremely busy.\n\n[Guide](../user/guide.md#usage) and [licence](../../../LICENSE).\n\n```console\n$ aussiefy "test"\nExact output.\n```\n')
    put(tmp_path, "docs/plain/user/guide.md", '# Usage\n\nShe was extremely busy.\n\n[Home](../root/README.md#intro)\n')
    put(tmp_path, "LICENSE", "Own fixture licence.\n")
    return tmp_path


def test_generate_is_repeatable_prose_changes_and_structure_examples_survive(repo):
    p.generate(repo)
    first = {d.output: (repo / d.output).read_bytes() for d in p.load(repo).documents}
    text = first["README.md"].decode()
    assert "I'm extremely busy.\n" not in text
    assert '[Guide](docs/user/guide.md#usage)' in text and '[licence](LICENSE)' in text
    assert '```console\n$ aussiefy "test"\nExact output.\n```' in text
    assert '# Intro\n' in text and "[Prefer docs that are as dry as a dead dingo's donger?](docs/plain/root/README.md)" in text
    p.generate(repo)
    assert first == {d.output: (repo / d.output).read_bytes() for d in p.load(repo).documents}
    p.check(repo)


def test_source_or_output_edit_is_stale_until_regenerated(repo):
    p.generate(repo)
    put(repo, 'docs/plain/user/guide.md', (repo / 'docs/plain/user/guide.md').read_text() + '\nMy friend was tired.\n')
    with pytest.raises(p.PublicationError, match='docs/user/guide.md: generated prose is stale'):
        p.check(repo)
    p.generate(repo)
    put(repo, 'README.md', (repo / 'README.md').read_text() + '\nHand edit.\n')
    with pytest.raises(p.PublicationError, match='README.md: generated prose is stale'):
        p.check(repo)
    p.generate(repo)
    p.check(repo)


def test_publication_protects_quoted_examples_and_neutral_people(repo):
    source = ('# Usage\n\nAn example: "mosquitoes" becomes "mozzies".\n\n'
              'The incorrect example is “is my togs”.\n\nSomeone is being addressed.\n\n'
              'You must use `dev` for changes.\n')
    put(repo, 'docs/plain/user/guide.md', source)
    p.generate(repo)
    rendered = (repo / 'docs/user/guide.md').read_text()
    assert '"mosquitoes" becomes "mozzies"' in rendered
    assert '“is my togs”' in rendered
    assert 'mongrel' not in rendered and 'bastard' not in rendered
    assert '`dev`' in rendered


def test_missing_unmapped_or_unexpected_files_fail(repo):
    p.generate(repo)
    put(repo, 'docs/leftover.md', p.MARKER + '\n')
    with pytest.raises(p.PublicationError, match='unexpected generated output'):
        p.check(repo)
    (repo / 'docs/leftover.md').unlink()
    put(repo, 'docs/plain/forgotten.md', '# Forgotten\n')
    with pytest.raises(p.PublicationError, match='plain sources differ from the map'):
        p.check(repo)
    (repo / 'docs/plain/forgotten.md').unlink()
    (repo / 'docs/plain/user/guide.md').unlink()
    with pytest.raises(p.PublicationError, match='plain sources differ from the map'):
        p.check(repo)


def test_relative_destinations_reference_definitions_images_titles_and_literals():
    source = ('[a [nested]](docs/user/guide.md#usage "title [literal](absent.md)")\n'
              '[![image](asset.png)](docs/user/guide.md)\n'
              '\n[ref]: <docs/user/guide.md#usage> "title"\n\n'
              '[read][ref]\n`[code](absent.md)`\n\n'
              '```md\n[example](absent.md)\n```\n'
              '[web](https://example.org/docs#part) [here](#intro)\n')
    mapping = {'docs/user/guide.md': 'docs/plain/user/guide.md'}
    moved = p.remap_links(source, 'README.md', 'docs/plain/root/README.md', mapping)
    assert '<../user/guide.md#usage>' in moved and '(../user/guide.md#usage "title [literal](absent.md)")' in moved
    assert '[![image](../../../asset.png)](../user/guide.md)' in moved
    assert '`[code](absent.md)`' in moved and '[example](absent.md)' in moved
    assert '[web](https://example.org/docs#part) [here](#intro)' in moved
    assert p.remap_links(moved, 'docs/plain/root/README.md', 'README.md', {v: k for k, v in mapping.items()}) == source


def test_unclosed_ticks_in_separate_paragraphs_do_not_hide_links():
    text = '`unclosed\n\n[valid](file.md)\n\n`other\n'
    assert [href for _, _, href in p.destinations(text)] == ['file.md']


def test_link_checks_use_rendered_heading_ids_and_actual_targets(repo):
    put(repo, 'docs/plain/user/guide.md', '# Usage\n\n## `Code` & *voice*\n\n## `Code` & *voice*\n\n<a id="explicit"></a>\n')
    assert {'usage', 'code--voice', 'code--voice-1', 'explicit'} <= p.anchors((repo / 'docs/plain/user/guide.md').read_text())
    p.check_links(repo, ['docs/plain/root/README.md'])
    put(repo, 'docs/plain/root/README.md', '[bad](../user/guide.md#missing)\n')
    with pytest.raises(p.PublicationError, match='missing anchor'):
        p.check_links(repo, ['docs/plain/root/README.md'])
    put(repo, 'docs/plain/root/README.md', '[bad](absent.md)\n')
    with pytest.raises(p.PublicationError, match='missing repository target'):
        p.check_links(repo, ['docs/plain/root/README.md'])


def test_discovery_has_each_authoritative_source_once_and_no_published_copies(repo):
    put(repo, 'skills/test/SKILL.md', '# Toolkit\n')
    put(repo, 'docs/architecture/decisions/dd-001-example.md', '# Historical ADR\n')
    docs = p.authoritative_docs(repo, p.load(repo))
    assert docs == ['docs/plain/root/README.md', 'docs/plain/user/guide.md', 'skills/test/SKILL.md']
    assert len(docs) == len(set(docs))


def test_actual_authoritative_links_resolve_and_map_covers_sources():
    publication = p.load(ROOT)
    sources = {d.source for d in publication.documents}
    assert sources == {f.relative_to(ROOT).as_posix() for f in (ROOT / 'docs/plain').rglob('*.md')}
    assert not set(publication.sources) & set(p.authoritative_docs(ROOT, publication))
    p.check_links(ROOT, list(sources))


@pytest.mark.parametrize('changed', ['duplicate', 'outside', 'recursive', 'settings'])
def test_invalid_publication_map_is_diagnosed(repo, changed):
    data = yaml.safe_load((repo / p.CONFIG).read_text())
    if changed == 'duplicate':
        data['documents'].append(data['documents'][0])
    elif changed == 'outside':
        data['documents'][0]['output'] = '../README.md'
    elif changed == 'recursive':
        data['documents'][0]['output'] = 'docs/plain/generated.md'
    else:
        data['translation']['seed'] = False
    put(repo, p.CONFIG, yaml.safe_dump(data))
    with pytest.raises(p.PublicationError):
        p.load(repo)


def test_cli_paths_do_not_depend_on_cwd(repo, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path.parent)
    assert p.main(['generate', '--root', str(repo)]) == 0
    assert p.main(['check', '--root', str(repo)]) == 0
    assert 'passed' in capsys.readouterr().out


def test_inline_html_literals_survive_destination_remapping():
    text = ('prefix <!-- [literal](absent.md) --> suffix\n'
            '<span data-example="[literal](absent.md)">[real](file.md)</span>\n')
    assert [href for _, _, href in p.destinations(text)] == ['file.md']
    moved = p.remap_links(text, 'README.md', 'docs/plain/root/README.md', {})
    assert '<!-- [literal](absent.md) -->' in moved
    assert 'data-example="[literal](absent.md)"' in moved
    assert '[real](../../../file.md)' in moved


def test_invalid_local_destination_is_diagnosed_by_cli(repo, capsys):
    put(repo, 'docs/plain/root/README.md', '[bad](missing%00.md)\n')
    assert p.main(['generate', '--root', str(repo)]) == 1
    assert 'embedded NUL' in capsys.readouterr().err
    assert not (repo / 'README.md').exists()


def test_obstructed_output_directory_is_diagnosed_by_cli(repo, capsys):
    put(repo, 'docs/user', 'An output parent is a file.\n')
    assert p.main(['generate', '--root', str(repo)]) == 1
    assert 'docs/user/guide.md: could not save generated prose' in capsys.readouterr().err


def test_remapping_preserves_literal_query_and_fragment_suffixes():
    text = '[empty](guide.md#) [query](guide.md?query#) [bare](guide.md?) [escaped](guide.md?q=\\(x\\)#part)'
    moved = p.remap_links(text, 'README.md', 'docs/plain/root/README.md', {})
    assert moved == text.replace('guide.md', '../../../guide.md')
    assert p.remap_links(moved, 'docs/plain/root/README.md', 'README.md', {}) == text
