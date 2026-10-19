"""Verify the fixed current cohort and recheck known previous errors; retain no complete outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from aussiefy import Translator
from aussiefy.harness import verify
from aussiefy.static import dictionary_fingerprint

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--before',type=Path,required=True)
parser.add_argument('--after',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
tr=Translator(lookup_embedder=None)

def check(row):
 result=verify(row['text'],original=row['source'],level=5,vulgarity=2,
               embellishment=row['step'],document_type='auto',translator=tr)
 return {**{k:row[k] for k in ['case','mode','step','seed']},'ok':result['ok'],
         'counts':result['counts'],'problems':[{k:p[k] for k in ['kind','severity']}
                                             for p in result['problems']]}

previous=json.loads((args.before/'challenge-outputs.json').read_text())
known=[r for r in previous if (r['case']=='hunger_complement' and r['text'].lower().count('enough')>1)
       or (r['case']=='hunger' and "now I'm peckish" in r['text'])]
current=json.loads((args.after/'challenge-outputs.json').read_text())
result={'scope':'Known diagnostic cohort, not unseen generalisation. Bounded verification may abstain when other edits prevent local source pairing.',
        'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'packet_sha256':{label:hashlib.sha256((folder/'challenge-outputs.json').read_bytes()).hexdigest()
                         for label,folder in [('before',args.before),('after',args.after)]},
        'runtime_sha256':{name:hashlib.sha256((ROOT/'aussiefy'/name).read_bytes()).hexdigest()
                          for name in ['semantic_checks.py','verify.py','lint.py']},
        'dictionary_sha256':dictionary_fingerprint(),
        'current':[check(r) for r in current], 'selected_previous_errors':[check(r) for r in known]}
args.out.write_text(json.dumps(result,indent=2)+'\n')
for label in ['current','selected_previous_errors']:
 rows=result[label]
 print(label,len(rows),'failed',sum(not r['ok'] for r in rows),flush=True)
