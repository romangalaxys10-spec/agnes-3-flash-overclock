# Review of romangalaxys10-spec/fable for embedding

Read on 2026-10-10 at commit 963e824. Fable is a large QA/agent-skills plugin (28 skills, TypeScript server, vendored third-party folders).

## Embedded

Nothing was copied from fable.

## Why

- The repo has no `LICENSE` file at its root, although the README says MIT. Several folders under `vendor/` are third-party and one is listed as CC-BY-NC 4.0 (non-commercial, incompatible with MIT redistribution).
- Where fable vendors Headroom, Self-Learning-Agents and superpowers, this repo uses the upstream projects directly instead, so licenses and attribution trace to the real source.
- Fable's `speed-prompt` and "smart protocol" are heavy prompts. This repo's own benchmark found a heavier prompt alone scored worse (71%) than the plain task (84%), so they were not added without evidence.

## Candidates worth a later, separate evaluation

| Candidate | Fit | Blocker |
| --- | --- | --- |
| `skills/stop-slop` (writing-quality rubric) | Could become extra checker rules for Russian scripts | Upstream license not confirmed |
| `vendor/sec-scan`, `vendor/seo-geo` | None: unrelated to Agnes script work | n/a |
| `docs/self-healing.md` tiers | Idea parallel to the v2 repair loop | Design doc only; adopt as a concept if tested |

Add a root `LICENSE` to fable before anything is lifted from it.
