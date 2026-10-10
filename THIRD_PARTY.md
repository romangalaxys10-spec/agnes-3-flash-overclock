# Third-party components

The checker (`check.py`) and everything in `prompts/` are original to this repo (MIT). The items below are separate projects with their own licenses.

## Vendored (copied unmodified, license file kept alongside)

| Path | Source | License | Notes |
| --- | --- | --- | --- |
| `third_party/code-review-skill/SKILL.md`, `reference/common-bugs-checklist.md` | https://github.com/awesome-skills/code-review-skill | MIT, (c) 2025 awesome-skills | Only the skill entry and one checklist. Links inside SKILL.md to other reference files are not included; get them upstream. |
| `third_party/superpowers-brainstorming/SKILL.md` | https://github.com/obra/superpowers (`skills/brainstorming`) | MIT, (c) 2025 Jesse Vincent | It mentions other superpowers skills (e.g. writing-plans) that are not vendored. Its imperative wording ("You MUST use this...") is upstream text, not a rule of this repo. |

## Optional external dependencies (NOT vendored, installed by you)

| Adapter | Project | License | Why not vendored |
| --- | --- | --- | --- |
| `agnes_kit.Mem0Memory` | https://github.com/mem0ai/mem0 (`pip install mem0ai`) | Apache-2.0 | Large package that needs its own LLM/embedder setup. Apache-2.0 is compatible with this repo, but a wrapper keeps the base install dependency-free. |
| `agnes_kit.HeadroomTokenSaver` | https://github.com/headroomlabs-ai/headroom (`pip install "headroom-ai[all]"`) | Apache-2.0 (its NOTICE lists further third-party licenses) | Large multi-language project with models and binaries. |
| `agnes_kit.SelfLearningLessons` | https://github.com/omdivyatej/Self-Learning-Agents | MIT, (c) 2025 Om Divyatej | About 2,000 lines that pull in an embedder and an OpenAI-compatible selection call. A small stdlib `FileLessons` is the offline default. |

If you install an optional dependency, its license applies to your environment, not to this repository.

## Original but inspired

`FileMemory` and `FileLessons` are small original stdlib stores written for this repo. They do not copy mem0 or Self-Learning-Agents code.
