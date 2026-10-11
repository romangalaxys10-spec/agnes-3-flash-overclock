"""Generic OpenAI-compatible usage: generate -> editor -> check. UNTESTED against Agnes.
Set AGNES_BASE_URL and AGNES_API_KEY in the environment. Standard library only.
Verify the model's current billing and rate limits before running."""
import ipaddress
import json, os, sys, urllib.request
from urllib.parse import urlsplit
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from agnes_kit import build_generation_messages, load_config
import check as ck

cfg = load_config()

def validated_base_url(url):
    parsed = urlsplit(url)
    host = parsed.hostname
    try:
        loopback = ipaddress.ip_address(host or "").is_loopback
    except ValueError:
        loopback = host == "localhost"
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("AGNES_BASE_URL must not contain credentials, query or fragment")
    if not host or parsed.scheme not in ("http", "https") or (parsed.scheme == "http" and not loopback):
        raise ValueError("AGNES_BASE_URL requires HTTPS except for localhost/loopback development")
    return url.rstrip("/")


def build_editor_messages(task, draft):
    editor = (ROOT / "prompts" / "v1-editor-tested.txt").read_text("utf-8")
    return [{"role": "system", "content": editor},
            {"role": "user", "content": "ЗАДАЧА:\n" + task + "\n\nЧЕРНОВИК:\n" + draft}]


class SecureRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the bearer key to another origin or downgrade HTTPS.
        original, target = urlsplit(req.full_url), urlsplit(newurl)
        if (original.scheme, original.hostname, original.port) != (target.scheme, target.hostname, target.port):
            raise ValueError("Refusing cross-origin API redirect")
        validated_base_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def chat(messages):
    base = validated_base_url(os.environ["AGNES_BASE_URL"])
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps({"model": cfg["model"], "messages": messages}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ[cfg["api_key_env"]]})
    with urllib.request.build_opener(SecureRedirectHandler()).open(req, timeout=120) as r:
        return json.load(r)["choices"][0]["message"]["content"]

if __name__ == "__main__":
    task_id = sys.argv[1]  # e.g. T1_script60
    task = next(t for t in json.loads((ROOT / "tasks.json").read_text("utf-8")) if t["id"] == task_id)["task"]
    draft = ck.extract_final(chat(build_generation_messages(task)))
    final = ck.extract_final(chat(build_editor_messages(task, draft)))
    print(json.dumps(ck.check(final, ck.PRESETS[task_id]), ensure_ascii=False, indent=2))
