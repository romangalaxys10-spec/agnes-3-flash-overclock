"""Task/phase router (experimental). Returns only the repo pieces relevant to one task phase.

Offline, deterministic, stdlib only. Query matching is plain keyword overlap, not a model; when the
match is not clear the router returns candidates and no content so the caller must choose.
"""
import json
import re
from pathlib import Path

from . import qa_panel

ROOT = Path(__file__).resolve().parents[1]
MAX_ITEM_BYTES = 6000


def load_index(path=None):
    p = Path(path) if path else ROOT / "route" / "index.json"
    idx = json.loads(p.read_text(encoding="utf-8"))
    ids = [r["id"] for r in idx["routes"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate route ids")
    return idx


def list_routes(idx=None):
    idx = idx or load_index()
    out = {}
    for r in idx["routes"]:
        out.setdefault(r["task"], []).append(r["phase"])
    return out


def _safe(rel):
    p = (ROOT / rel).resolve()
    if ROOT not in p.parents and p != ROOT:
        raise ValueError(f"path escapes repo: {rel}")
    return p


def extract_section(text, heading):
    """Markdown section body from `## heading` to the next heading of same or higher level."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        m = re.match(r"^(#+)\s+(.*?)\s*$", ln)
        if m and m.group(2).lower() == heading.lower():
            lvl, out = len(m.group(1)), [ln]
            for nxt in lines[i + 1:]:
                m2 = re.match(r"^(#+)\s", nxt)
                if m2 and len(m2.group(1)) <= lvl:
                    break
                out.append(nxt)
            return "\n".join(out).strip() + "\n"
    raise KeyError(f"heading not found: {heading}")


def _item(it, args):
    t = it["type"]
    if t == "file":
        return it["path"], _safe(it["path"]).read_text(encoding="utf-8")
    if t == "section":
        return f"{it['path']}#{it['heading']}", extract_section(_safe(it["path"]).read_text(encoding="utf-8"), it["heading"])
    persp = qa_panel.load_perspectives(with_optional=True)
    if t == "wave-list":
        lines = [f"{p['number']:>2}. wave {p['wave']} {p['id']}: {p['name']}" for p in persp]
        return "qa-panel/perspectives.json (ids only)", "\n".join(lines) + "\n"
    if t == "agent-brief":
        agent = args.get("agent")
        known = {p["id"] for p in persp}
        if agent not in known:
            raise ValueError(f"agent must be one of the 25 lens ids; got {agent!r}")
        sha = args.get("base_sha") or "<FROZEN_SHA>"
        tpl = (ROOT / "qa-panel" / "agent-brief.md").read_text(encoding="utf-8")
        p = next(x for x in persp if x["id"] == agent)
        txt = (tpl.replace("{{agent_id}}", p["id"]).replace("{{number}}", str(p["number"])).replace("{{wave}}", str(p["wave"]))
               .replace("{{wave_name}}", p["wave_name"]).replace("{{name}}", p["name"]).replace("{{focus}}", p["focus"])
               .replace("{{total}}", str(len(persp))).replace("{{base_sha}}", sha).replace("{{repo_url}}", args.get("repo_url") or "<repo-url>"))
        return f"qa-panel/agent-brief.md rendered for {agent}", txt
    raise ValueError(f"unknown item type {t}")


def _score(route, query):
    words = set(re.findall(r"[a-z0-9_]+", query.lower()))
    s = 0
    for k in route.get("keywords", []):
        kw = set(re.findall(r"[a-z0-9_]+", k.lower()))
        if kw and kw <= words:
            s += 2 * len(kw)
        elif kw & words:
            s += len(kw & words)
    s += 1 if route["task"] in words else 0
    s += 1 if route["phase"] in words else 0
    return s


def route(task=None, phase=None, query=None, agent=None, base_sha=None, repo_url=None, idx=None):
    """Resolve to one route and return only its items. Exact task+phase wins; otherwise a query is
    scored. A tie or a weak match returns candidates and no content."""
    idx = idx or load_index()
    routes = idx["routes"]
    if task and phase:
        hit = [r for r in routes if r["task"] == task and r["phase"] == phase]
        if not hit:
            return {"status": "unknown", "message": f"no route for task={task!r} phase={phase!r}", "available": list_routes(idx)}
        chosen = hit[0]
    elif query:
        pool = [r for r in routes if not task or r["task"] == task]
        scored = sorted(((_score(r, query), r) for r in pool), key=lambda x: (-x[0], x[1]["id"]))
        top = [(s, r) for s, r in scored if s > 0][:3]
        if not top or (len(top) > 1 and top[0][0] == top[1][0]) or top[0][0] < 2:
            return {"status": "ambiguous", "message": "no clear match; pass task and phase explicitly",
                    "candidates": [r["id"] for _, r in top] or [], "available": list_routes(idx)}
        chosen = top[0][1]
    else:
        return {"status": "need-input", "message": "give task+phase, or a query", "available": list_routes(idx)}
    args = {"agent": agent, "base_sha": base_sha, "repo_url": repo_url}
    missing = [n for n in chosen.get("needs", []) if not args.get(n)]
    if missing:
        return {"status": "need-input", "route": chosen["id"], "message": f"missing required: {', '.join(missing)}"}
    items, total = [], 0
    for it in chosen["items"]:
        name, text = _item(it, args)
        if len(text.encode()) > MAX_ITEM_BYTES:
            raise ValueError(f"routed item too large ({name}); split the source section")
        items.append({"source": name, "content": text})
        total += len(text.encode())
    siblings = [r["phase"] for r in routes if r["task"] == chosen["task"] and r["id"] != chosen["id"]]
    return {"status": "ok", "route": chosen["id"], "task": chosen["task"], "phase": chosen["phase"],
            "items": items, "bytes": total, "other_phases_of_task": siblings}


def corpus_bytes():
    """Size of all files the index can point at, for honest size comparison."""
    paths = set()
    for r in load_index()["routes"]:
        for it in r["items"]:
            if "path" in it:
                paths.add(it["path"])
    paths |= {"qa-panel/perspectives.json", "qa-panel/agent-brief.md"}
    return sum(_safe(p).stat().st_size for p in paths)
