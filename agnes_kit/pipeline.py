"""Message builders. They only assemble messages; they never call a model.
The tested v1 prompts are used verbatim. Everything extra is optional and UNTESTED."""
from __future__ import annotations

import re

from .adapters import ROOT

TP = ROOT / "third_party"


def load_skill(name: str) -> str:
    """Return a vendored skill body (frontmatter stripped). Names:
    'superpowers-brainstorming', 'code-review-skill'."""
    text = (TP / name / "SKILL.md").read_text("utf-8")
    return re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()


def build_generation_messages(task: str, *, memories=(), lessons=(), lesson_store=None, user_id="default", token_saver=None) -> list[dict]:
    """v1 generation prompt + task. Memories/lessons are appended as a labeled
    block only when given (UNTESTED: the measured v1 had none)."""
    if lesson_store is not None:
        if lessons:
            raise ValueError("provide explicit lessons or lesson_store, not both")
        lessons = lesson_store.relevant(task, user_id=user_id)
    system = (ROOT / "prompts" / "v1-generation-tested.txt").read_text("utf-8")
    extra = []
    if memories:
        extra.append("Relevant memory (may be stale, do not invent beyond it):\n" + "\n".join(f"- {m}" for m in memories))
    if lessons:
        extra.append("Past feedback on similar tasks:\n" + "\n".join(f"- {m}" for m in lessons))
    user = task + ("\n\n" + "\n\n".join(extra) if extra else "")
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    return token_saver.compress(msgs) if token_saver else msgs


def review_messages(diff: str, *, language_note: str = "") -> list[dict]:
    """Code-review request using the vendored checklist (UNTESTED on Agnes).
    Output is advisory; run the project's tests regardless."""
    checklist = (TP / "code-review-skill" / "reference" / "common-bugs-checklist.md").read_text("utf-8")
    system = (
        "You review code changes. Use the checklist below. Report only issues you can point to "
        "in the diff, with file and line, ordered by severity. Say 'no issues found' if none.\n\n"
        + checklist
    )
    return [{"role": "system", "content": system},
            {"role": "user", "content": (language_note + "\n\n" if language_note else "") + diff}]
