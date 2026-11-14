"""Every real substitution fixture's offered plain source replays with its complete surrounding pins."""
from pathlib import Path
import sys

from aussiefy import Translator, translate_changes


def test_all_real_fixture_plain_source_choices_replay_exactly_with_existing_garnish(dictionary):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
    from regen_changes_fixtures import CASES, build
    tr = Translator(dictionary, lookup_embedder=None)
    checked = []
    for name in CASES:
        request = build(name, tr)['request']
        cs = translate_changes(translator=tr, **request)
        for change in cs.changes:
            # Personal choices deliberately have no share-pin contract.
            if change['kind'] != 'substitution':
                continue
            option = next((option for option in change['alternatives'] if option['key'] == 'plain:source'), None)
            if option is None:
                continue
            packet = cs.replay_pins({change['id']: 'plain:source'})
            replay = translate_changes(translator=tr, **(request | {'pins': packet}))
            a, b = option['out_span']
            assert replay.text == cs.text[:a] + option['rendered'] + cs.text[b:], (name, change['id'])
            assert translate_changes(translator=tr, **(request | {'pins': replay.replay_pins()})).text == replay.text
            if name == 'every-kind' and change['original'] == 'Calm down':
                assert 'Now, Calm down' in replay.text
                assert any(g.entry_id == 'c-now' and g.text for g in replay.result.garnish)
            checked.append((name, change['original']))
    assert len(checked) >= 20 and ('every-kind', 'Calm down') in checked
