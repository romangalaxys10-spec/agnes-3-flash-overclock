#!/usr/bin/env python3
"""CLI: get only the repo guidance for one task phase. See docs/routing.md.
Examples: route.py --list | route.py --task qa-panel --phase run --agent edge-inputs --base-sha abc1234 | route.py --query "audit my css for slop"
"""
import argparse, json, sys
from agnes_kit import router as r


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true"); ap.add_argument("--task"); ap.add_argument("--phase")
    ap.add_argument("--query"); ap.add_argument("--agent"); ap.add_argument("--base-sha"); ap.add_argument("--repo-url")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.list:
            print(json.dumps(r.list_routes(), indent=2)); return 0
        res = r.route(a.task, a.phase, a.query, a.agent, a.base_sha, a.repo_url)
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr); return 2
    if a.json or res["status"] != "ok":
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"# route {res['route']} ({res['bytes']} bytes). Other phases: {', '.join(res['other_phases_of_task'])}\n")
        for it in res["items"]:
            print(f"--- {it['source']}\n{it['content']}")
    return 0 if res["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
