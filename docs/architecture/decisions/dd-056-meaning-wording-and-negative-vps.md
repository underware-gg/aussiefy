# DD-056: separate meaning wording and exact discovery

Status: accepted implementation direction for slice 7; 13 November 2026.

R64 gives a concept three separate jobs. Keep `plain` as the display name, add exact `search_words`
for lookup only, and add optional `plain_forms` by grammatical frame for sentence rendering. Missing
sentence forms default to the display wording where it fits. Reuse entry slot/frame validation; reject
markup, sentence punctuation and malformed forms at load. These are dictionary fields, not new fields
in the frozen changes/card v3 response. Later slice 7 producers will render plain alternatives through
the same fit and splice path as entries.

Exact authored names and search aliases both establish and score the named meaning. Incidental
readings of a name's component words cannot prevent its own words being offered. Search words never
become automatic source patterns, and sentence forms never become search words implicitly. Explicit
concept IDs remain a discovery route. Review collisions against actual meanings rather than assuming
that hiding a previous result proves a fault; Rob's marked sample overrides its older draft tables.

Optional imagery is not a dictionary word. A recognised meaning with only imagery remains waiting,
and eligible imagery can accompany `no_word_yet`. Keep the image and its maker; do not delete it to
repair discovery. Named queries select images for their named meaning under the same permissions.
The existing construction/dialect exclusion is unchanged in this checkpoint.

Rob approved the HEART_SPIRIT split (courage retains the ID; compassion and effort gain IDs) and
puffed for BREATHLESS only, level 1 / Nan, shared English. Puffed uses the ordinary lexical adjective
frame, which can fill a predicate slot at level 1. The idiom-style predicate-adjective frame is not
enabled there. No global level/frame permission is widened. Record the six vocabulary forms and the
rate/don't-rate pair together on one-person testimony, without fabricated publications or first-use dates.
The two oily-rag senses need two grammatical entry records: continuing with little energy is a
predicate phrase, while getting by with little money is an inflected verb phrase.

Negative verb phrases need grammatical realisation rather than inflection of the word “don't”. The
shared reader records the governing VP auxiliary, including inverted subjects. Realisation retains an
outer modal/infinitive, handles perfect/progressive forms, and otherwise inflects do-support. This is a
grammar rule over a form's shape, not a rate-specific exception. Scoring uses and rating requests are
reviewed phrase fences; person-supported evaluation patterns stay separate. Actual source-slot tests
cover tense, questions, modals and wrong senses.

This checkpoint does not implement kept/held changes, personal terms, selection or ED14 browsing,
finish all concept wording or freeze the later slice 7 response version. The accepted v3 schemas and
historical freeze bundle remain unchanged. Full checkpoint gates and remaining curation decisions
are recorded in the Brain report.
