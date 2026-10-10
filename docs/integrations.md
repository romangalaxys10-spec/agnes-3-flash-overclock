# Using Agnes Overclock in other tools

Everything below is **untested with Agnes and untested in the listed hosts**. The MCP server has automated tests of its own JSON-RPC flow only (`tests/test_mcp.py`). No model is called by the repo's tools; you supply the model access.

## Parts

| Surface | What | Where |
| --- | --- | --- |
| Skill | `SKILL.md` convention: frontmatter plus prompts and checker | repo root |
| MCP server | stdio, newline-delimited JSON-RPC, stdlib only (no MCP SDK needed) | `python3 agnes_mcp.py` |
| Rules files | Cursor `.mdc`, Windsurf rules | `integrations/cursor/`, `integrations/windsurf/` |
| Claude Code plugin | `.claude-plugin/plugin.json` | repo root |
| Generic API | OpenAI-compatible generate, editor, check script | `integrations/generic/openai_compatible.py` |

## MCP tools

`agnes_check`, `agnes_list_tasks`, `agnes_get_prompt`, `agnes_build_messages`, `agnes_review_messages`. Run `python3 /abs/path/agnes_mcp.py` (works from any directory). Per-host config files and a verification matrix are in `docs/hosts.md`. Works with any host that launches stdio MCP servers (Claude Desktop/Code, Cursor, Windsurf, Cline, Zed and others) but none were tried.

## ACP (Agent Client Protocol)

Full ACP is not provided. ACP connects an editor to a coding **agent**; this repo is a toolkit, not an agent. The practical route is: run an ACP-capable agent in your editor and give that agent this MCP server (most ACP agents accept MCP servers). Write a real ACP adapter only if you want this repo to host its own agent loop.

## Agnes parameters

`agnes.config.json`: model `agnes-3.0-flash`, 512K context (524288 tokens), OpenAI-compatible API, base URL and key read from environment variables `AGNES_BASE_URL` and `AGNES_API_KEY`. No keys in the repo. Check current pricing and rate limits yourself before running.

## Optional adapters

Memory (mem0), token saver (Headroom) and lessons (Self-Learning-Agents) are adapters in `agnes_kit/adapters.py`; install each dependency yourself. See `THIRD_PARTY.md`. Whether memory, lessons or compression improve Agnes output is **untested**; the measured result only covers v1 generate + editor.
