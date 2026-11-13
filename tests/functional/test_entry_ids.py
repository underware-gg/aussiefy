"""Public URL history survives renamed, merged and removed entries without evading discovery policy."""
import asyncio
import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from aussiefy import Translator, get_entry, load_dictionary
from aussiefy.entry_ids import FORMAT, parse_entry_ids, preserve_entry_ids
from aussiefy.errors import SchemaError
from aussiefy.loader import DATA_DIR


def register(ids, entries):
    return parse_entry_ids({'format': FORMAT, 'ids': ids}, entries)


def test_published_ids_including_the_last_release_are_permanently_reserved(dictionary):
    baseline = json.loads((Path(__file__).parents[1] / 'fixtures/entry-id-baseline.json').read_text())
    raw = yaml.safe_load((DATA_DIR / 'entry_ids.yaml').read_text())['ids']
    preserve_entry_ids(baseline['ids'], raw)
    assert set(dictionary.entries) <= raw.keys(), 'Register every new core ID before publishing it'
    assert baseline['release']['tag'] == 'v0.2.0' and baseline['release']['entry_count'] == 1228
    assert get_entry('g-bugger-me-sideways', translator=Translator(dictionary))['outcome'] == 'removed'


def test_rename_merge_chain_and_removed_ids_keep_requested_key_and_current_card(dictionary):
    ids = register({'first-name':'second-name', 'second-name':'stoked', 'merged-name':'stoked',
                    'removed-name':None, 'retired-alias':'removed-name'}, dictionary.entries)
    tr = Translator(replace(dictionary, entry_ids=ids))
    for old in ('first-name', 'second-name', 'merged-name'):
        result = get_entry(old, translator=tr)
        assert result['outcome'] == 'matched' and result['entry_id'] == old
        assert result['entry'] == get_entry('stoked', translator=tr)['entry']
        assert result['entry']['id'] == 'stoked'
    for old in ('removed-name', 'retired-alias'):
        result = get_entry(old, translator=tr)
        assert result['outcome'] == 'removed' and result['entry_id'] == old and result['entry'] is None
    assert get_entry('never-published', translator=tr)['outcome'] == 'not_in_dictionary'


def test_aliases_reapply_dials_gates_and_omissions(dictionary):
    for changes in ({'vulgarity':3}, {'status':'gate'}, {'status':'omit'}, {'reads_as':'british'}):
        entries = {**dictionary.entries, 'stoked': replace(dictionary.entries['stoked'], **changes)}
        tr = Translator(replace(dictionary, entries=entries, entry_ids={'old-name':'stoked'}))
        for include in (False, True):
            direct = get_entry('stoked', translator=tr, vulgarity=0, include_gated=include)
            alias = get_entry('old-name', translator=tr, vulgarity=0, include_gated=include)
            assert {k:v for k,v in alias.items() if k != 'entry_id'} == {k:v for k,v in direct.items() if k != 'entry_id'}


@pytest.mark.parametrize('ids,entries,match', [
    ({'old':'missing'}, {}, 'missing target'), ({'old':'next','next':'old'}, {}, 'cycle'),
    ({'old':None}, {'old'}, 'reserved ID'), ({'old':'new'}, {'old','new'}, 'reserved ID'),
    ({'missing':'missing'}, {}, 'missing target'), ({'bad id':'new'}, {'new'}, 'invalid entry ID'),
    ({'old':False}, {}, 'invalid entry ID'),
])
def test_invalid_or_reused_history_is_rejected(ids, entries, match):
    with pytest.raises(SchemaError, match=match):
        register(ids, entries)


@pytest.mark.parametrize('previous,current', [({'old':'old'}, {}), ({'old':None}, {'old':'old'}),
                                              ({'old':'new'}, {'old':'old'})])
def test_published_keys_cannot_disappear_or_be_reused(previous, current):
    with pytest.raises(SchemaError, match='disappeared|cannot be reused'):
        preserve_entry_ids(previous, current)


def test_loader_validates_history_and_extra_dictionaries_cannot_take_reserved_ids(data_copy, tmp_path):
    path = data_copy / 'entry_ids.yaml'
    raw = yaml.safe_load(path.read_text())
    raw['ids'].update({'old-name':'middle-name', 'middle-name':'stoked'})
    path.write_text(yaml.safe_dump(raw))
    d = load_dictionary(data_dir=data_copy)
    assert d.entry_ids['old-name'] == 'stoked'
    assert d.identity != load_dictionary().identity
    extra = tmp_path / 'reuse.yaml'
    extra.write_text(yaml.safe_dump([{'id':'old-name','form':'another term','concept':['HAPPY'],'frame':'adj'}]))
    with pytest.raises(SchemaError, match='reserved ID'):
        load_dictionary([extra], data_dir=data_copy)
    path.write_text('format: aussiefy-entry-ids/v1\nids: {old: stoked, old: stoked}\n')
    with pytest.raises(SchemaError, match='duplicate mapping key'):
        load_dictionary(data_dir=data_copy)


def test_cli_resolves_aliases_and_reports_removed_ids(dictionary, monkeypatch, capsys):
    from aussiefy.cli import main
    tr = Translator(replace(dictionary, entry_ids={'old-name':'stoked','gone':None}))
    monkeypatch.setattr('aussiefy.cli._translator', lambda args: tr)
    assert main(['entry', 'old-name', '--json']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['entry_id'] == 'old-name' and result['entry']['id'] == 'stoked'
    assert main(['entry', 'old-name']) == 0
    assert 'old-name -> stoked' in capsys.readouterr().out
    assert main(['entry', 'gone', '--json']) == 1
    assert json.loads(capsys.readouterr().out)['outcome'] == 'removed'


def test_mcp_resolves_aliases_and_reports_removed_ids(dictionary):
    from aussiefy.mcp_server import build_server
    tr = Translator(replace(dictionary, entry_ids={'old-name':'stoked','gone':None}))
    server = build_server(translator=tr)
    for key in ('old-name', 'gone'):
        result = asyncio.run(server.call_tool('aussie_entry', {'entry_id':key}))
        structured = result[1] if isinstance(result, tuple) else result.structured_content
        assert structured == get_entry(key, translator=tr)
