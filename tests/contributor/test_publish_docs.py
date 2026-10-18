"""Plain/public placement, source-preserving publication and the promotion freshness boundary."""

import copy
import json
from pathlib import Path
import sys

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import publish_docs as p  # noqa: E402
from aussiefy.policy import EMBELLISHMENTS, LEVELS, VULGARITIES  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TRANSLATION = yaml.safe_load((ROOT / p.CONFIG).read_text())['translation']


def put(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def repo(tmp_path):
    rows = [{"source": "docs/plain/root/README.md", "output": "README.md"},
            {"source": "docs/plain/user/guide.md", "output": "docs/user/guide.md"}]
    put(tmp_path, p.CONFIG, yaml.safe_dump({"translation": TRANSLATION, "documents": rows}))
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


@pytest.mark.parametrize('changed', ['duplicate', 'outside', 'recursive', 'settings', 'unnamed', 'missing', 'config'])
def test_invalid_publication_map_is_diagnosed(repo, changed):
    data = yaml.safe_load((repo / p.CONFIG).read_text())
    if changed == 'duplicate':
        data['documents'].append(data['documents'][0])
    elif changed == 'outside':
        data['documents'][0]['output'] = '../README.md'
    elif changed == 'recursive':
        data['documents'][0]['output'] = 'docs/plain/generated.md'
    elif changed == 'unnamed':
        data['translation']['embellishment'] = None
    elif changed == 'missing':
        del data['translation']['vulgarity']
    elif changed == 'config':
        data['translation']['document_config']['bogus'] = True
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


TRADIE_OVERLAY_SOURCE = ('# Usage\n\nShe was extremely busy.\n\n'
                         'Gated entries are held back for a reason; `--unlock all` allows every one.\n\n'
                         'With 0, the default, it is weighted over every eligible term.\n\n'
                         '[Home](../root/README.md#intro)\n')


@pytest.fixture
def checkout(repo):
    """A fixture repository whose package is the engine this process imported, as in a real checkout."""
    (repo / 'aussiefy').symlink_to(ROOT / 'aussiefy', target_is_directory=True)
    return repo


@pytest.fixture
def out(tmp_path_factory):
    return tmp_path_factory.mktemp('site')


def tradie_overlay(publication):
    return {'garnish': [*publication.document_config['garnish'], 'infix'], 'profile': {'swearing': {'exclaim': 0.4}}}


def test_export_builds_a_variant_at_caller_settings_without_touching_the_repository(checkout, out):
    put(checkout, 'docs/plain/user/guide.md', TRADIE_OVERLAY_SOURCE)
    base = p.load(checkout)
    variants = {'dad': {}, 'tradie': {'vulgarity': 'tradie'},
                'overlay': {'vulgarity': 'tradie', 'document_config_overlay': tradie_overlay(base)}}
    pages = {}
    for name, settings in variants.items():
        publication = p.export(checkout, out / name, **settings)
        assert publication.sources == base.sources
        pages[name] = (out / name / 'docs/user/guide.md').read_text()
    assert not (checkout / 'README.md').exists() and not (checkout / 'docs/user').exists()

    p.generate(checkout)
    assert pages['dad'] == (checkout / 'docs/user/guide.md').read_text()
    assert len(set(pages.values())) == 3
    assert "fuckin'" in pages['overlay'] and "fuckin'" not in pages['tradie'] + pages['dad']
    assert '**Tradie** vulgarity' in pages['overlay'] and '**Dad** vulgarity' in pages['dad']
    assert '[Home](../../README.md#intro)' in pages['overlay']
    assert "[Prefer docs that are as dry as a dead dingo's donger?](../plain/user/guide.md)" in pages['overlay']


def test_overlay_merges_maps_replaces_lists_and_shares_nothing(repo):
    base = p.load(repo)
    before = copy.deepcopy(base.document_config)
    overlay = tradie_overlay(base)
    variant = p.with_settings(base, vulgarity=3, document_config_overlay=overlay)
    assert variant.vulgarity == 'tradie'
    assert variant.document_config == {**before, 'garnish': [*before['garnish'], 'infix'],
                                       'profile': {**before['profile'], 'swearing': {'exclaim': 0.4}}}
    variant.document_config['garnish'].append('riff')
    variant.document_config['profile']['garnish']['tag'] = 1
    assert base.document_config == before
    assert overlay == tradie_overlay(base)


def test_notice_names_the_publication_settings(repo):
    data = yaml.safe_load((repo / p.CONFIG).read_text())
    data['translation']['embellishment'] = 'deadset'
    put(repo, p.CONFIG, yaml.safe_dump(data))
    p.generate(repo)
    assert ('> Aussiefied at **Swaggie** level, with **Deadset** embellishment and **Dad** vulgarity. '
            "[Prefer docs that are as dry as a dead dingo's donger?](docs/plain/root/README.md)\n"
            in (repo / 'README.md').read_text())
    publication = p.load(repo)
    assert p.with_settings(publication, vulgarity=3).notice('x') == p.with_settings(publication, vulgarity='tradie').notice('x')
    assert '**Uncle Bob** vulgarity' in p.with_settings(publication, vulgarity=2).notice('x')


def test_every_stop_has_a_notice_label_and_a_missing_one_is_refused(repo, monkeypatch):
    assert set(p.LABELS) == set(LEVELS) | set(VULGARITIES) | set(EMBELLISHMENTS)
    monkeypatch.delitem(p.LABELS, 'tradie')
    with pytest.raises(p.PublicationError, match='no notice label for tradie'):
        p.with_settings(p.load(repo), vulgarity='tradie')


@pytest.mark.parametrize('settings', [
    {'document_config_overlay': {'bogus': True}},
    {'document_config_overlay': {'profile': {'swearing': {'bogus': 0.4}}}},
    {'document_config_overlay': {'garnish': ['infix', 'nonsense']}},
    {'document_config_overlay': ['infix']},
    {'vulgarity': 'filthy'},
])
def test_invalid_caller_settings_are_refused(checkout, out, settings):
    with pytest.raises(p.PublicationError):
        p.export(checkout, out / 'variant', **settings)
    assert not (out / 'variant').exists()


def test_export_refuses_a_used_or_inner_directory_and_another_engine(checkout, out):
    put(out, 'stale.md', 'An earlier export.\n')
    with pytest.raises(p.PublicationError, match='new or empty directory outside the repository'):
        p.export(checkout, out)
    with pytest.raises(p.PublicationError, match='new or empty directory outside the repository'):
        p.export(checkout, checkout / 'site')
    (checkout / 'aussiefy').unlink()
    with pytest.raises(p.PublicationError, match="repository's own engine"):
        p.export(checkout, out / 'fresh')
    assert not (out / 'fresh').exists() and not (checkout / 'site').exists()


def test_export_cli_writes_pages_and_prints_the_manifest(checkout, out, tmp_path, capsys):
    put(checkout, 'docs/architecture/decisions/dd-001-example.md', '# Historical ADR\n')
    overlay = tmp_path / 'overlay.yaml'
    overlay.write_text(yaml.safe_dump({'profile': {'swearing': {'exclaim': 0.4}}}))
    assert p.main(['export', '--root', str(checkout), '--out', str(out / 'tradie'), '--vulgarity', '3',
                   '--overlay', str(overlay)]) == 0
    manifest = json.loads(capsys.readouterr().out)
    assert set(manifest) == {'settings', 'documents', 'kept_plain'}
    assert manifest['settings']['vulgarity'] == 'tradie' and manifest['settings']['level'] == 5
    assert manifest['settings']['document_config']['profile']['swearing'] == {'exclaim': 0.4}
    assert manifest['documents'] == [{'source': 'docs/plain/root/README.md', 'output': 'README.md'},
                                     {'source': 'docs/plain/user/guide.md', 'output': 'docs/user/guide.md'}]
    assert manifest['kept_plain'] == ['docs/architecture/decisions/dd-001-example.md']
    assert (out / 'tradie/docs/user/guide.md').is_file()


def test_export_options_belong_to_export(repo):
    with pytest.raises(SystemExit):
        p.main(['generate', '--root', str(repo), '--vulgarity', 'tradie'])
    with pytest.raises(SystemExit):
        p.main(['export', '--root', str(repo)])


def test_kept_plain_lists_the_documents_publication_never_translates(repo):
    for name in ('docs/architecture/decisions/dd-001-example.md', 'docs/architecture/reviews/design-review-1.md',
                 'docs/standards/agent-ready-documentation.md', 'docs/architecture/current.md'):
        put(repo, name, '# Plain\n')
    assert p.kept_plain(repo) == ['docs/architecture/decisions/dd-001-example.md',
                                  'docs/architecture/reviews/design-review-1.md',
                                  'docs/standards/agent-ready-documentation.md']


def test_every_actual_document_is_exactly_one_of_source_output_or_kept_plain():
    publication = p.load(ROOT)
    kinds = ({d.source for d in publication.documents}, {d.output for d in publication.documents},
             set(p.kept_plain(ROOT)))
    for document in (f.relative_to(ROOT).as_posix() for f in (ROOT / 'docs').rglob('*.md')):
        assert sum(document in kind for kind in kinds) == 1, document
