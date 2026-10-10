"""Adapters behind small interfaces. Third-party packages are imported only
when the adapter is constructed, so the base install needs nothing.

Interfaces (duck-typed):
  token saver : compress(messages) -> messages
  memory      : add(text, user_id) -> None ; search(query, user_id, top_k) -> list[str]
  lessons     : save(task, feedback) -> None ; relevant(task, max_items) -> list[str]
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: str | Path | None = None) -> dict:
    p = Path(path) if path else ROOT / "agnes.config.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _words(text: str) -> set[str]:
    return set(re.findall(r"\w{3,}", text.lower()))


def _overlap(a: str, b: str) -> float:
    wa, wb = _words(a), _words(b)
    return len(wa & wb) / max(1, len(wa | wb))


# ---- token saver (Headroom, Apache-2.0, optional external dependency) ----

class NullTokenSaver:
    def compress(self, messages: list[dict]) -> list[dict]:
        return messages


class HeadroomTokenSaver:
    """Wraps `headroom.compress` (pip install headroom-ai). Not vendored."""

    def __init__(self, model: str = "agnes-3.0-flash", model_limit: int = 524288):
        try:
            from headroom import compress  # type: ignore
        except ImportError as exc:
            raise RuntimeError('Install the optional dependency: pip install "headroom-ai[all]"') from exc
        self._compress, self.model, self.model_limit = compress, model, model_limit

    def compress(self, messages: list[dict]) -> list[dict]:
        return self._compress(messages, model=self.model, model_limit=self.model_limit).messages


# ---- memory (mem0, Apache-2.0, optional external dependency) ----

class FileMemory:
    """Stdlib JSON memory with word-overlap ranking. Default, offline."""

    def __init__(self, path: str | Path = "memory_store.json"):
        self.path = Path(path)

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text("utf-8"))
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise ValueError(f"{self.path} is not valid JSON; fix or delete it") from exc
        return data if isinstance(data, list) else []

    def add(self, text: str, user_id: str = "default") -> None:
        items = self._load()
        items.append({"user_id": user_id, "text": text})
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=1), "utf-8")

    def search(self, query: str, user_id: str = "default", top_k: int = 3) -> list[str]:
        scored = [(_overlap(query, i["text"]), i["text"]) for i in self._load() if i["user_id"] == user_id]
        return [t for s, t in sorted(scored, reverse=True) if s > 0][:top_k]


class Mem0Memory:
    """Wraps mem0's `Memory` (pip install mem0ai). Not vendored.
    mem0 needs its own LLM/embedder configuration; see its docs."""

    def __init__(self, **memory_kwargs):
        try:
            from mem0 import Memory  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install the optional dependency: pip install mem0ai") from exc
        self._m = Memory(**memory_kwargs) if memory_kwargs else Memory()

    def add(self, text: str, user_id: str = "default") -> None:
        self._m.add([{"role": "user", "content": text}], user_id=user_id)

    def search(self, query: str, user_id: str = "default", top_k: int = 3) -> list[str]:
        res = self._m.search(query=query, filters={"user_id": user_id}, top_k=top_k)
        rows = res.get("results", []) if isinstance(res, dict) else res
        return [r.get("memory", "") for r in rows if r.get("memory")]


# ---- lessons / self-improvement (Self-Learning-Agents, MIT, optional) ----

class FileLessons:
    """Stdlib store of human-written feedback on past tasks. Default, offline."""

    def __init__(self, path: str | Path = "lessons.json"):
        self._mem = FileMemory(path)

    def save(self, task: str, feedback: str) -> None:
        self._mem.add(json.dumps({"task": task, "feedback": feedback}, ensure_ascii=False))

    def relevant(self, task: str, max_items: int = 2) -> list[str]:
        out = []
        for raw in self._mem._load():
            d = json.loads(raw["text"])
            out.append((_overlap(task, d["task"]), d["feedback"]))
        return [f for s, f in sorted(out, reverse=True) if s > 0][:max_items]


class SelfLearningLessons:
    """Wraps dead_simple_self_learning.SelfLearner (pip install from
    https://github.com/omdivyatej/Self-Learning-Agents). Not vendored.
    Its default feedback-selection layer calls an OpenAI-compatible LLM
    and its default embedder downloads a model: configure before use."""

    def __init__(self, **learner_kwargs):
        try:
            from dead_simple_self_learning import SelfLearner  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install the optional dependency from the Self-Learning-Agents repo") from exc
        self._l = SelfLearner(**learner_kwargs)

    def save(self, task: str, feedback: str) -> None:
        self._l.save_feedback(task, feedback)

    def relevant(self, task: str, max_items: int = 2) -> list[str]:
        # Formatter returns only the selected feedback, so an empty base prompt
        # yields "" when nothing matched.
        self._l.set_feedback_formatter(lambda base, fb: fb)
        out = (self._l.apply_feedback(task, "") or "").strip()
        return [out][:max_items] if out else []
