"""Quiz exclusions are dictionary evidence; similarity only chooses difficulty bands."""
from dataclasses import replace

import pytest

from aussiefy import Translator, meaning_quiz
from aussiefy.embed import NgramEmbedder
from aussiefy.explore import _context, _entries
from aussiefy.lookup import lookup
from aussiefy.quiz import askable_pool, bands, candidates, content_words, option_text, question_for
from aussiefy.schema import Entry, parse_concept
from aussiefy.errors import UserError


@pytest.mark.parametrize('gloss,expected', [
    ('Done for, beyond saving ("we are cooked"); another sense.', 'Done for, beyond saving.'),
    ('A person (with an aside (and another)). More here.', 'A person.'),
    ('Stop now!; an example follows', 'Stop now!'),
    ('Really?: a question', 'Really?'),
    ('No!','No!'), ('What?', 'What?'), ('A South Australian (person).', 'A South Australian.'),
    ('First clause: then another.', 'First clause.'), ('', ''),
])
def test_option_text_is_the_gloss_first_clause_without_examples(gloss, expected):
    assert option_text(gloss) == expected


def test_self_naming_variants_garnish_and_empty_glosses_are_not_asked(dictionary):
    rows = [Entry('self', 'whinge', ('HUNGRY',), 'vp', gloss='Whinge about something.'),
            Entry('variant', 'zorbulate', ('HUNGRY',), 'vp', variants=('whinge',), gloss='Whinge.'),
            Entry('garnish', 'gday', ('HUNGRY',), 'interjection', type='garnish', placement='opener', gloss='Greetings.'),
            Entry('empty', 'zorb', ('HUNGRY',), 'np', gloss=''),
            Entry('valid', 'zorb', ('HUNGRY',), 'np', gloss='A biscuit.'),
            Entry('short', 'aye', ('HUNGRY',), 'interjection', gloss='Yes.'),
            Entry('short-self', 'sav', ('HUNGRY',), 'np', gloss='A sav.')]
    assert [row.entry.id for row in askable_pool(rows, dictionary.concepts)] == ['short', 'valid']


def toy_pool():
    words = ['Brilliant circles.', 'Scarlet triangles.', 'Purple squares.', 'Silver rectangles.',
             'Gentle whispers.', 'Stormy oceans.', 'Sandy beaches.', 'Busy markets.', 'Silent valleys.',
             'Wild rivers.', 'Steep mountains.', 'Broad forests.', 'Clever inventors.', 'Patient teachers.',
             'Hidden tunnels.', 'Distant islands.', 'Golden temples.', 'Narrow alleys.', 'Heavy engines.', 'Fresh orchards.']
    concepts = {f'C{i}': parse_concept(f'C{i}', {'description': text, 'person': bool(i % 2)})
                for i, text in enumerate(words)}
    forms = 'abacus badger cactus dahlia eagle falcon gecko heron ibis jaguar koala lemur marmot newt ocelot panda quokka raven stoat tapir'.split()
    entries = [Entry(f'term-{i:02}', forms[i], (f'C{i}',), 'np', gloss=text) for i, text in enumerate(words)]
    return askable_pool(entries, concepts)


def test_band_boundaries_and_person_preference_are_over_ranked_candidates():
    pool = list(toy_pool())
    close, middle, far = bands(pool, True)
    assert [x.entry.id for x in close] == ['term-01','term-03','term-05','term-07','term-09']
    assert middle == pool[8:12]
    assert {x.entry.id for x in far} == {x.entry.id for x in pool[17:]}
    assert far[0].person is False
    assert bands([], False) == ((), (), ())


def test_true_reading_oracle_excludes_forward_and_reverse_candidates_and_retries():
    pool = toy_pool()
    right = pool[0]
    def offers(text):
        return {pool[1].entry.id} if text == right.text else {right.entry.id} if text == pool[2].text else set()
    result = question_for(right, pool, NgramEmbedder(), offers, 7)
    assert result and len(result.options) == 4
    assert not {pool[1].entry.id, pool[2].entry.id} & {x['entry_id'] for x in result.options}
    assert result.options[result.answer]['entry_id'] == right.entry.id
    assert result == question_for(right, tuple(reversed(pool)), NgramEmbedder(), offers, 7)
    assert question_for(right, pool, NgramEmbedder(), lambda text: {x.entry.id for x in pool}, 7) is None


def test_same_frame_is_preferred_but_thin_frames_borrow_only_the_same_word_class():
    pool = toy_pool()
    right = replace(pool[0], entry=replace(pool[0].entry, frame='adj'))
    predicates = [replace(x, entry=replace(x.entry, frame='predicate_adj')) for x in pool[1:]]
    assert len(candidates(right, [right, *predicates])) == 19
    assert not candidates(right, pool)


def test_seed_repeat_and_explicit_ranking_fallback(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    result = meaning_quiz(seed=17, translator=tr, vulgarity=0)
    assert result == meaning_quiz(seed=17, translator=tr, vulgarity=0)
    assert result['ranking'] == {'model':'char-trigram', 'fallback':True}
    assert result['options'][result['answer']]['entry_id'] == result['entry']['id']
    assert len({x['text'] for x in result['options']}) == len({x['entry_id'] for x in result['options']}) == 4
    assert result['dictionary_id'] == dictionary.identity and result['card_version'] == 4
    modeled = meaning_quiz(seed=17, translator=Translator(dictionary, lookup_embedder='bundled'))
    assert modeled['ranking']['model'].startswith('bundled:') and modeled['ranking']['fallback'] is False


def test_question_and_options_respect_dials_permissions_and_gates(dictionary):
    ordinary = [Entry(f'normal-{i}', ['ibis','quokka','dingo','gecko'][i], (cid,), 'np', gloss=gloss)
        for i,(cid,gloss) in enumerate(zip(['HUNGRY','THIRSTY','DOLLAR','BREAKFAST'],
                                         ['Crimson triangles.','Silent circles.','Golden squares.','Purple rectangles.']))]
    forbidden = [replace(ordinary[0], id='rude', vulgarity=3),
                 replace(ordinary[0], id='held', status='gate'),
                 replace(ordinary[0], id='foreign', reads_as='british'),
                 replace(ordinary[0], id='theme', themes=('sex',)),
                 replace(ordinary[0], id='omitted', status='omit')]
    tr = Translator(replace(dictionary, entries={e.id:e for e in [*ordinary,*forbidden]}), lookup_embedder=None)
    allowed = {e.id for e in ordinary}
    for seed in range(8):
        result = meaning_quiz(seed=seed, vulgarity=0, themes={'sex':False}, translator=tr)
        assert result['outcome'] == 'matched'
        assert {row['entry_id'] for row in result['options']} == allowed
        assert result['entry']['held_back'] == []
    thin = Translator(replace(dictionary, entries={e.id:e for e in ordinary[:3]}), lookup_embedder=None)
    result = meaning_quiz(translator=thin)
    assert result['outcome'] == 'nothing_fits' and result['entry'] is result['answer'] is None and result['options'] == []


@pytest.mark.parametrize('seed', [True, 1.5, '1'])
def test_invalid_seed_is_a_user_error(translator, seed):
    with pytest.raises(UserError, match='seed'):
        meaning_quiz(seed=seed, translator=translator)


@pytest.mark.parametrize('vulgarity', range(4))
def test_every_askable_entry_has_safe_distractors_at_each_vulgarity(dictionary, vulgarity):
    tr = Translator(dictionary, lookup_embedder='bundled')
    d, eff, _, _ = _context(tr, 5, vulgarity, 0, 'general', None)
    eligible = _entries(d, eff, None, None, False)
    pool = askable_pool(eligible, d.concepts)
    cache = {}
    def offers(text):
        if text not in cache:
            cache[text] = {row['id'] for row in lookup(text, translator=tr, level=5, vulgarity=vulgarity,
                embellishment=0, limit=50, short=True)['results']}
        return cache[text]
    by_id = {row.entry.id:row for row in pool}
    playable = 0
    for right in pool:
        result = question_for(right, pool, tr.lookup_embedder, offers, 13)
        assert not content_words(right.text) & right.form_words
        if result is None:
            continue
        playable += 1
        assert len(result.options) == 4 and result.options[result.answer]['entry_id'] == right.entry.id
        possible = {row.entry.id for row in candidates(right, pool, offers(right.text))}
        for option in result.options:
            candidate = by_id[option['entry_id']]
            assert candidate.entry.vulgarity <= vulgarity and not candidate.entry.held_back
            if candidate.entry.id == right.entry.id:
                continue
            assert candidate.entry.id in possible
            assert candidate.entry.id not in offers(right.text) and right.entry.id not in offers(candidate.text)
            assert not set(candidate.entry.concept) & set(right.entry.concept)
    print(f'vulgarity {vulgarity}: {playable}/{len(pool)} askable entries playable')
    assert playable >= len(pool) * .98, (vulgarity, playable, len(pool))


def test_quoted_examples_do_not_remove_ordinary_apostrophes_or_ignore_unicode_words():
    assert option_text("Broken 'I'm cooked'; another sense.") == 'Broken.'
    assert option_text("Someone's unusual habit.") == "Someone's unusual habit."
    assert content_words('un café') == frozenset({'café'})


def test_far_band_preserves_other_person_preference_after_the_roll():
    pool = toy_pool()
    indices = {row.meaning:i for i,row in enumerate(pool)}
    class Ranked:
        def similarity(self, a, b):
            return -indices[b]
    for seed in range(16):
        question = question_for(pool[0], pool, Ranked(), lambda text: set(), seed)
        ids = {row['entry_id'] for row in question.options}
        assert 'term-18' not in ids and len(ids & {'term-17', 'term-19'}) == 1


def test_frame_fallback_counts_candidates_after_forward_lookup_exclusions():
    pool = toy_pool()
    right = replace(pool[0], entry=replace(pool[0].entry, frame='adj'))
    others = [replace(row, entry=replace(row.entry, frame='adj' if i < 12 else 'predicate_adj'))
              for i,row in enumerate(pool[1:])]
    assert len(candidates(right, [right,*others])) == 12
    excluded = {others[0].entry.id, others[1].entry.id}
    widened = candidates(right, [right,*others], excluded)
    assert len(widened) == 17 and any(row.entry.frame == 'predicate_adj' for row in widened)
    assert not excluded & {row.entry.id for row in widened}


def test_current_real_emitter_fixture(dictionary):
    import json
    from pathlib import Path

    fixture = json.loads((Path(__file__).parents[1] / 'fixtures/meaning-quiz.json').read_text())
    result = meaning_quiz(translator=Translator(dictionary, lookup_embedder=fixture['lookup_embedder']),
                          **fixture['request'])
    assert result == fixture['response']


def test_quiz_word_classes_cover_every_valid_dictionary_frame():
    from aussiefy.quiz import WORD_CLASSES
    from aussiefy.schema import FRAMES
    assert set(WORD_CLASSES) == set(FRAMES)
