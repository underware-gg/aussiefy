"""Suggestions at an output selection, mapped through the translation's actual edit traces."""

from bisect import bisect_left, bisect_right
from dataclasses import replace
import re
from typing import Sequence

from .changes import Watch, _Builder
from .engine import Spot, SubstitutionRecord, default_translator, resolve_request
from .errors import UserError
from .markdown import DocumentResult, _escape_map
from .offsets import unmap_position
from .translation import translate_changes
from .v3_contract import response_metadata

_WORD = re.compile(r"[^\W_]+(?:[-'’][^\W_]+)*['’]?")


def _intersects(a, b):
    return a[0] < b[1] and b[0] < a[1]


def _snap(text, selected, changes):
    start, end = selected
    words = [match.span() for match in _WORD.finditer(text)]
    while True:
        touching = [span for span in [*words, *(change['out_span'] for change in changes)]
                    if _intersects((start, end), span)]
        expanded = (min([start, *(span[0] for span in touching)]),
                    max([end, *(span[1] for span in touching)]))
        if expanded == (start, end):
            return expanded
        start, end = expanded


def _back(builder, position, side):
    for step in reversed(builder.passes):
        position = unmap_position(step.edits, position, side)
    if builder.closer is not None:
        position = unmap_position([builder.closer.edit], position, side)
    previous = None
    for sentence in builder.sentences:
        start = sentence.trace.start
        end = start + len(sentence.layout.text)
        if start <= position <= end:
            return sentence.offset + sentence.layout.back(position - start, side)
        if position < start:
            return (previous.trace.sent.end + position - previous.trace.start - len(previous.layout.text)
                    if previous else position)
        previous = sentence
    if previous:
        return previous.trace.sent.end + position - previous.trace.start - len(previous.layout.text)
    return position


def _relocate(group, unit):
    if unit is None:
        return group
    _, escape = _escape_map(unit.result.text)
    source, output = unit.source_span[0], unit.output_span[0]
    group['src_span'] = [position + source for position in group['src_span']]
    group['out_span'] = [escape[position] + output for position in group['out_span']]
    for option in [*group['options'], *(word for reading in group['ruled_out'] for word in reading['words'])]:
        a, b = option['out_span']
        rendered, positions = _escape_map(option['rendered'])
        option['rendered'] = rendered
        option['out_span'] = [escape[a] + output, escape[b] + output]
        for annotation in [*option.get('parts', []), *option.get('riffs', []), *option['masks']]:
            field = 'out_span' if 'out_span' in annotation else 'span'
            x, y = annotation[field]
            annotation[field] = [positions[x], positions[y]]
            if 'ending_start' in annotation:
                annotation['ending_start'] = positions[annotation['ending_start']]
            if 'text' in annotation:
                annotation['text'] = rendered[slice(*annotation[field])]
    return group


def _source_frames(tokens, tags, first, last):
    """Require a source role before trying a discovered target's grammatical frame."""
    from . import pos
    from .detect import predicate_context
    from .context import AUXILIARIES
    selected = tags[first:last]
    if selected[-1].startswith('JJ'):
        return {'predicate_adj', 'adj', 'clause'} if predicate_context(tokens, first) is not None else {'adj'}
    if all(tag.startswith('RB') for tag in selected):
        return {'adv'}
    breaks = [-1, *(index for index, tag in enumerate(selected) if tag in {'IN', 'TO'}), len(selected)]
    nominal = [selected[a + 1:b] for a, b in zip(breaks, breaks[1:])]
    if all(chunk and chunk[-1] in pos.NOUNS and all(tag in pos.NOUNS or tag.startswith(('JJ', 'RB'))
             or tag in {'DT', 'CD', 'PRP$', 'POS'} for tag in chunk) for chunk in nominal):
        return {'np'}
    if selected[0] in pos.VERBS and not (len(selected) == 1 and tokens[first].norm in AUXILIARIES):
        return {'vp'}
    return set()


def _fallback(builder, source_span):
    from .lookup import lookup
    from .matcher import PatternIndex, compile_pattern
    from .detect import detect, read_meanings
    from .select import narrow
    from .tuning import Tuning

    output, recognised, protected = [], False, False
    dictionary = builder.translator.dictionary
    for sentence in builder.sentences:
        tokens = sentence.trace.sent.tokens
        indexes = [i for i, token in enumerate(tokens) if token.is_word
                   and _intersects((token.start, token.end), source_span)]
        if not indexes:
            continue
        first, last = min(indexes), max(indexes) + 1
        from . import pos
        selected_tags = sentence.trace.sent.tags[first:last]
        if any(tag in pos.NAMES for tag in selected_tags) or not any(
                tag in pos.NOUNS | pos.VERBS or tag.startswith(('JJ', 'RB')) for tag in selected_tags):
            continue
        start, end = tokens[first].start, tokens[last - 1].end
        # Never turn the ASCII part of a Unicode word into a separate edit.
        if (start > 0 and builder.source[start - 1].isalpha()
                or end < len(builder.source) and builder.source[end].isalpha()):
            continue
        held = builder.run.held(tokens) | {i for i, token in enumerate(tokens)
            if any(_intersects((token.start, token.end), (a, b)) for a, b, _ in builder.run.masked.spans)}
        if any(i in held for i in range(first, last)):
            protected = True
            continue
        source_readings = read_meanings(tokens, dictionary, tags=sentence.trace.sent.tags,
                                       complete=sentence.trace.sent.complete).detections
        if any(reading.source_pattern is not None and reading.source_pattern.fence is not None
               and _intersects((start, end), (tokens[reading.start].start, tokens[reading.end - 1].end))
               for reading in source_readings):
            protected = True
            continue
        query = builder.source[start:end]
        found = lookup(query, translator=builder.translator, level=builder.result.level,
            vulgarity=builder.result.vulgarity, embellishment=builder.result.embellishment.step,
            document_type=builder.result.genre.selected, document_config=builder.run.pol.document_config,
            unlock=builder.run.pol.unlock, limit=8)
        if found['outcome'] == 'left_as_written':
            protected = True
            continue
        recognised |= found['outcome'] in {'matched', 'no_word_yet', 'nothing_fits'}
        following = next((spot for spot in builder.watch.spots
                          if spot.sent.index == sentence.trace.sent.index and spot.rec.span[0] >= start), None)
        state = following.state.copy() if following else sentence.trace.state_after.copy()
        checking = replace(builder.run, pol=replace(builder.run.pol, variety=0), tuning=Tuning(),
                           preferences_used=set())
        source_frames = _source_frames(tokens, sentence.trace.sent.tags, first, last)
        choices, rejected = [], []
        for card in found['results']:
            entry = dictionary.entries[card['id']]
            if entry.frame not in source_frames:
                continue
            frame = 'predicate_adj' if entry.frame == 'clause' else entry.frame
            pattern = compile_pattern(query, frame, entry.concept, 3)
            parsed = detect(tokens, PatternIndex([pattern]), tags=sentence.trace.sent.tags,
                            adjective_nouns=dictionary.adjective_nouns, concepts=dictionary.concepts,
                            complete=sentence.trace.sent.complete, person_nouns=dictionary.person_nouns)
            detection = next((reading for reading in parsed if reading.start == first and reading.end == last), None)
            if detection is None:
                continue
            detection = replace(detection, source_pattern=None)
            candidates, failures = builder.translator.eligible(detection, sentence.trace.sent, checking,
                builder.run.eff, state, held, [entry])
            rejected.extend(failures)
            choices.extend(replace(candidate, reading=candidate.reading or detection) for candidate in candidates)
        choices = narrow(choices, rejected, builder.run.pol.variety, state)
        if choices:
            rec = SubstitutionRecord((start, end), query, choices[0].reading, sentence.trace.sent.index)
            spot = Spot(sentence.trace.sent, rec, choices, state, set(), {}, held, len(sentence.splices))
            group = builder.suggestion(spot)
            group['reading'], group['ruled_out'] = None, []
            output.append(group)
    return output, recognised, protected


def _gaps(span, covered):
    start, end = span
    for a, b in sorted(covered):
        if b <= start or a >= end:
            continue
        if start < a:
            yield start, min(a, end)
        start = max(start, b)
    if start < end:
        yield start, end

def suggest_selection(text: str, *, span: Sequence[int], level: int | str = 5, seed: int = 0,
                      vulgarity: int | str | None = None, variety: int = 0,
                      registers: Sequence[str] | None = None, regions: Sequence[str] | None = None,
                      unlock: Sequence[str] | None = None, markdown: bool = False, markup: str = 'text',
                      english: str | None = None, embellishment: int | str | None = None,
                      document_type: str = 'general', document_config: dict | None = None,
                      themes: dict[str, bool] | None = None, invention: bool | None = None,
                      popularity: bool = False, preferences: list[dict] | None = None, pins: dict | None = None,
                      personal_terms: list[dict] | None = None, _preferences_hook=None, _personal_terms_hook=None,
                      embedder: str | None = None, translator=None) -> dict:
    """Translate once and offer grammatical replacements at a span of that translated output."""
    if (not isinstance(span, (list, tuple)) or len(span) != 2 or any(type(x) is not int for x in span)
            or not 0 <= span[0] < span[1]):
        raise UserError('span must be two ordered output offsets with a non-empty selection')
    translator, document_config = resolve_request(translator, document_config, themes=themes, invention=invention)
    tr = translator or default_translator()
    watches = []
    def watch(index):
        observer = Watch()
        watches.append(observer)
        return observer
    changes = translate_changes(text, translator=tr, level=level, seed=seed, vulgarity=vulgarity, variety=variety,
        registers=registers, regions=regions, unlock=unlock, markdown=markdown, markup=markup, english=english,
        embellishment=embellishment, document_type=document_type, document_config=document_config,
        popularity=popularity, preferences=preferences, pins=pins, personal_terms=personal_terms,
        _preferences_hook=_preferences_hook, _personal_terms_hook=_personal_terms_hook, embedder=embedder, _watch=watch)
    if span[1] > len(changes.text):
        raise UserError('span extends past the translated output')
    selected = _snap(changes.text, tuple(span), changes.changes)
    document = isinstance(changes.result, DocumentResult)
    units = changes.result.units if document else [None]
    builders = [_Builder(tr, observer, unit.result if unit else changes.result)
                for observer, unit in zip(watches, units, strict=True)]
    def source_position(position, side):
        if not document:
            return _back(builders[0], position, side)
        for unit, builder in zip(units, builders, strict=True):
            if unit.output_span[0] <= position <= unit.output_span[1]:
                _, escaped = _escape_map(unit.result.text)
                local = position - unit.output_span[0]
                index = (bisect_right(escaped, local) - 1 if side == 'start' else bisect_left(escaped, local))
                return unit.source_span[0] + _back(builder, index, side)
        for protected in changes.result.protected:
            if protected.output_span[0] <= position <= protected.output_span[1]:
                return protected.source_span[0] + position - protected.output_span[0]
        raise ValueError('document offset is not covered by a prose or protected span')
    source = (source_position(selected[0], 'start'), source_position(selected[1], 'end'))
    groups, recognised, protected = [], False, False
    used_changes = set()
    if document:
        protected = any(_intersects(source, item.source_span) for item in changes.result.protected)
    for unit, builder in zip(units, builders, strict=True):
        offset = unit.source_span[0] if unit else 0
        local = (source[0] - offset, source[1] - offset)
        covered = []
        protected |= any(_intersects(local, (a, b)) for a, b, _ in builder.run.masked.spans)
        for spot in builder.watch.spots:
            if not _intersects(spot.rec.span, local):
                continue
            recognised |= bool(spot.rec.det.concepts)
            fenced = spot.rec.det.source_pattern is not None and spot.rec.det.source_pattern.fence is not None
            protected |= fenced
            if spot.rec.kind in {'kept', 'personal'} or spot.rec.substituted:
                matching = [c for c in changes.changes if c['kind'] == spot.rec.kind
                            and c['src_span'][0] <= spot.rec.span[0] + offset
                            and spot.rec.span[1] + offset <= c['src_span'][1]]
                if matching:
                    change = matching[0]
                    group = {key: change[key] for key in ('src_span', 'out_span', 'reading', 'ruled_out')}
                    group['options'] = change['alternatives']
                    group['origin'] = 'kept' if spot.rec.kind == 'kept' else 'existing'
                    used_changes.add(change['id'])
                    groups.append(group)
                    covered.append(spot.rec.span)
                    continue
            group = builder.suggestion(spot)
            group['origin'] = ('passed_over' if spot.rec.kind == 'substitution' and not fenced
                               and spot.rec.roll is not None else 'lookup')
            groups.append(_relocate(group, unit))
            covered.append(spot.rec.span)
        for gap in _gaps(local, covered):
            fallback, known, blocked = _fallback(builder, gap)
            recognised |= known
            protected |= blocked
            for group in fallback:
                group['origin'] = 'lookup'
                groups.append(_relocate(group, unit))
    for change in changes.changes:
        if change['id'] not in used_changes and change['alternatives'] and _intersects(change['out_span'], selected):
            groups.append({'origin': 'existing', 'src_span': change['src_span'], 'out_span': change['out_span'],
                           'reading': change['reading'], 'ruled_out': change['ruled_out'],
                           'options': change['alternatives']})
    priority = {'passed_over': 0, 'kept': 1, 'lookup': 2, 'existing': 3}
    groups.sort(key=lambda group: (priority[group['origin']], group['src_span']))
    offers = any(group['options'] for group in groups)
    readings = {group['reading']['concept'] for group in groups if group['reading'] is not None}
    reading = next((group['reading'] for group in groups if group['reading']), None) if len(groups) == 1 and len(readings) == 1 else None
    wordless = bool(readings) and readings <= set(tr.dictionary.wordless_meanings)
    outcome = ('matched' if offers else 'left_as_written' if protected else 'no_word_yet' if wordless else
               'nothing_fits' if recognised else 'not_in_dictionary')
    return {'version': 4, **response_metadata(changes.result), 'text': changes.text,
            'src_span': list(source), 'out_span': list(selected), 'outcome': outcome, 'reading': reading,
            'ruled_out': groups[0]['ruled_out'] if len(groups) == 1 else [], 'suggestions': groups}
