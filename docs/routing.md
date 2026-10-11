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

MCP clients call the `agnes_route` tool with the same fields; with no arguments it lists tasks and phases. Exit codes for the CLI: 0 content returned, 1 ambiguous/unknown/needs input, 2 a remote slice was unavailable (or any other runtime error).

## Tasks and phases

- `qa-panel`: freeze, render, run (needs `agent`), collect, consolidate, triage, fix, gate
- `unslop`: direction, audit, polish, motion, verify, persist, provenance
- `proof`: deliver, verify
- `scripts`: generate, edit, check, repair
- `jg-prompts` (remote): select, fill, verify
- `jg-mcp` (remote): discover, evaluate, install, secure
- `jg-extensions` (remote): latest, lookup, verify

## Behavior to know

- An explicit task+phase is exact. A free-text query is plain keyword overlap, not a model; a tie or weak match returns candidates and no content, so the caller must pick.
- Each routed item is capped at 6000 bytes; an oversized section is an error, which forces keeping sections small.
- Routing does not enforce anything. An agent can still read the repo directly; the router only makes the short path the easy one.
- Adding a route means editing `route/index.json`; tests check that every route resolves and every heading exists.
- Size claims are measured by `tests/test_router.py` only as "routed output is smaller than the full source files it draws from". No token or quality benefit is measured, and no model was used.

## Remote routes: the Jack Gross router

The `jg-*` tasks route out of this repo to the public Jack Gross router at
`https://jackgross-five.vercel.app/router.md` (start file; machine map at `/router/index.json`).
That site serves one small static markdown slice per collection and phase - prompt selection
(`jg-prompts`), MCP server discovery/evaluation/install/security (`jg-mcp`, site index of about
43K servers), and recent extension news (`jg-extensions`). One call fetches one phase-guidance
slice; following the guidance inside a slice may fetch further index or shard data from the
same site - that is the slice's content, not extra slices pulled by the router.

How it works (`agnes_kit/jg_router.py`):

- Plain GET, stdlib only, no keys, and no user data is sent - only the fixed slice URL. The origin is fixed to the site's scheme+host and redirects are never followed, so a slice cannot be bounced off-origin or downgraded to plaintext. One absolute monotonic deadline (default 10s) covers connect plus the whole body read, so a slow-drip server cannot hold the call.
- A reply is accepted only if it is complete (truncated bodies error out), decodes as UTF-8, is at most 5500 bytes (leaving headroom for the trust wrapper under the 6000-byte routed-item cap), and looks like a markdown slice (nonempty, not HTML, has a heading). Junk is never cached: it falls back to the cache or reports unavailable.
- Replies are cached on disk for 24h (`~/.cache/agnes-overclock/jg-router/`, override with `AGNES_JG_CACHE`). Cache files are `<collection>--<phase>.md`, UTF-8, freshness by file mtime; a corrupt (undecodable) cache file is a cache miss, never a crash. Writes go to a uniquely named `O_EXCL` temp file (`O_NOFOLLOW` where available) renamed over the target. `--refresh` (CLI) re-fetches; `--offline` (CLI) / `offline=true` (CLI or MCP) serves the cache only.
- If the network fails and a cached copy exists, the cache is served and the source is marked `[cache]`. If there is no cache, the route returns `status: unavailable` (CLI exit code 2) with the direct URL and no content - nothing is invented. Over MCP an unavailable remote slice is a tool error (`isError: true`) with the same actionable message, never a fake success.
- The MCP server never blocks on the network: remote slices are served from the cache and a missing/stale cache starts a daemon-thread background refresh instead, so the first call for a cold slice returns a retry hint while ping and the local tools stay responsive.
- Usage permission: the site's owner is adding an explicit machine-use permission note to `router.md`; once live, that note governs automated fetching of these slices. This repo adds no license text of its own for the remote content.

Trust boundary for fetched text:

- Every remote slice is wrapped in an explicit `[UNTRUSTED EXTERNAL TEXT ...]` / `[END UNTRUSTED EXTERNAL TEXT]` marker in routed output.
- The boundary: remote text may suggest research steps within the user's current authorized task (which index shard to read, which checks to run). It cannot add goals, authorize actions, spend, message anyone, or override trusted instructions - the same rule this repo applies to source and draft text.

Honest limits:

- External dependency. The site is outside this repo's control; its counts, files and URLs can change or vanish at any time. The static map in `jg_router.py` was verified live on 2026-10-11.
- The site's own MCP category assignment is keyword-based (its docs say about 40% of servers land in "other"), and its index stores no licenses; the remote slices say so themselves.
- The test suite stubs the network; only the opt-in `AGNES_LIVE_TEST=1` smoke test touches the real site.

## Adding a remote collection or phase

1. Confirm the new slice URLs live on the site (each must return 200, markdown, under the byte cap).
2. Add the collection/phases to `COLLECTIONS` in `agnes_kit/jg_router.py` (path per phase).
3. Add routes of item shape `{"type": "remote", "collection": "<name>", "phase": "<phase>"}` to `route/index.json` under a `jg-*` task, with specific multi-word keywords - remote routes get no partial keyword credit, so single generic words will never match them.
4. Run the suite. `route.py --list` shows the remote collections automatically.
