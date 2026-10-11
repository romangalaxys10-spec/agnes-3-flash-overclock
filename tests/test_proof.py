"""Proof presence/shape regressions. Synthetic code/visual evidence is not real proof."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import check
from agnes_kit.mcp_server import call_tool


class ProofTests(unittest.TestCase):
    def example(self):
        return json.loads((ROOT/'examples/proof-delivery.json').read_text())

    def run_gate(self, delivery, **extra):
        return check.check(json.dumps(delivery), {'require_proof':True, **extra})

    def full(self):
        d=self.example();p=d['proof']
        p['artifacts'] += [dict(id='diff',path='synthetic.patch',role='diff',sha256='a'*64),dict(id='image',path='synthetic.png',role='render',sha256='b'*64)]
        p['code']={'applicable':True,'baseline':'synthetic-test-baseline','diff_artifact':'diff','test_commands':['verify'],'reproduce':'Synthetic test fixture, not an executed software change.'}
        p['visual']={'applicable':True,'evidence':[{'artifact':'image','kind':'render','pixel_inspected':True,'inspection_note':'Synthetic unit-test assertion only, no actual visual delivery.'}]}
        return d

    def test_valid_work_example(self):
        self.assertTrue(self.run_gate(self.example())['ok'])

    def test_example_manifest_hashes_match_shipped_bytes(self):
        for a in self.example()['proof']['artifacts']:
            self.assertEqual(hashlib.sha256((ROOT/a['path']).read_bytes()).hexdigest(),a['sha256'])

    def test_proofless_text_rejected(self):
        r=check.check('done',{'require_proof':True})
        self.assertFalse(r['ok'])
        self.assertTrue(any('Proof:' in v for v in r['violations']))

    def test_missing_proof_rejected(self):
        self.assertFalse(self.run_gate({'payload':'done'})['ok'])

    def test_missing_work_fields(self):
        for field in ['summary','files_touched','artifacts','commands','schema_version','status','code','visual']:
            d=self.example();del d['proof'][field]
            with self.subTest(field=field):self.assertFalse(self.run_gate(d)['ok'])

    def test_bad_artifact_hashes(self):
        for value in ['sha256', 'a'*63,'z'*64,[],None]:
            d=self.example();d['proof']['artifacts'][0]['sha256']=value
            with self.subTest(value=value):self.assertFalse(self.run_gate(d)['ok'])

    def test_duplicate_and_missing_artifact_ids(self):
        d=self.example();d['proof']['artifacts'][1]['id']='note'
        self.assertFalse(self.run_gate(d)['ok'])
        d=self.example();del d['proof']['artifacts'][0]['id']
        self.assertFalse(self.run_gate(d)['ok'])

    def test_command_output_must_reference_manifest(self):
        d=self.example();d['proof']['commands'][0]['output_artifact']='missing'
        self.assertFalse(self.run_gate(d)['ok'])

    def test_invalid_command_ledger(self):
        for field,value in [('exit_code',True),('cwd',''),('command',''),('id',[]),('output_artifact',{})]:
            d=self.example();d['proof']['commands'][0][field]=value
            with self.subTest(field=field):self.assertFalse(self.run_gate(d)['ok'])

    def test_full_code_visual_fixture_well_formed(self):
        self.assertTrue(self.run_gate(self.full(),require_code_proof=True,require_visual_proof=True)['ok'])

    def test_code_optout_cannot_bypass_task_constraint(self):
        self.assertFalse(self.run_gate(self.example(),require_code_proof=True)['ok'])

    def test_visual_optout_cannot_bypass_task_constraint(self):
        self.assertFalse(self.run_gate(self.example(),require_visual_proof=True)['ok'])

    def test_code_diff_test_and_reproduction_required(self):
        for field in ['baseline','diff_artifact','test_commands','reproduce']:
            d=self.full();del d['proof']['code'][field]
            with self.subTest(field=field):self.assertFalse(self.run_gate(d)['ok'])
        d=self.full();d['proof']['code']['diff_artifact']='absent'
        self.assertFalse(self.run_gate(d)['ok'])

    def test_failed_or_unknown_test_command_rejected(self):
        d=self.full();d['proof']['commands'][0]['exit_code']=1
        self.assertFalse(self.run_gate(d)['ok'])
        d=self.full();d['proof']['code']['test_commands']=['missing']
        self.assertFalse(self.run_gate(d)['ok'])

    def test_visual_pixel_inspection_and_artifact_required(self):
        for field,value in [('artifact','missing'),('kind','ocr'),('pixel_inspected',False),('inspection_note','')]:
            d=self.full();d['proof']['visual']['evidence'][0][field]=value
            with self.subTest(field=field):self.assertFalse(self.run_gate(d)['ok'])

    def test_empty_visual_evidence_rejected(self):
        d=self.full();d['proof']['visual']['evidence']=[]
        self.assertFalse(self.run_gate(d)['ok'])

    def test_not_applicable_needs_reason(self):
        d=self.example();del d['proof']['visual']['reason']
        self.assertFalse(self.run_gate(d)['ok'])

    def test_blocked_status_cannot_pass_delivery(self):
        d=self.example();d['proof']['status']='blocked'
        self.assertFalse(self.run_gate(d)['ok'])

    def test_existing_constraints_check_payload_not_envelope(self):
        self.assertTrue(self.run_gate(self.example(),word_range=[7,7])['ok'])
        self.assertFalse(self.run_gate(self.example(),word_range=[90,110])['ok'])

    def test_malformed_shapes_fail_without_crash(self):
        for bad in [None, [], 1, {'proof':5}, {'payload':'x','proof':{'artifacts':[None], 'commands':[None], 'code':[], 'visual':[]}}]:
            with self.subTest(bad=bad):self.assertFalse(self.run_gate(bad)['ok'])

    def test_flags_validate_as_booleans(self):
        for key in check.PROOF_FLAGS:
            with self.assertRaises(ValueError):check.validate_config({key:1})

    def test_mcp_dispatch_and_prompt_discovery(self):
        r=call_tool('agnes_check',{'config':{'require_proof':True},'text':json.dumps(self.example())})
        self.assertTrue(r['ok'])
        self.assertFalse(call_tool('agnes_check',{'config':{'require_proof':True},'text':'done'})['ok'])
        self.assertIn('proof-of-delivery contract',call_tool('agnes_get_prompt',{'name':'proof-of-delivery-untested'}))

    def test_cli_proof_pass_and_failure(self):
        p=subprocess.run([sys.executable,str(ROOT/'check.py'),'--config',str(ROOT/'examples/proof-constraints.json'),'--input',str(ROOT/'examples/proof-delivery.json')],capture_output=True,timeout=10)
        self.assertEqual(p.returncode,0);self.assertTrue(json.loads(p.stdout)['ok'])

    def test_presence_not_truth_boundary(self):
        d=self.example();d['proof']['artifacts'][0]['sha256']='f'*64
        r=self.run_gate(d)
        self.assertTrue(r['ok'])  # deliberate: shape checker never reads artifact bytes
        self.assertTrue(any('does not verify hashes' in w for w in r['manual_review']))

    def test_duplicate_json_keys_rejected(self):
        r=check.check('{"payload":"x","payload":"y","proof":{}}',{'require_proof':True})
        self.assertFalse(r['ok'])

    def test_touched_file_without_artifact_rejected(self):
        d=self.example();d['proof']['files_touched'].append('unlisted.py')
        self.assertFalse(self.run_gate(d)['ok'])

    def test_duplicate_command_ids_rejected(self):
        d=self.example();d['proof']['commands'].append(dict(d['proof']['commands'][0]))
        self.assertFalse(self.run_gate(d)['ok'])
