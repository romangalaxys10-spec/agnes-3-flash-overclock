"""Scanner tests. Synthetic CSS only; a clean scan does not prove good design."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agnes_kit import unslop as u


def rules(css):
    return {f["rule"] for f in u.check_text(css)}


class UnslopTests(unittest.TestCase):
    def test_each_rule(self):
        cases = {
            "gradient-text": ".a{background:linear-gradient(#000,#fff);background-clip:text}",
            "side-stripe-border": ".a{border-left:4px solid red}",
            "default-font-as-brand": "body{font-family:Inter,sans-serif}",
            "purple-gradient": ".a{background:linear-gradient(90deg,#6366f1,#fff)}",
            "large-radius": ".a{border-radius:28px}",
            "ghost-card": ".a{border:1px solid #ddd;box-shadow:0 8px 32px rgba(0,0,0,.1)}",
            "bounce-easing": ".a{transition:transform .3s cubic-bezier(.34,1.56,.64,1)}",
            "hover-scale-image": ".c img:hover{transform:scale(1.1)}",
            "low-contrast": ".a{color:#aaa;background:#fff}",
            "z-index-soup": ".a{z-index:9999}",
            "tight-tracking": "h1{letter-spacing:-0.06em}",
            "display-too-large": "h1{font-size:clamp(3rem,10vw,9rem)}",
            "glassmorphism": ".a{backdrop-filter:blur(12px)}",
            "no-reduced-motion": ".a{transition:opacity .2s}",
        }
        for rule, css in cases.items():
            self.assertIn(rule, rules(css), rule)

    def test_no_false_positives_on_clean(self):
        css = ('body{font-family:Georgia,serif;color:#111;background:#fff}'
               '.a{border:1px solid #ddd;border-radius:12px;border-left:1px solid #ccc;z-index:10}'
               '.b{border-radius:999px;transition:opacity .2s cubic-bezier(.25,1,.5,1)}'
               '@media (prefers-reduced-motion:reduce){.b{transition:none}}')
        self.assertEqual(rules(css), set())

    def test_border_with_small_shadow_not_ghost(self):
        self.assertNotIn("ghost-card", rules(".a{border:1px solid #ddd;box-shadow:0 1px 2px rgba(0,0,0,.1)}"))

    def test_comments_ignored(self):
        self.assertEqual(rules("/* border-left: 4px solid red; */ .a{color:#000}"), set())

    def test_tailwind(self):
        r = rules('<div class="bg-clip-text rounded-3xl from-purple-500 animate-bounce">')
        self.assertTrue({"gradient-text", "large-radius", "purple-gradient", "bounce-easing"} <= r)

    def test_contrast_math(self):
        self.assertAlmostEqual(u.contrast("#000", "#fff"), 21.0, places=1)

    def test_cli(self):
        run = lambda *a: subprocess.run([sys.executable, str(ROOT / "unslop_check.py"), *a], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(run("unslop/examples/sloppy.css").returncode, 1)
        self.assertEqual(run("unslop/examples/clean.css").returncode, 0)
        self.assertEqual(run("--fail-on", "critical", "unslop/examples/clean.css").returncode, 0)
        j = json.loads(run("unslop/examples/sloppy.css", "--json").stdout)
        self.assertGreater(j["failing"], 0)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run(d).returncode, 2)
        self.assertEqual(run("does/not/exist").returncode, 2)


if __name__ == "__main__":
    unittest.main()
