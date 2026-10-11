"""QA panel helper tests. Synthetic data only; checks bookkeeping, not finding truth."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agnes_kit import qa_panel as q

P = q.load_perspectives()
SHA = "c7d4f39"


def rep(agent, findings, sha=SHA):
    return {"agent": agent, "base_sha": sha, "reviewed_clean_clone": True, "findings": findings}


def fnd(title, sev="major", file="a.py"):
    return {"title": title, "severity": sev, "file": file, "evidence": "ran X"}


class PanelTests(unittest.TestCase):
    def test_perspectives_shape(self):
        self.assertEqual(len(P), 25)
        self.assertEqual(len({p["id"] for p in P}), 25)
        for w in range(1, 6):
            self.assertEqual(sum(1 for p in P if p["wave"] == w), 5)

    def test_optional_lens(self):
        full = q.load_perspectives(with_optional=True)
        self.assertEqual(len(full), 26)
        self.assertEqual(full[-1]["id"], "ui-slop")

    def test_render_briefs(self):
        b = q.render_briefs(P, SHA, "https://x/y")
        self.assertEqual(len(b), 25)
        for t in b.values():
            self.assertIn(SHA, t); self.assertNotIn("{{", t)
        with self.assertRaises(ValueError):
            q.render_briefs(P, "main")

    def test_validate(self):
        self.assertEqual(q.validate_report(rep("edge-inputs", []), P, SHA), [])
        self.assertTrue(q.validate_report(rep("nobody", []), P, SHA))
        self.assertTrue(q.validate_report(rep("edge-inputs", [], "deadbee"), P, SHA))
        bad = rep("edge-inputs", [{"title": "t", "severity": "huge", "file": "f", "evidence": ""}])
        self.assertGreaterEqual(len(q.validate_report(bad, P, SHA)), 2)
        self.assertTrue(q.validate_report({"agent": "edge-inputs"}, P, SHA))

    def test_consolidate_merges_and_takes_max_severity(self):
        r = [rep("edge-inputs", [fnd("Crash on empty input", "minor")]),
             rep("docs-accuracy", [fnd("empty input crash", "blocker")]),
             rep("onboarding", [fnd("Unrelated thing", "nit", "b.py")])]
        issues = q.consolidate(r)
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0]["severity"], "blocker")
        self.assertEqual(sorted(issues[0]["agents"]), ["docs-accuracy", "edge-inputs"])

    def test_gate(self):
        r = [rep(p["id"], []) for p in P]
        cov = q.coverage(r, P)
        self.assertTrue(q.gate([], cov)["passed"])
        self.assertFalse(q.gate([], q.coverage(r[:3], P))["passed"])
        self.assertTrue(q.gate([], q.coverage(r[:3], P), False)["passed"])
        it = {"id": "QA-001", "severity": "major", "title": "t", "status": "open"}
        self.assertFalse(q.gate([it], cov)["passed"])
        it["status"] = "fixed"
        self.assertFalse(q.gate([it], cov)["passed"])
        it.update(fix_commit="abc1234", verification="suite")
        self.assertTrue(q.gate([it], cov)["passed"])
        it.update(status="wontfix", reason="")
        self.assertFalse(q.gate([it], cov)["passed"])

    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            run = lambda *a: subprocess.run([sys.executable, str(ROOT / "qa_panel.py"), *a], capture_output=True, text=True, cwd=ROOT)
            r = run("render", "--base-sha", SHA, "--out", d + "/b")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(len(list(Path(d, "b").glob("*.md"))), 25)
            r = run("consolidate", "--reports", str(ROOT / "qa-panel/examples"), "--base-sha", SHA, "--out", d + "/o")
            self.assertEqual(r.returncode, 0, r.stderr)
            doc = json.loads(Path(d, "o/issues.json").read_text())
            self.assertEqual(len(doc["issues"]), 1)
            self.assertEqual(run("gate", "--issues", d + "/o/issues.json").returncode, 1)
            self.assertEqual(run("gate", "--issues", d + "/o/issues.json", "--allow-partial").returncode, 1)  # open major
            Path(d, "bad").mkdir(); Path(d, "bad/x.json").write_text('{"agent":"nope"}')
            self.assertEqual(run("consolidate", "--reports", d + "/bad", "--base-sha", SHA, "--out", d + "/o2").returncode, 2)


if __name__ == "__main__":
    unittest.main()
