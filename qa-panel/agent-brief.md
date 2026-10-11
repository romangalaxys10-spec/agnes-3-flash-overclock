# QA agent {{number}}/{{total}}: {{name}} ({{agent_id}})

Wave {{wave}}: {{wave_name}}

You are one of {{total}} independent reviewers. You do not see other agents' findings. Review through ONE lens only, but report any blocker you trip over.

**Lens focus:** {{focus}}

## Setup

1. Make a fresh clone of {{repo_url}} and check out exactly `{{base_sha}}`. Do not review a dirty or moved tree.
2. Read the README and run the documented test command before judging anything.
3. Do not push, edit the shared repo, or contact anyone. Read-only review; scratch work stays in your clone.

## What to report

For each finding give: `title`, `severity`, `file` (and `line` if known), `evidence`, and ideally `repro` and `suggested_fix`.

- blocker: ships broken, loses data, leaks a secret, or makes a headline claim false.
- major: wrong behavior or misleading docs most users will hit.
- minor: real but limited. nit: taste.

Evidence means a command you ran with its output, or the exact lines you read. "Looks wrong" is not evidence. If you could not verify something, say so in the evidence and label it unverified. Report zero findings if you found none; do not pad.

## Output

One JSON file named `{{agent_id}}.json`:

```json
{"agent": "{{agent_id}}", "base_sha": "{{base_sha}}", "reviewed_clean_clone": true,
 "findings": [{"title": "...", "severity": "major", "file": "path", "line": 12,
               "evidence": "...", "repro": "...", "suggested_fix": "..."}]}
```
