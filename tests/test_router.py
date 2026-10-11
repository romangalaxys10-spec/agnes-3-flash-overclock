"""Router tests: every route resolves, headings exist, output stays small, ambiguity yields no content.

Remote (jg-*) routes are tested with a stubbed fetcher and a temp cache dir; the suite never
touches the network. A live smoke test runs only when AGNES_LIVE_TEST=1 is set.
"""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agnes_kit import jg_router, router as r
from agnes_kit import qa_panel
from agnes_kit.mcp_server import call_tool

AGENT = qa_panel.load_perspectives()[0]["id"]
STUB_TEXT = "# stub slice\nstubbed remote content\n"


def stub_fetch(url, timeout):
    return STUB_TEXT + url + "\n"


def is_remote(route):
    return any(it["type"] == "remote" for it in route["items"])


class RouterTests(unittest.TestCase):
    def test_every_route_resolves(self):
        idx = r.load_index()
        with tempfile.TemporaryDirectory() as td:
            os.environ[jg_router.ENV_CACHE_DIR] = td
            for rt in idx["routes"]:
                res = r.route(rt["task"], rt["phase"], agent=AGENT, base_sha="abc1234",
                              fetcher=stub_fetch)
                self.assertEqual(res["status"], "ok", rt["id"])
                self.assertTrue(all(i["content"].strip() for i in res["items"]), rt["id"])
                self.assertLessEqual(res["bytes"], r.MAX_ITEM_BYTES * len(rt["items"]))

    def test_routed_is_smaller_than_corpus(self):
        biggest = max(r.route(t, p, agent=AGENT)["bytes"]
                      for rt in r.load_index()["routes"] if not is_remote(rt)
                      for t, p in [(rt["task"], rt["phase"])])
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

    def test_remote_route_with_stub(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ[jg_router.ENV_CACHE_DIR] = td
            res = r.route("jg-mcp", "discover", fetcher=stub_fetch)
            self.assertEqual(res["status"], "ok")
            self.assertIn("https://jackgross-five.vercel.app/router/mcp/discover.md", res["items"][0]["source"])
            self.assertIn("stubbed remote content", res["items"][0]["content"])
            # second call served from cache even when the network is gone
            def boom(url, timeout):
                raise OSError("network down")
            res2 = r.route("jg-mcp", "discover", fetcher=boom, refresh=True)
            self.assertEqual(res2["status"], "ok")
            self.assertIn("[cache]", res2["items"][0]["source"])

    def test_remote_offline_fallback_and_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ[jg_router.ENV_CACHE_DIR] = td
            res = r.route("jg-mcp", "secure", offline=True)
            self.assertEqual(res["status"], "unavailable")
            self.assertNotIn("items", res)
            self.assertIn("https://", res["message"])
            # seed the cache, then offline serves it
            jg_router.fetch("mcp", "secure", fetcher=stub_fetch)
            res2 = r.route("jg-mcp", "secure", offline=True)
            self.assertEqual(res2["status"], "ok")
            self.assertIn("[cache]", res2["items"][0]["source"])

    def test_remote_query_match(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ[jg_router.ENV_CACHE_DIR] = td
            res = r.route(query="find an mcp server for postgres", fetcher=stub_fetch)
            self.assertEqual((res["status"], res["route"]), ("ok", "jg-mcp.discover"))
            res = r.route(query="latest extensions digest news", fetcher=stub_fetch)
            self.assertEqual(res["route"], "jg-extensions.latest")

    def test_jg_router_unit(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ[jg_router.ENV_CACHE_DIR] = td
            with self.assertRaises(ValueError):
                jg_router.url_for("nope", "x")
            text, meta = jg_router.fetch("prompts", "fill", fetcher=stub_fetch)
            self.assertEqual(meta["status"], "live")
            text2, meta2 = jg_router.fetch("prompts", "fill", fetcher=lambda u, t: 1 / 0)
            self.assertEqual((text2, meta2["status"]), (text, "cache"))
            with self.assertRaises(jg_router.Unavailable):
                jg_router.fetch("extensions", "latest", offline=True)
            big = "x" * (jg_router.MAX_REMOTE_BYTES + 1)
            with self.assertRaises(ValueError):
                jg_router.fetch("extensions", "latest", fetcher=lambda u, t: big)

    def test_mcp_remote_offline_arg(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ[jg_router.ENV_CACHE_DIR] = td
            out = call_tool("agnes_route", {"task": "jg-prompts", "phase": "verify", "offline": True})
            self.assertEqual(out["status"], "unavailable")

    @unittest.skipUnless(os.environ.get("AGNES_LIVE_TEST") == "1", "live network smoke test opt-in")
    def test_live_site_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ[jg_router.ENV_CACHE_DIR] = td
            text, meta = jg_router.fetch("prompts", "select")
            self.assertEqual(meta["status"], "live")
            self.assertIn("prompts", text.lower())
            self.assertLess(len(text.encode()), jg_router.MAX_REMOTE_BYTES)


if __name__ == "__main__":
    unittest.main()
