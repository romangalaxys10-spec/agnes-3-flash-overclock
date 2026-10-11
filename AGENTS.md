# Agent instructions

This repo is an Agnes 3.0 Flash prompt and validation kit. See `SKILL.md` for the workflow.
Run tests with `python3 -m unittest discover -s tests`. `check.py` must stay offline and stdlib-only.
Everything beyond the tested v1 prompts is labeled UNTESTED; do not add benchmark numbers without running them.

Do not load the whole repo into context. Use `python3 route.py --task <task> --phase <phase>` (see `docs/routing.md`) to fetch only the guidance for your current phase.
