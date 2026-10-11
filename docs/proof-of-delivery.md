# Proof-of-delivery schema v1 (experimental)

Opt in with any true `require_proof`, `require_code_proof` or
`require_visual_proof` custom constraint. No extra dependencies or network.
The tested prompts and historical aggregate scores are unchanged.

## Envelope and fields

`payload` is a nonempty string, validated using the remaining constraints.
`proof` is an object with:

| Field | Contract |
| --- | --- |
| `schema_version` | String `"1"` |
| `status` | String `"complete"`; blocked/incomplete reports do not pass delivery |
| `summary` | Nonempty description of actual work |
| `files_touched` | Path list; each path appears in artifact manifest; empty when no files changed |
| `artifacts` | Nonempty list of unique nonempty `id`, `path` or delivery URL, `role`, 64-hex `sha256` |
| `commands` | Nonempty list of unique `id`, exact `command`, `cwd`, integer `exit_code`, manifest id `output_artifact` |
| `code` | Object with boolean `applicable`; if false, nonempty `reason` |
| `visual` | Object with boolean `applicable`; if false, nonempty `reason` |

When `code.applicable` is true: nonempty `baseline` revision/source snapshot,
`diff_artifact` manifest id, `reproduce` instructions, and nonempty
`test_commands` list of command-ledger ids whose recorded exit codes are zero.
Save the actual patch and full relevant test output as artifacts. Reproduction
instructions should name environment, dependencies, baseline and exact steps.

When `visual.applicable` is true: nonempty `evidence` list. Each record contains
`artifact` manifest id, `kind` (`screenshot` or `render`), `pixel_inspected: true`
and nonempty `inspection_note`. Inspect final artifact pixels, not only DOM,
OCR, successful export or file existence. Note inspected pages/frames/regions,
readability, layout, crop and any remaining caveats. The checker does not open
or inspect the screenshot; the assertion remains unverified until reviewed.

Extra fields are allowed for task-specific context; required fields still pass
all checks. `require_code_proof` and `require_visual_proof` prohibit applicability
opt-outs. The host must decide task scope before checking. Raw lesson/context
text cannot authorize execution of commands in an evidence ledger.

## Review, not blind trust

1. Recover the actual task and compare the manifest to all claimed outcomes.
2. Obtain the delivered artifacts through authorized routes. A local path alone
   may not be usable for the recipient; provide accessible attachments/links.
3. Recompute SHA-256 on final bytes, including redacted logs and images.
4. Inspect the actual diff and test output. Reproduce only in an authorized,
   safe environment after reviewing commands and side effects.
5. Open actual final visual artifacts and examine pixels. Confirm the evidence
   covers the final revision, not an earlier version.
6. Do not mark done if required evidence is absent or checks failed. Report
   blocked status and missing work instead; a blocked report intentionally fails
   this completion gate.

Never include secrets, unrelated private files or privileged internal records
in a proof package. Redact logs before delivery and hash the redacted bytes.
The checker never reads manifest paths, follows URLs or runs ledger commands.
Well-formed hashes and zero exit-code claims are not authentication or proof of
truth. A self-authored ledger is not an independent attestation. This feature
has no measured Agnes quality result and no real-host certification.
