import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from writing_routes import resource_routes


class WritingRouteTests(unittest.TestCase):
    def test_four_user_problems_reach_specific_chapters(self):
        expected = {
            '对白 生硬': ('stiff_dialogue', '词语句式与语体的取舍'),
            '这段像说明书': ('exposition', '把材料写成有分量的场面'),
            '谁在说话？': ('speaker_clarity', '从发言到接收先辨清当前对象'),
            '人物说话一个味': ('same_voice', '先找到这部故事的说话方式'),
        }
        for query, (problem, anchor) in expected.items():
            with self.subTest(query=query):
                rows = resource_routes(query)
                self.assertEqual([r['problem'] for r in rows], [problem])
                self.assertTrue(any(p.endswith('#' + anchor) for p in rows[0]['chapters']))
                self.assertTrue(rows[0]['matched_phrases'])
                self.assertIn('not semantic diagnosis', rows[0]['notice'])

    def test_plain_explanation_or_normal_qa_does_not_force_diagnosis(self):
        for query in ('', '普通问答与必要解释保留', '解释设备原理', '悬疑 证据 揭示'):
            self.assertEqual(resource_routes(query), [])

    def test_multiple_problems_are_separate_and_not_quality_ranked(self):
        rows = resource_routes('解释腔，也分不清谁在说话')
        self.assertEqual({r['problem'] for r in rows}, {'exposition', 'speaker_clarity'})
        self.assertTrue(all('score' not in r for r in rows))

    def test_reference_files_and_exact_heading_anchors_exist(self):
        for row in resource_routes('对白生硬 解释腔 说话人不清 口吻雷同'):
            for link in row['chapters'] + row['contextual_cases']:
                name, anchor = link.split('#', 1)
                path = ROOT / name
                self.assertTrue(path.is_file(), link)
                headings = re.findall(r'^#{1,6}\s+(.+)$', path.read_text(), re.M)
                slugs = {re.sub(r'\s', '-', re.sub(r'[^\w\-\s]', '', h.lower())) for h in headings}
                self.assertIn(unquote(anchor), slugs, link)

    def test_scene_bridge_requires_narrow_context_and_approved_analysis(self):
        self.assertNotIn('optional_scene_study', resource_routes('对白生硬')[0])
        self.assertNotIn('optional_scene_study', resource_routes('合作对白生硬')[0])
        ref = resource_routes('职业合作对白生硬')[0]['optional_scene_study']
        self.assertEqual(ref['section'], 'curated_analysis')
        data = json.loads((ROOT / ref['index']).read_text())
        case = next(c for c in data[ref['section']] if c['case_id'] == ref['case_id'])
        self.assertEqual(case['use_status'], 'approved_narrow_analysis')
        self.assertIn('L39–43', case['reading_scope'])
        self.assertFalse(case['visual_evidence']['whole_film_viewed'])

    def test_both_clis_separate_navigation_from_record_count(self):
        for name, args, key in (
            ('query_knowledge.py', ['--query', '对白生硬', '--limit', '1'], 'records'),
            ('query_methods.py', ['--genre', '家庭', '--query', '对白生硬', '--limit', '1'], 'results'),
        ):
            raw = subprocess.check_output([sys.executable, '-B', str(ROOT / 'scripts' / name), *args], text=True)
            result = json.loads(raw)
            self.assertEqual(result['resource_routes'][0]['problem'], 'stiff_dialogue')
            self.assertLessEqual(len(result[key]), 1)
            if key == 'records':
                self.assertEqual(result['returned'], len(result[key]))

    def test_exact_id_and_route_listing_keep_existing_behavior(self):
        index = json.loads((ROOT / 'data/knowledge-index.json').read_text())
        record_id = index['records'][0]['id']
        raw = subprocess.check_output([sys.executable, '-B', str(ROOT / 'scripts/query_knowledge.py'),
                                       '--id', record_id, '--query', '解释腔'], text=True)
        result = json.loads(raw)
        self.assertEqual([r['id'] for r in result['records']], [record_id])
        self.assertNotIn('resource_routes', result)
        raw = subprocess.check_output([sys.executable, '-B', str(ROOT / 'scripts/query_methods.py'), '--list-routes'], text=True)
        self.assertIsInstance(json.loads(raw), list)


if __name__ == '__main__':
    unittest.main()
