"""Generic OpenAI-compatible usage: generate -> editor -> check. UNTESTED against Agnes.
Set AGNES_BASE_URL and AGNES_API_KEY in the environment. Standard library only.
Verify the model's current billing and rate limits before running."""
import json, os, sys, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from agnes_kit import build_generation_messages, load_config
import check as ck

cfg = load_config()

def chat(messages):
    req = urllib.request.Request(
        os.environ["AGNES_BASE_URL"].rstrip("/") + "/chat/completions",
        data=json.dumps({"model": cfg["model"], "messages": messages}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ[cfg["api_key_env"]]})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["choices"][0]["message"]["content"]

if __name__ == "__main__":
    task_id = sys.argv[1]  # e.g. T1_script60
    task = next(t for t in json.loads((ROOT / "tasks.json").read_text("utf-8")) if t["id"] == task_id)["task"]
    draft = ck.extract_final(chat(build_generation_messages(task)))
    editor = (ROOT / "prompts" / "v1-editor-tested.txt").read_text("utf-8")
    final = ck.extract_final(chat([{"role": "system", "content": editor},
                                   {"role": "user", "content": task + "\n\n" + draft}]))
    print(json.dumps(ck.check(final, ck.PRESETS[task_id]), ensure_ascii=False, indent=2))
