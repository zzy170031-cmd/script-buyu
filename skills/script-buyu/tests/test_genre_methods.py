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

    def test_planned_and_unknown_genres_do_not_masquerade_as_ready(self):
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


if __name__ == '__main__':
    unittest.main()
