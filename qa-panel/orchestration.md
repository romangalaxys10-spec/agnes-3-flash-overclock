# Running the panel (wave orchestration)

A procedure for humans or an orchestrating agent. The repo does not launch agents; you need an environment that can run independent agents (separate sessions or processes). Each phase below is its own section so the router (`docs/routing.md`) can hand out one phase at a time.

## Phase: freeze

Pick the commit under review and record its full SHA. Tests must pass on it first (`python3 -m unittest discover -s tests`). Nothing merges to that branch during the run.

## Phase: render

`python3 qa_panel.py render --base-sha <sha> --repo-url <url> --out /tmp/qa/briefs` writes 25 briefs, one per lens.

## Phase: run

Run in 5 waves of 5. Start wave 1's five agents, wait for their reports, then wave 2, and so on. Waves are a pacing and rate-limit choice; agents must still not see each other's output. Each agent gets only its own brief and a fresh clone at the frozen SHA. An agent with no findings still files a report with an empty list.

## Phase: collect

Save each agent's JSON as `/tmp/qa/reports/<agent_id>.json`.

## Phase: consolidate

`python3 qa_panel.py consolidate --reports /tmp/qa/reports --base-sha <sha> --out /tmp/qa/out`. Reports with a wrong SHA, unknown agent or bad shape are rejected (exit 2) rather than silently dropped. Merging is by file plus title-word overlap; a lead must read `report.md` and split or merge by hand where the heuristic is wrong.

## Phase: triage

The lead sets each issue's `status` in `issues.json`: `fixed` (needs `fix_commit` and `verification`), `wontfix` or `invalid` (need `reason`). Reproduce every blocker and major before fixing; some findings are false.

## Phase: fix

Fix on a branch, add a regression test per real bug, rerun the full suite. Note the new SHA in each issue's `fix_commit`.

## Phase: gate

`python3 qa_panel.py gate --issues /tmp/qa/out/issues.json` exits 0 only if all 25 agents reported and no blocker or major is open. `--allow-partial` skips the completeness check; do not call a partial run a 25-agent panel. After large fixes, optionally rerun the affected waves against the new SHA.

## What the gate does not prove

It checks bookkeeping. It cannot tell whether agents were truly independent, whether findings are correct, or whether fixes are good. Keep the human triage step.
