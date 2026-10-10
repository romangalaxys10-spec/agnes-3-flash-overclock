import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('agnes_check',Path(__file__).resolve().parents[1]/'check.py')
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class GateTests(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(gate.words('два-три слова 2,5'),4)
        r=gate.check('слово '*138,{'word_range':[150,170]})
        self.assertFalse(r['ok'])
        self.assertIn('138',r['violations'][0])
    def test_valid_prose(self):
        self.assertTrue(gate.check('Разве '+('слово '*149)+'так?',gate.PRESETS['T1_script60'])['ok'])
    def test_preamble_and_quotes(self):
        for s in ['Вот закадровый текст:\nПривет.', '"Привет"', '```json\n{}\n```', '<final>hi</final>', '']:
            self.assertFalse(gate.check(s,{})['ok'])
    def test_decimal_and_extra(self):
        cfg={'preserve_source_numbers':True,'required_numbers':['10','2.5']}
        self.assertTrue(gate.check('10 процентов; 2,5 процента',cfg,'10 2.5')['ok'])
        self.assertFalse(gate.check('10 2,5 7',cfg,'10 2,5')['ok'])
        self.assertFalse(gate.check('10',cfg,'10 2,5')['ok'])
    def test_no_digits(self):
        self.assertFalse(gate.check('Нам １２ лет',{'no_digits':True})['ok'])
    def test_json_strict(self):
        for s in ['{"title":"x","title":"y"}', '{"x":NaN}', 'Here is {}', 'null']:
            self.assertFalse(gate.check(s,{'json_mode':'meta'})['ok'])
    def scenes(self):
        return [dict(scene=i,narration='русское '*20,visual_prompt='cinematic '*15,duration_sec=10) for i in range(1,7)]
    def test_scenes_pass(self):
        import json
        self.assertTrue(gate.check(json.dumps(self.scenes(),ensure_ascii=False),gate.PRESETS['T2_scenejson'])['ok'])
    def test_scene_invalid_types(self):
        import json
        for value in [True,10.0,'10',0,-1]:
            j=self.scenes(); j[0]['duration_sec']=value
            self.assertFalse(gate.check(json.dumps(j),gate.PRESETS['T2_scenejson'])['ok'])
        j=self.scenes(); j[0]['scene']=True
        self.assertFalse(gate.check(json.dumps(j),gate.PRESETS['T2_scenejson'])['ok'])
    def test_duration_and_lengths(self):
        import json
        j=self.scenes(); j[0]['duration_sec']=9; j[0]['narration']='коротко'
        r=gate.check(json.dumps(j),gate.PRESETS['T2_scenejson'])
        self.assertEqual(r['metrics']['duration_sum'],59)
        self.assertTrue(any('1 words' in x for x in r['violations']))
    def test_meta(self):
        import json
        j=dict(title='Ночь',caption='Смотри. Ты здесь?',hashtags=['#ночь','#сон','#night','#dream','#time'])
        self.assertTrue(gate.check(json.dumps(j),gate.PRESETS['T4_meta'])['ok'])
        j['caption']='Да. Нет. Возможно.'
        self.assertFalse(gate.check(json.dumps(j),gate.PRESETS['T4_meta'])['ok'])
    def test_paragraphs(self):
        s='\n\n'.join(f'{x} смотрит. Он ждёт.' for x in ['Ребёнок','Старик','Один','Другой','Каждый'])
        self.assertTrue(gate.check(s,gate.PRESETS['T3_constraints'])['ok'])
        self.assertFalse(gate.check(s+' Быстро.',gate.PRESETS['T3_constraints'])['ok'])
    def test_extract_final(self):
        self.assertEqual(gate.extract_final('<check>нет</check><final>Текст</final>'),'Текст')
        for s in ['<final>x', '<final>x</final><final>y</final>', '<final>x</final>tail']:
            with self.assertRaises(ValueError):
                gate.extract_final(s)
    def test_config_errors(self):
        for cfg in [{'typo':True},{'word_range':[100,80]},{'no_digits':1},{'json_mode':'scenes'},{'preserve_source_numbers':True}]:
            with self.assertRaises(ValueError):
                gate.check('текст',cfg)
    def test_subscription_last(self):
        self.assertFalse(gate.check('Подпишись. Теперь другой конец.',{'subscribe_ending':True})['ok'])
        self.assertTrue(gate.check('Что дальше? Подпишись.',{'subscribe_ending':True})['ok'])

if __name__=='__main__':
    unittest.main()
