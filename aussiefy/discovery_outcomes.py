"""Machine-readable outcomes shared by dictionary discovery surfaces."""

MATCHED = 'matched'
NOTHING_FITS = 'nothing_fits'
OUTSIDE_DIALS = 'outside_dials'
NOT_IN_DICTIONARY = 'not_in_dictionary'
NO_WORD_YET = 'no_word_yet'
LEFT_AS_WRITTEN = 'left_as_written'
PAGE_EXHAUSTED = 'page_exhausted'
REMOVED = 'removed'

OUTCOMES = frozenset({MATCHED, NOTHING_FITS, OUTSIDE_DIALS, NOT_IN_DICTIONARY, NO_WORD_YET, LEFT_AS_WRITTEN, PAGE_EXHAUSTED, REMOVED})
MATCH_KINDS = frozenset({'term', 'phrase', 'meaning', 'model'})
