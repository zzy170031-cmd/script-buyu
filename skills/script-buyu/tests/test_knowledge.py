"""Behavioral integrity checks for lookup and bundled-record provenance."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from query_knowledge import load_index,search,bounded_result
from verify_knowledge import inside,pointer,verify


class KnowledgeTests(unittest.TestCase):
    def test_bundled_sources_and_record_pointers(self):
        self.assertEqual(verify()['status'],'integrity_and_pointers_passed')

    def test_golden_lookup_keeps_status_and_excludes_production_payload(self):
        result=search(load_index(),record_id='golden:GS-7')[0]
        self.assertEqual(result['category'],'golden')
        self.assertIn('upstream_fewshot',result['content'])
        self.assertNotIn('prompt_body',result['content'])
        self.assertNotIn('technical_profile',result['content'])
        self.assertNotEqual(result['status'],'verified')

    def test_search_filter_and_no_match_are_real(self):
        results=search(load_index(),'对白',category='craft',limit=2)
        self.assertTrue(results)
        self.assertTrue(all(r['category']=='craft' for r in results))
        self.assertEqual(search(load_index(),'IMPOSSIBLE_728429'),[])

    def test_negative_examples_require_explicit_usage(self):
        records=load_index()
        candidates=search(records,category='golden',limit=20)
        self.assertTrue(all(r['status']=='source_candidate_unreviewed_for_story' for r in candidates))
        negative=search(records,category='golden',usage='negative',limit=20)
        self.assertTrue(negative)
        self.assertTrue(all(r['status']=='negative_analysis' for r in negative))
        self.assertIn('negative_signals',negative[0]['content'])

    def test_unknown_id_and_unbounded_query_rejected(self):
        with self.assertRaises(ValueError): search(load_index(),record_id='../../secret')
        with self.assertRaises(ValueError): search(load_index(),limit=10000)

    def test_truncation_does_not_claim_complete_record(self):
        r=copy.deepcopy(load_index()[0]);r['content']={'text':'x'*1000}
        result=bounded_result(r,200)
        self.assertTrue(result['truncated'])
        self.assertGreater(result['full_content_chars'],len(result['content_excerpt']))

    def test_pointer_and_root_escape(self):
        self.assertEqual(pointer({'a/b':[{'~c':7}]},'/a~1b/0/~0c'),7)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): inside(Path(tmp),'../outside')

    def test_stale_projection_rejected_even_with_updated_file_hashes(self):
        record=copy.deepcopy(next(r for r in load_index() if r['id']=='golden:GS-7'))
        source_root=Path(__file__).resolve().parents[1]
        original=pointer(json.loads((source_root/record['source_path']).read_text(encoding='utf-8')),record['pointer'])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir()
            record['source_path']='data/source.json';record['pointer']='/0'
            original['source_fields']['scene_performance_core']='动作：人物合上门。'
            record['source_record_sha256']=hashlib.sha256(json.dumps(original,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            for name,value in [('source.json',[original]),('knowledge-index.json',{'records':[record]})]:
                (root/'data'/name).write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
            manifest={'complete':True,'source_commits':{record['repository']:record['commit']},
                'golden_population':{'current_seed_records':1},
                'files':[{'disposition':'archive','local_path':'data/source.json','sha256':hashlib.sha256((root/'data/source.json').read_bytes()).hexdigest()}],
                'managed_files':[{'path':'data/knowledge-index.json','sha256':hashlib.sha256((root/'data/knowledge-index.json').read_bytes()).hexdigest()}]}
            (root/'data/source-manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'projection mismatch'): verify(root)

    def test_incomplete_batch_rejected_before_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir()
            (root/'data/source-manifest.json').write_text('{"complete":false}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'incomplete'): load_index(root)


if __name__=='__main__': unittest.main()
