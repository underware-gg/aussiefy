"""Render every authored concept example, retaining unmet R64 cases as explicit coordination evidence."""
from __future__ import annotations

from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from aussiefy import Translator
from aussiefy.changes import Watch
from aussiefy.plain_wording import plain_entry
from aussiefy.select import Candidate

MODALS = re.compile(r'\b(?:can|could|would|should|may|might|must|shall|will)\b', re.I)
DOUBLE = re.compile(r'\b([a-z]+)\s+\1\b', re.I)


def audit(translator=None):
    tr = translator or Translator(lookup_embedder=None)
    rows = []
    for cid, concept in tr.dictionary.concepts.items():
        for example in concept.examples:
            watch = Watch()
            tr.translate(example, level=5, vulgarity=0, embellishment=0, embedder=None, _observer=watch,
                         document_config={'garnish': [], 'profile': {'phonetic': 0, 'stack': 0}})
            spots = [spot for spot in watch.spots if cid in spot.rec.det.concepts]
            if not spots:
                raise AssertionError(f'example has no source reading: {cid}: {example}')
            for spot in spots:
                row = {'concept': cid, 'example': example, 'source_span': list(spot.rec.span)}
                plain = plain_entry(concept, spot.rec.det, tr.dictionary, tokens=spot.sent.tokens, tags=spot.sent.tags)
                if plain is None:
                    row.update(status='needs_sentence_form', source_preserved=True,
                               reason='No safe authored sentence wording for this grammatical scope.')
                else:
                    candidate = Candidate(plain[0], 0, 'plain English', kind='plain', reading=plain[1])
                    rendering = tr.render_at_spot(candidate, spot, replace(watch.run, state=spot.state.copy()))
                    if rendering.echo:
                        raise AssertionError(f'example sentence wording echoes its context: {cid}: {example}')
                    a, b = spot.sent.tokens[rendering.start].start, spot.sent.tokens[rendering.end-1].end
                    whole = example[:a] + rendering.text + example[b:]
                    issues = []
                    if re.search(r'[{}<>]', rendering.text):
                        issues.append('leftover slot or markup')
                    if re.search(r'[.;:!?]', rendering.text):
                        issues.append('internal sentence punctuation')
                    if DOUBLE.search(whole) and not DOUBLE.search(example):
                        issues.append('new doubled word')
                    if Counter(MODALS.findall(whole.lower())) != Counter(MODALS.findall(example.lower())):
                        issues.append('changed modality')
                    row.update(status='needs_sentence_form' if issues else 'rendered', rendered=rendering.text,
                               whole=whole, issues=issues)
                rows.append(row)
    unresolved = [row for row in rows if row['status'] != 'rendered']
    return {'requirement': 'R64: every authored example renders safely with sentence wording',
            'dictionary_id': tr.dictionary.identity, 'examples': len(rows), 'rendered': len(rows)-len(unresolved),
            'all_examples_meet_R64': not unresolved, 'unresolved': unresolved, 'rows': rows}


if __name__ == '__main__':
    report = audit()
    Path(__file__).with_name('plain-example-audit.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'rows'}, indent=2))
