import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agnes_kit import (FileLessons, FileMemory, HeadroomTokenSaver, Mem0Memory,
                       NullTokenSaver, build_generation_messages, load_config,
                       load_skill, review_messages)


class KitTests(unittest.TestCase):
    def test_config_has_no_secret_values(self):
        c = load_config()
        self.assertEqual(c["context_window_tokens"], 524288)
        self.assertNotIn("sk-", json.dumps(c))

    def test_file_memory_and_lessons(self):
        with tempfile.TemporaryDirectory() as d:
            m = FileMemory(Path(d) / "m.json")
            m.add("client prefers short hooks", "u1")
            m.add("unrelated cooking note", "u2")
            self.assertEqual(m.search("short hooks please", "u1"), ["client prefers short hooks"])
            self.assertEqual(m.search("short hooks", "u2"), [])
            l = FileLessons(Path(d) / "l.json")
            l.save("write 60 second script about tea", "avoid numbers in hook")
            self.assertEqual(l.relevant("script about tea"), ["avoid numbers in hook"])
            self.assertEqual(l.relevant("quantum"), [])

    def test_messages_use_tested_prompt_verbatim(self):
        sysmsg = (Path(__file__).resolve().parent.parent / "prompts" / "v1-generation-tested.txt").read_text("utf-8")
        msgs = build_generation_messages("task", memories=["a"], lessons=["b"], token_saver=NullTokenSaver())
        self.assertEqual(msgs[0]["content"], sysmsg)
        self.assertIn("- a", msgs[1]["content"])
        self.assertEqual(build_generation_messages("task")[1]["content"], "task")

    def test_vendored_skills_load(self):
        self.assertTrue(load_skill("superpowers-brainstorming").startswith("# Brainstorming"))
        self.assertIn("bug", review_messages("diff")[0]["content"].lower())

    def test_optional_deps_fail_clearly(self):
        for cls in (HeadroomTokenSaver, Mem0Memory):
            try:
                cls()
            except RuntimeError as e:
                self.assertIn("pip install", str(e))
            except Exception:
                pass  # package present: constructor may need its own config


if __name__ == "__main__":
    unittest.main()
