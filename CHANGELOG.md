# Changelog

## 0.1.1 - 2026-10-11 QA changes (unreleased)

Experimental maintenance patch. Public plugin and MCP runtime identifiers stay
aligned at 0.1.0 until a separately approved release updates both. Prompt v1/v2
names describe evidence tiers, not software release versions. This is not v1.0.

- Restore the benchmark-documented v1 generation prompt; label editor inputs.
- Require HTTPS for remote API endpoints and reject cross-origin redirects.
- Fix Unicode letter ratios, scene language heuristics, Markdown detection,
  UTF-8 console output and deeply nested JSON CLI errors.
- Make file memory writes atomic and fail closed on unknown schemas.
- Add owner-scoped lesson selection with a minimum overlap threshold.
- Validate MCP task/config exclusivity and JSON-RPC 2.0 version.
- Add the ZCode project config, host setup checks, sample inputs, regression
  tests, honest benchmark accounting and optional-dependency caveats.

- Add opt-in Anti Helizzinator proof-of-delivery prompt and structural gate:
  work manifest/hashes/command logs, code diff/test records, visual inspection
  assertions, CLI/MCP examples and rejection regressions. Presence is not truth.

Release policy: keep plugin/runtime version fields equal. Changes stay
experimental and unreleased until explicitly approved; no benchmark gain or
host certification is implied by a patch release.
