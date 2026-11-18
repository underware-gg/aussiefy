"""Dial goals favour permitted colour; they never relax eligibility or level."""
import json
from pathlib import Path

import pytest

from aussiefy import Translator, translate_changes, suggest_selection
from aussiefy.errors import UserError, SchemaError
from aussiefy.dial_goals import parse_goals
from aussiefy.garnish import garnish_weights
from aussiefy.schema import Entry


@pytest.mark.parametrize('bad', [0, True, '', 'AIM', 'target'])
def test_unknown_modes_fail_before_translation(translator, bad):
    with pytest.raises(UserError, match='dial_mode'):
        translator.translate('She is tired.', dial_mode=bad)


def test_cap_matches_the_captured_pre_change_outputs(translator):
    rows = json.loads((Path(__file__).parents[2] / 'research/dial-goals-2026-11-19/cap-baseline.json').read_text())
    for row in rows:
        assert translator.translate(row['text'], dial_mode='cap', **row['options']).text == row['output']
        assert translator.translate(row['text'], **row['options']).text == row['output']


def test_aim_keeps_every_level_setting_outside_garnish(translator):
    for level in range(1, 6):
        cap = translator.effective(level=level)
        for step in range(3):
            aim = translator.effective(level=level, dial_mode='aim', embellishment=step)
            for key in ('level', 'substitution', 'frames', 'phonetic', 'stack', 'stretch', 'rewrite'):
                assert getattr(aim.profile, key) == getattr(cap.profile, key)


def test_the_same_tier_preference_reaches_mixed_garnish(translator):
    eff = translator.effective(dial_mode='aim', vulgarity=3)
    entries = [Entry(str(v), 'term', (), 'interjection', vulgarity=v) for v in range(4)]
    weights = garnish_weights(entries, eff, None)
    assert weights == [eff.metadata_weight(e) * eff.vulgarity_weight(e.vulgarity) for e in entries]
    assert weights[3] > weights[2] > weights[1] > 0 and weights[0] > 0


@pytest.mark.parametrize('kind', ['news', 'technical', 'official', 'custom'])
def test_aim_does_not_put_troppo_garnish_in_a_restricted_form(translator, kind):
    for seed in range(4):
        result = translator.translate('I walked home. We bought bread and milk.', level=5, vulgarity=3,
            embellishment=2, dial_mode='aim', document_type=kind, seed=seed)
        assert not result.genre.setting(2).garnish
        assert not result.garnish and not any(p.rule.startswith('infix') for p in result.phonetic)


def test_aim_respects_exact_zero_rates_and_budgets(translator):
    profile = {'garnish': {p: 0 for p in ('opener','tag','aside','tail','closer','connective','riff')}}
    r = translator.translate('I walked home. We bought bread and milk.', dial_mode='aim', embellishment=2,
                             vulgarity=3, document_config={'profile': profile})
    assert not r.garnish
    assert all(v == 0 for v in r.profile_config['garnish'].values())


def test_deadset_remains_straight_in_aim(translator):
    r = translator.translate('I walked home. We bought bread and milk.', dial_mode='aim', embellishment=0, vulgarity=3)
    assert not r.garnish and not r.embellishment.garnish


@pytest.mark.parametrize('level', [1,3,5])
def test_embellishment_rates_belong_to_the_setting(translator, level):
    a = translator.effective(level=level, vulgarity=0, embellishment=2, dial_mode='aim')
    b = translator.effective(level=5, vulgarity=0, embellishment=2, dial_mode='aim')
    assert a.profile.garnish == b.profile.garnish
    assert a.profile.max_garnish == b.profile.max_garnish
    assert a.profile.garnish['opener'] > translator.effective(level=level, vulgarity=0, embellishment=1, dial_mode='aim').profile.garnish['opener']


@pytest.mark.parametrize('markdown', [False,True])
def test_aim_real_changes_validate_and_replay(dictionary, markdown):
    tr = Translator(dictionary, lookup_embedder=None)
    text = 'I am very tired. The car is broken. We had a long day.'
    opts = dict(dial_mode='aim', level=5, vulgarity=3, embellishment=2, seed=3, markdown=markdown, translator=tr)
    first = translate_changes(text, **opts)
    from aussiefy.v3_contract import validate_response
    validate_response(first.to_dict(), text, dictionary, result_warnings=first.result.warnings)
    again = translate_changes(text, pins=first.replay_pins(), **opts)
    assert first.text == again.text
    assert first.result.genre.dial_mode == 'aim'


@pytest.mark.parametrize('text', ['Thanks','Thanks.','Thanks!','Thank you.','Thanks for understanding.', 'Thank you for coming.', 'Thanks for breakfast, my friend.'])
def test_cheers_is_offered_and_pins_in_context(text, translator):
    opts = dict(level=5, embellishment=0, translator=translator)
    cs = translate_changes(text, **opts)
    change = next(c for c in cs.changes if c.get('reading',{}).get('concept') == 'THANKS')
    assert any(o.get('entry_id') == 'cheers' for o in change['alternatives'])
    pins = cs.replay_pins({change['id']: 'entry:cheers'})
    assert translate_changes(text, pins=pins, **opts).text.startswith('Cheers')
    response = suggest_selection(text, span=[0,len(cs.text)], **opts)
    assert any(o.get('entry_id') == 'cheers' for g in response['suggestions'] for o in g['options'])


@pytest.mark.parametrize('mutation', [lambda x:x.update(tier_decay=0), lambda x:x.update(tier_decay=float('nan')),
    lambda x:x['embellishment'][1].update(substitution={'lexical':1})])
def test_goal_data_does_not_change_the_level(mutation, dictionary):
    import yaml
    from aussiefy.loader import DATA_DIR
    data = yaml.safe_load((DATA_DIR/'dial-goals.yaml').read_text())
    mutation(data)
    with pytest.raises(SchemaError):
        parse_goals(data)


def test_catalogue_size_does_not_turn_a_goal_into_a_cap(translator):
    e = translator.effective(dial_mode='aim', vulgarity=3)
    weights = e.balance_weights([0]*20+[2], [1]*20+[e.vulgarity_weight(2)])
    assert sum(weights[:20]) == pytest.approx(1)
    assert weights[-1] > sum(weights[:20])
    assert e.balance_weights([2], [0]) == [0]


def test_australian_voice_goal_has_colour_and_restraint(translator):
    from collections import Counter
    text = 'I walked home. The dog waited by the gate. We bought bread and milk. It was a long day. I was very tired. The car was broken.'
    counts = {}
    for mode in ('cap','aim'):
        tiers = Counter()
        for seed in range(24):
            r = translator.translate(text, level=5, vulgarity=3, embellishment=2, dial_mode=mode, seed=seed)
            for g in r.garnish:
                if g.text:
                    entry = translator.dictionary.entries.get(g.entry_id)
                    tiers[entry.vulgarity if entry else g.construction.vulgarity] += 1
        counts[mode] = tiers
    a,b = counts['aim'],counts['cap']
    assert sum(n for tier,n in a.items() if tier) > 2 * sum(n for tier,n in b.items() if tier)
    assert a[2] > a[1] and a[0] > 0
    assert sum(n for tier,n in a.items() if tier) < 6*24


def test_low_level_troppo_has_more_colour_than_dinkum(translator):
    text = 'I walked home. The dog waited by the gate. We bought bread and milk. It was a long day.'
    counts = []
    for step in (0,1,2):
        total = sum(sum(bool(g.text) for g in translator.translate(text, level=1, vulgarity=0,
                    embellishment=step, dial_mode='aim', seed=seed).garnish) for seed in range(24))
        counts.append(total)
    assert counts[0] == 0 < counts[1] < counts[2]


@pytest.mark.parametrize('source', ['I give my thanks.', 'The thanks were heartfelt.', 'Thanks to the rain, we stayed home.',
                                  'Thanks for.', 'I thank you for coming.'])
def test_gratitude_complement_does_not_make_nouns_or_causation_interjections(translator, source):
    result = translator.translate(source, embellishment=0)
    assert not any('THANKS' in r.det.concepts for r in result.records)
