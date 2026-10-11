# 25-agent QA panel (experimental)

A repeatable review method: 25 independent reviewers, each with one distinct lens, in 5 waves of 5, all reading a fresh clone at a frozen commit. Findings are consolidated, triaged, fixed, and verified by the full test suite.

## Provenance and honesty

This method was used on this repository on 2026-10-10/11 (the "25-reviewer QA fixes" in the changelog). That run reported 1 blocker and 11 majors, all fixed. The exact per-agent prompts used then are not archived here; `qa-panel/perspectives.json` is a reconstructed, generalized lens set written for reuse, not a verbatim copy. The tooling in this directory was added afterwards and has been tested only with offline unit tests and synthetic example reports. No claim is made that 25 agents find more bugs than fewer, and no detection-rate numbers are given.

## Files

| Path | Purpose |
| --- | --- |
| `qa-panel/perspectives.json` | 25 lenses across 5 waves |
| `qa-panel/agent-brief.md` | Brief template, one per agent |
| `qa-panel/orchestration.md` | Step by step wave procedure |
| `qa-panel/examples/` | Synthetic reports and a consolidated example; not real findings |
| `qa_panel.py`, `agnes_kit/qa_panel.py` | Offline CLI: `render`, `consolidate`, `gate` |
| `tests/test_qa_panel.py` | Tests for the above |

Phase-by-phase retrieval: `python3 route.py --task qa-panel --phase <freeze|render|run|collect|consolidate|triage|fix|gate>` (see `docs/routing.md`).

## Waves

1. Correctness and backend. 2. Frontend, UX and flow. 3. Security and robustness. 4. Documentation and claims honesty. 5. Tests and cross-cutting, ending with an adversarial skeptic. Lenses that do not apply (for example visual rendering on a CLI-only project) should report "not applicable" with the evidence, or be swapped for a lens that fits.

## Quick use

```bash
python3 qa_panel.py render --base-sha $(git rev-parse HEAD) --repo-url <url> --out /tmp/qa/briefs
# run 25 agents, save reports to /tmp/qa/reports/<agent>.json
python3 qa_panel.py consolidate --reports /tmp/qa/reports --base-sha $(git rev-parse HEAD) --out /tmp/qa/out
# triage statuses in /tmp/qa/out/issues.json, fix, retest
python3 qa_panel.py gate --issues /tmp/qa/out/issues.json
```

## Using it with Anti Helizzinator

Ask each QA agent, and the fixing agent, to return a proof-of-delivery envelope (see `docs/proof-of-delivery.md`) with their report or fix: diff, test log and hashes. The proof gate checks presence and shape only; the panel gate checks bookkeeping only. Neither proves a finding or fix is true.

## Limits

- The repo cannot start agents; independence depends on how you run them.
- Consolidation similarity is a heuristic.
- Not tested with Agnes or any live model. Whether Agnes 3.0 Flash makes a good reviewer is unmeasured.
