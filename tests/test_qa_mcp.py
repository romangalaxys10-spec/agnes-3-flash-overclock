"""MCP contract regressions. Offline only."""
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agnes_kit.mcp_server import handle, call_tool


class McpQaTests(unittest.TestCase):
    def test_check_requires_exactly_one_selector(self):
        for args in [{'text':'abc'}, {'text':'abc','task':'T1_script60','config':{}}, {'text':'abc','task':'','config':{}}]:
            with self.assertRaisesRegex(ValueError,'exactly one'):call_tool('agnes_check',args)
        self.assertTrue(call_tool('agnes_check',{'text':'abc','config':{}})['ok'])

    def test_version_missing_or_wrong_rejected(self):
        for version in [None, '1.0', 2.0]:
            req={'id':1,'method':'ping'}
            if version is not None:req['jsonrpc']=version
            self.assertEqual(handle(req)['error']['code'],-32600)
        self.assertIsNone(handle({'jsonrpc':'2.0','method':'notifications/initialized'}))
        self.assertEqual(handle({'method':'notifications/initialized'})['error']['code'],-32600)
