#!/usr/bin/env python3
"""CLI: scan CSS/HTML/JSX for AI-slop tells. See docs/unslop.md. Exit 0 none at/above --fail-on, 1 found, 2 error."""
import argparse, json, sys
from agnes_kit import unslop as u


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", choices=u.SEV, default="high", help="lowest severity that fails the run (default high)")
    a = ap.parse_args(argv)
    try:
        res, n = u.check_path(a.path)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr); return 2
    if n == 0:
        print("error: no scannable files", file=sys.stderr); return 2
    lim = u.SEV.index(a.fail_on)
    bad = [r for r in res if u.SEV.index(r["severity"]) <= lim]
    if a.json:
        print(json.dumps({"files_scanned": n, "findings": res, "failing": len(bad)}, indent=2, ensure_ascii=False))
    else:
        for r in res:
            print(f"{r['file']}:{r['line']} [{r['severity']}] {r['rule']}: {r['message']}")
        print(f"{n} files scanned, {len(res)} findings, {len(bad)} at or above {a.fail_on}. Static text check only; manual review still required (docs/unslop.md).")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
