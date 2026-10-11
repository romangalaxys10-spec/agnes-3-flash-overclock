# Evidence ledger

## Benchmark, 2026-10-10

Source: `docs/benchmark-report.md`, a public-safe copy of the supplied benchmark pack. Exact generation/editor prompts and six tasks are copied into this skill. Results are reproduced in SKILL.md, not recomputed. No raw run outputs were attached. The published aggregates cannot be regenerated from repository contents: raw outputs, full `ref.py`, the executable original scorer and call ledger are absent. A scorer excerpt is not a reproducibility pack. No missing output or exclusion reason has been invented.

Sample accounting: 36 planned, 35 calls reported complete, 32 samples included (B 11, A 11, AR 10). Four planned samples were excluded: one B, one A and two AR. The report mentions an empty AR answer and an incomplete AR call, but exact sample identities and the relationship to the unfinished call are unrecoverable. B/A exclusion identities and reasons are unrecoverable. See `docs/benchmark-report.md`.

Recovered scorer: word regex, per-task constraints. `check.py` is an adaptation, not an identical reproduction. It removes `exec(ref.py)` and dependence on raw response wrappers; rejects fenced/duplicate-key/non-finite JSON; checks types, keys, scene indices, positive integer durations, metadata sentence count and hashtag form; adds preamble detection and structured exact violations. T5 fixes the original decimal-regex pitfall that could treat the trailing `5` in `2,5` as a new number. Therefore new scores must not be directly substituted into the old aggregate percentages.

Known old-scorer gaps: did not verify scene field types/indices, full Russian narration, title/caption types, metadata sentence count, all fact preservation, new names, spelled-out new numbers or source truth. T6 checked subscription by stem anywhere, not necessarily an ending invitation. New checker improves the ending heuristic but still needs review.

The run's final benchmark report also mentioned an empty AR answer and one incomplete AR call. Denominators excluded empty/incomplete outputs, so percentages are directional, not failure-inclusive reliability. No new Agnes call was made while building this skill.

## Operating observations

- Run report, 2026-10-10: roughly 30-100s per call, some timeout/retry behavior; calls through Muse Bench, user-turn-only; possible harness wrapper.

## Public sources, fetched 2026-10-10

- https://wiki.agnes-ai.com/en/docs/agnes-30-flash : model ID, API compatibility, current $0 input/output/cache, account-dependent limits.
- https://wiki.agnes-ai.com/en/docs/pricing : current $0 for Agnes 3.0 Flash; promotions/account eligibility may change; account bill is actual-charge authority. Flash Max is paid.

No claim that either prompt is optimal, no measured v2 lift, no Opus parity, no guarantee of no fabrication.
