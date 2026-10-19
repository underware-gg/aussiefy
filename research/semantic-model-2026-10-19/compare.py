"""Bounded current-dictionary lookup comparison; run in the pinned training environment."""
import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, '/Users/robmorris/Development/Underware/aussiefy')
from aussiefy import Translator
from aussiefy.harness import lookup
from aussiefy.loader import load_dictionary
from aussiefy.static import StaticEmbedder, dictionary_fingerprint
from scripts import train_embedder as t

t.R = t.load_recipe()
dictionary = load_dictionary()
queries_path = Path('/private/tmp/aussiefy-maintenance-model-queries.json')
queries = json.loads(queries_path.read_text())
queries['historical_queries'] = list(queries['queries'])
queries['new_audit_queries'] = ['a cold one at the pub', 'feeling lonely in a crowd', 'lonely', 'alone', 'a small bottle of beer', 'a can of beer', 'beer', 'pounds sterling']
queries['new_audit_selection'] = 'Current source-audit distinctions and diagnosed reference failure, selected before candidate measurements; not an unseen test claim.'
queries['queries'] += queries['new_audit_queries']
work = Path('/private/tmp/aussiefy-semantic-model-20261019/work')

class TrialEmbedder:
    """The existing injectable Embedder protocol, reading isolated Model2Vec trial artifacts."""
    name = 'isolated candidate Model2Vec static; not package export'
    lookup_threshold = t.R['cutoffs']['lookup']
    gaps_confident = t.R['cutoffs']['gaps']

    def __init__(self):
        self.model = t.Static(work / 'release' / 'static-aussie-tuned')

    @lru_cache(maxsize=8192)
    def encode(self, text):
        return tuple(float(v) for v in self.model.encode([text])[0])

    def similarity(self, a, b):
        return sum(x*y for x,y in zip(self.encode(a), self.encode(b)))

settings = {'level':5,'vulgarity':'uncle-bob','limit':8,'embellishment':'dinkum','document_type':'general'}
rows=[]
for label, encoder in [('shipped1.2.0', StaticEmbedder()), ('candidate_full_fit', TrialEmbedder())]:
    translator = Translator(dictionary, lookup_embedder=encoder)
    results = [{'query':q,'result':lookup(q, translator=translator, **settings)} for q in queries['queries']]
    rows.append({'model':label,'encoder':encoder.name,'lookups':results})
ref = t.reference(dictionary,t.Static(work/'release'/'static-aussie-tuned'),t.R['cutoffs']['lookup'])
report = {'purpose':'Actual shared lookup ranking under a fixed policy; candidate uses isolated Model2Vec adapter, not package-reader parity.',
          'dictionary_sha256':dictionary_fingerprint(),'recipe_sha256':t.sha256(t.RECIPE_PATH),
          'trainer_sha256':t.sha256(Path(t.__file__)),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'query_selection':queries,'settings':settings,'models':rows,'candidate_final_reference':ref, 'shipped_final_reference':t.reference(dictionary,t.Bundled(),t.R['cutoffs']['lookup'])}
Path('/private/tmp/aussiefy-semantic-model-20261019/comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print('Candidate final reference:',ref['passed'],'/',ref['required'])
print('Failed required:',[r['query'] for r in ref['checks'] if not r['known'] and not r['pass']])
