# Smart routing (experimental)

Goal: an agent or LLM should not read the whole skill, QA system and filter set. It declares its task and phase and gets only the pieces that apply.

## How it works

`route/index.json` lists routes. A route is one (task, phase) with a few keywords and a list of items. An item is a whole small file, one markdown section (matched by heading), or a generated piece (an agent's brief rendered for its lens, a one-line-per-lens list). `agnes_kit/router.py` resolves a request to one route and returns just those items plus the names of the task's other phases, so the agent can ask for the next one.

## Use

```bash
python3 route.py --list
python3 route.py --task qa-panel --phase run --agent edge-inputs --base-sha <sha>
python3 route.py --task unslop --phase motion
python3 route.py --query "audit my css for slop"      # keyword match; ambiguous returns candidates, no content
```

MCP clients call the `agnes_route` tool with the same fields; with no arguments it lists tasks and phases. Exit codes for the CLI: 0 content returned, 1 ambiguous/unknown/needs input, 2 error.

## Tasks and phases

- `qa-panel`: freeze, render, run (needs `agent`), collect, consolidate, triage, fix, gate
- `unslop`: direction, audit, polish, motion, verify, persist, provenance
- `proof`: deliver, verify
- `scripts`: generate, edit, check, repair

## Behavior to know

- An explicit task+phase is exact. A free-text query is plain keyword overlap, not a model; a tie or weak match returns candidates and no content, so the caller must pick.
- Each routed item is capped at 6000 bytes; an oversized section is an error, which forces keeping sections small.
- Routing does not enforce anything. An agent can still read the repo directly; the router only makes the short path the easy one.
- Adding a route means editing `route/index.json`; tests check that every route resolves and every heading exists.
- Size claims are measured by `tests/test_router.py` only as "routed output is smaller than the full source files it draws from". No token or quality benefit is measured, and no model was used.
