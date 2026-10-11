# Using Agnes Overclock in other tools

Everything below is **untested with Agnes and untested in the listed hosts**. The MCP server has automated tests of its own JSON-RPC flow only (`tests/test_mcp.py`). The offline checker, message builders and MCP server do not call a model. The opt-in generic API example does call the model; you supply model access.

## Parts

| Surface | What | Where |
| --- | --- | --- |
| Skill | `SKILL.md` convention: frontmatter plus prompts and checker | repo root |
| MCP server | stdio, newline-delimited JSON-RPC, stdlib only (no MCP SDK needed) | `python3 agnes_mcp.py` |
| Rules files | Cursor `.mdc`, Windsurf rules | `integrations/cursor/`, `integrations/windsurf/` |
| Claude Code plugin | `.claude-plugin/plugin.json` | repo root |
| Generic API | OpenAI-compatible generate, editor, check script | `integrations/generic/openai_compatible.py` |

## MCP tools

`agnes_check`, `agnes_list_tasks`, `agnes_get_prompt`, `agnes_build_messages`, `agnes_review_messages`. Run `python3 /abs/path/agnes_mcp.py` (works from any directory). Per-host config files and a verification matrix are in `docs/hosts.md`. Designed for hosts that support stdio MCP and this server's protocol subset. Host compatibility and protocol negotiation are untested; this is not a claim of support for every MCP host.

## ACP (Agent Client Protocol)

Full ACP is not provided. ACP connects an editor to a coding **agent**; this repo is a toolkit, not an agent. The practical route is: run an ACP-capable agent in your editor and give that agent this MCP server (most ACP agents accept MCP servers). Write a real ACP adapter only if you want this repo to host its own agent loop.

## Agnes parameters

`agnes.config.json`: model `agnes-3.0-flash`, 512K context (524288 tokens), OpenAI-compatible API, base URL and key read from environment variables `AGNES_BASE_URL` and `AGNES_API_KEY`. No keys in the repo. Check current pricing and rate limits yourself before running.

## Optional adapters

Memory (mem0), token saver (Headroom) and lessons (Self-Learning-Agents) are adapters in `agnes_kit/adapters.py`; install each dependency yourself. See `THIRD_PARTY.md`. Whether memory, lessons or compression improve Agnes output is **untested**; the measured result only covers v1 generate + editor.


### Scoped offline lessons and memory

`FileLessons.save(task, feedback, user_id="default")` and
`relevant(task, user_id="default", min_relevance=0.5)` use exact owner matching
and a Jaccard word-overlap threshold of 0.5 by default. Specify a distinct stable
`user_id` per user in a shared store; old default-user records stay in the
`default` scope and are not assigned to named users automatically. Overlap is a
heuristic, not semantic relevance. `FileMemory` refuses unknown schemas and
uses same-directory temporary files plus atomic replace; it is not a
concurrent multi-writer database. Use separate stores or external locking for
concurrent writes.

For automatic filtering, call
`build_generation_messages(task, lesson_store=store, user_id="alice")`.
Explicit `lessons=[...]` and MCP `lessons` arrays are caller-selected data;
callers own their scope and relevance. They cannot be combined with
`lesson_store`. These additions were not benchmarked.

`SelfLearningLessons` is NOT offline: upstream's feedback selection makes an
OpenAI-compatible LLM call and its default embedder downloads a model. Configure
network access, credentials, cost and isolation before constructing it. The
external wrapper does not implement `FileLessons` user filtering; use an
isolated configured learner per user, not a shared instance.

The generic API example requires HTTPS for remote endpoints (HTTP only for
localhost/loopback) and refuses cross-origin redirects to protect the bearer
key. It has not been run against Agnes.
