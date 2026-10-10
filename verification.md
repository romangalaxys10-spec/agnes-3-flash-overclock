# Local verification, 2026-10-10

- 14 unittest cases passed: word bands, valid Russian prose, wrappers/preambles, decimal literals, missing/new numbers, Unicode digits, strict JSON, scene sums/lengths/types, metadata, paragraphs, final extraction, malformed configs, subscription ending.
- Adversarial JSON shapes (null, scalar, wrong collections/types) return violations without crashing.
- CLI exercised: valid = exit 0; invalid payload = exit 1 with exact violations; invalid config = exit 2 with error JSON on stderr.
- Both v1 Russian prompt files compared byte-for-byte with the supplied benchmark pack's fenced prompt bodies (one trailing newline added).
- No model generation or new quality experiment was run. v2 remains untested against Agnes.

## Adversarial review

Strongest objection: structural compliance can hide fabricated prose and false numeric associations. Addressed by separating code pass from manual factual/voice review and rejecting use for unsupervised factual accuracy. Preamble detection and sentence splitting are explicit heuristics. Digit sets do not catch names, spelled-out numbers, number occurrence counts or association changes. A literal rewritten as words is conservatively flagged missing, not silently accepted.

A null JSON payload initially escaped the mode-specific checks because null shared the parse-failure sentinel. The regression found it; parser-success is now tracked separately and null is rejected for scene/metadata modes. Other malformed payload shapes were checked after the fix.
