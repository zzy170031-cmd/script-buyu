"""Bounded offline keyword search and integrity checks for the pinned prompt library."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'data' / 'image-prompts'
ALIASES = {'人物': ['portrait', 'character'], '写实': ['realistic'],
           '国漫': ['chinese', 'illustration'], '漫画': ['comic', 'manga'],
           '古代': ['historical', 'ancient'], '服装': ['costume', 'clothing'],
           '水彩': ['watercolor'], '奇幻': ['fantasy'], '游戏': ['game']}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def rows(root=ROOT, categories=None):
    manifest = read(root / 'manifest.json')
    known = {c['slug'] for c in manifest['categories']}
    if categories and not set(categories) <= known:
        raise ValueError('Unknown category: ' + ', '.join(sorted(set(categories) - known)))
    for category in manifest['categories']:
        if categories and category['slug'] not in categories:
            continue
        path = (root / category['file']).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Category file escapes library')
        for item in read(path):
            yield category['slug'], item


def search(query='', categories=None, item_id=None, root=ROOT):
    terms = set(re.findall(r'[\w-]+', query.casefold()))
    for word, aliases in ALIASES.items():
        if word in query:
            terms.update(aliases)
    matches = {}
    for category, item in rows(root, categories):
        if item_id is not None and str(item['id']) != str(item_id):
            continue
        title = (item.get('title', '') + ' ' + item.get('description', '')).casefold()
        content = item.get('content', '').casefold()
        score = sum(3 * (t in title) + (t in content) for t in terms)
        if item_id is None and not score:
            continue
        key = str(item['id'])
        if key not in matches:
            matches[key] = dict(item, categories=[category], score=score)
        else:
            matches[key]['categories'].append(category)
    return sorted(matches.values(), key=lambda x: (-x['score'], str(x['id'])))


def verify(root=ROOT):
    manifest = read(root / 'manifest.json')
    ids, contents, missing, conflicts = {}, set(), [], []
    count = 0
    per_category = {}
    for category, item in rows(root):
        count += 1
        per_category[category] = per_category.get(category, 0) + 1
        value = item.get('content', '')
        if not isinstance(value, str) or not value.strip():
            missing.append(item.get('id'))
        digest = hashlib.sha256(value.encode('utf-8')).hexdigest()
        contents.add(digest)
        key = str(item['id'])
        if key in ids and ids[key] != digest:
            conflicts.append(key)
        ids[key] = digest
    errors, warnings = [], []
    if len(ids) != manifest['totalPrompts']:
        warnings.append('Upstream manifest total differs from observed unique IDs')
    for c in manifest['categories']:
        if per_category.get(c['slug'], 0) != c['count']:
            errors.append('Category count differs: ' + c['slug'])
    if missing or conflicts:
        errors.append('Empty content or conflicting duplicate ID')
    snapshot_path = root / 'snapshot.json'
    if snapshot_path.exists():
        snapshot = read(snapshot_path)
        if snapshot['observed']['unique_ids'] != len(ids) or snapshot['observed']['unique_prompt_texts'] != len(contents):
            errors.append('Observed counts differ from pinned snapshot')
        for f in snapshot['files']:
            path = (root / f['file']).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                errors.append('Missing/invalid snapshot file: ' + f['file'])
            elif hashlib.sha256(path.read_bytes()).hexdigest() != f['sha256']:
                errors.append('Hash differs: ' + f['file'])
    return {'category_count': len(per_category), 'category_entries': count,
            'unique_ids': len(ids), 'unique_prompt_texts': len(contents),
            'empty_content_count': len(missing), 'conflicting_id_count': len(set(conflicts)),
            'upstream_declared_total': manifest['totalPrompts'],
            'warnings': warnings, 'errors': errors, 'verified': not errors}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--query', default='')
    p.add_argument('--category', action='append')
    p.add_argument('--id')
    p.add_argument('--limit', type=int, default=3)
    p.add_argument('--full', action='store_true')
    p.add_argument('--verify', action='store_true')
    a = p.parse_args()
    if a.verify:
        result = verify()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result['verified'] else 1)
    if not a.query.strip() and a.id is None:
        p.error('Specify --query, --id, or --verify')
    if not 1 <= a.limit <= 10:
        p.error('--limit must be 1..10')
    try:
        result = search(a.query, a.category, a.id)[:a.limit]
    except ValueError as exc:
        p.error(str(exc))
    for item in result:
        if not a.full:
            item['content'] = item.get('content', '')[:300]
        item['source_url'] = 'https://youmind.com/nano-banana-pro-prompts?id=' + str(item['id'])
    print(json.dumps({'matches': result, 'full_content': a.full}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
