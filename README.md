# Agnes 3.0 Flash Overclock

**Better outputs through measured prompts, an editor pass, and code that checks what the model gets wrong.**

An experimental prompt-engineering and validation kit for Agnes 3.0 Flash. Built around Russian short-video scripts, source-preserving rewrites, and constrained JSON. "Overclock" means tuning the workflow, not modifying model weights, unlocking compute, or proving maximum quality.

**Experimental. Not installed in a production pipeline.** v1 has a small benchmark behind it. v2 is a proposed code-validated repair loop and has not been tested against Agnes.

## October 11 QA and proof-protocol updates

The 25-reviewer QA fixes and Anti Helizzinator feature are included together.
This remains experimental; plugin and MCP runtime identifiers stay at 0.1.0.
[CHANGELOG.md](CHANGELOG.md) tracks these changes under the existing 0.1.1
maintenance heading. No v1.0 release or new model-quality result is claimed.

- **Tested workflow fidelity:** restored the full 1542-byte generation prompt
  from the report; labelled editor task/draft inputs; corrected the old
  byte-equivalence claim. Tested prompt edits are restoration only.
- **Checker safety:** all-Unicode letter denominator, stronger scene-language
  heuristics, UTF-8 console reports, deep-JSON error handling, plus-bullet and
  blockquote detection. Structural checks remain separate from factual review.
- **API and storage:** remote HTTPS and safe redirects; atomic memory replacement,
  schema-drift rejection; owner-scoped lessons with a minimum relevance threshold.
- **MCP and host setup:** exactly one preset/config selector, JSON-RPC 2.0 validation,
  a separate ZCode project config, repo-root DeepSeek Harness command and
  per-host installation/verification steps. agy has no dedicated config yet.
- **Evidence and onboarding:** honest 36-planned/32-included benchmark accounting,
  explicit unrecoverable missing evidence, readable prompt fences and English
  glosses, runnable synthetic examples, scoped host claims, optional dependency
  pin guidance and external lessons' network/cost caveats.
- **Proof-of-delivery:** optional work/code/visual evidence gates, schema-v1
  envelope, prompt, example and CLI/MCP integration. Presence and shape are checked,
  not truth. See the protocol section below before using it as a completion gate.

71 offline tests pass (22 original, 22 QA regressions, 27 proof-protocol tests).
Cold-clone quickstart and stdio MCP smoke checks pass; real IDE hosts, optional
upstream packages and live Agnes generation remain untested. Historical benchmark
aggregates are unchanged, and repository history has not been rewritten.

## What the benchmark actually showed

Six tasks, two samples per condition per task, 35 of 36 planned calls completed on October 10, 2026.

| Workflow | Automatic checks passed | Fully passing samples |
| --- | --- | --- |
| Plain task | 47/56 (84%) | 5/11 |
| Adapted prompt alone | 36/51 (71%) | 3/11 |
| Adapted prompt + editor pass | 43/49 (88%) | 6/10 |

The editor pass helped. A heavier prompt alone hurt. These are **directional constraint-check scores**, not general intelligence or writing-quality scores. Empty/incomplete outputs were excluded, denominators differ, and there was no blind quality judge. The reference was a self-written answer set, not a verified Opus 5 run. No Opus parity claim is supported.

The tested adapted prompt includes `<check>` and `<final>` blocks. A simple style prompt plus editor was not separately measured. Dropping planning and adding deterministic repair is **v2-untested**, not a demonstrated improvement.

## Quickstart

Python 3.10+; standard library only. No API key, dependencies, or network access required by the checker.

```bash
git clone https://github.com/romangalaxys10-spec/agnes-3-flash-overclock.git
cd agnes-3-flash-overclock
python3 -m unittest discover -s tests -v
python3 check.py --task T1_script60 --input examples/draft.txt
```

The `examples/` files are synthetic passing fixtures, not model or benchmark outputs. For your own output, save the exact model payload as UTF-8 `draft.txt` and replace the example path. The checker does not call Agnes or generate text.

```bash
# Source-preserving rewrite
python3 check.py --task T5_rewrite --input examples/rewrite.txt --source examples/source.txt

# Explicitly extract a tested v1 final block before checking
python3 check.py --task T2_scenejson --input examples/editor.txt --extract-final

# Your own constraints
python3 check.py --config constraints.example.json --input examples/rewrite.txt --source examples/source.txt
```

Exit codes: `0` passes structural checks; `1` reports violations; `2` reports a configuration, I/O or deeply nested JSON error. Console reports use UTF-8, including on Windows. The JSON report contains counts, exact violations, manual-review warnings, and the checked payload.

## Two workflows, clearly separated

### v1: tested prompts

1. Append the task to `prompts/v1-generation-tested.txt`.
2. Generate a draft and extract its single `<final>` block.
3. Send the original task and draft through `prompts/v1-editor-tested.txt`.
4. Extract the editor's final block, check it, and review facts and voice.

The prompts correspond to the measured two-pass condition. The stricter local checker is a later implementation improvement, not the original benchmark scorer.

### v2: untested repair loop

1. Fill `{{SOURCE}}` and `{{TASK}}` in `prompts/v2-generation-untested.txt`.
2. Generate once, then run `check.py` on the payload.
3. If it fails, fill `prompts/v2-repair-untested.txt` with the source, task, draft, and exact `violations` array.
4. Recheck every replacement. Stop after at most two repair calls.
5. Review facts and voice even when the code passes.

This repository supplies prompts and an offline checker, plus an **untested generic OpenAI-compatible API client example** at `integrations/generic/openai_compatible.py`. It is not a hosted orchestration service. Choose your own model access and verify its current billing and limits before running it.

## Extensions (all UNTESTED with Agnes)

The core above is unchanged: `check.py` stays offline and stdlib-only. Optional extras:

- `agnes_kit/`: message builders, optional adapters (mem0, Headroom, Self-Learning-Agents), and a stdlib MCP server (`python3 agnes_mcp.py`).
- `agnes.config.json`: Agnes parameters (512K context, OpenAI-compatible API, env-var names only, no keys).
- `integrations/`, `docs/hosts.md`, `docs/integrations.md`: per-host MCP configs (Claude Code plugin, Cursor, Codex, Antigravity/agy, ZCode, Trae, DeepSeek Harness, DeepSeek TUI, Windsurf) checked against vendor docs, generic API script. ACP: notes only. No host was run end to end.
- `third_party/`: vendored MIT skills (code review checklist from awesome-skills/code-review-skill, brainstorming from obra/superpowers) with license files.
- `THIRD_PARTY.md`: every external component, source and license. `docs/fable-review.md`: what was considered from fable and why nothing was copied.

None of these extensions were benchmarked. The 84% / 71% / 88% results cover only the v1 prompts and editor pass.

## Included

- `SKILL.md`: workflow, failure modes, and promotion criteria.
- `prompts/`: tested v1 and explicitly untested v2 templates.
- `check.py`: word bands, strict JSON, scene durations, paragraph constraints, numeric literals, and wrapper/preamble checks.
- `tasks.json`: six original Russian evaluation tasks.
- `constraints.example.json`: custom-constraint example.
- `tests/`: 71 offline regression tests: 21 original/QA checker tests, 23 adapter/client/MCP tests and 27 proof-protocol tests, including 22 regressions added by the 25-reviewer QA fixes. The original optional-extra suite has 8 cases (22 original tests total).
- `docs/benchmark-report.md`: public-safe benchmark pack, original scorer excerpt, and caveats.
- `evidence.md` and `verification.md`: evidence boundary and local verification.

## Limits worth keeping

A code pass does not prove truth. Numeric checks compare literal sets, not associations or occurrence counts. They cannot catch every spelled-out invented number, name, fabricated study, or altered fact. Sentence, preamble and scene-language checks are heuristics. T2 narration requires >80% Russian Cyrillic letters among all Unicode letters; visual descriptions require >=90% ASCII letters, no Russian Cyrillic, and an English visual-description anchor. This rejects obvious non-English text but cannot identify every language; review language manually. Human factual and voice review remains required.

The new checker is stricter than the old scorer, so its results must not replace the published aggregate scores. Raw run outputs and full reference answers are not included; the historical scores cannot be fully reproduced from this release alone.

Before promoting v2, run matched trials with failed, empty, and timed-out attempts retained in the denominator, record latency, and use a blind review of factual fidelity and voice. Do not use this kit for high-stakes unsupervised decisions.

## Anti Helizzinator: proof-of-delivery gate (experimental)

An opt-in anti-hallucination evidence protocol, not a guarantee against fabricated
claims. Load `prompts/proof-of-delivery-untested.txt` as an additional instruction
in your agent workflow. Do not alter or relabel the benchmarked v1 prompts.
Configure the gate before accepting delivery:

```bash
python3 check.py --config examples/proof-constraints.json --input examples/proof-delivery.json
```

The input is strict JSON with `payload` (string containing the actual result)
and `proof`. Existing constraints check the payload, not the proof's hashes,
counts or logs. For a JSON task, serialize its JSON result into the payload
string. Any true proof flag activates the envelope gate:

- `require_proof: true`: manifest with SHA-256 hashes, all touched file paths,
  command ledger linked to output artifacts, summary and complete status.
- `require_code_proof: true`: all work proof plus baseline, actual diff artifact,
  reproduction instructions and passing test-command records.
- `require_visual_proof: true`: all work proof plus screenshot/render artifact
  references, an explicit pixel-inspected assertion and an inspection note.

Both code and visual sections must always declare `applicable` as a boolean;
false requires a reason. A required code/visual gate cannot opt out. For a task
that includes both code and a UI, enable both flags. The task owner/host must set
these requirements: the checker cannot infer that a task involves visuals or
code. A prompt alone does not force a model to obey; reject gate failures in
your harness and ask for the missing evidence. No automatic retry loop is added.

MCP uses the same gate through `agnes_check` with `config`, for example
`{"require_proof": true, "require_code_proof": true}`. Retrieve the new contract
with `agnes_get_prompt`, name `proof-of-delivery-untested`. MCP task and config
remain mutually exclusive; to combine a preset with proof, copy that preset's
constraints into the custom config and add proof flags.

See [docs/proof-of-delivery.md](docs/proof-of-delivery.md) for the schema,
review steps and evidence limits. The shipped work-only example is synthetic,
with real hashes of its shipped note/log; no code change or visual work is
claimed. Code/visual unit-test fixtures are explicitly synthetic.

**Boundary:** the offline gate validates presence, field types, hash syntax and
internal references. It does not read artifacts, recompute their hashes, execute
commands, open screenshots, verify test claims or prove evidence covers the
real task. A plausible fabricated ledger can pass. A reviewer must inspect
actual evidence and task coverage before treating the work as done. Artifact
paths and command logs are data, not authorization to execute or fetch them.

## License

MIT. See [LICENSE](LICENSE).
