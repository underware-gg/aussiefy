"""Retain bounded benchmark metadata and aggregates without full reference texts."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--before',type=Path,required=True)
parser.add_argument('--after',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
BEFORE=args.before
AFTER=args.after

def load(folder,name): return json.loads((folder/name).read_text())
def snapshot(folder):
 slang=load(folder,'slang.json'); smart=load(folder,'smart.json'); quantity=load(folder,'quantity.json')
 challenges=load(folder,'challenge-outputs.json'); refs=load(folder,'reference-outputs.json')
 return {
  'metadata':load(folder,'metadata.json'),
  'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir()) if p.is_file() and p.name not in {'aggregate.json','REPORT.md'}},
  'curated':{k:slang[k] for k in ['labels_sha256','scorer_sha256','contract','documents']},
  'historical_wording':{k:quantity[k] for k in ['source_sha256','anchors_sha256','level','seeds','measure']},
  'historical_wording_rows':[{k:r[k] for k in ['document_type','embellishment','hits','denominator','quantity_approximation']} for r in quantity['runs']],
  'smart':smart,
  'changes':load(folder,'changes.json'),
  'writer':load(folder,'writer.json'),
  'core_mode_timings':load(folder,'core-mode-timings.json'),
  'cpu_warm':load(folder,'cpu-current.json'),
  'diagnostics':{'rows':len(challenges),'reference_rows':len(refs),
   'known_literal_reproductions':{
    'hunger_complement_repeats_enough':sum(r['text'].lower().count('enough')>1 for r in challenges if r['case']=='hunger_complement'),
    'explicit_very_hungry_to_now_im_peckish':sum("now I'm peckish" in r['text'] for r in challenges if r['case']=='hunger'),
    'embedded_knackered_rooted_checked_stack':sum('knackered, rooted checked' in r['text'] for r in challenges if r['case']=='embedded')},
   'structural_failures':sum(bool(r['structural_error']) for r in refs),
   'verify_failed':sum(not r['verification']['ok'] for r in refs),
   'verify_counts':{severity:sum(r['verification']['counts'].get(severity,0) for r in refs) for severity in ['critical','major','minor']}},
  'lookup':[{'backend':r['backend'],'query':r['query'],'note':r['result'].get('note'),'results':[{k:s[k] for k in ['id','concepts','match','score']} for s in r['result']['results']]} for r in load(folder,'lookup.json')]
 }

before=snapshot(BEFORE); after=snapshot(AFTER)
comparisons={
 'curated labels':(before['curated']['labels_sha256'],after['curated']['labels_sha256']),
 'curated scorer':(before['curated']['scorer_sha256'],after['curated']['scorer_sha256']),
 'historical wording contract':(before['historical_wording'],after['historical_wording']),
 'bundled model assets':tuple({name:row['smart']['source_hashes']['aussiefy/data/model/'+name]
                              for name in ['meta.json','vocab.txt','vectors.f16']} for row in [before,after]),
 'Smart input cohort':tuple([(r['input'],r['sha256']) for r in row['smart']['benchmarks']]
                           for row in [before,after]),
}
for name,(baseline,current) in comparisons.items():
 if baseline != current:
  raise ValueError(f'Baseline/repeat mismatch: {name}; unchanged evidence must not be written')
args.out.write_text(json.dumps({'scope':'Known diagnostic reproduction and fixed benchmark comparison; no unseen generalisation or causal speedup claim. Literal signatures require manual output review. Full reference outputs remain local.','driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'bundled_model_assets_unchanged':True,'before':before,'after':after,'unchanged_labels_scorer_anchors_and_smart_inputs':True},indent=2)+'\n')
print('Aggregate saved; labels, scorer, historical anchors and core timing sources remain frozen.')
