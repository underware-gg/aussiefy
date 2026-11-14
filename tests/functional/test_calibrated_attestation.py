"""Source-based weights keep weak repetition and private testimony below attested."""

from aussiefy.evidence import Source, TermMetadata, Testimony as SpeakerSummary, assess


def witness(kind, publisher):
    return Source(kind, publisher, ('term', 'meaning'))


def test_reviewed_evidence_anchors_cross_the_existing_four_bar_boundary(dictionary):
    weights = dictionary.evidence_weights
    assert not weights.provisional and weights.version == '20261114-source-hunt-1'
    for kind, count in [('scholarly_dictionary', 1), ('literature', 2), ('media', 3)]:
        result = assess(TermMetadata(sources=tuple(witness(kind, f'work-{i}') for i in range(count))), weights)
        assert result.evidence == 'attested' and result.attestation.bars >= weights.attested_bars


def test_crowd_volume_and_testimony_alone_do_not_become_attested(dictionary):
    weights = dictionary.evidence_weights
    crowded = TermMetadata(sources=tuple(witness('crowd_dictionary', f'publisher-{i}') for i in range(1000)))
    assert assess(crowded, weights).evidence == 'unverified'
    people = SpeakerSummary(10000, 10000, 10000, None, None, '2026-11-14')
    assert assess(TermMetadata(testimony=people), weights).evidence == 'unverified'


def test_one_publisher_does_not_get_more_votes_from_urls_or_source_kinds(dictionary):
    weights = dictionary.evidence_weights
    one = assess(TermMetadata(sources=(witness('scholarly_dictionary', 'Same Publisher'),)), weights)
    repeated = assess(TermMetadata(sources=(witness('media', 'same publisher'),
                                            witness('literature', ' Same Publisher '),
                                            witness('scholarly_dictionary', 'Same Publisher'))), weights)
    assert one.attestation == repeated.attestation


def test_unsupported_components_and_explicit_coinage_keep_their_distinct_labels(dictionary):
    weights = dictionary.evidence_weights
    partial = Source('media', 'Primary page', ())
    assert assess(TermMetadata(sources=(partial,)), weights).attestation.score == 0
    coined = TermMetadata(coined_by='agent', sources=(witness('scholarly_dictionary', 'Edited dictionary'),))
    assert assess(coined, weights).evidence == 'bulldust'
