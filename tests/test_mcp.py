import json, subprocess, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent


def rpc(*msgs):
    p = subprocess.run([sys.executable, "-m", "agnes_kit.mcp_server"], input="\n".join(json.dumps(m) for m in msgs) + "\n",
                       capture_output=True, text=True, cwd=ROOT, timeout=20)
    return [json.loads(l) for l in p.stdout.splitlines()]


class McpTests(unittest.TestCase):
    def test_flow(self):
        r = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "agnes_check",
                 "arguments": {"task": "T1_script60", "text": "Слишком коротко."}}},
                {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "agnes_get_prompt",
                 "arguments": {"name": "v1-editor-tested"}}},
                {"jsonrpc": "2.0", "id": 5, "method": "nope"})
        self.assertEqual([x["id"] for x in r], [1, 2, 3, 4, 5])  # notification gets no reply
        self.assertEqual(r[0]["result"]["serverInfo"]["name"], "agnes-overclock")
        self.assertEqual(len(r[1]["result"]["tools"]), 5)
        rep = json.loads(r[2]["result"]["content"][0]["text"])
        self.assertFalse(rep["ok"])
        self.assertTrue(r[3]["result"]["content"][0]["text"])
        self.assertEqual(r[4]["error"]["code"], -32601)


    def test_robustness(self):
        import subprocess
        p = subprocess.run([sys.executable, str(ROOT / "agnes_mcp.py")], input='[1]\nnot json\n{"jsonrpc":"2.0","id":0,"method":"tools/call","params":{"name":"agnes_check","arguments":{"text":5,"task":"T1_script60"}}}\n{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"zzz"}}\n',
                           capture_output=True, text=True, cwd="/", timeout=20)
        r = [json.loads(l) for l in p.stdout.splitlines()]
        self.assertEqual(r[0]["error"]["code"], -32600)
        self.assertEqual(r[1]["error"]["code"], -32700)
        self.assertTrue(r[2]["result"]["isError"])  # bad arg type reported, server alive
        self.assertEqual(r[3]["error"]["code"], -32602)

    def test_unknown_method(self):
        r = rpc({"jsonrpc": "2.0", "id": 9, "method": "nope"})
        self.assertEqual(r[0]["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
