"""Prompt, host config and client safety regressions. Offline only."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agnes_kit.mcp_server import handle
spec = importlib.util.spec_from_file_location('generic_client', ROOT / 'integrations/generic/openai_compatible.py')
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


class PromptAndClientTests(unittest.TestCase):
    def test_generation_prompt_matches_report_bytes(self):
        report = (ROOT / 'docs/benchmark-report.md').read_text('utf-8')
        body = report.split('## pre.txt (adapted prompt v1 - generation pass)\n````text\n')[1].split('\n````\n\n## rev.txt')[0]
        self.assertEqual((ROOT / 'prompts/v1-generation-tested.txt').read_bytes(), (body+'\n').encode('utf-8'))
        self.assertTrue(body.endswith('ЗАДАЧА:'))

    def test_editor_labels_and_prompt(self):
        msgs = client.build_editor_messages('task', 'draft')
        self.assertEqual(msgs[0]['content'], (ROOT / 'prompts/v1-editor-tested.txt').read_text('utf-8'))
        self.assertEqual(msgs[1]['content'], 'ЗАДАЧА:\ntask\n\nЧЕРНОВИК:\ndraft')

    def test_insecure_remote_urls_rejected(self):
        for url in ['http://api.example/v1', 'ftp://localhost', 'api.example', 'https://user:pass@api.example', 'http://localhost.evil/v1']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                client.validated_base_url(url)

    def test_https_and_loopback_allowed(self):
        for url in ['https://api.example/v1', 'http://localhost/v1', 'http://127.0.0.1:8000/v1', 'http://[::1]:8000/v1']:
            self.assertEqual(client.validated_base_url(url), url)

    def test_validation_precedes_key_or_network(self):
        with patch.dict(os.environ, {'AGNES_BASE_URL': 'http://api.example'}, clear=True), patch.object(client.urllib.request, 'build_opener') as opener:
            with self.assertRaisesRegex(ValueError, 'HTTPS'):
                client.chat([])
            opener.assert_not_called()

    def test_redirect_does_not_leak_key(self):
        req = client.urllib.request.Request('https://api.example/v1/chat/completions')
        for url in ['http://api.example/other', 'https://other.example/other']:
            with self.assertRaises(ValueError):
                client.SecureRedirectHandler().redirect_request(req, None, 302, 'redirect', {}, url)

    def test_zcode_config_variants(self):
        glob = json.loads((ROOT/'integrations/zcode/config.json').read_text())
        project = json.loads((ROOT/'integrations/zcode/mcp.json').read_text())
        self.assertEqual(glob['mcp']['servers'], project['mcpServers'])

    def test_runtime_and_manifest_versions_align(self):
        version = json.loads((ROOT/'.claude-plugin/plugin.json').read_text())['version']
        response = handle({'jsonrpc':'2.0','id':1,'method':'initialize'})
        self.assertEqual(version, '0.1.0')
        self.assertEqual(response['result']['serverInfo']['version'], version)


