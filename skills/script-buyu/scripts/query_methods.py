"""Read-only lookup of genre-bound public methods, not a screenplay generator."""
import argparse
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

from story_contract import ROOT, ContractError, read_json, require, unique


def normalized(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text).casefold())


def source_records(library):
    origins = unique(library.get('source_origins', []), 'origin_id', 'source origin')
    for origin in origins.values():
        require(origin['availability'] in ('active', 'candidate', 'isolated'), 'invalid origin availability')
        require(urlparse(origin['url']).scheme == 'https', 'origin needs HTTPS evidence')
    sources = unique(library['sources'], 'source_id', 'source')
    resolved = {}
    for sid, source in sources.items():
        origin = origins.get(source.get('origin_id'))
        if source.get('origin_id'):
            require(origin is not None, 'unknown source origin')
        resolved[sid] = dict(source, _origin_availability=origin['availability'] if origin else 'active')
    return resolved


def source_active(source):
    return (source.get('availability', 'active') == 'active'
            and source.get('_origin_availability', 'active') == 'active')


def method_active(method, sources):
    return (method.get('availability', 'active') == 'active'
            and all(source_active(sources[sid]) for sid in method['source_ids']))


def active(entry, sources, methods):
    return (entry.get('availability', 'active') == 'active'
            and entry.get('qualification', {}).get('status') == 'documented'
            and source_active(sources[entry['source_id']])
            and any(method_active(methods[mid], sources) for mid in entry['method_ids']))


def fallback_routes():
    return {
        'scope': 'manual_navigation_not_method_matches',
        'dialogue': 'references/dialogue-craft.md',
        'professional_support': 'references/genre-professional-support.md',
        'scene_revision': 'references/scene-methods.md',
        'notice': 'Read only what fits the current problem. Keep the requested stage and story constraints; these links are not retrieved or qualified expert matches.'
    }


def validate_index(index, library):
    sources = source_records(library)
    methods = unique(library['methods'], 'method_id', 'method')
    genres = unique(index['genres'], 'genre_id', 'genre')
    baseline = set(index['baseline_entity_ids'])
    minimum = index['minimum_new_people_per_genre']
    require(minimum == 10, 'genre coverage requires ten new people')
    people_registry = unique(index['people'], 'person_id', 'person')
    identity_names = {}
    for person in people_registry.values():
        for name in [person['name']] + person.get('aliases', []):
            key = normalized(name)
            require(key not in identity_names or identity_names[key] == person['person_id'], 'person alias collision: ' + name)
            identity_names[key] = person['person_id']
    for record in library['sources'] + library['methods']:
        require(record.get('availability', 'active') in ('active', 'candidate', 'isolated'), 'invalid availability')
    for method in methods.values():
        require(set(method['source_ids']) <= set(sources), 'unknown method evidence source')
        # Legacy and manually selected cards must obey the same stage boundary.
        if 'stages' in method:
            require(method['stages'] and set(method['stages']) <= {'draft', 'authorized_revision', 'confirmed_translation'}, 'missing or invalid stage scope')
            require(method.get('field_scope'), 'missing editable field boundary')
        if 'confirmed_translation' in method.get('stages', []):
            steps = method.get('confirmed_steps')
            require(isinstance(steps, list) and len(steps) >= 2
                    and all(isinstance(step, str) and step.strip() for step in steps),
                    'confirmed method lacks dedicated executable steps: ' + method['method_id'])
    aliases = {}
    people_names = {}
    for source in sources.values():
        if source['entity_type'] != 'person':
            continue
        for name in [source['name']] + source.get('aliases', []):
            key = normalized(name)
            require(key not in people_names or people_names[key] == source['entity_id'], 'one person has conflicting identities: ' + name)
            people_names[key] = source['entity_id']
    coverage = []
    for genre in genres.values():
        require(genre['status'] in ('planned', 'active'), 'unknown genre status')
        for name in [genre['genre_id'], genre['label']] + genre.get('aliases', []):
            key = normalized(name)
            require(key not in aliases or aliases[key] == genre['genre_id'], 'ambiguous genre alias: ' + name)
            aliases[key] = genre['genre_id']
        people = set()
        eligible = set()
        roles = set()
        role_people = {'writer': set(), 'director': set()}
        for entry in genre['entries']:
            require(entry.get('availability', 'active') in ('active', 'candidate', 'isolated'), 'invalid binding availability')
            source = sources.get(entry['source_id'])
            require(source is not None, 'unknown genre source')
            require(source['entity_type'] == 'person', 'teams are not individual people')
            require(entry['person_id'] == source['entity_id'], 'genre person/source identity mismatch')
            require(entry['person_id'] not in people, 'duplicate person within genre')
            require(entry['person_id'] not in baseline, 'baseline person cannot count as newly added')
            person = people_registry.get(entry['person_id'])
            require(person is not None and not person['baseline'], 'unknown or baseline person')
            for name in [source['name']] + source.get('aliases', []):
                owner = identity_names.get(normalized(name))
                require(owner == entry['person_id'], 'source name/alias points to another person')
            require(entry['fit'] and entry['work_evidence'] and entry['evidence_locator'], 'missing genre-specific evidence')
            qualification = entry.get('qualification', {})
            require(qualification.get('status') in ('documented', 'candidate', 'rejected'), 'missing qualification status')
            if qualification['status'] == 'documented':
                require(qualification.get('evidence') and qualification.get('role_evidence')
                        and urlparse(qualification.get('url', '')).scheme == 'https', 'missing qualification evidence')
            require(entry.get('distinctive_contribution') and entry.get('selection_limits'), 'missing selection evidence')
            require(entry.get('method_basis') in ('creator_statement_adaptation', 'primary_work_analysis'), 'unknown method attribution')
            require(source.get('origin_id'), 'indexed source requires origin identity')
            require(entry['roles'] and set(entry['roles']) <= {'writer', 'director'}, 'invalid creator role')
            require(entry['method_ids'] and len(entry['method_ids']) == len(set(entry['method_ids'])), 'invalid genre method ids')
            for mid in entry['method_ids']:
                method = methods.get(mid)
                require(method is not None, 'unknown genre method')
                require(entry['source_id'] in method['source_ids'], 'method is not supported by this source')
                require(method.get('stages') and set(method['stages']) <= {'draft', 'authorized_revision', 'confirmed_translation'}, 'missing or invalid stage scope')
                require(method.get('field_scope'), 'missing editable field boundary')
            people.add(entry['person_id'])
            if active(entry, sources, methods):
                eligible.add(entry['person_id'])
                roles.update(entry['roles'])
                for role in entry['roles']:
                    role_people[role].add(entry['person_id'])
        complete = len(eligible) >= minimum and roles == {'writer', 'director'}
        status = 'planned' if genre['status'] == 'planned' else ('source_ready' if complete else 'partial')
        coverage.append({'genre_id': genre['genre_id'], 'label': genre['label'], 'status': status,
                         'new_people': len(eligible), 'writers': len(role_people['writer']),
                         'directors': len(role_people['director']),
                         'dual_role_people': len(role_people['writer'] & role_people['director']),
                         'target': minimum, 'target_basis': 'combined_unique_people_with_both_disciplines'})
    routes = unique(index.get('routes', []), 'route_id', 'composite route')
    for route in routes.values():
        require(route.get('genre_ids') and len(set(route['genre_ids'])) == len(route['genre_ids'])
                and set(route['genre_ids']) <= set(genres), 'invalid composite genre references')
        require(route.get('guidance') and route.get('scope') == 'composite_navigation_not_separate_coverage', 'missing composite boundary')
        for name in [route['route_id'], route['label']] + route.get('aliases', []):
            key = normalized(name)
            require(key not in aliases or aliases[key] == route['route_id'], 'ambiguous route alias: ' + name)
            aliases[key] = route['route_id']
    return coverage


def search(index, library, genre_name, query='', stage='draft', limit=3):
    require(1 <= limit <= 20, 'limit must be 1..20')
    require(stage in ('draft', 'authorized_revision', 'confirmed_translation'), 'unknown stage')
    coverage = validate_index(index, library)
    routes = [r for r in index.get('routes', []) if normalized(genre_name) in
              {normalized(n) for n in [r['route_id'], r['label']] + r.get('aliases', [])}]
    if routes:
        route = routes[0]
        groups = [search(index, library, gid, query, stage, 20) for gid in route['genre_ids']]
        results, seen = [], set()
        for offset in range(20):
            for group in groups:
                rows = group['results']
                if offset < len(rows) and rows[offset]['person_id'] not in seen:
                    row = dict(rows[offset], matched_genre=group['genre'])
                    results.append(row)
                    seen.add(row['person_id'])
                    if len(results) == limit:
                        break
            if len(results) == limit:
                break
        return {'kind': 'composite_route', 'route': route['label'], 'scope': route['scope'],
                'stage': stage, 'guidance': route['guidance'], 'genre_options': route['genre_ids'],
                'results': results, 'fallback': fallback_routes() if not results else None,
                'notice': 'These are optional genre paths, not an independent ten-person pool or a requirement to combine all genres. No matches do not relax the requested stage.'}
    selected = [g for g in index['genres'] if normalized(genre_name) in {normalized(n) for n in [g['genre_id'], g['label']] + g.get('aliases', [])}]
    require(len(selected) == 1, 'unknown genre: ' + genre_name
            + '; keep this topic and stage, use references/genre-professional-support.md and references/scene-methods.md for manual research/writing; do not claim registered coverage')
    genre = selected[0]
    if genre['status'] == 'planned':
        return {'genre': genre['label'], 'status': genre['status'], 'stage': stage, 'results': [],
                'fallback': fallback_routes(), 'notice': 'Coverage is planned, not ready. General writing can continue; do not claim ten supported new people.'}
    sources = source_records(library)
    methods = {m['method_id']: m for m in library['methods']}
    words = query.casefold().split()
    ranked = []
    for entry in genre['entries']:
        if not active(entry, sources, methods):
            continue
        source = sources[entry['source_id']]
        for mid in entry['method_ids']:
            method = methods[mid]
            if stage not in method['stages'] or not method_active(method, sources):
                continue
            haystack = json.dumps([source['name'], method['task'], method['when'], method.get('scene_tags', []), method['steps'], entry['fit']], ensure_ascii=False).casefold()
            score = sum(word in haystack for word in words)
            if words and not score:
                continue
            ranked.append((score, entry, method, source))
    ranked.sort(key=lambda item: (-item[0], item[2]['method_id']))
    results, seen = [], set()
    for score, entry, method, source in ranked:
        if entry['person_id'] in seen:
            continue
        selected_method = dict(method)
        if stage == 'confirmed_translation':
            selected_method['steps'] = method['confirmed_steps']
        selected_method.pop('confirmed_steps', None)
        selected_method['selected_stage'] = stage
        results.append({'person_id': entry['person_id'], 'name': source['name'], 'genre_fit': entry['fit'],
                        'work_evidence': entry['work_evidence'], 'qualification': entry['qualification'],
                        'distinctive_contribution': entry['distinctive_contribution'], 'selection_limits': entry['selection_limits'],
                        'method_basis': entry['method_basis'],
                        'source': {k: source.get(k) for k in ('url', 'origin_id', 'locator', 'evidence_summary', 'read_status', 'accessed_at')},
                        'method': selected_method})
        seen.add(entry['person_id'])
        if len(results) >= limit:
            break
    state = next(c for c in coverage if c['genre_id'] == genre['genre_id'])
    return {'genre': genre['label'], 'coverage': state, 'stage': stage, 'results': results,
            'fallback': fallback_routes() if not results else None,
            'notice': 'Optional public-method adaptations, not real people participating. Search limit is not a writing quota; no matches do not authorize changing stage or genre. Source isolation reduces coverage without disabling independent cards.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--genre')
    parser.add_argument('--query', default='')
    parser.add_argument('--stage', choices=['draft', 'authorized_revision', 'confirmed_translation'], default='draft')
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--list-genres', action='store_true')
    parser.add_argument('--list-routes', action='store_true')
    args = parser.parse_args()
    if not (args.genre or args.list_genres or args.list_routes):
        parser.error('provide --genre or --list-genres')
    try:
        index = read_json(ROOT / 'data/genre-index.json')
        library = read_json(ROOT / 'data/story-methods.json')
        validate_index(index, library)
        result = (index.get('routes', []) if args.list_routes else validate_index(index, library)
                  if args.list_genres else search(index, library, args.genre, args.query, args.stage, args.limit))
    except (ContractError, KeyError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
