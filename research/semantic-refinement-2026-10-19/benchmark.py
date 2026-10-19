"""Bounded warm-translation timings; run each checkout separately with PYTHONPATH."""
import json
from pathlib import Path
import statistics
import time
import aussiefy
from aussiefy import Translator, load_dictionary

SAMPLES = {
    'ordinary': [
        'The young man arrived late. His wife had cooked dinner for the children.',
        'We drove to the service station, bought some food and went to the beach.',
        'The politician gave a speech about the difficult work ahead.',
        'My friend said the new house was wonderful, but the car was broken.',
        'He thanked his fellow Texans and his fellow citizens.',
        'The engineer carefully checked the pressure before opening the valve.',
    ],
    'degree': [
        'She is tipsy, and he is legless.',
        'She is very drunk. He is slightly drunk.',
        'She is not very drunk. He is very pissed.',
        'She was so drunk that she fell asleep.',
        'They are drunk. She is very sozzled.',
        'She is very tipsy. He is slightly legless.',
    ],
}
tr=Translator(load_dictionary(), lookup_embedder=None)
rows=[]
for name,texts in SAMPLES.items():
    for embellishment,vulgarity in [('deadset',0),('troppo',3)]:
        def batch(repeats):
            for seed in range(repeats):
                for text in texts:
                    tr.translate(text,level=5,seed=seed,vulgarity=vulgarity,embellishment=embellishment)
        batch(3)
        samples=[]
        for _ in range(5):
            before=time.perf_counter(); batch(30); samples.append(time.perf_counter()-before)
        rows.append({'corpus':name,'embellishment':embellishment,'vulgarity':vulgarity,
                     'translations_per_batch':30*len(texts),'seconds':samples,
                     'median_ms_per_translation':1000*statistics.median(samples)/(30*len(texts))})
print(json.dumps({'module':str(Path(aussiefy.__file__).resolve()),'samples':SAMPLES,'timings':rows},indent=2))
