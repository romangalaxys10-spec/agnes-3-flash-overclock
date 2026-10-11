# Local verification, 2026-10-10

- 14 unittest cases passed: word bands, valid Russian prose, wrappers/preambles, decimal literals, missing/new numbers, Unicode digits, strict JSON, scene sums/lengths/types, metadata, paragraphs, final extraction, malformed configs, subscription ending.
- Adversarial JSON shapes (null, scalar, wrong collections/types) return violations without crashing.
- CLI exercised: valid = exit 0; invalid payload = exit 1 with exact violations; invalid config = exit 2 with error JSON on stderr.
- Correction on 2026-10-11, local QA branch `fix/25qa-panel`: the generation prompt at frozen commit `b549e8a8` was truncated (1523 bytes); the earlier byte-equivalence claim was incorrect. Restored the full documented generation body (1542 bytes including one trailing newline) from `docs/benchmark-report.md`, with the literal triple-backticks sentence and `ЗАДАЧА:` intact. A byte-equality regression checks the restored prompt against that report. The editor prompt was not changed.
- No model generation or new quality experiment was run. v2 remains untested against Agnes.

## Adversarial review

Strongest objection: structural compliance can hide fabricated prose and false numeric associations. Addressed by separating code pass from manual factual/voice review and rejecting use for unsupervised factual accuracy. Preamble detection and sentence splitting are explicit heuristics. Digit sets do not catch names, spelled-out numbers, number occurrence counts or association changes. A literal rewritten as words is conservatively flagged missing, not silently accepted.

A null JSON payload initially escaped the mode-specific checks because null shared the parse-failure sentinel. The regression found it; parser-success is now tracked separately and null is rejected for scene/metadata modes. Other malformed payload shapes were checked after the fix.


## 2026-10-11 QA verification

- 44 offline unittest cases pass (22 original plus 22 QA regressions).
- Regression coverage includes UTF-8 reports under a cp1252 environment; all-Unicode
  letter denominators; Russian/English scene gates; atomic write/replace failures;
  schema drift; owner-scoped lesson selection; HTTPS and redirect safety; MCP
  exclusivity/version checks; deep JSON exit 2; restored prompt byte equivalence.
- Synthetic quickstart fixtures pass all four advertised checker commands.
- Plugin manifest and MCP initialize both remain experimental version 0.1.0.
- No real host, optional upstream dependency or Agnes endpoint was exercised.


## Proof protocol verification, 2026-10-11

71 offline tests pass, including 27 proof-gate regressions. Coverage rejects
missing proof, malformed fields/hashes, dangling/duplicate artifact or command
references, unmanifested touched files, failed tests, missing code/visual proof,
opt-out bypasses and missing pixel-inspection assertions. Tests also show that
a well-formed but false hash passes: the checker does not verify truth. Shipped
work-only sample hashes were independently recomputed in a unit test. No real
visual delivery or live Agnes generation was run for this feature.
