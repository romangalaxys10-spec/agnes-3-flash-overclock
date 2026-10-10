#!/usr/bin/env python3
"""Minimal stdio MCP server (JSON-RPC 2.0, newline-delimited). Stdlib only.

Tools: agnes_check, agnes_list_tasks, agnes_get_prompt, agnes_build_messages,
agnes_review_messages. It never calls a model and needs no key.
Protocol conformance: written against the MCP spec's initialize / tools/list /
tools/call flow. UNTESTED in real hosts; see docs/integrations.md.

Run:  python3 -m agnes_kit.mcp_server
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from .adapters import ROOT
from .pipeline import build_generation_messages, review_messages

PROTOCOL = "2024-11-05"
_spec = importlib.util.spec_from_file_location("agnes_check", ROOT / "check.py")
_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_check)

PROMPTS = {p.stem: p for p in sorted((ROOT / "prompts").glob("*.txt"))}

def _obj(props, req):
    return {"type": "object", "properties": props, "required": req}

S = {"type": "string"}
TOOLS = [
    {"name": "agnes_check", "description": "Run the offline Agnes checker on a model output. Provide either task (preset id) or config (JSON object).",
     "inputSchema": _obj({"text": S, "task": {"type": "string", "enum": sorted(_check.PRESETS)}, "config": {"type": "object"},
                          "source": S, "extract_final": {"type": "boolean"}}, ["text"])},
    {"name": "agnes_list_tasks", "description": "List the six benchmark tasks (id, task text, check spec).", "inputSchema": _obj({}, [])},
    {"name": "agnes_get_prompt", "description": "Return a prompt template by name (v1 tested, v2 untested).",
     "inputSchema": _obj({"name": {"type": "string", "enum": sorted(PROMPTS)}}, ["name"])},
    {"name": "agnes_build_messages", "description": "Build OpenAI-style messages: tested v1 generation prompt + task (+ optional memories/lessons). Does not call a model.",
     "inputSchema": _obj({"task": S, "memories": {"type": "array", "items": S}, "lessons": {"type": "array", "items": S}}, ["task"])},
    {"name": "agnes_review_messages", "description": "Build code-review messages from a diff using the vendored checklist. UNTESTED on Agnes.",
     "inputSchema": _obj({"diff": S, "language_note": S}, ["diff"])},
]


def call_tool(name: str, a: dict):
    if name == "agnes_check":
        text = a["text"]
        if a.get("extract_final"):
            try:
                text = _check.extract_final(text)
            except ValueError as e:
                return dict(ok=False, violations=[str(e)])
        cfg = _check.PRESETS[a["task"]] if a.get("task") else a.get("config")
        if cfg is None:
            raise ValueError("provide task or config")
        _check.validate_config(cfg)
        source = a.get("source") or (_check.DEFAULT_SOURCE if a.get("task") == "T5_rewrite" else None)
        return _check.check(text, cfg, source)
    if name == "agnes_list_tasks":
        return json.loads((ROOT / "tasks.json").read_text("utf-8"))
    if name == "agnes_get_prompt":
        return PROMPTS[a["name"]].read_text("utf-8")
    if name == "agnes_build_messages":
        return build_generation_messages(a["task"], memories=a.get("memories", ()), lessons=a.get("lessons", ()))
    if name == "agnes_review_messages":
        return review_messages(a["diff"], language_note=a.get("language_note", ""))
    raise KeyError(name)


def handle(req: dict):
    """Return a response dict, or None for notifications."""
    if not isinstance(req, dict):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "invalid request (batches are not supported)"}}
    rid, method = req.get("id"), req.get("method", "")
    if rid is None:
        return None
    def ok(result): return {"jsonrpc": "2.0", "id": rid, "result": result}
    def err(code, msg): return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": msg}}
    if method == "initialize":
        return ok({"protocolVersion": PROTOCOL, "capabilities": {"tools": {}},
                   "serverInfo": {"name": "agnes-overclock", "version": "0.1.0"}})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        p = req.get("params", {})
        try:
            out = call_tool(p.get("name", ""), p.get("arguments") or {})
            text = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2)
            return ok({"content": [{"type": "text", "text": text}], "isError": False})
        except KeyError as e:
            return err(-32602, f"unknown tool or argument: {e}")
        except Exception as e:  # tool errors are reported to the model, not fatal
            return ok({"content": [{"type": "text", "text": str(e)}], "isError": True})
    return err(-32601, f"method not found: {method}")


def main() -> int:
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            resp = handle(json.loads(line))
        except json.JSONDecodeError:
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
