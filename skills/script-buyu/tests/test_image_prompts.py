import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from query_image_prompts import search,verify


class PromptLibraryTests(unittest.TestCase):
    def test_search_deduplicates_and_retains_required_reference_flag(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            item={'id':1,'title':'Portrait','description':'character','content':'A watercolor portrait','needReferenceImages':True}
            for name in ['a','b']:
                (root/(name+'.json')).write_text(json.dumps([item]),encoding='utf-8')
            (root/'manifest.json').write_text(json.dumps({'totalPrompts':2,'categories':[{'slug':x,'file':x+'.json','count':1} for x in ['a','b']]}),encoding='utf-8')
            results=search('人物 水彩',root=root)
            self.assertEqual(len(results),1)
            self.assertTrue(results[0]['needReferenceImages'])
            self.assertEqual(results[0]['categories'],['a','b'])
            self.assertEqual(search(item_id='1',root=root)[0]['content'],item['content'])
            result=verify(root)
            self.assertEqual(result['unique_ids'],1)
            self.assertTrue(result['warnings'])
            with self.assertRaises(ValueError):search('portrait',['missing'],root=root)


if __name__=='__main__':unittest.main()
