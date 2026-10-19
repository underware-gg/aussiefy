"""Read-only current engine diagnostics. Own-work literals; reference text remains at source."""
import argparse
import cProfile
import hashlib
import json
from pathlib import Path
import platform
import pstats
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, required=True, help='local output directory outside the repository')
OUT = parser.parse_args().out.resolve()
if OUT.is_relative_to(ROOT):
    parser.error('Full reference outputs must remain outside the repository')
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from aussiefy import Translator
from aussiefy.harness import lookup, verify
from aussiefy.static import MODEL_DIR, dictionary_fingerprint
from _checks import assert_well_formed

def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + '\n')

CHALLENGES = {
 'showcase': "Hi everyone, the meeting this afternoon is cancelled. I'm sick and very tired, so I'll be working from home tomorrow. Thanks for understanding.",
 'hunger': "I'm feeling pretty hungry. I wasn't hungry earlier, but now I'm very hungry.",
 'hunger_attribute': 'The hungry children waited for dinner. Hunger made the journey difficult.',
 'hunger_complement': "I feel hungry enough to eat anything. She said she could do with some food.",
 'address': 'Good morning, everyone. Please take a seat. Everyone received the report.',
 'address_complex': 'Thank you, everyone who stayed late. Everyone in the office was helpful.',
 'degree': 'She is tipsy, but he is legless. He is slightly drunk. She is very drunk.',
 'degree_negation': 'She is not very drunk. He is almost drunk. She is barely drunk.',
 'quantity': 'Four score and seven years ago, they built the town. The tank holds 87 litres and feeds 12 valves.',
 'technical': 'Close the valve before the pressure reaches 120 kPa. Do not increase the temperature above 40 degrees.',
 'work': 'She worked hard to finish the report. The report was hard to finish. Her hard work paid off.',
 'work_polysemy': 'The labour lasted six hours. Her artwork was beautiful. The new machine works well.',
 'intention': 'He tried to open the door, but it was locked. She tried the soup and tasted salt.',
 'polarity': 'That is not impossible. It is not out of the question. I doubt it, but I cannot rule it out.',
 'modality': 'They might arrive tomorrow. They must leave now. They should call before coming.',
 'certainty': 'She will probably come. He is definitely coming. We are not sure whether the plan will work.',
 'alone': 'She lives alone but does not feel lonely. He feels lonely in the crowd.',
 'party': 'The party was really lively. The angry customer shouted at the manager.',
 'noun_compounds': 'The glossy ibis stood beside the wheeled bin. The antennae of the insect moved.',
 'professional': 'The comedian was not funny. The nice person helped a child. The good man thanked her.',
 'movement': 'She walked home. He walked there. They walked to the hospital.',
 'solemn': 'Our friend died yesterday. We remember the people who died and the soldiers who survived.',
 'embedded': 'The engineer who was very tired checked the valve that had broken before he went home.',
 'morphology': 'I was hungry. They were hungry. We have been hungry. She will be hungry soon.',
}

tr = Translator(lookup_embedder=None)
metadata = {'git_head': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
            'python':sys.version,'platform':platform.platform(),'machine':platform.machine(),
            'dictionary_sha256':dictionary_fingerprint(),
            'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'bundled_model':{'version':json.loads((MODEL_DIR/'meta.json').read_text())['version'],
                'sha256':{name:hashlib.sha256((MODEL_DIR/name).read_bytes()).hexdigest()
                          for name in ('meta.json','vocab.txt','vectors.f16')}},
            'purpose':'Fixed known-diagnostic and new composed sentences; not held-out generalisation or a blind judge.',
            'seeds':[0,1,42], 'level':5,'vulgarity':2,'document_type':'auto'}
save('metadata.json', metadata)
rows=[]
for name,text in CHALLENGES.items():
    for mode in ('none','ngram','bundled'):
        for step in ('deadset','dinkum','troppo'):
            for seed in metadata['seeds']:
                result=tr.translate(text,level=5,vulgarity=2,seed=seed,document_type='auto',embellishment=step,embedder=mode)
                rows.append({'case':name,'source':text,'mode':mode,'step':step,'seed':seed,
                             'genre':result.genre.name,'text':result.text,
                             'swaps':[{'source':r.text,'output':r.output,'concepts':r.det.concepts,
                                       'entry':r.chosen.entry.id} for r in result.records if r.substituted]})
save('challenge-outputs.json',rows)
print('challenge rows',len(rows),flush=True)

references=[]
for path in sorted((ROOT/'tests/corpus/reference').glob('*.txt')):
    source=path.read_text()
    for step in ('deadset','dinkum','troppo'):
        for seed in (0,42):
            r=tr.translate(source,level=5,vulgarity=2,seed=seed,document_type='auto',embellishment=step)
            structural_error=None
            try: assert_well_formed(source,r,path.name)
            except AssertionError as e: structural_error=str(e)[:160]
            check=verify(r.text,original=source,level=5,vulgarity=2,embellishment=step,document_type='auto',translator=tr)
            references.append({'path':str(path.relative_to(ROOT)), 'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                'step':step,'seed':seed,'genre':r.genre.name,'words':len(source.split()),'text':r.text,
                'substitutions':sum(x.substituted for x in r.records),'structural_error':structural_error,
                'verification':check})
save('reference-outputs.json',references)
print('reference rows',len(references),'structural failures',sum(bool(x['structural_error']) for x in references),flush=True)

queries=['feeling pretty hungry','hungry','could do with some food','a cold one at the pub','probably',
         'wake up','not out of the question','very tired','hard to finish','worked hard','everyone',
         'alone','lonely','a small bottle of beer','a can of beer']
lookups=[]
for backend in (None,'bundled'):
    lt=Translator(tr.dictionary,lookup_embedder=backend)
    for q in queries:
        start=time.perf_counter()
        result=lookup(q,level=5,vulgarity=2,embellishment='dinkum',limit=5,translator=lt)
        lookups.append({'backend':backend or 'lexical','query':q,'seconds':time.perf_counter()-start,'result':result})
save('lookup.json',lookups)
print('lookup complete',flush=True)

# Warm timings: distinct current modes rotate order; startup and loading excluded.
timings=[]
for name,text in [('showcase',CHALLENGES['showcase']),('composed', ' '.join(CHALLENGES.values()))]:
    options=dict(level=4,vulgarity=1,seed=42,embellishment=1,document_type='general')
    times={m:[] for m in ('none','ngram','bundled')}
    outputs={m:tr.translate(text,embedder=m,**options).text for m in times}
    for repeat in range(7):
        order=list(times); offset=repeat%len(order)
        for m in order[offset:]+order[:offset]:
            start=time.perf_counter()
            result=tr.translate(text,embedder=m,**options)
            times[m].append(time.perf_counter()-start)
            assert result.text==outputs[m]
    timings.append({'input':name,'characters':len(text),'words':len(text.split()),'options':options,
        'modes':{m:{'median_ms':1000*statistics.median(ts),'seconds':ts,
                    'output_sha256':hashlib.sha256(outputs[m].encode()).hexdigest()} for m,ts in times.items()}})
save('core-mode-timings.json',timings)
profile=cProfile.Profile()
profile.runcall(tr.translate,' '.join(CHALLENGES.values()),level=4,vulgarity=1,seed=42,embellishment=1,embedder='bundled')
with (OUT/'bundled-profile.txt').open('w') as stream:
    pstats.Stats(profile,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(45)
print('timings complete',flush=True)
