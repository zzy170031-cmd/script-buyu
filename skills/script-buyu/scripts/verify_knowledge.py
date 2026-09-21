"""Offline integrity and record-pointer check, not a creative-quality verdict."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def inside(root, relative):
    root=root.resolve()
    candidate=(root/relative).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise ValueError('missing or escaping resource: '+relative)
    return candidate


def pointer(value, path):
    if not path:
        return value
    if not path.startswith('/'):
        raise ValueError('invalid JSON pointer')
    for token in path[1:].split('/'):
        token=token.replace('~1','/').replace('~0','~')
        value=value[int(token)] if isinstance(value,list) else value[token]
    return value


def verify(root=ROOT):
    manifest=json.loads((root/'data/source-manifest.json').read_text(encoding='utf-8'))
    if manifest.get('complete') is not True:
        raise ValueError('incomplete knowledge integration')
    archives=[r for r in manifest['files'] if r['disposition']=='archive']
    managed=manifest['managed_files']
    paths=[r['local_path'] for r in archives]+[r['path'] for r in managed]
    if len(paths)!=len(set(paths)):
        raise ValueError('duplicate managed path')
    for row in archives+managed:
        relative=row.get('local_path',row.get('path'))
        actual=hashlib.sha256(inside(root,relative).read_bytes()).hexdigest()
        if actual!=row['sha256']:
            raise ValueError('hash mismatch: '+relative)
    known={r['local_path'] for r in archives}
    records=json.loads((root/'data/knowledge-index.json').read_text(encoding='utf-8'))['records']
    ids=set()
    loaded={}
    for record in records:
        if record['id'] in ids:
            raise ValueError('duplicate knowledge id: '+record['id'])
        ids.add(record['id'])
        relative=record['source_path']
        if relative not in known:
            raise ValueError('unmanifested source: '+relative)
        if record['commit']!=manifest['source_commits'][record['repository']]:
            raise ValueError('record commit differs from batch: '+record['id'])
        source=inside(root,relative)
        if record['pointer']:
            if relative not in loaded:
                loaded[relative]=json.loads(source.read_text(encoding='utf-8-sig'))
            original=pointer(loaded[relative],record['pointer'])
            record_hash=hashlib.sha256(json.dumps(original,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
            if record_hash!=record.get('source_record_sha256'):
                raise ValueError('stale source-record projection: '+record['id'])
            if record['category']=='golden' and record['id']!='golden:'+original['sample_id']:
                raise ValueError('golden identity mismatch: '+record['id'])
            if record['category']=='golden':
                fields=original['source_fields']
                lines=[line for line in fields.get('scene_performance_core','').splitlines() if re.match(r'^(动作|细微表演|细微表情|人物动作|行为)[：:]',line.strip())]
                lines=[line for line in lines if not re.search(r'\b\d+(?:\.\d+)?\s*(?:mm|fps|s)\b|焦段|运镜|构图|镜头|画幅|光圈|前景|景别',line)]
                expected='\n'.join(lines) or '原记录无可直接分离的动作段；仅可由编剧阅读原件后归纳，不能自动补造。'
                negative=original.get('negative_sample',{}).get('is_negative_sample',False)
                status='negative_analysis' if negative else 'reserve_analysis' if fields.get('library_status')!='official' else 'source_candidate_unreviewed_for_story'
                if record['status']!=status or record['content']['story_observation']!=expected or record['content']['upstream_fewshot']!=original.get('fewshot',{}):
                    raise ValueError('golden content or status projection mismatch: '+record['id'])
            if record['category']=='craft' and record['id']!='kb:'+original['machine_id']:
                raise ValueError('craft identity mismatch: '+record['id'])
            if record['category']=='craft' and any(k not in original or original[k]!=v for k,v in record['content'].items()):
                raise ValueError('craft content projection mismatch: '+record['id'])
        if record['category']=='wiki':
            text=source.read_text(encoding='utf-8')
            match=re.search(r'## Claims Summary\s*(.*?)(?=\n## |\Z)',text,re.S)
            expected=match.group(1).strip() if match else ''
            if record['content']['source_claims']!=expected:
                raise ValueError('wiki content projection mismatch: '+record['id'])
        if record['category']=='golden':
            forbidden={'prompt_body','technical_profile','camera_directing_core','reference_bundle'}
            if forbidden.intersection(record['content']):
                raise ValueError('production field in golden retrieval')
    counts=dict(Counter(r['category'] for r in records))
    if counts.get('golden')!=manifest['golden_population']['current_seed_records']:
        raise ValueError('golden population mismatch')
    return {'status':'integrity_and_pointers_passed','archive_files':len(archives),'index_records':len(records),
            'categories':counts,'limits':'Does not certify literary quality, rights of third-party originals, or live agent routing.'}


if __name__=='__main__':
    try:
        print(json.dumps(verify(),ensure_ascii=False))
    except (ValueError,KeyError,IndexError,OSError) as exc:
        raise SystemExit('Knowledge verification failed: '+str(exc))
