"""Exact owned spans survive sequential rules without protecting identical words elsewhere."""

import re
from dataclasses import replace

from aussiefy.garnish import apply_phonetic, PhoneticTrace
from aussiefy.model import PhoneticRule


def rule(key, before, after):
    return PhoneticRule(key, re.compile(before), after, 1, 1, kind='spelling')


def test_literal_coordinates_follow_prior_length_changes(dictionary):
    from aussiefy import Translator
    eff = Translator(dictionary).effective(level=5, vulgarity=0)
    trace = PhoneticTrace(None, None)
    text, records = apply_phonetic('one keep two keep',
        [rule('grow', 'one', 'eleven'), rule('change', 'keep', 'changed')], eff, 0,
        literal_spans=((4, 8),), trace=trace)
    assert text == 'eleven keep two changed'
    assert [(r.before, r.after) for r in records] == [('one', 'eleven'), ('keep', 'changed')]
    assert trace.passes[0].literal == ((4, 8),)
    assert trace.passes[1].literal == ((7, 11),)
    assert trace.passes[1].starts == [7, 16]


def test_whole_match_is_blocked_when_only_its_end_intersects_owned_words(dictionary):
    from aussiefy import Translator
    eff = Translator(dictionary).effective(level=5, vulgarity=0)
    rules = [rule('cross', 'one keep', 'different'), rule('tail', 'two', 'second')]
    assert apply_phonetic('one keep two', rules, eff, 0, literal_spans=((4, 8),))[0] == 'one keep second'
    assert apply_phonetic('one keep two', rules, eff, 0)[0] == 'different second'


def test_skipped_literal_matches_retain_the_same_rule_counter(dictionary):
    from aussiefy import Translator
    eff = Translator(dictionary).effective(level=5, vulgarity=0)
    trace = PhoneticTrace(None, None)
    text, _ = apply_phonetic('keep keep keep', [replace(rule('each', 'keep', 'changed'), prob=.5)], eff, 0,
                             trace=trace, literal_spans=((5, 9),))
    assert text == 'keep keep changed'
    assert trace.passes[0].starts == [0, 5, 10]


def test_an_emphasis_edit_owns_its_head_across_later_rules(dictionary):
    from aussiefy import Translator
    eff = Translator(dictionary).effective(level=5, vulgarity=2)
    eff = replace(eff, swearing=replace(eff.swearing, infix=10))
    rules = [
        PhoneticRule('prefix', re.compile(r"(?=good)"), "bloody ", 1, None, vulgarity=1),
        PhoneticRule('tail', re.compile(r"bloody good"), "good as fuck", 1, None, vulgarity=2),
        PhoneticRule('another-prefix', re.compile(r"(?=good)"), "fuckin' ", 1, None, vulgarity=2),
    ]
    text, records = apply_phonetic('very good; very good', rules, eff, 0)
    assert text == 'very bloody good; very bloody good'
    assert [record.rule for record in records] == ['prefix', 'prefix']
    # The same ownership follows changed lengths and admits a separate head.
    rules[0] = replace(rules[0], pattern=re.compile('very good'), replace='good as fuck')
    assert apply_phonetic('very good; very good', rules, eff, 0)[0] == 'good as fuck; good as fuck'


def test_allocated_degree_and_stack_spans_block_only_further_emphasis(dictionary):
    from aussiefy import Translator
    eff = Translator(dictionary).effective(level=5, vulgarity=2)
    eff = replace(eff, swearing=replace(eff.swearing, infix=10))
    rules = [rule('drawl', 'coming', "comin'"),
             PhoneticRule('prefix', re.compile(r"(?=good)"), "bloody ", 1, None, vulgarity=1)]
    text = 'coming dead good; very good'
    owned = ((7,16),)
    assert apply_phonetic(text, rules, eff, 0, emphasis_spans=owned)[0] == "comin' dead good; very bloody good"


def test_possessive_and_adjective_emphasis_compete_for_the_same_modified_head(dictionary):
    from aussiefy import Translator
    eff = Translator(dictionary).effective(level=5, vulgarity=2)
    eff = replace(eff, swearing=replace(eff.swearing, infix=10))
    rules = [PhoneticRule('adj', re.compile(r"(?=good)"), 'bloody ', 1, None, vulgarity=1),
             PhoneticRule('poss', re.compile(r"my "), 'my bloody ', 1, None, vulgarity=1)]
    for degree in ('very', 'really', 'exceptionally'):
        text = f'we saw my {degree} good car and my dog'
        assert apply_phonetic(text,rules,eff,0)[0] == f'we saw my {degree} bloody good car and my bloody dog'
