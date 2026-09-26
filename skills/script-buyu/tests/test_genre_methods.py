"""Coverage and retrieval boundary tests; not literary quality evaluation."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from story_contract import ROOT, ContractError, read_json
from query_methods import search, validate_index


class GenreMethodsTests(unittest.TestCase):
    def setUp(self):
        self.index = read_json(ROOT / 'data/genre-index.json')
        self.library = read_json(ROOT / 'data/story-methods.json')
        self.romance = next(g for g in self.index['genres'] if g['genre_id'] == 'romance')

    def source(self, sid):
        return next(s for s in self.library['sources'] if s['source_id'] == sid)

    def method(self, mid):
        return next(m for m in self.library['methods'] if m['method_id'] == mid)

    def test_initial_six_have_new_people_and_both_disciplines(self):
        coverage = validate_index(self.index, self.library)
        initial = {'mystery', 'romance', 'action', 'gunfight', 'science-fiction', 'thriller'}
        byid = {row['genre_id']: row for row in coverage}
        for gid in initial:
            self.assertEqual(byid[gid]['status'], 'source_ready')
            self.assertGreaterEqual(byid[gid]['new_people'], 10)

    def test_repeated_person_is_not_another_person(self):
        self.romance['entries'].append(copy.deepcopy(self.romance['entries'][0]))
        with self.assertRaisesRegex(ContractError, 'duplicate person'):
            validate_index(self.index, self.library)

    def test_legacy_person_cannot_be_reintroduced(self):
        person = self.romance['entries'][0]['person_id']
        self.index['baseline_entity_ids'].append(person)
        with self.assertRaisesRegex(ContractError, 'baseline person'):
            validate_index(self.index, self.library)

    def test_old_name_under_new_id_is_rejected(self):
        self.source(self.romance['entries'][0]['source_id'])['aliases'].append('Joe Russo')
        with self.assertRaisesRegex(ContractError, 'another person'):
            validate_index(self.index, self.library)

    def test_russo_brothers_are_both_in_baseline(self):
        old = {p['person_id'] for p in self.index['people'] if p['baseline']}
        self.assertTrue({'joe-russo', 'anthony-russo'} <= old)

    def test_team_does_not_count_as_individual(self):
        self.source(self.romance['entries'][0]['source_id'])['entity_type'] = 'team'
        with self.assertRaisesRegex(ContractError, 'teams'):
            validate_index(self.index, self.library)

    def test_unknown_source_and_wrong_method_binding_fail(self):
        entry = self.romance['entries'][0]
        entry['method_ids'] = ['M01']
        with self.assertRaisesRegex(ContractError, 'not supported'):
            validate_index(self.index, self.library)
        entry['source_id'] = 'NOT-A-SOURCE'
        with self.assertRaisesRegex(ContractError, 'unknown genre source'):
            validate_index(self.index, self.library)

    def test_source_isolation_reduces_only_dependent_coverage(self):
        entry = self.romance['entries'][0]
        self.source(entry['source_id'])['availability'] = 'isolated'
        coverage = {row['genre_id']: row for row in validate_index(self.index, self.library)}
        self.assertEqual(coverage['romance']['new_people'], 9)
        self.assertEqual(coverage['romance']['status'], 'partial')
        self.assertEqual(coverage['gunfight']['status'], 'source_ready')
        result = search(self.index, self.library, '爱情', limit=20)
        self.assertNotIn(entry['person_id'], {r['person_id'] for r in result['results']})
        self.assertEqual(len(result['results']), 9)

    def test_secondary_source_isolation_propagates(self):
        entry = self.romance['entries'][0]
        self.method(entry['method_ids'][0])['source_ids'].append('SRC-MAZIN-403')
        self.source('SRC-MAZIN-403')['availability'] = 'isolated'
        result = search(self.index, self.library, '爱情', limit=20)
        self.assertNotIn(entry['person_id'], {r['person_id'] for r in result['results']})

    def test_method_isolation_and_binding_candidate_are_excluded(self):
        first, second = self.romance['entries'][:2]
        self.method(first['method_ids'][0])['availability'] = 'isolated'
        second['availability'] = 'candidate'
        result = search(self.index, self.library, '爱情', limit=20)
        ids = {r['person_id'] for r in result['results']}
        self.assertNotIn(first['person_id'], ids)
        self.assertNotIn(second['person_id'], ids)

    def test_confirmed_stage_excludes_draft_only_writing(self):
        result = search(self.index, self.library, '科幻', stage='confirmed_translation', limit=20)
        ids = {r['person_id'] for r in result['results']}
        self.assertNotIn('ted-chiang', ids)
        self.assertNotIn('andy-weir', ids)
        self.assertNotIn('duncan-jones', ids)
        self.assertNotIn('alex-garland', ids)
        visual = search(self.index, self.library, '悬疑', stage='confirmed_translation', limit=20)
        self.assertIn('david-fincher', {r['person_id'] for r in visual['results']})

    def test_confirmed_results_replace_draft_operations(self):
        result = search(self.index, self.library, '枪战', stage='confirmed_translation', limit=20)
        ids = {r['person_id'] for r in result['results']}
        self.assertNotIn('ben-wheatley', ids)
        self.assertNotIn('chad-stahelski', ids)
        for record in result['results']:
            original = self.method(record['method']['method_id'])
            self.assertEqual(record['method']['steps'], original['confirmed_steps'])
            self.assertNotEqual(record['method']['steps'], original['steps'])

    def test_confirmed_method_without_dedicated_steps_is_rejected(self):
        method = self.method('G006')
        method.pop('confirmed_steps', None)
        with self.assertRaisesRegex(ContractError, 'dedicated executable steps'):
            validate_index(self.index, self.library)

    def test_unbound_legacy_director_has_same_stage_gate(self):
        method = self.method('D03')
        self.assertTrue(method['confirmed_steps'])
        self.assertFalse(any('D03' in entry['method_ids']
                             for genre in self.index['genres'] for entry in genre['entries']))
        method.pop('confirmed_steps')
        with self.assertRaisesRegex(ContractError, 'dedicated executable steps'):
            validate_index(self.index, self.library)

    def test_confirmed_steps_must_be_real_nonempty_list(self):
        for invalid in ('two characters', ['', ' '], [1, 2]):
            with self.subTest(invalid=invalid):
                self.method('D08')['confirmed_steps'] = invalid
                with self.assertRaisesRegex(ContractError, 'dedicated executable steps'):
                    validate_index(self.index, self.library)

    def test_role_counts_deduplicate_dual_roles_and_track_isolation(self):
        before = search(self.index, self.library, '爱情')['coverage']
        self.assertEqual(before['new_people'], before['writers'] + before['directors'] - before['dual_role_people'])
        entry = next(e for e in self.romance['entries'] if set(e['roles']) == {'writer', 'director'})
        entry['availability'] = 'isolated'
        after = search(self.index, self.library, '爱情')['coverage']
        for field in ('new_people', 'writers', 'directors', 'dual_role_people'):
            self.assertEqual(after[field], before[field] - 1)

    def test_empty_lookup_preserves_stage_with_manual_routes(self):
        for genre in ('爱情', self.index['routes'][0]['route_id']):
            result = search(self.index, self.library, genre, 'NOMATCH876543', 'confirmed_translation')
            self.assertEqual(result['results'], [])
            self.assertEqual(result['stage'], 'confirmed_translation')
            self.assertEqual(result['fallback']['scope'], 'manual_navigation_not_method_matches')
            for key in ('dialogue', 'professional_support', 'scene_revision'):
                self.assertTrue((ROOT / result['fallback'][key]).is_file())

    def test_unknown_topic_stays_explicit_and_has_manual_navigation(self):
        with self.assertRaises(ContractError) as caught:
            search(self.index, self.library, 'UNREGISTERED-TOPIC', stage='confirmed_translation')
        message = str(caught.exception)
        self.assertIn('unknown genre', message)
        self.assertIn('UNREGISTERED-TOPIC', message)
        self.assertIn('references/genre-professional-support.md', message)

    def test_planned_and_unknown_genres_do_not_masquerade_as_ready(self):
        next(g for g in self.index['genres'] if g['label'] == '武侠')['status'] = 'planned'
        result = search(self.index, self.library, '武侠')
        self.assertEqual(result['status'], 'planned')
        self.assertEqual(result['results'], [])
        with self.assertRaisesRegex(ContractError, 'unknown genre'):
            search(self.index, self.library, 'NOT-A-GENRE')

    def test_no_matches_does_not_silently_relax_constraints(self):
        result = search(self.index, self.library, '爱情', query='DOESNOTEXIST98765')
        self.assertEqual(result['results'], [])

    def test_limit_and_person_dedup(self):
        result = search(self.index, self.library, '动作', limit=3)
        self.assertEqual(len(result['results']), 3)
        self.assertEqual(len({r['person_id'] for r in result['results']}), 3)
        with self.assertRaisesRegex(ContractError, 'limit'):
            search(self.index, self.library, '动作', limit=0)

    def test_ambiguous_alias_is_rejected(self):
        self.romance['aliases'].append('动作')
        with self.assertRaisesRegex(ContractError, 'ambiguous'):
            validate_index(self.index, self.library)

    def test_invalid_availability_and_stage_rejected(self):
        self.source(self.romance['entries'][0]['source_id'])['availability'] = 'maybe'
        with self.assertRaisesRegex(ContractError, 'availability'):
            validate_index(self.index, self.library)
        with self.assertRaisesRegex(ContractError, 'unknown stage'):
            search(self.index, self.library, '动作', stage='anything')

    def test_all_core_genres_have_qualified_coverage(self):
        coverage = validate_index(self.index, self.library)
        self.assertEqual(len(coverage), 26)
        self.assertTrue(all(r['status'] == 'source_ready' and r['new_people'] >= 10 for r in coverage))
        self.assertEqual(len(self.index['routes']), 31)

    def test_unqualified_candidates_are_neither_counted_nor_returned(self):
        for entry, status in zip(self.romance['entries'][:2], ('candidate', 'rejected')):
            entry['qualification']['status'] = status
        result = search(self.index, self.library, '爱情', limit=20)
        self.assertEqual(result['coverage']['new_people'], 8)
        self.assertEqual(len(result['results']), 8)

    def test_documented_qualification_requires_evidence(self):
        self.romance['entries'][0]['qualification'].pop('role_evidence')
        with self.assertRaisesRegex(ContractError, 'qualification evidence'):
            validate_index(self.index, self.library)

    def test_shared_origin_withdrawal_removes_both_people(self):
        first = next(e for e in self.romance['entries'] if e['person_id'] == 'park-chan-wook')
        origin_id = self.source(first['source_id'])['origin_id']
        affected = {e['person_id'] for e in self.romance['entries']
                    if self.source(e['source_id'])['origin_id'] == origin_id}
        self.assertEqual(len(affected), 2)
        next(o for o in self.library['source_origins'] if o['origin_id'] == origin_id)['availability'] = 'isolated'
        result = search(self.index, self.library, '爱情', limit=20)
        self.assertEqual(result['coverage']['new_people'], 8)
        self.assertFalse(affected & {r['person_id'] for r in result['results']})
        self.assertEqual(search(self.index, self.library, '枪战')['coverage']['status'], 'source_ready')

    def test_unknown_origin_is_rejected(self):
        self.source(self.romance['entries'][0]['source_id'])['origin_id'] = 'unknown'
        with self.assertRaisesRegex(ContractError, 'unknown source origin'):
            validate_index(self.index, self.library)

    def test_composite_navigation_is_bounded_and_deduplicated(self):
        for route in self.index['routes']:
            result = search(self.index, self.library, route['route_id'], limit=3)
            self.assertEqual(result['scope'], 'composite_navigation_not_separate_coverage')
            self.assertLessEqual(len(result['results']), 3)
            self.assertEqual(len({r['person_id'] for r in result['results']}), len(result['results']))
            self.assertTrue(all(r['qualification']['status'] == 'documented' for r in result['results']))

    def test_composite_retains_query_and_stage_filters(self):
        route = self.index['routes'][0]['route_id']
        self.assertEqual(search(self.index, self.library, route, query='NORESULT987654')['results'], [])
        for row in search(self.index, self.library, route, stage='confirmed_translation', limit=20)['results']:
            self.assertFalse(row['method']['method_id'].startswith('X'))
            self.assertEqual(row['method']['steps'], self.method(row['method']['method_id'])['confirmed_steps'])

    def test_composite_alias_and_reference_errors_are_rejected(self):
        self.index['routes'][0]['aliases'].append('爱情')
        with self.assertRaisesRegex(ContractError, 'ambiguous route alias'):
            validate_index(self.index, self.library)
        self.index['routes'][0]['aliases'].pop()
        self.index['routes'][0]['genre_ids'].append('missing')
        with self.assertRaisesRegex(ContractError, 'composite genre references'):
            validate_index(self.index, self.library)

    def test_primary_work_analysis_is_distinguished_from_creator_claims(self):
        methods = [m for m in self.library['methods'] if m.get('method_basis') == 'primary_work_analysis']
        self.assertEqual(len(methods), 3)
        for genre in self.index['genres']:
            result = search(self.index, self.library, genre['genre_id'], stage='confirmed_translation', limit=20)
            self.assertTrue(all(not r['method']['method_id'].startswith('X') for r in result['results']))


if __name__ == '__main__':
    unittest.main()
