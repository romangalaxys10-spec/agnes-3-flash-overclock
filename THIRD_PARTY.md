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


## Optional dependency version policy

No minimum compatible release has been validated for these optional adapters.
Do not read unversioned `pip install` examples as a tested compatibility promise.
Before adoption, test the upstream API used by the adapter in a disposable
Python 3.10+ environment, then pin the working release and lock transitive
versions (`pip freeze` or your package manager's lock file).

- mem0ai: needs `Memory.add` and `Memory.search(query=..., filters=..., top_k=...)`;
  pin `mem0ai==<validated-version>` after checking that signature.
- headroom-ai: needs `headroom.compress(messages, model=..., model_limit=...)`
  returning an object with `.messages`; pin `headroom-ai[all]==<validated-version>`.
- Self-Learning-Agents: needs `SelfLearner`, `save_feedback`,
  `set_feedback_formatter` and `apply_feedback`; pin an exact upstream commit
  rather than a moving Git branch. No compatible commit is certified here.

The placeholders above are pin guidance, not installable requirements or
invented minimum versions. Update this file with exact versions only after
adapter integration tests against those dependencies pass. Offline tests cover
missing-dependency errors, not optional upstream integration compatibility.
