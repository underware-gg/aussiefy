"""Reconcile approved source/sense edits with the immutable Gate 4 weight calibration."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))


def recheck():
    from aussiefy import load_dictionary
    folder=ROOT/'research/gate4-evidence-2026-11-14'
    archived=json.loads((folder/'calibration.json').read_text())
    fresh=json.loads(json.dumps(runpy.run_path(str(folder/'calibrate.py'))['compare']()))
    approved=json.loads((ROOT/'research/gate4-rulings-2026-11-17/applied-rulings.json').read_text())
    allowed={f'entry/{r["id"]}' for r in approved['changed_records']}
    allowed|={f'entry/{eid}' for eid in approved['new_entry_ids']}
    before={r['key']:r for r in archived['after']}
    now={r['key']:r for r in fresh['after']}
    missing=sorted(set(before)-set(now))
    revised=[{'key':key,'before':before[key],'after':now[key]} for key in sorted(set(before)&set(now)) if before[key]!=now[key]]
    added=[now[key] for key in sorted(set(now)-set(before))]
    unexpected=[r['key'] for r in revised+added if r['key'] not in allowed]
    if missing or unexpected:
        raise AssertionError({'missing_archive_keys':missing,'unexplained_changed_rows':unexpected})
    if fresh['weights']!=archived['weights'] or fresh['baseline_weights']!=archived['baseline_weights']:
        raise AssertionError('R80 approves curation; it does not recalibrate evidence weights')
    d=load_dictionary()
    terms=[*d.entries.values(),*(r for e in d.entries.values() for r in e.riffs),*d.imagery]
    missing_search=[getattr(t,'id',getattr(t,'text','')) for t in terms if not t.searched]
    if missing_search:raise AssertionError({'missing_searched':missing_search})
    return {'reviewed':'2026-11-17','dictionary_id':d.identity,'terms':len(terms),'all_terms_have_searched':True,
            'weights_unchanged':True,'weights':fresh['weights'],'unchanged_archive_rows_verified':True,
            'unchanged_archive_rows':len(before)-len(revised),'approved_revised_rows':revised,'approved_added_rows':added,
            'unexplained_changed_rows':unexpected,'labels':dict(Counter(r['evidence'] for r in now.values())),
            'archive_labels':archived['labels'],'archive_weight_only_label_changes':len(archived['label_changes']),
            'archive_sha256':hashlib.sha256((folder/'calibration.json').read_bytes()).hexdigest(),
            'acceptance':'Rob R80 approved recommendations; current scoped source facts are distinguished from the immutable calibration archive. No independent measured accuracy claim.'}


if __name__=='__main__':
    report=recheck()
    (ROOT/'research/gate4-rulings-2026-11-17/calibration-recheck.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'approved_revised_rows','approved_added_rows','weights'}},indent=2))
