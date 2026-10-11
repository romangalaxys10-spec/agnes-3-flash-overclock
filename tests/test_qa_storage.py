"""Atomic storage and lesson-isolation regressions. Offline only."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agnes_kit.adapters import FileMemory, FileLessons
from agnes_kit.pipeline import build_generation_messages


class StorageQaTests(unittest.TestCase):
    def test_atomic_replace_failure_preserves_old_store(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'memory.json'; memory=FileMemory(path)
            memory.add('original', 'u1'); before=path.read_bytes()
            with patch('agnes_kit.adapters.os.replace',side_effect=OSError('simulated failure')):
                with self.assertRaises(OSError):
                    memory.add('new', 'u1')
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(list(Path(d).glob('*.tmp')),[])
            self.assertEqual(memory.search('original','u1'),['original'])

    def test_failed_temp_write_preserves_original(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'memory.json'; memory=FileMemory(path);memory.add('original')
            before=path.read_bytes()
            with patch('agnes_kit.adapters.json.dump',side_effect=OSError('disk full')):
                with self.assertRaises(OSError): memory.add('new')
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(list(Path(d).glob('*.tmp')),[])

    def test_schema_drift_refuses_search_and_overwrite(self):
        bad=[{}, {'records':[]}, [1], [{'text':'x'}], [{'user_id':'u','text':5}], [{'user_id':'u','text':'x','extra':1}]]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'memory.json'
            for data in bad:
                path.write_text(json.dumps(data)); before=path.read_bytes();memory=FileMemory(path)
                with self.subTest(data=data):
                    with self.assertRaises(ValueError):memory.add('new')
                    with self.assertRaises(ValueError):memory.search('new')
                    self.assertEqual(path.read_bytes(),before)

    def test_lessons_owner_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            lessons=FileLessons(Path(d)/'lessons.json')
            lessons.save('task alpha','private A','a')
            lessons.save('task alpha','private B','b')
            self.assertEqual(lessons.relevant('task alpha',user_id='a'),['private A'])
            self.assertEqual(lessons.relevant('task alpha'),[])

    def test_lessons_threshold_and_pipeline_scope(self):
        with tempfile.TemporaryDirectory() as d:
            lessons=FileLessons(Path(d)/'lessons.json')
            lessons.save('task alpha','match','a');lessons.save('task beta','weak overlap','a')
            lessons.save('task alpha','private B','b')
            messages=build_generation_messages('task alpha',lesson_store=lessons,user_id='a')
            self.assertIn('match',messages[1]['content'])
            self.assertNotIn('weak overlap',messages[1]['content'])
            self.assertNotIn('private B',messages[1]['content'])
            with self.assertRaises(ValueError):lessons.relevant('task',min_relevance=0)
            with self.assertRaises(ValueError):build_generation_messages('task',lessons=['raw'],lesson_store=lessons)
