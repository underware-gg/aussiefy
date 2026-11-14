"""Real expression forms survive morphology controls and lookup capitalisation."""

import pytest

from aussiefy import Translator, lookup
from aussiefy.detect import read_meanings
from aussiefy.morph import plural_forms, singular_of, verb_forms
from aussiefy.text import tokenize


# Reviewed independently of compiled patterns: a new fixed-head decision needs its
# real forms here, so a lost inflection cannot vanish from the test's own inputs.
FIXED_REAL_FORMS = (
    'silence was broken', 'silence is broken', 'spell was broken', 'spell is broken',
    'record was broken', 'record is broken', 'records were broken', 'promise was broken',
    'promises were broken', 'law was broken', 'laws were broken', 'rules were broken',
    'rule was broken', 'ice was broken', 'news was broken', 'deadlock was broken',
    'fast was broken', 'will was broken', 'spirit was broken', 'was heartbroken',
    'the horse has bolted', 'horse has bolted', 'the horse had bolted', 'horse had bolted',
    'the horse has already bolted', 'horse has already bolted', 'the horse is bolted',
    'dedicated to', 'dedicated here to', 'dedicated there to', 'here dedicated to',
    'a dollar is worth', 'the dollar is worth', 'dollar is worth', 'dollars are worth',
    'the boys in blue', '{poss} hands are tied', '{poss} hands were tied', 'hands down',
    '{poss} hands full', 'hands full', 'the gift of the gab', 'shy and retiring',
    'quiet and retiring', 'modest and retiring', 'toss up', 'toss ups', 'toss-up', 'toss-ups',
)


SOURCE_FIXED_FORMS = {
    'barbie doll|dolls': ('Barbie doll', 'barbie dolls'),
    'railway|railroad|train|bus|police|radio|television|tv|fire|space station|stations':
        ('railway station', 'railway stations', 'police stations', 'radio stations'),
    'station wagon|wagons': ('station wagon', 'station wagons'),
    'a|an|the|this|that|these|those|some|my|your|his|her|our|their|its flat strap':
        ('a flat strap', 'the flat strap', 'his flat strap'),
    'a|an|the|this|that|these|those|some|my|your|his|her|our|their|its flat-strap':
        ('a flat-strap', 'the flat-strap'),
}


def test_real_forms_survive_every_fixed_head_decision(dictionary):
    reviewed = set(FIXED_REAL_FORMS) - {'toss up', 'toss ups', 'toss-up', 'toss-ups'}
    assert {f.phrase for f in dictionary.fences if not f.inflect_head} == reviewed | SOURCE_FIXED_FORMS.keys()
    tr = Translator(dictionary, lookup_embedder=None)
    for template in (*FIXED_REAL_FORMS, *(form for forms in SOURCE_FIXED_FORMS.values() for form in forms)):
        for poss in ('my', 'your', 'his', 'her', 'its', 'our', 'their') if '{poss}' in template else ('',):
            phrase = template.replace('{poss}', poss)
            tokens = tokenize(phrase)
            readings = read_meanings(tokens, dictionary, fragment=True).detections
            assert any(r.start == 0 and r.end == len(tokens) and r.source_pattern
                       and r.source_pattern.fence is not None for r in readings), phrase
            result = lookup(phrase, translator=tr, vulgarity=2)
            if phrase in WHOLE_EXPRESSION_ENTRIES:
                assert result['outcome'] == 'matched'
                assert WHOLE_EXPRESSION_ENTRIES[phrase] <= {row['id'] for row in result['results']}
            else:
                assert result['outcome'] == 'left_as_written', (phrase, result)
                assert all(p['reason'] or p['ruled_out'] for p in result['protections']), phrase


@pytest.mark.parametrize('seed', range(8))
@pytest.mark.parametrize('phrase', ['toss ups', 'toss-ups'])
def test_plural_toss_up_is_not_a_throw(dictionary, seed, phrase):
    tr = Translator(dictionary, lookup_embedder=None)
    source = f'Both marginal seats are {phrase}.'
    result = tr.translate(source, level=5, vulgarity=2, embellishment=0, english='none',
                          embedder='none', seed=seed)
    assert result.text == source
    assert not any('THROW' in r.det.concepts for r in result.records)
    result = lookup(phrase, translator=tr, vulgarity=2)
    assert result['outcome'] == 'left_as_written' and not result['results']


def _simple_forms(fence):
    """Literal/possessive expressions and head forms; reviewed fixed forms remain independent."""
    if any(c in fence.phrase for c in '?!@^'):
        return ()
    phrase = fence.phrase.replace('{poss}', 'their')
    if any(c in phrase for c in '{}'):
        return ()
    bases = (phrase,)
    if '|' in phrase:
        stem, _, head = phrase.rpartition(' ')
        pair = head.split('|')
        if ('|' in stem or len(pair) != 2 or fence.frame != 'np'
                or singular_of(pair[1]) != pair[0].lower()):
            return ()
        bases = tuple(f'{stem} {form}'.strip() for form in pair)
    forms = set(bases)
    for phrase in bases:
        if fence.inflect_head and fence.frame == 'np':
            stem, _, head = phrase.rpartition(' ')
            if head.isalpha() and not singular_of(head):
                forms.update(f'{stem} {form}'.strip() for form in plural_forms(head))
        elif fence.inflect_head and fence.frame == 'vp':
            head, _, tail = phrase.partition(' ')
            forms.update(f'{form} {tail}'.strip() for form in verb_forms(head.lower()))
    return tuple(sorted(forms))


# Explicit reviewed whole-expression exceptions, never inferred from a failing lookup.
WHOLE_EXPRESSION_ENTRIES = {
    # Existing whole-term priority remains: these literal source controls also name the complete Aussie term.
    'a flat strap': {'flat-strap-busy', 'flat-strap-fast'},
    'the flat strap': {'flat-strap-busy', 'flat-strap-fast'},
    'a flat-strap': {'flat-strap-busy', 'flat-strap-fast'},
    'the flat-strap': {'flat-strap-busy', 'flat-strap-fast'},
    'his flat strap': {'flat-strap-busy', 'flat-strap-fast'},
    "dog's breakfast": {'dogs-breakfast', 'g-aside-dogs-breakfast'},
    "dog's breakfasts": {'dogs-breakfast', 'g-aside-dogs-breakfast'},
    'rainforest': {'the-brush'},
    # Already an explicit BEER_CAN concept-ID lookup before the new source fence.
    'beer can': {'tinnie'},
    'rainforests': {'the-brush'},
    'ranch hands': {'a-stockman'},
}


def test_every_simple_fence_and_inflection_survives_lookup_casing(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    failures = []
    for fence in dictionary.fences:
        for phrase in _simple_forms(fence):
            for query in dict.fromkeys((phrase, phrase.lower(), phrase.title(), phrase.upper())):
                result = lookup(query, translator=tr, vulgarity=2)
                if result['outcome'] == 'left_as_written':
                    assert not result['results'], query
                    for protection in result['protections']:
                        assert query[slice(*protection['span'])] == protection['original'], query
                        assert protection['reason'] or protection['ruled_out'], query
                else:
                    allowed = WHOLE_EXPRESSION_ENTRIES.get(query.lower(), set())
                    if (result['outcome'] != 'matched' or not result['results']
                            or not {r['id'] for r in result['results']} <= allowed):
                        failures.append((query, result['outcome'], [r['id'] for r in result['results']]))
    assert failures == []


AMERICAN_GROUP_PREFIXES = (
    'African', 'Native', 'Asian', 'Latin', 'Hispanic', 'Mexican', 'Japanese', 'Chinese', 'Korean',
    'Indian', 'Arab', 'Muslim', 'Jewish', 'Irish', 'Italian', 'Filipino', 'Cuban', 'Latino',
    'Indigenous', 'black', 'white', 'South', 'Central', 'North', 'LGBT', 'LGBTQ',
)


@pytest.mark.parametrize('prefix', AMERICAN_GROUP_PREFIXES)
def test_every_american_identity_has_both_number_forms(dictionary, prefix):
    fence = next(f for f in dictionary.fences if f.phrase == f'{prefix} American|Americans')
    tr = Translator(dictionary, lookup_embedder=None)
    for number in ('American', 'Americans'):
        phrase = f'{prefix} {number}'
        for query in dict.fromkeys((phrase, phrase.lower(), phrase.title(), phrase.upper())):
            result = lookup(query, translator=tr, vulgarity=2)
            assert result['outcome'] == 'left_as_written' and result['results'] == [], query
            protection, = result['protections']
            assert query[slice(*protection['span'])] == query, query
            assert protection['reason'] == fence.reason and (protection['reason'] or protection['ruled_out'])
    source = f'They met a {prefix} American yesterday.'
    result = tr.translate(source, level=5, vulgarity=2, embellishment=0, embedder='none', english='none')
    assert f'{prefix} American' in result.text


@pytest.mark.parametrize('query', ['Native Americans and hungry', 'National Forest and hungry'])
def test_capitalised_protection_keeps_independent_meanings(query, dictionary):
    result = lookup(query, translator=Translator(dictionary, lookup_embedder=None), vulgarity=2)
    assert result['outcome'] == 'matched' and 'protections' not in result
    assert result['results'] and all('HUNGRY' in word['concepts'] for word in result['results'])


def test_authored_protections_do_not_license_replacements_inside_other_names(dictionary):
    readings = read_meanings(tokenize('Boston University'), dictionary, fragment=True).detections
    assert not readings


def test_capitalised_query_spans_preserve_original_offsets(dictionary):
    query = '  Native Americans  '
    result = lookup(query, translator=Translator(dictionary, lookup_embedder=None))
    assert result['query'] == query and result['outcome'] == 'left_as_written'
    protection, = result['protections']
    assert protection['original'] == 'Native Americans' and protection['span'] == [2, 18]
    assert protection['ruled_out']


@pytest.mark.parametrize('query', ['the toss', 'The Toss', 'THE TOSS', 'The toss'])
def test_the_toss_is_not_the_death_idiom(dictionary, query):
    result = lookup(query, translator=Translator(dictionary, lookup_embedder=None), vulgarity=2)
    assert result['outcome'] == 'left_as_written' and not result['results']


def test_complete_death_idiom_remains_discoverable(dictionary):
    result = lookup('toss in the alley', translator=Translator(dictionary, lookup_embedder=None),
                    vulgarity=2, include_gated=True)
    assert result['outcome'] == 'matched'
    assert any(word['id'] == 'toss-in-the-alley' and word['match_kind'] == 'term'
               for word in result['results'])


@pytest.mark.parametrize('source', [
    'We camped in the Kaibab National Forest.',
    'The Gulf Stream warms Europe.',
    'Native Americans were here first.',
    'The bill passed the US Congress.',
    'Several Native Americans spoke.',
    'Most Asian Americans voted.',
    'A National Forest is public land.',
])
def test_names_with_protected_phrases_still_translate_safely(dictionary, source):
    tr = Translator(dictionary, lookup_embedder=None)
    for seed in range(3):
        result = tr.translate(source, level=5, vulgarity=2, embellishment=0, english='none',
                              embedder='none', seed=seed)
        assert result.text == source
