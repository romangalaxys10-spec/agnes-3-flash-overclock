"""Checker regressions for the QA defects. Offline only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import check


class CheckerQaTests(unittest.TestCase):
    def cli(self, args, env=None):
        return subprocess.run([sys.executable, str(ROOT/'check.py'), *args], capture_output=True, env=env, timeout=10)

    def test_cyrillic_denominator_all_unicode_letters(self):
        r = check.check('中中文文文文文文文Я', {'cyrillic_ratio':.8})
        self.assertFalse(r['ok'])
        self.assertEqual(r['metrics']['cyrillic_ratio'], .1)
        self.assertEqual(check.letter_share('Я 123!?', r'[А-Яа-яЁё]'), 1)

    def test_markdown_plus_and_blockquote(self):
        for text in ['+ list entry', '> quoted text']:
            self.assertFalse(check.check(text, {'no_markdown':True})['ok'])

    def scene(self, narration='русское '*20, visual='cinematic '*15):
        return json.dumps([{'scene':i,'narration':narration,'visual_prompt':visual,'duration_sec':10} for i in range(1,7)])

    def test_mostly_english_narration_rejected(self):
        r = check.check(self.scene('english '*19+'Я'), check.PRESETS['T2_scenejson'])
        self.assertTrue(any('predominantly Russian' in v for v in r['violations']))

    def test_french_visual_rejected(self):
        for text in ['Le soleil éclaire une rue déserte tandis que des silhouettes traversent lentement une ancienne place pavée', 'Une rue ancienne sous une lune pleine montre plusieurs personnes marchant vers une grande maison blanche']:
            r = check.check(self.scene(visual=text), check.PRESETS['T2_scenejson'])
            self.assertTrue(any('ASCII English' in v for v in r['violations']))

    def test_chinese_visual_rejected(self):
        r = check.check(self.scene(visual='中文 '*15), check.PRESETS['T2_scenejson'])
        self.assertTrue(any('ASCII English' in v for v in r['violations']))

    def test_cp1252_stdout_and_stderr_are_utf8(self):
        with tempfile.TemporaryDirectory() as d:
            draft=Path(d)/'draft.txt'; draft.write_text('Русский текст',encoding='utf-8')
            env=dict(os.environ, PYTHONIOENCODING='cp1252')
            out=self.cli(['--task','T1_script60','--input',str(draft)],env)
            self.assertEqual(out.returncode,1)
            self.assertEqual(json.loads(out.stdout.decode('utf-8'))['payload'],'Русский текст')
            cfg=Path(d)/'cfg.json'; cfg.write_text('{"ошибка":true}',encoding='utf-8')
            out=self.cli(['--config',str(cfg),'--input',str(draft)],env)
            self.assertEqual(out.returncode,2)
            self.assertIn('ошибка',json.loads(out.stderr.decode('utf-8'))['error'])

    def test_deep_json_returns_error_exit2(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'deep.txt'; path.write_text('['*2000+'0'+']'*2000)
            for args in [['--config',str(path),'--input',str(path)], ['--task','T2_scenejson','--input',str(path)]]:
                out=self.cli(args)
                self.assertEqual(out.returncode,2)
                self.assertFalse(json.loads(out.stderr)['ok'])


