"""Conventional appetite degree uses the shared semantic certificates, not style intensity."""

import pytest

from aussiefy import Translator, harness, load_dictionary, translate_changes

PROFILE = {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1},
           'stack': 0, 'swearing': {'infix': 0, 'exclaim': 0, 'closer': 0}}
OPTIONS = {'level': 5, 'vulgarity': 3, 'embellishment': 0, 'embedder': 'none',
           'document_type': 'custom', 'document_config': {'profile': PROFILE}}


@pytest.mark.parametrize('source,band', [('She is peckish.', 'mild'), ('She is starving.', 'strong'),
    ('She is famished.', 'strong'), ('She is ravenous.', 'strong')])
@pytest.mark.parametrize('backend', ['none', 'ngram', 'bundled'])
def test_explicit_appetite_grade_is_preserved(translator, source, band, backend):
    for seed in (0, 1, 42):
        result = translator.translate(source, **{**OPTIONS, 'embedder': backend}, seed=seed)
        record = next(r for r in result.records if 'HUNGRY' in r.det.concepts)
        assert record.eligible
        assert all(c.entry.semantic_degree.get('HUNGRY') == band for c in record.eligible)


@pytest.mark.parametrize('source', ['She is not very hungry.', 'She is very peckish.', 'She is barely hungry.'])
def test_unsupported_modifier_and_target_compositions_remain_plain(translator, source):
    assert translator.translate(source, **OPTIONS).text == source


def test_unmarked_appetite_keeps_colourful_choices_and_vp_grammar(translator):
    result = translator.translate('She is hungry.', **OPTIONS)
    record = next(r for r in result.records if 'HUNGRY' in r.det.concepts)
    assert {'peckish', 'starvin', 'hungry-enough-horse-jockey'} <= {c.entry.id for c in record.eligible}
    result = translator.translate('I am feeling pretty hungry.', **OPTIONS)
    assert result.text in {'I am feeling like a decent feed.', 'I am feeling like some tucker.'}


def test_plans_and_editor_choices_cannot_downgrade_appetite(translator):
    source = 'She is starving.'
    plan = harness.plan(source, translator=translator, **{k:v for k,v in OPTIONS.items() if k != 'embedder'})
    assert 'peckish' not in plan['draft']
    changes = translate_changes(source, translator=translator, **OPTIONS)
    offered = [o for c in changes.changes if c['kind'] == 'substitution'
               for o in c['alternatives'] + c['locked']]
    assert offered
    assert all(translator.dictionary.entries[o['entry_id']].semantic_degree.get('HUNGRY') == 'strong'
               for o in offered)
    assert translate_changes('She is very hungry.', translator=translator, **OPTIONS).text != 'She is very hungry.'


@pytest.mark.parametrize('source,target', [
    ('She is very hungry.', 'She is peckish.'),
    ('She is starving.', 'She is peckish.'),
    ('She is peckish.', "She is starvin'."),
    ('She is legless.', 'She is a bit full.'),
    ('She is very drunk.', 'She is pissed.'),
])
def test_verification_reports_known_local_grade_changes_as_major(translator, source, target):
    report = harness.verify(target, original=source, translator=translator, level=5, vulgarity=3)
    assert not report['ok']
    assert any(p['kind'] == 'semantic_degree' and p['severity'] == 'major' for p in report['problems'])


@pytest.mark.parametrize('source,target', [
    ('She is very hungry.', "She is starvin'."),
    ('She is slightly hungry.', 'She is peckish.'),
    ('She is legless.', 'She is very pissed.'),
    ('She is very drunk.', 'She is very pissed.'),
    ('She is hungry.', 'She is peckish.'),
    ('She is very hungry.', 'She is very peckish.'),
    ('She is not very hungry.', 'She is not peckish.'),
    ('She is very hungry.', 'She is not peckish.'),
    ('She is starving. She is starving.', 'She is peckish.'),
    ('She is starving after work.', 'She is peckish before work.'),
    ('She is very hungry.', 'She is ravenous.'),  # no recognised target entry, not a universal prose judge
])
def test_verification_accepts_known_matches_or_abstains_without_local_evidence(translator, source, target):
    report = harness.lint(target, original=source, translator=translator, level=5, vulgarity=3, suggest=False)
    assert not any(p['kind'] == 'semantic_degree' for p in report['issues'])


def test_target_alone_cannot_establish_lost_degree(translator):
    report = harness.lint('She is peckish.', translator=translator, suggest=False)
    assert not any(p['kind'] == 'semantic_degree' for p in report['issues'])


@pytest.mark.parametrize('target,expected', [('testlow', True), ('testhigh', False),
    ('testopaque', False), ('testambiguous', False)])
def test_degree_verification_uses_new_dictionary_families_and_abstains_for_target_ambiguity(tmp_path, target, expected):
    import yaml
    path = tmp_path / 'graded.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'add_concepts': {'TEST_APPETITE_FREE': {'description': 'Independent graded test state.',
            'triggers': {'predicate_adj': ['teststate']},
            'trigger_degrees': {'predicate_adj': {'teststate': 'strong'}}}},
        'add_entries': [dict(id=id_, form=form, concept=['TEST_APPETITE_FREE'], frame='predicate_adj',
                            **({'semantic_degree': {'TEST_APPETITE_FREE': band}} if band else {}))
            for id_,form,band in [('test-low','testlow','mild'), ('test-high','testhigh','strong'),
                                  ('test-opaque','testopaque',None), ('test-ambiguous-low','testambiguous','mild'),
                                  ('test-ambiguous-high','testambiguous','strong')]]}))
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    report = harness.lint('She is ' + target + '.', original='She is teststate.', translator=tr, suggest=False)
    assert any(i['kind'] == 'semantic_degree' for i in report['issues']) == expected
