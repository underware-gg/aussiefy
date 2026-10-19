"""Detected solemn mood feeds an explicit substitution permission without changing other dials."""

import pytest

from aussiefy import Translator, harness, translate_changes
from aussiefy.context import text_mood
from aussiefy.errors import UserError
from aussiefy.genre import resolve_document
from aussiefy.policy import DocumentOverrides


SOURCE = 'He died aged 82. His funeral honours his sacrifice and devotion.'
PROFILE = {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}


@pytest.mark.parametrize('step', [0, 1, 2])
@pytest.mark.parametrize('kind', ['general', 'custom', 'story', 'technical', 'auto'])
def test_tone_permission_defaults_and_exact_overrides(dictionary, kind, step):
    genre = resolve_document(SOURCE, config=dictionary.genres, document_type=kind)
    assert genre.setting(step).solemn_comic_terms is (step == 2 and kind != 'custom')
    for enabled in (False, True):
        genre = resolve_document(SOURCE, config=dictionary.genres, document_type=kind,
                                 document_config={'solemn_comic_terms': enabled})
        assert genre.setting(step).solemn_comic_terms is enabled
        assert genre.envelope(step)['document_config']['solemn_comic_terms'] is enabled


@pytest.mark.parametrize('bad', [None, 0, 1, 'true', [], {}])
def test_tone_override_requires_an_actual_boolean(bad):
    with pytest.raises(UserError, match='solemn_comic_terms'):
        DocumentOverrides.parse({'solemn_comic_terms': bad})


@pytest.mark.parametrize('enabled', [False, True])
def test_translation_plan_and_changes_share_tone_permission(dictionary, enabled):
    tr = Translator(dictionary, lookup_embedder=None)
    options = dict(level=5, vulgarity=0, embellishment=0, embedder='none', document_type='custom',
                   document_config={'solemn_comic_terms': enabled, 'profile': PROFILE})
    assert text_mood(SOURCE) == 'solemn'
    result = tr.translate(SOURCE, **options)
    assert result.mood == 'solemn'
    assert not result.embellishment.garnish
    death = next(r for r in result.records if 'DIE' in r.det.concepts)
    assert ('cark-it' in {c.entry.id for c in death.eligible}) is enabled
    if not enabled:
        assert any('solemn_comic_terms is false' in why for _, why in death.rejected)
    plan_options = {k: v for k, v in options.items() if k != 'embedder'}
    plan = harness.plan(SOURCE, translator=tr, **plan_options)
    assert plan['mood'] == 'solemn'
    assert plan['document_config']['solemn_comic_terms'] is enabled
    changes = translate_changes(SOURCE, translator=tr, **options)
    death_changes = [c for c in changes.changes if c['kind'] == 'substitution'
                     and c.get('entry_id') in {candidate.entry.id for candidate in death.eligible}]
    assert death_changes
    offered = {c['entry_id'] for c in death_changes}
    offered |= {o['entry_id'] for c in death_changes for o in c['alternatives'] + c['locked']}
    assert ('cark-it' in offered) is enabled


def test_tone_permission_does_not_discard_a_source_modal(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    source = 'He shall not have died in vain. Honour his sacrifice and devotion.'
    result = tr.translate(source, level=5, embellishment=0, embedder='none',
                          document_config={'solemn_comic_terms': True, 'profile': PROFILE})
    assert 'shall' in result.text and 'not' in result.text
    assert not result.embellishment.narrator_opinion
