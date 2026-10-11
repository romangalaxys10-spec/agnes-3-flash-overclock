# 25-agent QA panel (experimental)

A repeatable review method: 25 independent reviewers, each with one distinct lens, in 5 waves of 5, all reading a fresh clone at a frozen commit. Findings are consolidated, triaged, fixed, and verified by the full test suite.

## Provenance and honesty

This method was used on this repository on 2026-10-10/11 (the "25-reviewer QA fixes" in the changelog). The run's lead agent consolidated the 25 reports into 1 blocker (benchmark results not reproducible from the repo, fixed by documenting that honestly, since raw outputs could not be recreated) and 11 majors, and the fixes landed in the repo with regression tests. Those counts come from the lead agent's own deduplicated list, not an independently re-audited record.

`qa-panel/perspectives.json` holds the 25 lenses recovered from that run's delegation commands (reviewers R1 to R25). Lens names and focus text are condensed from those prompts, not verbatim, and the wave names were written afterwards. Five lenses are specific to this repo (host install flows, benchmark reproducibility, localization); swap them for your codebase. `qa-panel/optional-lenses.json` adds a UI anti-slop lens that was NOT part of the original run (`--with-optional`). The tooling in this directory was added afterwards and has been tested only with offline unit tests and synthetic example reports. No claim is made that 25 agents find more bugs than fewer, and no detection-rate numbers are given.

## Files

| Path | Purpose |
| --- | --- |
| `qa-panel/perspectives.json` | The 25 lenses recovered from the original run, 5 waves |
| `qa-panel/optional-lenses.json` | Added UI anti-slop lens (not in the original run) |
| `qa-panel/agent-brief.md` | Brief template, one per agent |
| `qa-panel/orchestration.md` | Step by step wave procedure |
| `qa-panel/examples/` | Synthetic reports and a consolidated example; not real findings |
| `qa_panel.py`, `agnes_kit/qa_panel.py` | Offline CLI: `render`, `consolidate`, `gate` |
| `tests/test_qa_panel.py` | Tests for the above |

Phase-by-phase retrieval: `python3 route.py --task qa-panel --phase <freeze|render|run|collect|consolidate|triage|fix|gate>` (see `docs/routing.md`).

## Waves

1. Security, correctness, host install flows. 2. MCP server, ACP/plugin claims, prompt quality, test suite, docs accuracy. 3. License, benchmark reproducibility, portability, misuse, localization. 4. Git hygiene, dependencies, privacy, failure modes, API contract. 5. Onboarding, dead code, performance, docs clarity, release readiness. Lenses that do not apply to your codebase should report "not applicable" with evidence, or be swapped for one that fits.

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
