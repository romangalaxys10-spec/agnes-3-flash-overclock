#!/usr/bin/env python3
"""CLI for the offline 25-agent QA panel helpers. See docs/qa-panel.md."""
import argparse, json, sys
from pathlib import Path
from agnes_kit import qa_panel as q


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="write one brief per agent")
    r.add_argument("--base-sha", required=True); r.add_argument("--repo-url", default="<repo-url>")
    r.add_argument("--out", required=True); r.add_argument("--perspectives")
    c = sub.add_parser("consolidate", help="validate reports and merge findings")
    c.add_argument("--reports", required=True, help="directory of per-agent JSON reports")
    c.add_argument("--base-sha", required=True); c.add_argument("--out", required=True)
    c.add_argument("--perspectives")
    g = sub.add_parser("gate", help="check a consolidated issues file")
    g.add_argument("--issues", required=True); g.add_argument("--allow-partial", action="store_true")
    g.add_argument("--perspectives")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "gate":
            persp = q.load_perspectives(a.perspectives)
            doc = json.loads(Path(a.issues).read_text(encoding="utf-8"))
            res = q.gate(doc["issues"], doc["coverage"], not a.allow_partial)
            print(json.dumps(res, indent=2)); return 0 if res["passed"] else 1
        persp = q.load_perspectives(a.perspectives)
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        if a.cmd == "render":
            for k, v in q.render_briefs(persp, a.base_sha, a.repo_url).items():
                (out / f"{k}.md").write_text(v, encoding="utf-8")
            print(f"wrote {len(persp)} briefs to {out}"); return 0
        reports, bad = [], {}
        for f in sorted(Path(a.reports).glob("*.json")):
            rep = json.loads(f.read_text(encoding="utf-8"))
            e = q.validate_report(rep, persp, a.base_sha)
            (bad.__setitem__(f.name, e) if e else reports.append(rep))
        if bad:
            print(json.dumps({"invalid_reports": bad}, indent=2), file=sys.stderr); return 2
        issues = q.consolidate(reports); cov = q.coverage(reports, persp)
        (out / "issues.json").write_text(json.dumps({"base_sha": a.base_sha, "coverage": cov, "issues": issues}, indent=2), encoding="utf-8")
        (out / "report.md").write_text(q.render_markdown(issues, cov, a.base_sha), encoding="utf-8")
        print(f"{len(issues)} consolidated issues; {cov['reported']}/{cov['expected']} agents reported"); return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr); return 2


if __name__ == "__main__":
    sys.exit(main())
