# Host support matrix

Checked against vendor docs on 2026-10-10. "Verified format" means the config shape matches the host's published docs. **No host was run end to end with this server, and nothing was run against Agnes.** There is no official marketplace listing for any host; "official plugin support" here means the host's documented extension route.

All hosts launch the same stdio MCP server: `python3 /ABSOLUTE/PATH/agnes_mcp.py` (stdlib only). Replace the placeholder path with your clone. Config files never expand `~` or templates in some hosts; use absolute paths.

| Host | Route | File and location | Format source | Status |
| --- | --- | --- | --- | --- |
| Claude Code | Plugin: `.claude-plugin/plugin.json` with `skills` and inline `mcpServers` | repo root; load with `--plugin-dir` or from a marketplace you host | https://code.claude.com/docs/en/plugins/manifest-reference | Manifest fields verified. `${CLAUDE_PLUGIN_ROOT}` in `args` not re-checked in Claude docs. |
| Cursor | MCP via `mcp.json` | `.cursor/mcp.json` (project) or `~/.cursor/mcp.json`; copy `integrations/cursor/mcp.json` | https://cursor.com/docs/mcp.md | MCP format verified. Rules file `integrations/cursor/agnes-overclock.mdc` follows the commonly used `.cursor/rules/*.mdc` layout, not re-verified here. |
| Codex CLI | MCP via TOML | `~/.codex/config.toml`, table `[mcp_servers.<name>]` with `command`, `args` | https://developers.openai.com/codex/config-reference | Verified keys. Codex reads `AGENTS.md`; `AGENTS.md` here is a pointer to `SKILL.md`. |
| Antigravity IDE and `agy` CLI | MCP via `mcp_config.json` | global `~/.gemini/config/mcp_config.json`, workspace `.agents/mcp_config.json` | https://antigravity.google/docs/mcp/ | Verified. `agy` is the Antigravity CLI binary (https://github.com/google-antigravity/antigravity-cli). |
| ZCode | MCP via `~/.zcode/cli/config.json` key `mcp.servers`, or `.agents/mcp.json` with top-level `mcpServers` | `integrations/zcode/config.json` | https://zcode.z.ai/en/docs/mcp-services | Verified. A scope's `.zcode` servers shadow its `.agents/mcp.json`; use one. ZCode also accepts pasted JSON in Settings, MCP Servers. It opens project MCP entries automatically, so review repos before opening. |
| Trae | MCP via Settings, MCP, manual add (JSON `mcpServers`) | `integrations/trae/mcp-servers.json` | https://docs.trae.ai/solo/remote-mcp-server | Verified for stdio JSON shape. Trae supports `${workspaceFolder}` in values. |
| DeepSeek TUI (CodeWhale) | MCP via `~/.codewhale/mcp.json` (`~/.deepseek/mcp.json` is still read if absent); `servers` or `mcpServers` key | `integrations/deepseek/mcp.json` | https://github.com/Hmbown/DeepSeek-TUI (docs/MCP.md) | Verified shape for this community project. "DeepSeek harness" is ambiguous: DeepSeek itself ships an API and models, not an official IDE plugin. Confirm this is the tool you meant. |
| Windsurf | MCP via `mcp_config.json` | `~/.codeium/windsurf/mcp_config.json` | https://docs.devin.ai/windsurf/plugins/cascade/mcp | Path from docs and third-party notes; confirm in Settings, Cascade, MCP Servers. |
| Any other MCP host | stdio server | `python3 agnes_mcp.py` | MCP spec | Generic. |
| ACP editors (Zed etc.) | Not a plugin | give your ACP agent the MCP server | | No ACP adapter; this is a toolkit, not an agent. |

## Not provided

No VS Code extension, JetBrains plugin or marketplace package was built: that needs a published extension, publisher account and review, none of which exist here. Use the MCP route above.
