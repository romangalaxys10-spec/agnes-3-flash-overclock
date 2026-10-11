"""Router tests: every route resolves, headings exist, output stays small, ambiguity yields no content."""
import json, subprocess, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agnes_kit import router as r
from agnes_kit import qa_panel
from agnes_kit.mcp_server import call_tool

AGENT = qa_panel.load_perspectives()[0]["id"]


class RouterTests(unittest.TestCase):
    def test_every_route_resolves(self):
        idx = r.load_index()
        for rt in idx["routes"]:
            res = r.route(rt["task"], rt["phase"], agent=AGENT, base_sha="abc1234")
            self.assertEqual(res["status"], "ok", rt["id"])
            self.assertTrue(all(i["content"].strip() for i in res["items"]), rt["id"])
            self.assertLessEqual(res["bytes"], r.MAX_ITEM_BYTES * len(rt["items"]))

    def test_routed_is_smaller_than_corpus(self):
        biggest = max(r.route(t, p, agent=AGENT)["bytes"] for t, ps in r.list_routes().items() for p in ps)
        self.assertLess(biggest * 3, r.corpus_bytes())

    def test_only_requested_phase(self):
        a = r.route("unslop", "motion")["items"][0]["content"]
        self.assertIn("reduced-motion", a)
        self.assertNotIn("Phase: direction", a)
        self.assertNotIn("DESIGN.md", a)

    def test_agent_brief_needs_agent_and_renders(self):
        self.assertEqual(r.route("qa-panel", "run")["status"], "need-input")
        with self.assertRaises(ValueError):
            r.route("qa-panel", "run", agent="not-a-lens")
        res = r.route("qa-panel", "run", agent=AGENT, base_sha="abc1234")
        self.assertIn("abc1234", res["items"][0]["content"])
        self.assertNotIn("{{", res["items"][0]["content"])

    def test_unknown_and_ambiguous(self):
        self.assertEqual(r.route("nope", "x")["status"], "unknown")
        amb = r.route(query="hello there")
        self.assertEqual(amb["status"], "ambiguous"); self.assertNotIn("items", amb)
        self.assertEqual(r.route()["status"], "need-input")

    def test_query_match(self):
        res = r.route(query="audit my css for slop")
        self.assertEqual((res["status"], res["route"]), ("ok", "unslop.audit"))
        self.assertEqual(r.route(query="run the repair retry violations")["route"], "script.repair")

    def test_section_extraction(self):
        t = "# A\n## B\nx\n### C\ny\n## D\nz\n"
        self.assertEqual(r.extract_section(t, "B"), "## B\nx\n### C\ny\n")
        with self.assertRaises(KeyError):
            r.extract_section(t, "Q")

    def test_mcp_tool_and_cli(self):
        self.assertEqual(call_tool("agnes_route", {"task": "proof", "phase": "deliver"})["status"], "ok")
        p = subprocess.run([sys.executable, str(ROOT / "route.py"), "--task", "scripts", "--phase", "check"], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(p.returncode, 0, p.stderr)
        p = subprocess.run([sys.executable, str(ROOT / "route.py"), "--query", "zzz"], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(p.returncode, 1)


if __name__ == "__main__":
    unittest.main()
