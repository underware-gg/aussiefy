"""Headword collation is separate from the site's looser word-page grouping."""
import pytest

from aussiefy.terms import headword_key


@pytest.mark.parametrize('form, expected', [
    ('a Hanrahan', 'hanrahan'), ('AN earbashing', 'earbashing'), ('The bush', 'bush'),
    ('  A \t counter   meal  ', 'counter meal'), ('fair dinkum.', 'fair dinkum'),
    ('a bludger', 'bludger'), ('a stuff-up', 'stuff-up'), ('stuff up', 'stuff up'),
    ("The cat’s whiskers", "cat's whiskers"), ('another thing', 'another thing'),
    ('Some bludger', 'some bludger'), ('a the bush', 'the bush'), ('A', 'a'),
    ('an Éclair', 'éclair'), ('a 3D term', '3d term'), ('a {poss} mate', '{poss} mate'),
])
def test_article_free_key_preserves_punctuation_hyphens_and_slots(form, expected):
    assert headword_key(form) == expected
