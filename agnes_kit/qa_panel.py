"""Offline 25-agent QA panel helpers: render agent briefs, validate and consolidate findings, gate.

Stdlib only. Never calls a model or the network. It checks the shape and bookkeeping of a
panel run; it cannot judge whether a finding is true or whether the reviewers were independent.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEVERITIES = ("blocker", "major", "minor", "nit")
STATUSES = ("open", "fixed", "wontfix", "invalid")
REQUIRED = ("title", "severity", "file", "evidence")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def load_perspectives(path=None, with_optional=False):
    p = Path(path) if path else ROOT / "qa-panel" / "perspectives.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    items = list(data["perspectives"])
    if with_optional:
        items += json.loads((ROOT / "qa-panel" / "optional-lenses.json").read_text(encoding="utf-8"))["perspectives"]
    ids = [x["id"] for x in items]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate perspective ids")
    return items


def render_briefs(perspectives, base_sha, repo_url="<repo-url>", template=None):
    """Return {agent_id: brief_text}. base_sha freezes the review target."""
    if not SHA_RE.match(base_sha or ""):
        raise ValueError("base_sha must be a hex git revision (7-40 chars)")
    tpl = template or (ROOT / "qa-panel" / "agent-brief.md").read_text(encoding="utf-8")
    out = {}
    for p in perspectives:
        out[p["id"]] = (tpl.replace("{{agent_id}}", p["id"]).replace("{{number}}", str(p["number"]))
                        .replace("{{wave}}", str(p["wave"])).replace("{{wave_name}}", p["wave_name"])
                        .replace("{{name}}", p["name"]).replace("{{focus}}", p["focus"])
                        .replace("{{base_sha}}", base_sha).replace("{{repo_url}}", repo_url))
    return out


def validate_report(report, perspectives=None, base_sha=None):
    """Return a list of problems for one agent report."""
    errs = []
    if not isinstance(report, dict):
        return ["report must be an object"]
    agent = report.get("agent")
    known = {p["id"] for p in perspectives} if perspectives else None
    if not isinstance(agent, str) or not agent:
        errs.append("missing agent")
    elif known is not None and agent not in known:
        errs.append(f"unknown agent {agent!r}")
    sha = report.get("base_sha")
    if not isinstance(sha, str) or not SHA_RE.match(sha):
        errs.append("missing or malformed base_sha")
    elif base_sha and not (base_sha.startswith(sha) or sha.startswith(base_sha)):
        errs.append(f"base_sha {sha} does not match frozen {base_sha}")
    if not isinstance(report.get("reviewed_clean_clone"), bool):
        errs.append("reviewed_clean_clone must be boolean")
    f = report.get("findings")
    if not isinstance(f, list):
        errs.append("findings must be a list (empty means none found)")
        return errs
    for i, x in enumerate(f):
        if not isinstance(x, dict):
            errs.append(f"findings[{i}] not an object"); continue
        for k in REQUIRED:
            if not isinstance(x.get(k), str) or not x[k].strip():
                errs.append(f"findings[{i}] missing {k}")
        if x.get("severity") not in SEVERITIES:
            errs.append(f"findings[{i}] severity must be one of {SEVERITIES}")
        if "line" in x and not isinstance(x["line"], int):
            errs.append(f"findings[{i}] line must be integer")
    return errs


def _key(x):
    t = re.sub(r"[^a-z0-9 ]+", " ", x["title"].lower())
    t = " ".join(sorted(set(t.split())))
    return (x["file"].strip().lower(), t)


def _jaccard(a, b):
    a, b = set(a.split()), set(b.split())
    return len(a & b) / len(a | b) if a | b else 0.0


def consolidate(reports, threshold=0.6):
    """Merge findings from many reports. Same file plus similar title words = one issue.
    Severity is the highest reported; every reporting agent is kept. Similarity is a
    heuristic; a human or lead agent must confirm merges."""
    issues = []
    for r in reports:
        for x in r["findings"]:
            file_, words = _key(x)
            for it in issues:
                if it["file"] == file_ and _jaccard(it["_words"], words) >= threshold:
                    break
            else:
                it = {"file": file_, "_words": words, "title": x["title"], "severity": x["severity"],
                      "agents": [], "evidence": [], "status": "open"}
                issues.append(it)
            if SEVERITIES.index(x["severity"]) < SEVERITIES.index(it["severity"]):
                it["severity"] = x["severity"]
            if r["agent"] not in it["agents"]:
                it["agents"].append(r["agent"])
            it["evidence"].append({"agent": r["agent"], "text": x["evidence"]})
    issues.sort(key=lambda i: (SEVERITIES.index(i["severity"]), i["file"], i["title"]))
    for n, it in enumerate(issues, 1):
        it["id"] = f"QA-{n:03d}"
        del it["_words"]
    return issues


def coverage(reports, perspectives):
    have = {r["agent"] for r in reports}
    want = [p["id"] for p in perspectives]
    return {"expected": len(want), "reported": len(have & set(want)),
            "missing": [a for a in want if a not in have]}


def gate(issues, cov, require_full_panel=True):
    """Pass only when the panel is complete and no blocker/major is still open.
    Every non-open issue needs a resolution note: fix_commit + verification for fixed, reason otherwise."""
    problems = []
    if require_full_panel and cov["missing"]:
        problems.append(f"panel incomplete: missing {', '.join(cov['missing'])}")
    for it in issues:
        st = it.get("status", "open")
        if st not in STATUSES:
            problems.append(f"{it['id']}: bad status {st!r}"); continue
        if st == "open" and it["severity"] in ("blocker", "major"):
            problems.append(f"{it['id']}: open {it['severity']}: {it['title']}")
        if st == "fixed" and not (it.get("fix_commit") and it.get("verification")):
            problems.append(f"{it['id']}: fixed needs fix_commit and verification")
        if st in ("wontfix", "invalid") and not it.get("reason"):
            problems.append(f"{it['id']}: {st} needs a reason")
    return {"passed": not problems, "problems": problems}


def render_markdown(issues, cov, base_sha):
    lines = [f"# QA panel report", "", f"Frozen target: `{base_sha}`",
             f"Agents reported: {cov['reported']}/{cov['expected']}" +
             (f" (missing: {', '.join(cov['missing'])})" if cov["missing"] else ""), ""]
    counts = {s: sum(1 for i in issues if i["severity"] == s) for s in SEVERITIES}
    lines.append("Consolidated issues: " + ", ".join(f"{v} {k}" for k, v in counts.items()) + ".")
    lines.append("")
    for i in issues:
        lines += [f"## {i['id']} [{i['severity']}] {i['title']}", f"- File: `{i['file']}`",
                  f"- Status: {i.get('status','open')}", f"- Reported by: {', '.join(i['agents'])}"]
        if i.get("fix_commit"):
            lines.append(f"- Fix: `{i['fix_commit']}`; verified by: {i.get('verification','')}")
        lines.append("")
    return "\n".join(lines)
