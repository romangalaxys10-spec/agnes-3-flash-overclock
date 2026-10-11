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

- Add the experimental 25-agent QA panel: `qa-panel/` (25-lens set, agent brief, wave orchestration, synthetic examples), `qa_panel.py` plus `agnes_kit/qa_panel.py` (render briefs, validate/consolidate reports, completeness and fix-status gate), `docs/qa-panel.md` and `tests/test_qa_panel.py`. Offline only; untested with live agents or Agnes.

### Detailed QA and feature inventory

- Workflow: restore the benchmark generation body and preserve editor prompt
  bytes; label editor inputs; add byte-equivalence regression coverage.
- Checker: Unicode-letter ratios, Russian/ASCII-English scene heuristics,
  cp1252-console UTF-8 output, RecursionError exit 2, `+` bullets and `>` quotes.
- API: reject non-loopback plaintext HTTP before reading a key or calling the
  network; reject cross-origin/downgrade redirects.
- Storage: flush/fsync temporary writes, atomic replace and failure cleanup;
  reject unknown memory schemas; user-scoped lessons at Jaccard >=0.5 and
  pipeline selection with explicit owner identity.
- MCP: reject both/neither preset/config inputs and missing/wrong JSON-RPC
  version; retain five tools and aligned runtime/plugin 0.1.0 identifiers.
- Hosts: ZCode global/project config split, working repo-root DSH invocation,
  scoped compatibility claims, host-by-host install/check steps and no
  agy-specific config claim. No end-to-end host certification added.
- Documentation: mark historical aggregates unreproducible from absent raw
  outputs/reference/scorer/call ledger; reconcile 36 planned versus 32 scored,
  preserve unknown exclusion identities/reasons, repair prompt fence rendering,
  add English task/prompt glosses, correct generic API-client description.
- Onboarding/dependencies: tracked synthetic checker fixtures and `.gitignore`
  exceptions, accurate test counts, deterministic absent-dependency tests,
  unused-import cleanup, honest minimum-version/pin guidance and explicit
  SelfLearningLessons LLM-call/model-download behavior.
- Anti Helizzinator: work manifest/hash/command-output references; code
  baseline/diff/reproduction/passing-test references; visual screenshot/render
  references and pixel-inspection assertions; explicit not-applicable reasons
  and no task-required opt-out. Payload constraints apply inside the envelope.
- Validation: 71 offline cases, including 27 proof-gate regressions; cold-clone
  checker examples and MCP prompt/accept/reject smoke checks. The checker only
  verifies evidence shape, never executes ledger commands or proves truth.

Historical benchmark numbers and tested editor content remain unchanged. No
raw evidence was invented, no history rewrite, no new release tag, no live
Agnes run, and no optional upstream integration certification.

Release policy: keep plugin/runtime version fields equal. Changes stay
experimental and unreleased until explicitly approved; no benchmark gain or
host certification is implied by a patch release.
